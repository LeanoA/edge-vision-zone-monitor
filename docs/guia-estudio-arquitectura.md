# Guía de Estudio: Arquitectura de Edge Safety Guard

> **Guía Técnica de Estudio & Fundamentos de Arquitectura**  
> *Diseño Guiado por la Física, Geometría Planar Proyectiva y Criterios de Seguridad Industrial (Basado en ISO 13855 / IEC 61496).*

> [!IMPORTANT]
> **Alcance y Fundamentación Normativa:**  
> Este desarrollo es un prototipo experimental de investigación aplicada y evaluación de arquitecturas Edge AI. Su diseño y presupuestos de tiempo están **basados en el modelo físico y razonamiento de distancias de separación de la norma ISO 13855:2024**, adoptando principios de diseño de IEC 61496 e ISO 13849-1. **No constituye un dispositivo de protección certificado (ESPE/VBPD)** ni debe utilizarse para el control directo de maquinaria peligrosa sin certificación formal de seguridad funcional (SIL / PL) y canales de hardware redundantes calificados.

---

## Filosofía Central y Primeros Principios

> **"No todos los problemas de un sistema de Inteligencia Artificial se resuelven con más Inteligencia Artificial."**

En el desarrollo contemporáneo de software y Edge AI, existe la tentación recurrente de tratar a las redes neuronales como una "caja negra" universal: pretender entrenar un modelo que prediga directamente si un operario "está cometiendo una infracción" o "cuánto tiempo lleva dentro de una zona de riesgo".

Ese enfoque es probabilístico, opaco, computacionalmente costoso y no verificable formalmente. Este proyecto adopta una arquitectura basada en primeros principios **(Concepts > Code)**, descomponiendo el problema en cuatro etapas ortogonales y deterministas:

1. **La IA se restringe a la Percepción Pura:** Detectar la ubicación de los tobillos anatómicos en píxeles.
2. **La Geometría resuelve el Espacio:** Transformación proyectiva homográfica $3 \times 3$ a coordenadas métricas reales ($Z_w = 0$).
3. **La Cinemática resuelve la Incertidumbre:** Filtro de Kalman 2D continuo con modelos de covarianza, compuertas de Mahalanobis y estados epistemológicos de observación.
4. **La Lógica Determinista toma las Decisiones:** Statecharts ortogonales concurrentes que evalúan topología espacial y permanencia temporal en menos de $0.05\text{ ms}$ de cómputo por cuadro.

---

## Arquitectura en Capas: El Flujo End-to-End

```
                    PERCEPTION
                         │
Camera frame ──► Pose inference (YOLO11-Pose ONNX / CoreML)
                         │
                         ▼
                 keypoint extraction (Tobillos 15 y 16)
                         │
                         ▼
                 ground-point estimate (Fallback a Bbox Bottom)
                         │
─────────────────────────┼────────────────────────────────────────
                    GEOMETRY
                         │
                         ▼
                   Homography (DLT 3x3, κ(H) < 10^6)
                         │
                         ▼
                 (X,Y) estimate [metros en piso físico]
                         │
─────────────────────────┼────────────────────────────────────────
                  STATE ESTIMATION
                         │
                         ▼
                Kalman Filter 2D (Velocidad Constante)
                         │
                         ▼
            filtered metric trajectory (OBSERVED / PREDICTED / STALE)
            + Mahalanobis χ² Gating + Hungarian Association
                         │
─────────────────────────┼────────────────────────────────────────
                 DECISION LOGIC
                         │
                         ▼
              Restricted zone test (Shapely Prepared Geometries)
                         │
                         ▼
                  Spatial FSM (OccupancyState: Schmitt Trigger)
                         │
                         ▼
                   Dwell timer (DwellState: t_dwell = ∫ dt)
                         │
─────────────────────────┼────────────────────────────────────────
                     OUTPUT
                         │
            events (JSONL) / overlay (Dual Perspective + BEV) / metrics

          ═══════════════════════════════════════════════════════
          PERFORMANCE PROFILER (Ortogonal)
          • T_capture : Latencia de buffer de hardware (V4L2 / RTSP)
          • T_system  : Latencia de procesamiento por fotograma (T1 ≈ 19ms)
          • T_event   : Latencia física real desde intrusión hasta disparo
          ═══════════════════════════════════════════════════════
```

---

## Mecanismos Clave de Seguridad y Lógica Industrial

### Schmitt Trigger Espacial y Asimetría ENTRY / EXIT ([ADR-004](decisions/adr-004-spatial-fsm-hysteresis.md), [ADR-006](decisions/adr-006-prepared-geometries-dynamic-debounce-bypass.md), [ADR-008](decisions/adr-008-kalman-epistemology-noise-divergence.md))

```
                      P_release (Límite de Liberación)
                   ┌───────────────────────────────────┐
                   │       Banda de Histéresis         │
                   │       (Δd = 200 mm)               │
                   │    P_danger (Límite de Peligro)   │
                   │   ┌───────────────────────────┐   │
                   │   │                           │   │
                   │   │          MÁQUINA          │   │
                   │   │                           │   │
                   │   └───────────────────────────┘   │
                   │                                   │
                   └───────────────────────────────────┘
```

* **El Problema del Chattering:** Un operario trabajando sobre la línea divisoria genera micro-oscilaciones de detección ($\approx \pm 15\text{ mm}$) debido al ruido estocástico de keypoints. Conmutar un relé a 30 Hz destruye contactores electromecánicos por fatiga térmica en pocas horas.
* **La Solución (Schmitt Trigger Espacial):** Se entra a zona de peligro al cruzar el polígono interior $P_{\text{danger}}$, pero no se desescala la alarma hasta que el sujeto cruza completamente el polígono exterior expandido:
  $$P_{\text{release}} = P_{\text{danger}} \oplus 0.20\text{ m}$$
* **Asimetría de Salvaguarda:**
  1. **ENTRY (Rápido y Conservador):**
     * Paso normal ($v_n < 1.6\text{ m/s}$): Debounce de confirmación de $N_{\text{confirm}} = 3$ cuadros.
     * Aproximación rápida ($v_n \ge 1.6\text{ m/s}$ — velocidad de aproximación humana según ISO 13855): **Bypass dinámico instantáneo ($N_{\text{confirm}} = 1$)** en el primer cuadro, sin esperar debounce.
  2. **EXIT (Histerético y Estricto):**
     * Exige $N_{\text{release}} = 5$ cuadros consecutivos fuera de $P_{\text{release}}$.
     * **Salvaguarda Asimétrica Fail-Safe:** Solo se permite desescalar si los cuadros provienen de observaciones ópticas frescas (`OBSERVED`). Si hay oclusión y el filtro de Kalman extrapola en `PREDICTED`, la salida se bloquea y el relé permanece en estado de disparo.

---

### Statecharts Ortogonales: Desacoplamiento Espacial y Temporal ([ADR-009](decisions/adr-009-decoupled-spatial-dwell-statecharts.md))

El estado del sistema se modela formalmente como el producto cartesiano de dos autómatas concurrentes e independientes:

$$\mathcal{S}_{\text{global}} = \mathcal{S}_{\text{occupancy}} \times \mathcal{S}_{\text{dwell}}$$

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. AUTÓMATA DE OCUPACIÓN ESPACIAL (OccupancyState)                          │
│    [ OUTSIDE ] ──► [ ENTER_PENDING ] ──► [ INSIDE ] ──► [ EXIT_PENDING ]     │
│                                        (trip=True)                          │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │ (Condición de guardia: INSIDE)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. CLASIFICADOR TEMPORAL DE PERMANENCIA (DwellState)                        │
│    [ NORMAL ] ──────(t >= Twarn)─────► [ WARNING ] ─────(t >= Tviol)─────► [ VIOLATION ] │
└─────────────────────────────────────────────────────────────────────────────┘
```

* **Invariante Fail-Safe:** La señal `trip = True` se dispara de inmediato en $t = 0.0\text{ s}$ ante la confirmación en `INSIDE`. El contador de permanencia (*dwell time*) no retarda la parada de seguridad; clasifica la gravedad operativa para auditoría e indicadores de planta.

---

### Doble Horizonte Temporal en Edge AI: $T_{\text{system}}$ vs $T_{\text{event}}$ ([ADR-010](decisions/adr-010-dual-latency-profiling-iso13855.md))

El sistema adopta el marco de cálculo de distancias de separación de la norma **ISO 13855:2024**:

$$S = (K \cdot T) + C + C_{\text{dyn}} + Z_{\text{extra}}$$

Donde el tiempo de respuesta total $T$ se desglosa en:
$$T = t_1 + t_2 + t_3$$

* $t_1$: Tiempo de respuesta del subsistema de visión (latencia de captura, inferencia y lógica).
* $t_2$: Tiempo de conmutación del actuador o relé de seguridad.
* $t_3$: Tiempo de frenado inercial de la máquina.

Para evaluar el subsistema de visión, se definen dos horizontes temporales desacoplados:

1. **Latencia de Hardware por Cuadro ($T_{\text{system}}$):**
   $$T_{\text{system}} = T_{\text{capture}} + T_{\text{pre}} + T_{\text{infer}} + T_{\text{pose}} + T_{\text{geom}} + T_{\text{track}} + T_{\text{fsm}}$$
   En hardware Edge de referencia (Apple Silicon CoreML / NVIDIA TensorRT INT8), $T_{\text{system}} \approx 18.5 - 20.5\text{ ms}$ por cuadro ($> 45\text{ FPS}$).
2. **Latencia de Reacción Física del Evento ($T_{\text{event}}$):**
   $$T_{\text{event}} = t_{\text{trip}} - t_{\text{physical-entry}}$$
   * *Aproximación normal:* $T_{\text{event}} = (N_{\text{confirm}} - 1) \cdot \Delta t_{\text{frame}} + T_{\text{system}} \approx 81.7\text{ ms}$ (a 30 FPS).
   * *Aproximación rápida ($v_n \ge 1.6\text{ m/s}$):* $T_{\text{event}} = T_{\text{system}} \approx 19\text{ ms}$, situándose dentro del presupuesto teórico $t_1 \le 50\text{ ms}$ recomendado por las directivas de seguridad.

---

### MOT Bayesiano y Asignación Combinatoria ([ADR-011](decisions/adr-011-mahalanobis-hungarian-mot.md))

Para resolver el seguimiento multiobjeto en presencia de cruces de operarios y detecciones redundantes:

1. **Compuerta de Mahalanobis $\chi^2_2(0.99) \le 9.210$:** Proyección de la covarianza de innovación que valida detecciones candidatas antes de la asociación:
   $$d_M^2 = (\mathbf{z} - \mathbf{H}\hat{\mathbf{x}}^-)^T \mathbf{S}^{-1} (\mathbf{z} - \mathbf{H}\hat{\mathbf{x}}^-) \le 9.210$$
   $$\mathbf{S} = \mathbf{H}\mathbf{P}^-\mathbf{H}^T + \mathbf{R}$$
   El elipsoide de búsqueda se ensancha longitudinalmente en la dirección del vector de velocidad $\vec{v}$, rechazando detecciones transversales o espurias.
2. **Asignación Global Húngara / Munkres:** Resuelve la asignación biyectiva óptima en $\mathcal{O}(N^3)$ en $0.017\text{ ms}$, eliminando permutaciones de ID durante cruces ocluidos.
3. **World-Space Spatial Birth NMS ($d_{\text{birth-min}} = 0.6\text{ m}$):** Supresión espacial métrica en el piso que evita duplicar identidades ante propuestas redundantes de la red neuronal.

---

### Cierre del Gap Sintético y Renderizado Pinhole ([ADR-012](decisions/adr-012-synthetic-yolo-video-generation.md), [Doc Técnico](data/synthetic_generation.md))

* **El Problema del Synthetic Domain Gap:** Las figuras geométricas 2D básicas (`cv2.line`/`cv2.rectangle`) provocan 0% de detección en detectores COCO por carecer de texturas, sombras y proporciones antropométricas realistas.
* **Solución Basada en Modelado Físico:**
  1. **Single-Identity Tracklet & Normalización:** Extracción continua de un sujeto en lienzo canónico ($160 \times 320\text{ RGBA}$) con alpha-feathering y sombra de contacto elíptica Gaussiana en el suelo.
  2. **Escala Pinhole Perspectiva:** Altura antropométrica modelada según óptica estenopeica:
     $$h(Y) = \frac{480}{1.0 + 0.165 \cdot Y}\text{ px}$$
     Mantiene al sujeto dentro del rango de resolución óptima ($h \in [240, 480]\text{ px}$).
  3. **Desacoplamiento de UI y Telemetría:** Reubicación de elementos gráficos de interfaz fuera del campo visual de la cámara ($y < 56\text{ px}$ y $y > 1040\text{ px}$), logrando **100% de detección** con confianza promedio de **0.835 - 0.861**.

---

## Catálogo Completo de Architecture Decision Records (ADRs)

| ADR | Documento | Decisión Arquitectónica & Fundamentación |
| :--- | :--- | :--- |
| **001** | [ADR-001](decisions/adr-001-yolo-pose-vs-bbox.md) | Keypoints de tobillos para anclaje físico al suelo inmune a posturas del torso o inclinaciones. |
| **002** | [ADR-002](decisions/adr-002-homography-vs-monocular-3d.md) | Mapeo proyectivo DLT $3 \times 3$ determinista en suelo ($Z_w=0$) en lugar de redes neuronales 3D pesadas. |
| **003** | [ADR-003](decisions/adr-003-onnx-runtime-coreml.md) | Inferencia desacoplada de PyTorch mediante ONNX Runtime (CoreML / INT8 TensorRT). |
| **004** | [ADR-004](decisions/adr-004-spatial-fsm-hysteresis.md) | Schmitt trigger espacial y filtrado cinemático contra el *chattering* en actuadores mecánicos. |
| **005** | [ADR-005](decisions/adr-005-homography-vectorization-geometric-validation.md) | Verificación matemática preventiva de colinealidad y condicionamiento numérico $\kappa(H) < 10^6$. |
| **006** | [ADR-006](decisions/adr-006-prepared-geometries-dynamic-debounce-bypass.md) | Micro-optimizaciones GEOS (C) y bypass instantáneo por vector de aproximación $v_n \ge 1.6\text{ m/s}$. |
| **007** | [ADR-007](decisions/adr-007-occlusion-handling-confidence-propagation.md) | Jerarquía de degradación ante oclusión de pies: tobillos duales $\to$ individual $\to$ bbox $\to$ Kalman coasting. |
| **008** | [ADR-008](decisions/adr-008-kalman-epistemology-noise-divergence.md) | Estados epistemológicos (`OBSERVED`, `PREDICTED`, `STALE`) y desescalada bloqueada sin fotones reales. |
| **009** | [ADR-009](decisions/adr-009-decoupled-spatial-dwell-statecharts.md) | Desacoplamiento formal entre autómata espacial de ocupación y temporizador de permanencia. |
| **010** | [ADR-010](decisions/adr-010-dual-latency-profiling-iso13855.md) | Doble horizonte temporal: rendimiento de hardware por frame ($T_{\text{system}}$) vs respuesta física ($T_{\text{event}}$). |
| **011** | [ADR-011](decisions/adr-011-mahalanobis-hungarian-mot.md) | Gating elipsoidal de Mahalanobis $\chi^2$, asignación global Húngara y Spatial Birth NMS. |
| **012** | [ADR-012](decisions/adr-012-synthetic-yolo-video-generation.md) | Composición fotorrealista pinhole de identidad única y HUD desacoplado para validación formal. |

---

## Síntesis Conceptual y Criterios de Diseño Arquitectónico

1. **Límites de la Inferencia Probabilística:**  
   En sistemas donde la seguridad de personas está en juego, la IA debe limitarse a la tarea de extracción sensorial (percepción de keypoints). Toda lógica de control, conversión métrica y decisión de parada debe ser estrictamente determinista, matemáticamente auditable e independiente de la incertidumbre del modelo.
2. **Colapso Dimensional mediante Restricción Planar ($Z_w = 0$):**  
   Una cámara 2D monocular no puede estimar profundidad de forma determinista. Sin embargo, al anclar la detección a los pies apoyados en el suelo, fijamos $Z_w = 0$ y reducimos el problema a una homografía $3 \times 3$, resolviendo distancias métricas euclidianas en microsegundos sin requerir cámaras estéreo o LiDAR.
3. **Invarianza Antropométrica (Keypoints vs Bounding Box):**  
   El centroide o base de un bounding box 2D se deforma drásticamente cuando un operario se inclina o extiende los brazos. El anclaje en tobillos anatómicos proporciona una referencia invariante a la postura corporal, eliminando falsos positivos en los límites de zona.
4. **Protección Mecánica y Prevención de Chattering:**  
   El ruido de detección en visión artificial oscila naturalmente a la frecuencia de adquisición. Un Schmitt trigger espacial con banda de histéresis ($\Delta d = 200\text{ mm}$) desacopla el punto de conmutación de entrada del punto de salida, protegiendo actuadores mecánicos de la fatiga por conmutación espuria.
5. **Epistemología de Estados y Fail-Safe Estricto:**  
   Cuando un objeto ocluye la visión, el filtro cinemático puede extrapolar la trayectoria temporalmente (`PREDICTED`). Sin embargo, en seguridad industrial rige el principio Fail-Safe: ante la ausencia de fotones ópticos comprobables (`OBSERVED`), la desescalada de alarma queda estrictamente bloqueada.
6. **Diseño Basado en Directivas Normativas:**  
   La formulación matemática de normas como ISO 13855:2024 proporciona un marco riguroso para dimensionar distancias de guarda y presupuestar latencias de percepción ($t_1$). Diseñar con base en estos principios permite garantizar que la física de parada de la máquina gobierne las especificaciones del software.
