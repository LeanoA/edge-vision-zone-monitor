# ADR-010: Doble Horizonte Temporal de Latencia en Edge AI Industrial (ISO 13855 / IEC 61496)

- **Estatus:** Aceptado
- **Fecha:** 2026-08-31
- **Módulos Asociados:** `src/pipeline/safety_pipeline.py`, `src/core/spatial_fsm.py`, `scripts/run_demo.py`, `scripts/benchmark.py`
- **Estándares Aplicables:** ISO 13855:2024 (Safety Distances & Overall Stopping Performance), IEC 61496 (VBPDs), IEC 61508 (SIL 2/3)

---

## 1. Contexto y Planteamiento del Problema

En aplicaciones de visión por computador para seguridad industrial y Edge AI, la métrica de rendimiento típicamente reportada en la literatura es la latencia de inferencia de la red neuronal ($T_{\text{infer}}$) o la tasa de cuadros por segundo ($\text{FPS}$).

Sin embargo, en sistemas de protección funcional certificados bajo **ISO 13855:2024**, la distancia de separación de seguridad requerida se rige por la ecuación:

$$S = K \cdot T + C = K \cdot (t_1 + t_2 + t_3) + C$$

Donde $t_1$ representa el tiempo de respuesta total del dispositivo sensor (VBPD).

### El Antipatrón: Conflación entre Throughput de Pipeline y Reacción del Evento Físico
Medir únicamente la latencia del fotograma dentro del pipeline ($T_{\text{system}}$) introduce dos errores de metrología críticos en planta:

1. **Omisión de la Latencia de Ingestión y Buffer ($T_{\text{capture}}$):**
   Los fotogramas capturados por sensores V4L2, MIPI-CSI o RTSP GStreamer pueden acumular retraso en colas del kernel del sistema operativo (*buffer bloat*), distorsionando el tiempo real de llegada de la imagen.
2. **Conflación de $T_{\text{pipeline}}$ con la Reacción del Evento ($T_{\text{event}}$):**
   Un pipeline que procesa a $15\text{ ms}$ ($66\text{ FPS}$) no detiene la máquina en $15\text{ ms}$ si implementa filtros de debounce temporal ($N_{\text{confirm}} = 3$ cuadros). A 30 FPS, la persona debe permanecer físicamente dentro de la zona durante 2 intervalos de cuadro adicionales ($\approx 66.7\text{ ms}$), haciendo que la latencia real del evento sea de $\approx 81.7\text{ ms}$.

---

## 2. Decisión Arquitectónica: Modelo de Doble Horizonte Temporal

Se implementa una arquitectura desacoplada de doble horizonte temporal para el perfilado de rendimiento en Edge AI:

```
════════════════════════════════════════════════════════════════════════════════
                        MODELO DE DOBLE HORIZONTE
════════════════════════════════════════════════════════════════════════════════

HORIZONTE 1: LATENCIA DE SISTEMA POR CUADRO (T_system)
┌───────────┐   ┌─────────────────────────────────────────────────────────┐
│ T_capture │ + │ T_pre + T_infer + T_pose + T_geom + T_track + T_fsm     │ = T_system
└───────────┘   └─────────────────────────────────────────────────────────┘
  (Buffer lag)                          (Pipeline T1)

HORIZONTE 2: LATENCIA DE REACCIÓN DEL EVENTO FÍSICO (T_event)
Entrada física en P_danger
(t = t_entry)
      │
      ▼
┌──────────────┐     ┌──────────────┐     ┌───────────────────┐
│ Frame 1      │ ──► │ Frame 2      │ ──► │ Frame N_confirm   │ ──► RELÉ ABIERTO (TRIP)
│ (t_entry)    │     │              │     │ (t_trip)          │     (t = t_trip)
└──────────────┘     └──────────────┘     └───────────────────┘
      │                                             ▲
      └────────────────── T_event ──────────────────┘
                 (t_trip - t_entry)
════════════════════════════════════════════════════════════════════════════════
```

### 1. Latencia de Sistema por Cuadro ($T_{\text{system}}$)
Mide la duración determinista de procesamiento de cada fotograma individual:
$$T_{\text{system}} = T_{\text{capture}} + T_{\text{pre}} + T_{\text{infer}} + T_{\text{pose}} + T_{\text{geom}} + T_{\text{track}} + T_{\text{fsm}}$$

### 2. Latencia de Reacción del Evento ($T_{\text{event}}$)
Mide el delta de tiempo físico continuo transcurrido desde el instante de la primera intrusión detectada en $P_{\text{danger}}$ ($t_{\text{entry}}$) hasta la confirmación y apertura del relé de parada (`trip = True` en $t_{\text{trip}}$):

$$T_{\text{event}} = t_{\text{trip}} - t_{\text{entry}}$$

* **En Aproximación Normal ($v_n < 1.6\text{ m/s}$):**
  $$T_{\text{event}} = (N_{\text{confirm}} - 1) \cdot \Delta t_{\text{frame}} + T_{\text{system}}$$
* **En Aproximación Rápida ($v_n \ge 1.6\text{ m/s}$ — Bypass ISO 13855):**
  $$T_{\text{event}} = 0 \cdot \Delta t_{\text{frame}} + T_{\text{system}} = T_{\text{system}}$$

---

## 3. Consecuencias y Beneficios

* **Cumplimiento Normativo Riguroso:** Proporciona los valores empíricos $t_1$ exactos requeridos por ISO 13855:2024 para el cálculo de distancias mínimas $S$.
* **Auditoría de Ingestión Edge AI:** Detecta saturación de buffer y pérdida de sincronismo en tiempo real.
* **Transparencia en Telemetría:** Cada evento de intrusión emitido en el stream JSONL incluye su `event_latency_ms` individual.
