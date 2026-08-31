# ADR-009: Desacoplamiento de Autómata Espacial y Clasificación Temporal de Dwell en Regiones Ortogonales (Statecharts)

- **Estatus:** Aceptado
- **Fecha:** 2026-08-31
- **Módulos Asociados:** `src/core/spatial_fsm.py`, `src/pipeline/safety_pipeline.py`, `src/utils/visualizer.py`
- **Estándares Aplicables:** ISO 13855:2024, ISO 13849-1 (PL d/e), IEC 61508 (SIL 2/3), Harel Statecharts (ISO/IEC 19501)

---

## 1. Contexto y Planteamiento del Defecto

En sistemas industriales de salvaguarda basados en visión por computador (VBPD - *Vision-Based Protective Devices*), la lógica de control debe responder simultáneamente a dos preguntas físicas fundamentales:

1. **Ocupación Espacial:** *¿Dónde se encuentra físicamente el trabajador respecto a los límites de la zona de peligro ($P_{\text{danger}}$), la banda de histéresis ($\Delta d$) y su vector cinemático ($\vec{v}$)?*
2. **Permanencia Temporal (*Dwell Time*):** *¿Cuánto tiempo lleva el trabajador presente de forma ininterrumpida dentro de la zona restringida?*

### El Antipatrón: Conflación de Estados en una FSM Plana
En implementaciones iniciales, estos dos dominios ortogonales se aplanaron en un único enum lineal:
```
OUTSIDE ──► ENTER_PENDING ──► INTRUSION_ACTIVE ──► DWELL_WARNING ──► DWELL_VIOLATION ──► EXIT_PENDING
```

Este diseño genera tres defectos arquitectónicos graves:

1. **Conflación de Disparadores (Triggers):**
   * Las transiciones espaciales son disparadas por observaciones métricas $(X_w, Y_w) \in \mathbb{R}^2$ y debounce discreto ($N_{\text{confirm}}, N_{\text{release}}$).
   * Las transiciones de *dwell* son disparadas por integración de tiempo continuo $t_{\text{dwell}} = \int dt$ condicionada a la presencia dentro de la zona.
2. **Ambigüedad en el Lazo de Seguridad:**
   * Un operario en `DWELL_WARNING` sigue estando físicamente en intrusión dentro de $P_{\text{danger}}$. Tratar `DWELL_WARNING` como un estado mutuamente excluyente de `INTRUSION_ACTIVE` confunde la semántica del relé de parada.
3. **Acoplamiento Rígido de Políticas:**
   * Modificar los umbrales de permanencia ($T_{\text{warn}}, T_{\text{violation}}$) o incorporar políticas de merodeo (*loitering*) multinivel forzaba a reescribir y re-validar la histéresis espacial y los contadores de debounce.

---

## 2. Decisión Arquitectónica: Descomposición en Regiones Ortogonales (Statecharts)

Se adopta el formalismo de **Statecharts de Harel** (regiones concurrentes ortogonales), donde el estado global del sistema es el producto cartesiano de dos autómatas desacoplados:

$$\mathcal{S}_{\text{global}} = \mathcal{S}_{\text{occupancy}} \times \mathcal{S}_{\text{dwell}}$$

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ REGION 1: AUTÓMATA DE OCUPACIÓN ESPACIAL (OccupancyState)                   │
│                                                                             │
│               [ OUTSIDE ] ◄─────────────────┐                               │
│                    │                        │                               │
│     (Punto dentro) │                        │ (N_release cuadros OBSERVED   │
│                    ▼                        │  fuera de P_release)          │
│            [ ENTER_PENDING ]                │                               │
│                    │                        │                               │
│ (N_confirm cuadros │                        │                               │
│  o vn >= 1.6 m/s)  ▼                        │                               │
│               [ INSIDE ] ──────────► [ EXIT_PENDING ]                       │
│              (trip=True)    (Punto fuera    │                               │
│                              de P_danger)   │                               │
└────────────────────┬────────────────────────┴───────────────────────────────┘
                     │ (Condición de guardia: Occupancy == INSIDE)
                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ REGION 2: CLASIFICADOR TEMPORAL DE PERMANENCIA (DwellState)                 │
│                                                                             │
│    (Occupancy != INSIDE) ──► [ NONE ] (Timer inactivo / reset a 0.0s)        │
│                                                                             │
│    [ NORMAL ] ──(t >= T_warn)──► [ WARNING ] ──(t >= T_violation)──► [ VIOLATION ] │
│   (0 <= t < T_warn)            (T_warn <= t < T_viol)           (t >= T_viol)│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Dinámica de Transición y Tablas de Verdad

### 3.1. Región 1: Estados de Ocupación Espacial (`OccupancyState`)
- **`OUTSIDE`:** Ningún track confirmado dentro de $P_{\text{danger}}$ ni en banda de histéresis $P_{\text{release}}$.
- **`ENTER_PENDING`:** Track detectado dentro de $P_{\text{danger}}$ con contador de confirmación $0 < n < N_{\text{confirm}}$ y velocidad normal $v_n < 1.6\text{ m/s}$.
- **`INSIDE`:** Incursión confirmada ($n \ge N_{\text{confirm}}$ o *bypass* cinemático por $v_n \ge 1.6\text{ m/s}$). **Abre contactores de seguridad (`trip=True`) inmediatamente ($t=0\text{ s}$).**
- **`EXIT_PENDING`:** Track previamente `INSIDE` que sale de $P_{\text{danger}}$ pero aún no completa $N_{\text{release}}$ cuadros estrictamente `OBSERVED` fuera de $P_{\text{release}}$.

### 3.2. Región 2: Estados de Permanencia Temporal (`DwellState`)
- **`NONE`:** Inactivo cuando `OccupancyState != INSIDE`.
- **`NORMAL`:** $0.0\text{ s} \le t_{\text{dwell}} < T_{\text{warn}}$ (presencia dentro del tiempo de ciclo permitido).
- **`WARNING`:** $T_{\text{warn}} \le t_{\text{dwell}} < T_{\text{violation}}$ (alerta de permanencia excesiva).
- **`VIOLATION`:** $t_{\text{dwell}} \ge T_{\text{violation}}$ (violación crítica de tiempo de permanencia).

---

## 4. Invariante de Seguridad Funcional (Fail-Safe Invariant)

$$\text{trip} = (\text{OccupancyState} == \text{INSIDE}) \lor \text{FAULT} \lor \text{LOCKOUT}$$

La parada de emergencia (`trip = True`) **NO espera a que el dwell timer alcance `WARNING` o `VIOLATION`**. El disparo ocurre en el instante $t = 0.0\text{ s}$ de la confirmación espacial de `INSIDE`. El estado de *dwell* actúa como un clasificador semántico y de diagnóstico operacional.

---

## 5. Consecuencias

* **Positivas:**
  * Separación total de responsabilidades entre geometría/cinemática y temporizadores.
  * Facilidad para reconfigurar tiempos de advertencia ($T_{\text{warn}}$) sin alterar el comportamiento de debounce espacial.
  * Claridad total en telemetría, visualización y auditoría funcional.
* **Neutras:**
  * Los consumidores de la API reciben `occupancy_state` y `dwell_state` en lugar de un único string.
