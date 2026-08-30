# Industrial Edge AI MVP: Intrusion Detection & Dwell Time Monitoring

MVP industrial en tiempo real para detección de incursiones y control de permanencia en zonas restringidas, combinando **YOLO Pose**, **Transformación Homográfica (2D Pixel a Plano Métrico)**, **Filtrado Kalman/Alpha-Beta** y **Máquinas de Estados Finitos Espaciales (Spatial FSM)**.

---

## 🎯 Objetivo del Proyecto

Diseñar un sistema de visión por computadora para entornos de borde (*Edge AI*) optimizado para **macOS (Apple Silicon M1/M2/M3)** y sistemas **Linux Edge** mediante **ONNX Runtime**, enfocado en la seguridad industrial (cumplimiento normativo ISO 13855:2024 sobre distancias de seguridad).

---

## 📐 Formulación Matemática & Arquitectura

### 1. Proyección Homográfica (Pixel $\rightarrow$ Métrico)
Las coordenadas de los pies de los trabajadores en la imagen 2D $(x, y)$ se proyectan al plano métrico $(X, Y)$ mediante una matriz de homografía $H \in \mathbb{R}^{3 \times 3}$:

$$\begin{bmatrix} X' \\ Y' \\ W \end{bmatrix} = H \begin{bmatrix} x \\ y \\ 1 \end{bmatrix}, \quad X = \frac{X'}{W}, \quad Y = \frac{Y'}{W}$$

La matriz $H$ se calcula mediante el algoritmo DLT (*Direct Linear Transformation*) usando 4 puntos de calibración en la imagen y sus correspondientes coordenadas reales en metros.

### 2. Máquina de Estados Finitos Espacial (Spatial FSM)
Para evitar oscilaciones (*flickering*) en los límites de las zonas restringidas, el tracker aplica histéresis espacial ($P_{\text{danger}}$ vs $P_{\text{release}}$) y temporal ($T_{\text{dwell}}$):

```
       [ OUTSIDE ]
            │ (Entra a P_danger)
            ▼
    [ ENTER_PENDING ] ──(Histéresis completada)──► [ INTRUSION_ACTIVE ]
            │                                             │ (Dwell time > T_warn)
            │ (Sale antes del timer)                      ▼
            └───────────────────────────────────► [ DWELL_WARNING ]
                                                          │ (Dwell time > T_violation)
                                                          ▼
                                                  [ DWELL_VIOLATION ]
                                                          │ (Sale de P_release)
                                                          ▼
                                                   [ EXIT_PENDING ]
                                                          │
                                                          ▼
                                                     [ OUTSIDE ]
```

---

## 🚀 Estructura del Repositorio

```
.
├── AGENTS.md                   # Reglas del proyecto, tono y flujo SDD
├── README.md                   # Especificación técnica y guía de arquitectura
├── configs/
│   └── default_config.yaml     # Puntos de calibración, polígonos y umbrales
├── data/
│   └── samples/                # Muestras de video y calibración
├── docs/
│   ├── architecture/           # Diagramas y especificaciones de diseño
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
│   │   ├── kalman_filter.py    # Filtro de suavizado espacial 2D
│   │   └── spatial_fsm.py      # Tracker de trabajador y FSM de incursión
│   ├── inference/
│   │   └── onnx_engine.py      # Wrapper ONNX Runtime (CoreML / CPU ARM NEON)
│   ├── pipeline/
│   │   └── edge_pipeline.py    # Loop principal de ejecución
│   └── utils/
│       ├── metrics.py          # Profiler de latencia (FPS, p50, p95, p99)
│       └── visualization.py    # Overlays OpenCV y vista Top-Down
├── tests/
│   ├── conftest.py             # Fixtures sintéticos (sin descargas en CI)
│   ├── test_export.py          # Pruebas de exportación y validación ONNX
│   ├── test_onnx_engine.py     # Pruebas de runtime e inferencia
│   ├── test_benchmark.py       # Pruebas de cálculo métrico y percentiles
│   ├── test_fsm.py             # Pruebas unitarias para transiciones FSM
│   └── test_homography.py      # Pruebas unitarias para la transformación métrica
└── scripts/
    ├── benchmark.py            # Latencia y throughput en ONNX Runtime
    └── run_demo.py             # CLI de ejecución principal
```

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
- [ ] **Paso 6:** Pipeline de Ejecución, Visualización Top-Down y Métricas (`src/pipeline/`, `src/utils/`).
- [ ] **Paso 7:** Scripts de Demo y Ejecución End-to-End (`scripts/run_demo.py`).
