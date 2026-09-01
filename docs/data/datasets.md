# Datasets de Referencia, Validación Experimental y Lecciones de Ingeniería

Este documento centraliza las fuentes de datos, secuencias de referencia, especificaciones métricas y descubrimientos técnicos obtenidos durante la validación de los algoritmos de visión artificial para seguridad industrial del proyecto (**Detección de Intrusiones**, **Homografía Planar DLT**, **Oclusiones de Extremidades Inferiores**, **Filtro de Kalman Cinemático**, **Tiempos de Permanencia / Dwell Time** y **Seguimiento en Celdas Robóticas Industriales**).

---

## 1. Criterios de Selección Metrológica (ISO 13855 / VBPD)

Para evaluar rigurosamente el pipeline de seguridad, las secuencias de video deben cumplir con los siguientes requisitos físicos y ópticos:

1. **Cámara Fija en Altura:** Montaje cenital o angular ($2.5\text{ a }4.0\text{ m}$ de altura, ángulo de inclinación / *pitch* entre $25^\circ$ y $45^\circ$). Sin paneo, tilt ni zoom dinámico para garantizar la invariancia de la matriz de homografía $H \in \mathbb{R}^{3 \times 3}$.
2. **Plano de Suelo Calibrable ($Z_w \approx 0$):** Baldosas, adoquines, cuadrículas o marcas físicas identificables para calibración DLT (*Direct Linear Transformation*) con 4 o más puntos coplanares.
3. **Casos de Borde de Seguridad:**
   - **Incursión Limpia y Cruce Rectilíneo:** Velocidad constante sin oclusión para medir latencia de disparo y error de estimación de velocidad $\vec{v} = [\dot{X}, \dot{Y}]$.
   - **Oclusión Parcial Inferior (Pies Ocultos):** Tránsito detrás de obstáculos bajos (pallets, cajas, barandas) para evaluar el modo *coasting* del filtro de Kalman y la degradación controlada (`ankles_dual` $\to$ `ankle_single` $\to$ `tracker_predicted` $\to$ `bbox_bottom`).
   - **Permanencia y Merodeo (*Loitering*):** Sujetos detenidos dentro de la zona protegida para verificar los temporizadores $T_{\text{warn}}$ y $T_{\text{violation}}$.
   - **Intervención en Celda de Maquinaria / Robótica:** Sujetos aproximándose a envolventes de peligro de maquinaria pesada o robots industriales.

---

## 2. Catálogo de Datasets: Características y Ground Truth

### 2.1 Muestras Sintéticas Locales con Ground Truth Analítico Exacto

Generadas determinísticamente mediante [`src/utils/synthetic_generator.py`](../../src/utils/synthetic_generator.py) y evaluables vía `scripts/generate_samples.py`:

* **`sequence_a_clean_incursion` (Incursión Limpia):**
  * **Geometría:** Celda métrica de $6\text{m} \times 6\text{m}$ con zona de peligro central ($[2.0, 2.0] \times [4.0, 4.0]\text{ m}$).
  * **Ground Truth:** Trayectoria analítica exacta ($\text{error} = 0.00\text{ mm}$), velocidad constante $v_x = 1.0\text{ m/s}$, $v_y = 0.0\text{ m/s}$.
  * **Propósito:** Medir la latencia de respuesta $T_1$ y verificar la precisión del debounce $N_{\text{confirm}} = 3$.

* **`sequence_b_occlusion_coasting` (Oclusión por Obstáculo Bajo):**
  * **Geometría:** Barrera baja de $0.5\text{ m}$ de altura que oculta los tobillos durante 15 cuadros ($0.5\text{ s}$).
  * **Ground Truth:** Estado de degradación de anclaje (`ankles_dual` $\to$ `tracker_predicted` $\to$ `bbox_bottom`).
  * **Propósito:** Validar el modo *coasting* del filtro de Kalman sin divergencia de covarianza.

* **`sequence_c_dwell_loitering` (Permanencia en Zona):**
  * **Geometría:** Operario ingresa a la zona de peligro y permanece detenido durante $7.0\text{ s}$.
  * **Ground Truth:** Temporizador de *dwell time* continuo ($T_{\text{warn}} = 3.0\text{s}$, $T_{\text{violation}} = 6.0\text{s}$).
  * **Propósito:** Validar la FSM de permanencia temporal desacoplada ([ADR-009](../decisions/adr-009-decoupled-spatial-dwell-statecharts.md)).

---

### 2.2 Datasets Empíricos Reales de Videovigilancia y Espacios Públicos

* **`opencv_vtest` (CCTV Cruce Peatonal - $768 \times 576$):**
  * **Calibración:** 4 puntos DLT sobre el plano de la calzada peatonal.
  * **Comportamiento:** Tránsito continuo de personas con incursión directa en el polígono rojo de seguridad.
  * **Resultado Empírico:** Detecta 10 eventos de intrusión confirmada y activa el enclave de seguridad `LOCKOUT` durante 583 frames ($77\%$), requiriendo rearme de operador.

* **`pets2009_s2_l1` (Benchmark PETS 2009 - Explanada Campus):**
  * **Calibración:** Matriz de cámara Tsai (intrínsecos y extrínsecos) y plano de suelo referenciado en adoquines.
  * **Comportamiento:** Seguimiento simultáneo denso (199 a 379 tracks) con cruces de trayectorias y oclusiones dinámicas.
  * **Resultado Empírico:** Permite evaluar la robustez del tracker multiobjetivo y la estabilidad de las predicciones cinemáticas sobre un área amplia ($12\text{m} \times 20\text{m}$).

* **`openvino_people` (Pasillo Comercial Full HD - $1920 \times 1080$):**
  * **Calibración:** Proyección planar longitudinal del corredor comercial.
  * **Comportamiento:** Flujo continuo de personas en alta resolución hacia y desde la cámara.
  * **Resultado Empírico:** Verificación del pipeline en resolución Full HD $1080\text{p}$ con latencia media de $22.02\text{ ms}$ ($> 35\text{ FPS}$).

---

### 2.3 Datasets de Entornos Industriales y Celdas Robóticas

* **`mendeley_industrial` (Mendeley Industrial Safety Dataset):**
  * **Origen:** Planta de manufactura metalmecánica y plásticos *Kafaoğlu Metal Plastik Makine* (Eskişehir, DOI: `10.17632/xjmtb22pff.1`).
  * **Secuencia Primaria:** `mendeley_unauthorized_intervention.mp4` (Clip `1_tr1.mp4`, 173 frames, $1080\text{p}$).
  * **Particularidad:** Operario aproximándose a maquinaria pesada e ingresando en el perímetro de operación no autorizada.
  * **Resultado Empírico:** 25 tracks observados, detección anatómica precisa y $13.9\%$ de frames en pre-alarma de aproximación (`WARNING_APPROACH`).

* **`InHARD` (Industrial Human Action Recognition Dataset - Hoja de Ruta):**
  * **Entorno:** Celda robótica colaborativa industrial real (*Human-Robot Collaboration - HRC*) con cobots y maquinaria CNC/soldadura.
  * **Ground Truth:** Anotaciones temporales de acciones de operarios dentro del envolvente de trabajo del manipulador robótico.
  * **Acceso:** Repositorio académico abierto en Zenodo.

* **`HA4M` (Human Action Analysis for Manufacturing - Hoja de Ruta):**
  * **Entorno:** Celdas de ensamblaje manual y robótico con sensores RGB-D calibrados (Azure Kinect).
  * **Ground Truth:** Matrices intrínsecas/extrínsecas y nubes de puntos 3D del suelo de la celda.

---

## 3. Descubrimientos Empíricos y Lecciones de Ingeniería (Lessons Learned)

Durante la integración y evaluación de estos datasets, se identificaron y resolvieron 4 problemas arquitectónicos y matemáticos críticos:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    LECCIONES DE INGENIERÍA Y HALLAZGOS                     │
├────────────────────────────────┬───────────────────────────────────────────┤
│ Hallazgo 1: Letterbox Pose Miss │ Inferencia a 640x640 dejaba keypoints sin │
│                                │ unletterbox -> Skeletons reducidos a 1/3. │
├────────────────────────────────┼───────────────────────────────────────────┤
│ Hallazgo 2: BEV Viewport Fijo  │ Canvas fijo a 100px/m recortaba plantas   │
│                                │ mayores a 6x6m -> Auto-Scale Dinámico.    │
├────────────────────────────────┼───────────────────────────────────────────┤
│ Hallazgo 3: Inversión Eje Y    │ Origen de imagen (v=0 arriba) invertía la │
│                                │ profundidad visual -> v = H - 1 - y.      │
├────────────────────────────────┼───────────────────────────────────────────┤
│ Hallazgo 4: MOT ID Switching   │ Coasting corto (max_missed=5) causaba     │
│                                │ cambio de color y vectores duplicados.    │
└────────────────────────────────┴───────────────────────────────────────────┘
```

### 3.1 Hallazgo 1: Inversión de Coordenadas de Letterbox en Inferencia de Pose
* **Problema:** En videos $1080\text{p}$, las bounding boxes se mapeaban correctamente, pero los 17 keypoints anatómicos de pose se mantenían en el canvas de inferencia de $640 \times 640\text{ px}$.
* **Efecto:** El esqueleto anatómico se dibujaba encogido a un tercio de su tamaño real ($3\times$ más chico) y desplazado hacia la esquina superior izquierda.
* **Solución:** Implementación de `unletterbox_keypoints` en [`src/pipeline/safety_pipeline.py`](../../src/pipeline/safety_pipeline.py):
  $$x_{\text{orig}} = \frac{x_{\text{canvas}} - \text{pad}_x}{\text{scale}}, \quad y_{\text{orig}} = \frac{y_{\text{canvas}} - \text{pad}_y}{\text{scale}}$$
  Promovido bajo la especificación formal [`openspec/specs/keypoint-unletterbox/spec.md`](../../openspec/specs/keypoint-unletterbox/spec.md).

---

### 3.2 Hallazgo 2: Viewport Cenital Fijo vs Dimensiones de Planta
* **Problema:** El visualizador utilizaba una escala fija de $100\text{ px/m}$ en un canvas de $600 \times 600\text{ px}$, limitando la visualización a recuadros de $6\text{m} \times 6\text{m}$. En naves industriales ($10\text{m} \times 15\text{m}$) o plazas ($12\text{m} \times 20\text{m}$), el operario y la máquina quedaban fuera de la pantalla.
* **Solución:** Auto-escala dinámico en [`DualVisualizer`](../../src/utils/visualizer.py) que calcula la envolvente métrica $[X_{\min}, Y_{\min}, X_{\max}, Y_{\max}]$ con margen de seguridad del $15\%$, adaptando automáticamente la cuadrícula métrica.
  Promovido bajo la especificación formal [`openspec/specs/dynamic-bev-viewport/spec.md`](../../openspec/specs/dynamic-bev-viewport/spec.md).

---

### 3.3 Hallazgo 3: Orientación del Eje de Profundidad en Presentación
* **Problema:** Al proyectar $(X_w, Y_w)$ a píxeles de pantalla $(u, v)$ donde $v=0$ es la fila superior, la base de la cámara ($Y_w = 0$) quedaba arriba y el fondo de la nave ($Y_w = 15$) abajo, invirtiendo el sentido visual de avance.
* **Solución:** Ajuste en la capa de presentación gráfica mediante $v = H - 1 - \text{offset}_y - (Y_w - Y_{\min}) \cdot s$, manteniendo el **Core** intacto (el álgebra euclidiana y la pertenencia a polígonos de Shapely siempre fueron matemáticamente consistentes).
  Promovido bajo la especificación formal [`openspec/specs/bev-y-axis-orientation/spec.md`](../../openspec/specs/bev-y-axis-orientation/spec.md).

---

### 3.4 Hallazgo 4: Desafíos de Seguimiento Multiobjetivo (MOT Challenges)
* **Problema:** En cruces peatonales densos, una oclusión de más de 5 cuadros ($150\text{ ms}$) destruía el track viejo, generando un ID nuevo y cambiando el color del operario (*ID Switching*). Asimismo, detecciones redundantes de YOLO producían vectores dobles sobre la misma persona (*Ghost Tracks*).
* **Solución Documentada en Hoja de Ruta:**
  1. Extensión de la ventana de *coasting* a $15 - 20$ cuadros ($0.5\text{s} - 0.7\text{s}$) aprovechando el modelo epistemológico asimétrico ([ADR-008](../decisions/adr-008-kalman-epistemology-noise-divergence.md)).
  2. Asignación global mediante el **Algoritmo Húngaro (Munkres)**.
  3. **Supresión Espacial al Nacer (*World-Space Spatial NMS*)** para evitar la creación de tracks a distancias menores a $0.6\text{ m}$ de un track existente.

---

### 3.5 Hallazgo 5: Gap de Dominio en Videos Sintéticos (Domain Gap en Deep Learning)
* **Problema:** Las secuencias sintéticas actuales (`sequence_a/b/c`) dibujan al operario mediante primitivas vectoriales planas de OpenCV (`cv2.rectangle`, `cv2.line`). Al estar YOLO11-Pose entrenado sobre fotografías reales de MS COCO (gradientes de iluminación, pliegues de ropa, texturas de piel), los mapas de activación de la red entregan confianza nula ($\text{conf} < 0.25$), por lo que el detector no genera propuestas de pose sobre las figuras geométricas simples.
* **Estrategia de Solución Acordada:**
  1. **Opción 1: Inyección Analítica / Mock Ground Truth (Seleccionada para CI & Core):** El generador sintético exporta las coordenadas analíticas exactas de los 17 keypoints y el bounding box en formato `.json` o memoria para ser consumidos directamente por el tracker y la FSM sin inferencia YOLO. Proporciona una suite determinista, exacta y ultrarrápida para integración continua.
  2. **Opción 2: Composición Fotorealista 2D con Sprites Alpha (Seleccionada para End-to-End):** Incrustar recortes fotográficos reales de operarios ($PNG$ con canal Alpha transparente) proyectados por la homografía sobre el fondo de la nave, permitiendo que YOLO detecte la silueta con alta confianza ($> 0.85$) sin perder el control de la trayectoria.
  3. **Opción 3: Motores de Simulación 3D (Descartada):** Descartada formalmente por sobrecarga computacional y complejidad innecesaria para los objetivos del proyecto.

---

## 4. Tabla Comparativa Integral de Rendimiento

| Dataset | Resolución | FPS Medido | Latencia Media ($T_1$) | $p95$ Latencia | Estado de Validación |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`synthetic_sequence_a`** | $1280 \times 720$ | $51.4\text{ FPS}$ | $16.24\text{ ms}$ | $24.68\text{ ms}$ | ✅ Ground truth exacto: incursión limpia |
| **`synthetic_sequence_b`** | $1280 \times 720$ | $36.5\text{ FPS}$ | $24.07\text{ ms}$ | $28.94\text{ ms}$ | ✅ Ground truth exacto: oclusión de pies |
| **`synthetic_sequence_c`** | $1280 \times 720$ | $37.4\text{ FPS}$ | $23.44\text{ ms}$ | $28.02\text{ ms}$ | ✅ Ground truth exacto: permanencia / dwell |
| **`mendeley_industrial`** | $1920 \times 1080$ | $37.5\text{ FPS}$ | $15.35\text{ ms}$ | $18.26\text{ ms}$ | ✅ Planta real: intervención no autorizada en máquina |
| **`opencv_vtest`** | $768 \times 576$ | $40.8\text{ FPS}$ | $21.26\text{ ms}$ | $29.31\text{ ms}$ | ✅ CCTV urbano: intrusión en zona y enclave lockout |
| **`openvino_people`** | $1920 \times 1080$ | $36.7\text{ FPS}$ | $18.27\text{ ms}$ | $22.41\text{ ms}$ | ✅ Pasillo comercial: pose 1080p unletterboxed |
| **`pets2009_s2_l1`** | $768 \times 576$ | $40.6\text{ FPS}$ | $21.38\text{ ms}$ | $30.53\text{ ms}$ | ✅ Explanada: tracking multiobjetivo y oclusiones |
