# Vision-Based Restricted Zone Monitoring: Intrusion Detection & Dwell Time Analysis

Prototipo experimental de visión artificial para monitoreo de incursiones y control de permanencia en zonas restringidas en tiempo real, combinando **YOLO Pose**, **Transformación Homográfica (2D Píxel a Plano Métrico)**, **Filtrado Kalman 2D Cinemático** y **Máquinas de Estados Finitos Espaciales (Spatial FSM)**.

---

## 🎯 Definición Formal del Problema

> Given a video stream from a fixed monocular camera observing an approximately planar floor, estimate the ground-plane position of visible workers, determine whether they enter a configured metric restricted zone, and emit temporally stable intrusion and dwell events while characterizing end-to-end processing latency.

> [!CAUTION]
> **Non-goal:** *This prototype is not a certified safety function and must not be used to stop or control hazardous machinery.*
> 
> **Aviso de Alcance y Seguridad Funcional (Disclaimer):**
> *Experimental vision-based intrusion monitoring system inspired by industrial safety-zone concepts and ISO 13855 safety-distance reasoning. Not a safety-rated protective device.*
> Este software es un desarrollo experimental de investigación y prototipado. No constituye un Equipo de Protección Electrosensible (ESPE) ni un Dispositivo de Protección Basado en Visión (VBPD) certificado funcionalmente bajo IEC 61496, ISO 13849 (PL) o IEC 61508 (SIL). No debe ser utilizado como mecanismo de parada de emergencia en maquinaria peligrosa sin salvaguardas mecánicas certificadas.

---

## 📌 Alcance y Funcionalidades (Scope Freeze)

Para garantizar la entrega de un sistema robusto, determinista y verificable sin sobreingeniería, el alcance del proyecto queda congelado y categorizado de la siguiente manera:

### 1. Núcleo Principal y Flujo de Datos End-to-End

El sistema está estructurado en 5 etapas secuenciales de percepción y decisión, integradas con un módulo ortogonal de perfilado de latencia (*Performance Profiler*) para garantizar presupuestos de tiempo real según **ISO 13855**:

```
                    PERCEPTION
                         │
Camera frame ──► Pose inference
                         │
                         ▼
                 keypoint extraction
                         │
                         ▼
                 ground-point estimate
                         │
─────────────────────────┼────────────────────────
                    GEOMETRY
                         │
                         ▼
                   Homography
                         │
                         ▼
                 (X,Y) estimate [m]
                         │
─────────────────────────┼────────────────────────
                  STATE ESTIMATION
                         │
                         ▼
                Alpha-Beta / Kalman
                         │
                         ▼
            filtered metric trajectory
                         │
─────────────────────────┼────────────────────────
                 DECISION LOGIC
                         │
                         ▼
              Restricted zone test
                         │
                         ▼
                  Spatial FSM
                         │
                         ▼
                   Dwell timer
                         │
─────────────────────────┼────────────────────────
                     OUTPUT
                         │
            events / overlay / metrics

          ═══════════════════════════
          PERFORMANCE PROFILER (Ortogonal)
          • Capture / Ingest Latency
          • Preprocess Latency
          • Inference Latency
          • Keypoint Extract Latency
          • Projection Latency
          • Tracking Latency
          • FSM Decision Latency
          • End-to-End Reaction Time (T1)
          ═══════════════════════════
```

#### Mapeo Arquitectónico y Estado de Implementación

| Capa Arquitectónica | Componente / Flujo | Módulo de Código | Estado y Próximos Pasos (Edge AI) |
| :--- | :--- | :--- | :--- |
| **1. PERCEPTION** | Camera Frame $\to$ Pose Inference $\to$ Keypoints $\to$ Ground Contact | `src/inference/onnx_engine.py`<br>`src/pipeline/safety_pipeline.py` | **100% Implementado**<br>• Inferencia YOLO11n-Pose ONNX (`CoreMLExecutionProvider` / CPU / CUDA).<br>• Extracción anatómica de tobillos (`left_ankle: 15`, `right_ankle: 16`) con fallback a borde inferior de Bbox ([ADR-001](docs/decisions/adr-001-yolo-pose-vs-bbox.md), [ADR-007](docs/decisions/adr-007-occlusion-handling-confidence-propagation.md)). |
| **2. GEOMETRY** | Proyección Homográfica $\to$ $(X,Y)$ métrico en plano de suelo ($Z_w=0$) | `src/core/homography.py` | **100% Implementado**<br>• Mapeo planar DLT $3 \times 3$ con validación geométrica de colinealidad y condicionamiento numérico $\kappa(H) < 10^6$ ([ADR-002](docs/decisions/adr-002-homography-vs-monocular-3d.md), [ADR-005](docs/decisions/adr-005-homography-vectorization-geometric-validation.md)). |
| **3. STATE ESTIMATION** | Filtro Kalman 2D Cinemático $\to$ Trayectoria Métrica Filtrada | `src/core/kalman_filter.py` | **100% Implementado**<br>• Modelo cinemático de Velocidad Constante (CV) con matriz de covarianza y ganancia $K_k$.<br>• Epistemología de 3 estados de observación (`OBSERVED`, `PREDICTED`, `STALE`) con límite de divergencia cuadrática ([ADR-004](docs/decisions/adr-004-spatial-fsm-hysteresis.md), [ADR-008](docs/decisions/adr-008-kalman-epistemology-noise-divergence.md)). |
| **4. DECISION LOGIC** | Zone Test $\to$ Spatial FSM $\to$ Dwell Timer | `src/core/spatial_fsm.py` | **100% Implementado**<br>• Regiones ortogonales Statecharts: `OccupancyState` (`OUTSIDE`, `ENTER_PENDING`, `INSIDE`, `EXIT_PENDING`) $\times$ `DwellState` (`NONE`, `NORMAL`, `WARNING`, `VIOLATION`) ([ADR-009](docs/decisions/adr-009-decoupled-spatial-dwell-statecharts.md)).<br>• Disparo fail-safe instantáneo en `INSIDE` ($t=0\text{ s}$) y bypass dinámico por velocidad $v_n \ge 1.6\text{ m/s}$ (ISO 13855). |
| **5. OUTPUT** | Overlay Dual $\to$ Stream de Telemetría $\to$ Métricas | `src/utils/visualizer.py`<br>`scripts/run_demo.py` | **100% Implementado**<br>• Compositor dual en tiempo real (Perspectiva anotada + Bird's-Eye View métrico).<br>• Emisión de telemetría estructurada JSONL y reporte de percentiles de rendimiento.<br>*(Roadmap Edge AI: Exporter industrial para protocolos de planta MQTT / ZeroMQ / gRPC)*. |
| **6. PROFILER (Ortogonal)** | Profiling granular por etapa $\to$ Latencia End-to-End ($T_1$) | `src/pipeline/safety_pipeline.py`<br>`src/inference/benchmark.py` | **95% Implementado**<br>• Medición de alta resolución en cada etapa ($T_1 = t_{\text{pre}} + t_{\text{inf}} + t_{\text{pose}} + t_{\text{proj}} + t_{\text{track}} + t_{\text{fsm}}$) con percentiles p50, p95 y p99.<br>*(Próximo paso 5%: Medición de hardware timestamp en captura e ingestión con ring buffer)*. |

### 2. Secundario (Sólo si sobra tiempo)
* **Comparación PyTorch vs ONNX:** Benchmark comparativo de throughput y latencia entre runtime nativo de PyTorch y ONNX Runtime.
* **Benchmark CoreML Execution Provider:** Profiling granular del motor CoreML en Apple Silicon (ANE vs GPU).
* **Baseline de Detector Alternativo:** Pruebas comparativas de precisión/latencia con detectores ligeros alternativos.

### 3. Fuera de Alcance del MVP (Definitivamente después)
* **Optimización en NVIDIA GTX 1050:** Cuantización post-entrenamiento a INT8 obligatoria para arquitectura Pascal sin Tensor Cores.
* **Compilación TensorRT / DeepStream:** Pipelines zero-copy en hardware NVIDIA.
* **Soporte Embebido Dedicado:** Adaptaciones para NVIDIA Jetson (Nano/Orin) y Raspberry Pi.
* **Contenedorización Docker:** Empaquetado en contenedor para producción.
* **Fusión Sensorial:** Integración de datos de LiDAR, radar o barreras fotoeléctricas físicas.
* **Topología Multi-Cámara:** Calibración extrínseca multicámara y re-identificación de operarios entre sensores.
* **Entrenamiento & Fine-Tuning:** Re-entrenamiento del modelo con datasets específicos de indumentaria industrial.

---

## 🔬 Objetivos de Estudio, Preguntas Clave y Validación

Este proyecto sirve como plataforma experimental para responder preguntas técnicas rigurosas sobre visión por computadora aplicada a la estimación cinemática y dimensionamiento de zonas. Las siguientes preguntas guían el análisis teórico y se validan empíricamente mediante código y suites de pruebas:

### 1. Estudios Teóricos & Metrología
* **Q1: ¿Cómo contribuye la latencia de percepción ($t_1$) a la distancia de separación física requerida?**
  * *Marco Teórico:* Bajo la formulación $S = K \cdot T + C = K(t_1 + t_2 + t_3) + C$, cada $10\text{ ms}$ de latencia en el pipeline a una velocidad de marcha de $K = 1.6\text{ m/s}$ ($1600\text{ mm/s}$) añade $16\text{ mm}$ directos a la distancia de separación requerida. Si el pipeline corre a 10 FPS ($100\text{ ms}$), $S$ debe incrementarse en $160\text{ mm}$ adicionales frente a una ejecución a 30 FPS ($33.3\text{ ms}$), reduciendo el espacio útil de la planta.
  * *Validación:* [`tests/test_pipeline.py`](tests/test_pipeline.py) y [`scripts/benchmark.py`](scripts/benchmark.py).
* **Q2: ¿Por qué la estimación de velocidad mediante derivada discreta simple ($\Delta x / \Delta t$) falla en video industrial?**
  * *Marco Teórico:* La diferenciación numérica amplifica el ruido de alta frecuencia. A 30 FPS ($\Delta t = 0.033\text{ s}$), una fluctuación estocástica de detección de keypoint de apenas $2\text{ cm}$ produce un pico ficticio de velocidad de $0.6\text{ m/s}$ ($2.16\text{ km/h}$).
  * *Solución & Validación:* El filtro de Kalman desacopla la medición ruidosa mediante la ganancia de Kalman $K_k$, estimando velocidad y posición continuas con covarianza acotada ([`tests/test_kalman.py`](tests/test_kalman.py)).
* **Q3: ¿Cuál es el error de reproyección real de una homografía planar y cómo impacta el condicionamiento matricial?**
  * *Marco Teórico:* Con $N=4$ puntos coplanares, el sistema lineal DLT es exactamente determinado ($8 \times 8$), por lo que el residuo algebraico de entrenamiento es idénticamente 0. Un número de condición $\kappa(H) > 10^5$ revela degeneración proyectiva (puntos casi colineales o ángulos rasantes), lo que dispara la amplificación de error métrico ante pequeños ruidos en píxeles.
  * *Validación:* [`tests/test_homography.py`](tests/test_homography.py) audita la colinealidad preventiva, el condicionamiento $\kappa(H)$ y la prueba de invariancia isométrica en transformaciones inversas.

### 2. Estudios Aplicados & Dinámica Temporal
* **Q4: ¿Cómo evitar el parpadeo de alarmas (*chattering*) en los límites de zona sin retrasar la respuesta ante intrusiones críticas?**
  * *Marco Aplicado:* Un operador trabajando en el borde de una zona activa/desactiva alarmas erráticamente si se usa un umbral único. La solución implementa **doble histéresis**:
    1. *Espacial:* Polígono de peligro $P_{\text{danger}}$ vs polígono de liberación $P_{\text{release}} = P_{\text{danger}} \oplus \Delta d$ ($\Delta d = 0.20\text{ m}$).
    2. *Temporal:* Debounce de $N_{\text{confirm}} \ge 3$ frames para personas a paso normal.
    3. *Bypass Cinemático:* Si el vector de aproximación normal hacia el peligro supera la velocidad crítica ($v_n \ge 1.6\text{ m/s}$), el debounce se puentea en el primer fotograma ($N_{\text{confirm}} = 1$) para activar la alerta inmediata.
  * *Validación:* [`tests/test_fsm.py`](tests/test_fsm.py) simula trayectorias tangenciales, oscilaciones de borde e incursiones de alta velocidad.
* **Q5: ¿Justifican los keypoints de tobillo el costo computacional frente a usar el borde inferior de una Bounding Box? ([Ver ADR-001](docs/decisions/adr-001-yolo-pose-vs-bbox.md))**
  * *Marco Aplicado:* El baseline realista no es el centroide 2D, sino el borde inferior central de la caja delimitadora:
    $$p_{\text{ground\_bbox}} = \left( \frac{x_{\min} + x_{\max}}{2}, \, y_{\max} \right)$$
    Frente a él, el estimador de pose infiere la semántica articular:
    $$p_{\text{ground\_pose}} = \text{mean}\left(\text{valid\_ankles}(k_{15}, k_{16})\right)$$
  * *Trade-Off Experimental:* Pose ofrece fidelidad anatómica independiente de la postura del torso o inclinación de cámara, pero acarrea mayor latencia y alta vulnerabilidad a oclusiones frecuentes en planta (pallets, maquinaria baja, indumentaria). Bbox bottom-center es $\approx 30\text{–}40\%$ más veloz e inmune a la pérdida de keypoints mientras el cuerpo sea visible.
  * *Pregunta de Investigación:* ¿La ganancia en estabilidad espacial de los tobillos compensa el costo de cómputo y las fallas por oclusión en comparación con un detector de cajas estándar acoplado a un filtro de Kalman?
* **Q6: ¿Qué hace el sistema cuando los pies/tobillos quedan ocluidos por maquinaria o pallets? ([Ver ADR-007](docs/decisions/adr-007-occlusion-handling-confidence-propagation.md))**
  * *Modo de Fallo Primario:* Si una máquina tapa los pies de un trabajador, el modelo de pose reporta baja confianza (`conf < 0.5`) en ambos tobillos. Descartar la detección crea un peligro ciego; usar puntos de baja confianza inyecta ruido catastrófico a la homografía.
  * *Jerarquía de Degradación Escalonada (Graceful Degradation):*
    1. *Tobillos duales ($conf \ge 0.5$):* Proyección directa del punto medio $\to$ certeza plena (`source="ankles_dual"`).
    2. *Tobillo monocular:* Fallback al tobillo visible si supera el umbral $\to$ sesgo acotado (`source="ankle_single"`).
    3. *Ambos ocluidos:* El filtro cinemático Kalman entra en modo *coasting* extrapolando $[\dot{X}, \dot{Y}]$ durante hasta 5 frames ($\approx 160\text{ ms}$) $\to$ continuidad sin saltos (`source="tracker_predicted"`).
    4. *Oclusión prolongada:* Fallback al borde inferior de la bounding box con penalización de confianza o eliminación controlada del track.
  * *Propagación de Confianza (Confidence Propagation):* Las posiciones métricas no son números abstractos; viajan tipadas como `PositionEstimate(xy_m, confidence, source)`, permitiendo a la FSM modular su toma de decisiones según la fiabilidad de la observación.
  * *Validación:* [`tests/test_pipeline.py`](tests/test_pipeline.py) y [`tests/test_kalman.py`](tests/test_kalman.py).
* **Q7: ¿Por qué la predicción de Kalman no es verdad física y por qué la desescalada de seguridad debe ser asimétrica? ([Ver ADR-008](docs/decisions/adr-008-kalman-epistemology-noise-divergence.md))**
  * *Conflación Epistemológica:* En ausencia de fotones, la predicción $\hat{\mathbf{x}}_k = F\hat{\mathbf{x}}_{k-1}$ es una conjetura a lazo abierto. Un trabajador puede frenar o tropezar sin ser visto; la divergencia cuadrática máxima $\|\Delta \mathbf{p}(t)\| \le \frac{1}{2} a_{\max} t^2 + v_0 t (1 - \cos \theta)$ supera el margen de histéresis ($\Delta d = 200\text{ mm}$) a partir del 4to cuadro ($>100\text{ ms}$).
  * *Modelo de Tres Estados:* Se formaliza el estado de observación: `OBSERVED` ($k=0$), `PREDICTED` ($1 \le k \le 3$, seguro dentro de $\Delta d$) y `STALE` ($4 \le k \le 5$, puramente especulativo).
  * *Salvaguarda Asimétrica:* Escalar hacia el peligro (`DANGER_INTRUSION`) es fail-safe y está permitido bajo cualquier estado (`OBSERVED`, `PREDICTED`, `STALE`). Desescalar hacia `SAFE` exige $N_{\text{release}}$ cuadros estrictamente `OBSERVED` fuera de $P_{\text{release}}$.
  * *Enclavamiento por Desaparición:* Un intruso que desaparece de los sensores dentro de la zona de peligro enclava en `LOCKOUT` con relé abierto hasta supervisión e intervención humana (`SpatialFSM.reset()`).
  * *Congelamiento de Dwell:* El tiempo de permanencia no se incrementa con predicciones fantasma; se congela durante oclusión.
  * *Validación:* [`tests/test_kalman.py`](tests/test_kalman.py) y [`tests/test_fsm.py`](tests/test_fsm.py).

---

## 📐 Formulación Matemática & Arquitectura

### 1. Proyección Homográfica: De Píxeles a Espacio Físicamente Interpretable

#### ¿Por qué Homografía en lugar de ROIs en Píxeles? ([Ver ADR-002](docs/decisions/adr-002-homography-vs-monocular-3d.md))
En enfoques tradicionales de visión, una zona restringida se define como un polígono arbitrario en el espacio de la imagen 2D:
```
pixel ROI: [(327, 412), (598, 390), (620, 580), (280, 560)] px
```
Este enfoque sufre de distorsión proyectiva severa: no preserva distancias euclidianas, ángulos ni paralelismo, impidiendo cualquier razonamiento físico.

Al incorporar una transformación homográfica planar $H \in \mathbb{R}^{3 \times 3}$, el pipeline proyecta el punto de apoyo real sobre el suelo:
```
camera image
     │
     ▼
pixel coordinates (u, v) [tobillos]
     │
     H (DLT 3x3)
     ▼
ground-plane coordinates (X, Y) [m]
```

Esto convierte la zona restringida en una entidad **físicamente interpretable y medible**:
```yaml
# Zona métrica real en el piso de la fábrica:
danger_zone:
  X: [1.0, 2.5] m
  Y: [0.5, 2.0] m
```

Habilitando métricas y análisis de ingeniería imposibles de calcular en píxeles:
* **Distancia euclidiana real** hacia una máquina o punto de peligro ($d_{\text{hazard}} = \|\mathbf{x} - \mathbf{x}_{\text{hazard}}\|$).
* **Velocidad de aproximación cinemática** ($\vec{v} = [\dot{X}, \dot{Y}]$) en $\text{m/s}$.
* **Distancia de permanencia** (*dwell distance*) y distancia al borde (*boundary distance*).
* **Zonas concéntricas** de pre-alerta con separación métrica garantizada.
* **Tiempo hasta la colisión** (*Time-to-Collision* - TTC) proyectado sobre la trayectoria métrica.
* **Cuantificación del error de calibración** y condicionamiento numérico $\kappa(H)$.

#### Cadena de Propagación de Errores e Incertidumbre

Una coordenada en metros $\hat{P}_{\text{world}}$ no representa la posición real exacta del operario, sino una estimación compuesta:
$$\hat{P}_{\text{world}} = H(\hat{p}_{\text{feet}})$$

Donde convergen cinco fuentes estocásticas y sistemáticas de error:
```
pose estimation error (detección de keypoints de tobillos)
        +
pixel quantization (discretización del sensor de cámara)
        +
camera calibration error (incertidumbre en puntos DLT ground-truth)
        +
ground-plane assumption (irregularidades o desnivel del piso Z ≠ 0)
        +
homography numerical error (número de condición matricial κ(H))
```

> **Consideración de Ingeniería:**
> *¿Qué significa que el sistema reporte que una persona está a $0.93\text{ m}$ del peligro?*
> Es una estimación sobre el plano del suelo con una ventana de incertidumbre ($\pm \epsilon$). No se debe asumir precisión centimétrica sin una calibración geométrica explícita, una auditoría del error de reproyección ($RMSE$) y un análisis del condicionamiento $\kappa(H)$ ante ángulos rasantes.

#### Formulación de la Transformación
$$\begin{bmatrix} X' \\ Y' \\ W \end{bmatrix} = H \begin{bmatrix} u \\ v \\ 1 \end{bmatrix}, \quad X = \frac{X'}{W}, \quad Y = \frac{Y'}{W}$$

La matriz $H$ se estima mediante el algoritmo DLT (*Direct Linear Transformation*) con validación de no-colinealidad y condicionamiento en [`src/core/homography.py`](src/core/homography.py). Para más detalles conceptuales, consultar [ADR-002](docs/decisions/adr-002-homography-vs-monocular-3d.md) y [ADR-005](docs/decisions/adr-005-homography-vectorization-geometric-validation.md).

### 2. Autómata de Seguridad: Regiones Ortogonales Desacopladas (Statecharts) ([Ver ADR-009](docs/decisions/adr-009-decoupled-spatial-dwell-statecharts.md))

Para evitar la conflación entre la **topología espacial** y la **acumulación temporal**, el sistema desacopla el razonamiento en dos autómatas concurrentes e independientes:

#### Schmitt Trigger Espacial y Asimetría Entry / Exit ([ADR-004](docs/decisions/adr-004-spatial-fsm-hysteresis.md), [ADR-006](docs/decisions/adr-006-prepared-geometries-dynamic-debounce-bypass.md), [ADR-008](docs/decisions/adr-008-kalman-epistemology-noise-divergence.md))

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

1. ENTRY POLICY (Conservative & Fast):
   • Aproximación normal (vn < 1.6 m/s) : Debounce de N_confirm = 3 cuadros.
   • Aproximación rápida (vn >= 1.6 m/s): Bypass instantáneo (N_confirm = 1) en cuadro 1 (ISO 13855).

2. EXIT POLICY (Hysteretic & Strict):
   • Debounce de salida: Exige N_release = 5 cuadros consecutivos fuera de P_release.
   • Salvaguarda asimétrica (ADR-008): Desescalada permitida estrictamente con fotones reales (OBSERVED).
     Si el objetivo queda ocluido (PREDICTED / STALE), la salida se bloquea y el relé permanece abierto.
```

#### Statecharts Ortogonales (Occupancy x Dwell)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. AUTÓMATA DE OCUPACIÓN ESPACIAL (OccupancyState)                          │
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
                     │ (Condición: Occupancy == INSIDE)
                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. CLASIFICADOR TEMPORAL DE PERMANENCIA (DwellState)                        │
│                                                                             │
│    (Occupancy != INSIDE) ──► [ NONE ] (Timer inactivo / reset a 0.0s)        │
│                                                                             │
│    [ NORMAL ] ──(t >= T_warn)──► [ WARNING ] ──(t >= T_violation)──► [ VIOLATION ] │
│   (0 <= t < T_warn)            (T_warn <= t < T_viol)           (t >= T_viol)│
└─────────────────────────────────────────────────────────────────────────────┘
```

* **Invariante Fail-Safe:** La señal de parada de emergencia (`trip = True`) se dispara en el instante $t = 0.0\text{ s}$ de confirmación en `INSIDE` (o ante `FAULT`/`LOCKOUT`). El clasificador de *dwell* categoriza la severidad operacional sin demorar la respuesta de parada.

---

## 🚀 Estructura del Repositorio

```
.
├── AGENTS.md                   # Reglas del proyecto, tono y flujo SDD
├── README.md                   # Especificación técnica y guía de arquitectura
├── configs/
│   ├── default_config.yaml     # Puntos de calibración, polígonos y umbrales base
│   └── datasets/               # Perfiles YAML específicos por dataset (PETS, OpenCV, OpenVINO)
├── data/
│   ├── raw/                    # Datasets de video descargados (ignorado en git)
│   ├── results/                # Videos anotados y telemetría JSONL (ignorado en git)
│   └── samples/                # Muestras sintéticas deterministas de calibración
├── docs/
│   ├── architecture/           # Diagramas y especificaciones de diseño
│   ├── data/datasets.md        # Especificación y catálogo de datasets empíricos
│   └── decisions/              # Architecture Decision Records (ADRs)
│       ├── README.md           # Índice de decisiones
│       └── adr-001-*.md        # YOLO-Pose vs Bounding Box Centroid
├── models/
│   └── export_onnx.py          # Exportación y validación de YOLO-Pose a ONNX
├── openspec/                   # Especificaciones canónicas y auditoría SDD
│   ├── config.yaml             # Configuración del arnés SDD
│   ├── specs/                  # Especificaciones funcionales (fuente de la verdad)
│   └── changes/                # Historial y paquetes de cambio archivados
├── src/
│   ├── core/
│   │   ├── homography.py       # HomographyManager (DLT 2D -> Métrico)
│   │   ├── kalman_filter.py    # Filtro métrico 2D y MultiTargetKalmanTracker
│   │   └── spatial_fsm.py      # SpatialFSM con histeresis dual y dwell time
│   ├── inference/
│   │   └── onnx_engine.py      # Wrapper ONNX Runtime (CoreML / CPU ARM NEON)
│   ├── pipeline/
│   │   └── safety_pipeline.py  # Orquestador end-to-end (ISO 13855 T1)
│   └── utils/
│       └── visualizer.py       # Compositor dual (Cámara + Bird's-Eye View métrico)
├── tests/
│   ├── conftest.py             # Fixtures sintéticos (sin descargas en CI)
│   ├── test_dataset_ingestion.py # Pruebas del downloader y arnés de ingesta
│   ├── test_export.py          # Pruebas de exportación y validación ONNX
│   ├── test_onnx_engine.py     # Pruebas de runtime e inferencia
│   ├── test_benchmark.py       # Pruebas de cálculo métrico y percentiles
│   ├── test_fsm.py             # Pruebas unitarias para transiciones FSM
│   ├── test_homography.py      # Pruebas unitarias para la transformación métrica
│   ├── test_kalman.py          # Pruebas del filtro de Kalman y tracking multiobjeto
│   ├── test_pipeline.py        # Pruebas del pipeline de seguridad integrado
│   └── test_visualizer.py      # Pruebas del compositor visual dual
└── scripts/
    ├── benchmark.py            # Latencia y throughput en ONNX Runtime
    ├── download_datasets.py    # Descargador resiliente multi-mirror con failover
    ├── generate_samples.py     # Generador determinista de secuencias sintéticas
    ├── run_dataset_test.py     # Arnés desacoplado de evaluación empírica
    └── run_demo.py             # Demo orchestrator interactivo y headless

---

## 📚 Documentación & Decisiones de Arquitectura (ADRs)

* **[Bitácora de Preguntas & Respuestas de Arquitectura](docs/architecture/preguntas-y-respuestas-arquitectura.md):** Guía conceptual y fundamentos de diseño (por qué homografía $3 \times 3$, anclaje en tobillos vs bounding boxes, matemática de 4 puntos DLT y restricciones de silicio Pascal INT8).
* **[Especificación Técnica Maestra](docs/architecture/industrial-edge-ai-specification.md):** Documento formal con marco normativo ISO 13855:2024, benchmark de modelos, restricciones de silicio (Pascal INT8 vs Apple Silicon), datasets industriales y arquitectura zero-copy.
* **[Directrices ISO 13855:2024 y Formulación](docs/architecture/safety-directives-iso13855.md):** Presupuesto temporal, fórmula de distancia de seguridad $S$, mitigación de falsos positivos y lazo de control.
* **Índice de Decisiones de Arquitectura ([ADRs](docs/decisions/README.md)):**
  * **[ADR-001](docs/decisions/adr-001-yolo-pose-vs-bbox.md):** Selección de YOLO-Pose vs Bounding Box Centroid para Detección de Incursión.
  * **[ADR-002](docs/decisions/adr-002-homography-vs-monocular-3d.md):** Proyección Homográfica 2D a Plano Métrico vs Estimación 3D Monocular.
  * **[ADR-003](docs/decisions/adr-003-onnx-runtime-coreml.md):** Runtime de Inferencia: ONNX Runtime (CoreML Provider) vs PyTorch Nativo.
  * **[ADR-004](docs/decisions/adr-004-spatial-fsm-hysteresis.md):** Gestión de Oscilaciones Espaciales mediante Spatial FSM + Filtro Kalman.
  * **[ADR-005](docs/decisions/adr-005-homography-vectorization-geometric-validation.md):** Validación Geométrica Preventiva y Proyección Vectorizada en Homografía Planar.
  * **[ADR-006](docs/decisions/adr-006-prepared-geometries-dynamic-debounce-bypass.md):** Geometrías Preparadas y Bypass Dinámico de Debounce en FSM de Seguridad (ISO 13855).
  * **[ADR-007](docs/decisions/adr-007-occlusion-handling-confidence-propagation.md):** Gestión de Oclusiones en Extremidades Inferiores y Propagación de Confianza.
  * **[ADR-008](docs/decisions/adr-008-kalman-epistemology-noise-divergence.md):** Epistemología de Estados de Observación Kalman, Ruido Espectral y Desescalada Asimétrica.
  * **[ADR-009](docs/decisions/adr-009-decoupled-spatial-dwell-statecharts.md):** Desacoplamiento de Autómata Espacial y Clasificación Temporal de Dwell en Regiones Ortogonales (Statecharts).
  * **[ADR-010](docs/decisions/adr-010-dual-latency-profiling-iso13855.md):** Doble Horizonte Temporal de Latencia en Edge AI Industrial ($T_{\text{system}}$ vs $T_{\text{event}}$ - ISO 13855 / IEC 61496).

---

## 🛠️ Tecnologías & Stack

* **Lenguaje:** Python 3.10+ (Tipado estricto)
* **Modelos:** YOLOv8/YOLO11 Pose (Ultralytics $\rightarrow$ ONNX)
* **Inferencia:** ONNX Runtime (`CoreMLExecutionProvider` en Apple Silicon / `CPUExecutionProvider`)
* **Matemática y Geometría:** OpenCV, NumPy, Shapely
* **Testing:** PyTest

---

## 🗺️ Roadmap de Desarrollo (Paso a Paso)

- [x] **Paso 0:** Definición del `README.md` y estructura inicial del repositorio.
- [x] **Paso 1:** Configuración de archivos YAML y modelo de calibración inicial (`configs/default_config.yaml`).
- [x] **Paso 2:** Módulo de Homografía (`src/core/homography.py`) y pruebas unitarias (`tests/test_homography.py`).
- [x] **Paso 3:** Filtro de suavizado métrico Kalman/Alpha-Beta (`src/core/kalman_filter.py`).
- [x] **Paso 4:** FSM Espacial de Incursión (`src/core/spatial_fsm.py`) y pruebas de estados (`tests/test_fsm.py`).
- [x] **Paso 5:** Exportador e Inferencia ONNX (`models/export_onnx.py` & `src/inference/onnx_engine.py`) y suite de benchmark (`scripts/benchmark.py`).
- [x] **Paso 6:** Pipeline de Ejecución, Visualización Top-Down y Métricas (`src/pipeline/safety_pipeline.py`, `src/utils/visualizer.py`).
- [x] **Paso 7:** Scripts de Demo y Ejecución End-to-End sobre video (`scripts/run_demo.py`).
- [ ] **Paso 8:** Optimización Edge AI: Profiling de captura de hardware (V4L2/RTSP timestamp delta), Ring Buffer desacoplado y exportador de telemetría industrial (MQTT/ZeroMQ).

---

## 💻 Ejecución del Demo CLI (`scripts/run_demo.py`)

Para ejecutar la demostración interactiva end-to-end con visualización dual en tiempo real:

```bash
# 1. Generar muestras sintéticas de calibración
python scripts/generate_samples.py --output-dir data/samples

# 2. Ejecutar Demo interactivo (Ventana dual OpenCV + controles SPACE / q)
python scripts/run_demo.py --source data/samples/sequence_a_clean_incursion.mp4

# 3. Ejecutar en modo Headless exportando video anotado y telemetría JSONL
python scripts/run_demo.py \
  --source data/samples/sequence_b_occlusion_coasting.mp4 \
  --no-display \
  --output-video output/demo_annotated.mp4 \
  --output-events output/telemetry_events.jsonl
```

---

## 🧪 Ingesta y Validación de Datasets Reales (PETS 2009, OpenCV, OpenVINO)

El repositorio incluye herramientas desacopladas para descargar, calibrar y evaluar secuencias empíricas de videovigilancia sin tocar el código del *core*:

```bash
# 1. Catálogo y descarga de secuencias (resiliente con failover de mirrors)
python scripts/download_datasets.py --list
python scripts/download_datasets.py --dataset pets2009_s2_l1
python scripts/download_datasets.py --dataset opencv_vtest
python scripts/download_datasets.py --dataset openvino_people

# 2. Ejecutar evaluación interactiva con ventana visual (OpenCV GUI)
python scripts/run_dataset_test.py --dataset pets2009_s2_l1 --display --realtime

# 3. Ejecutar evaluación en lote / headless (genera video compuesto, events.jsonl y summary.json)
python scripts/run_dataset_test.py --dataset pets2009_s2_l1 --no-display
```

### Resumen de Métricas Empíricas de Validación (ISO 13855 / $T_1 \le 50\text{ ms}$)

| Dataset / Secuencia | Escenario / Entorno | Resolución | Frames | Throughput | Latencia Media ($T_1$) | $p95$ Latencia | Estado de Validación |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`synthetic_sequence_a`** | Celda de Seguridad (Incursión Limpia) | $1280 \times 720$ | 180 | $51.4\text{ FPS}$ | $16.24\text{ ms}$ | $24.68\text{ ms}$ | ✅ Ground truth exacto ($\text{err} = 0.0\text{ mm}$) |
| **`synthetic_sequence_b`** | Celda de Seguridad (Oclusión de Pies) | $1280 \times 720$ | 180 | $36.5\text{ FPS}$ | $24.07\text{ ms}$ | $28.94\text{ ms}$ | ✅ Validado (Degradación y coasting Kalman) |
| **`synthetic_sequence_c`** | Celda de Seguridad (Permanencia / Dwell) | $1280 \times 720$ | 300 | $37.4\text{ FPS}$ | $23.44\text{ ms}$ | $28.02\text{ ms}$ | ✅ Validado (Temporizador dwell desacoplado) |
| **`mendeley_industrial`** | Planta Industrial (Intervención en Máquina) | $1920 \times 1080$ | 173 | $37.5\text{ FPS}$ | $15.35\text{ ms}$ | $18.26\text{ ms}$ | ✅ Validado (Pose $1080\text{p}$ y pre-alerta) |
| **`opencv_vtest`** | CCTV Vigilancia Peatonal | $768 \times 576$ | 795 | $40.8\text{ FPS}$ | $21.26\text{ ms}$ | $29.31\text{ ms}$ | ✅ Validado (Detección de intrusión y lockout) |
| **`openvino_people`** | Pasillo Mall Peatonal (Full HD) | $1920 \times 1080$ | 302 | $36.7\text{ FPS}$ | $18.27\text{ ms}$ | $22.41\text{ ms}$ | ✅ Validado (Tránsito perimetral seguro 1080p) |
| **`pets2009_s2_l1`** | Plaza Multi-Target (Cruce & Oclusión) | $768 \times 576$ | 795 | $40.6\text{ FPS}$ | $21.38\text{ ms}$ | $30.53\text{ ms}$ | ✅ Validado (Seguimiento denso y explanada) |

Para la memoria técnica completa, particularidades metrológicas de cada dataset, catálogo de celdas robóticas industriales (`InHARD`, `HA4M`) y descubrimientos de ingeniería, consultar [docs/data/datasets.md](docs/data/datasets.md).

---

## 🔍 Problemas Conocidos y Hoja de Ruta de Seguimiento (MOT Challenges)

Durante las pruebas de estrés con datasets de alta densidad peatonal y oclusiones complejas (`pets2009_s2_l1` y `opencv_vtest`), se han catalogado los siguientes desafíos en la capa de seguimiento multiobjetivo (*Multi-Object Tracking - MOT*):

### 1. Fragmentación de Tracks y Cambio de Identidad (*ID Switching* / Cambio de Color)
* **Síntoma:** Al ocurrir un cruce o una oclusión parcial entre personas, un operario pierde su vector de seguimiento y, al reaparecer tras unos cuadros, se le asigna un nuevo identificador (`ID: X` $\to$ `ID: Y`), lo que provoca que su color cambie repentinamente en la visualización cenital (BEV).
* **Causa Raíz:** La ventana de espera durante oclusiones en el tracker cinemático ([`src/core/kalman_filter.py`](src/core/kalman_filter.py)) está fijada en `max_missed = 5` cuadros ($\approx 150\text{ ms}$). Si la oclusión supera este umbral, el track se destruye (`TrackState.DELETED`) y el re-ingreso se interpreta como un nuevo sujeto.
* **Solución Propuesta:** 
  1. Ampliar el horizonte de *coasting* a $15 - 20$ cuadros ($0.5\text{s} - 0.7\text{s}$) aprovechando el modelo epistemológico asimétrico ([ADR-008](docs/decisions/adr-008-kalman-epistemology-noise-divergence.md)), permitiendo que la predicción de Kalman mantenga viva la hipótesis espacial.
  2. Implementar asignación combinatoria global mediante el **Algoritmo Húngaro (Munkres / `scipy.optimize.linear_sum_assignment`)** sobre la matriz de distancias métricas, sustituyendo la asignación codiciosa (*greedy*).

### 2. Vectores Múltiples y Duplicados sobre el Mismo Sujeto (*Ghost / Duplicate Tracks*)
* **Síntoma:** En momentos específicos, una sola persona puede mostrar dos o tres vectores de velocidad y puntos de apoyo simultáneos de distintos colores.
* **Causa Raíz:** Cuando el detector YOLO entrega dos propuestas de cajas o articulaciones cercanas sobre el mismo cuerpo (por ejemplo, extremidades separadas o falsos positivos en umbral de NMS 2D), la asignación *greedy* inicializa un segundo track en paralelo al no encontrar coincidencia biunívoca.
* **Solución Propuesta:**
  1. **Supresión Espacial al Nacer (*World-Space Spatial NMS*):** Imponer una regla de no-nacimiento: prohibir la inicialización de un nuevo track si ya existe un track confirmado/activo a una distancia métrica menor al radio del cuerpo humano ($d < 0.6\text{ m}$).
  2. **Fusión de Tracks Cercanos (*Track Merging*):** Colapsar tracks con covarianzas solapadas y trayectorias convergentes.

---


