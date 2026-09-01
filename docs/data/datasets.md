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

### 1.1 Metodología de Calibración Planar (DLT) y Fuentes de Metadatos de Cámara

Una duda arquitectónica fundamental es: **¿Los datasets ya traen la matriz de homografía calibrada o la definimos nosotros?**

Existen dos fuentes de datos para construir los archivos de configuración YAML:

#### Categoría A: Datasets Académicos con Metadatos Explícitos de Calibración
* **Ejemplos:** `PETS 2009`, `HA4M`.
* **Información que provee el dataset:** Archivos XML/YAML con matrices de cámara completas según el modelo pinhole de Tsai:
  * Matriz Intrínseca: $K = \begin{bmatrix} f_x & 0 & c_x \\ 0 & f_y & c_y \\ 0 & 0 & 1 \end{bmatrix}$ (distancia focal y centro óptico).
  * Matriz Extrínseca: $[R \mid \mathbf{t}]$ (rotación e inclinación tridimensional respecto al piso).
* **Cómo la usamos:** La homografía planar se deriva directamente de las dos primeras columnas de rotación y traslación:
  $$H = K \begin{bmatrix} \mathbf{r}_1 & \mathbf{r}_2 & \mathbf{t} \end{bmatrix}$$

#### Categoría B: Datasets de Videovigilancia y Plantas Industriales Reales
* **Ejemplos:** `mendeley_industrial` (planta metalmecánica real), `opencv_vtest`, `openvino_people`.
* **Información que provee el dataset:** Únicamente el metraje de video CCTV de cámara fija en alta resolución, sin matriz matricial explícita pero con referencias físicas reales en escena (líneas de seguridad pintadas en el suelo, ancho estándar de pasillos de $2.0\text{ m}$, juntas de baldosas o demarcaciones peatonales).
* **Cómo la calibramos nosotros:**
  1. Extraemos un cuadro estático y seleccionamos 4 vértices coplanares en el piso identificables en píxeles $(u_i, v_i)$.
  2. Asignamos las medidas métricas del mundo real $(X_i, Y_i)$ correspondientes a las dimensiones físicas de la nave (ej. $10\text{m} \times 15\text{m}$).
  3. El [`HomographyManager`](../../src/core/homography.py) resuelve el sistema homogéneo mediante el algoritmo **DLT (Direct Linear Transformation)** con descomposición en valores singulares (SVD) y valida que el error de reproyección sea $RMSE < 0.05\text{ m}$.

#### Procedimiento de Calibración en una Celda de Producción Real:
```
┌──────────────────────────────────────────────────────────────────────────┐
│              PROCEDIMIENTO DE INSTALACIÓN EN FÁBRICA                     │
├──────────────────────────────────────────────────────────────────────────┤
│ 1. Montaje Fijo   │ Instalar cámara CCTV fija (sin PTZ) a 3-4m de altura.│
├──────────────────────────────────────────────────────────────────────────┤
│ 2. Marcado Físico │ Colocar 4 marcas o cinta en el suelo (Z=0).         │
│                   │ Medir con telémetro láser las distancias métricas.   │
├──────────────────────────────────────────────────────────────────────────┤
│ 3. Perfil YAML    │ Ingresar los 4 pares [u, v] <-> [X, Y] y los         │
│                   │ polígonos de peligro de la máquina en el .yaml.      │
├──────────────────────────────────────────────────────────────────────────┤
│ 4. Verificación   │ El HomographyManager audita κ(H) y RMSE en runtime.  │
└──────────────────────────────────────────────────────────────────────────┘
```

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

#### Tabla de Relevamiento de Datasets de Celdas Robóticas (HRC / Cobots):

| Dataset | Entorno / Robot | Modalidades y Sensores | Tamaño / Empaquetado | DOI / Repositorio | Estado de Acceso |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`InHARD`** | Celda colaborativa con manipulador robótico industrial y estación de ensamble. | 3 cámaras RGB C920 (Top, $\pm 45^\circ$) + Esqueletos BVH (Perception Neuron 120Hz). | **$24.0\text{ GB}$** (12 volúmenes `.7z.001` a `.012` divididos). | [Zenodo 10.5281/zenodo.4003541](https://doi.org/10.5281/zenodo.4003541) | ✅ Público vía Zenodo (exige descargar los 12 archivos divididos para descomprimir secuencias). |
| **`InHARD-DT`** | Gemelo Digital (VR) de la celda robótica InHARD con modelos cinemáticos. | Simulación sintética VR + cinemática ST-GCN. | **$16.8\text{ GB}$** (6 archivos `.zip` divididos). | [Zenodo 10.5281/zenodo.7644247](https://doi.org/10.5281/zenodo.7644247) | ✅ Público en Zenodo (paquete multipartición). |
| **`HA4M`** | Celda de ensamble industrial de trenes epicicloidales. | 6 modalidades: RGB, Depth, IR, RGBA, Nubes de Puntos y Azure Kinect SDK. | **$4.1\text{ TB}$** (Archivos crudos en contenedor Matroska `.mkv`). | [Science Data Bank 10.57760/sciencedb.01872](https://doi.org/10.57760/sciencedb.01872) | ✅ Disponible en CNR Baltig / ScienceDB (orientado a servidores de Big Data por su volumen de $4\text{TB}$). |
| **`Sheffield UR5 Factory`** | Planta de manufactura real con cobot **UR5**. | Video CCTV de fábrica con interacción humano-cobot. | **$13.5\text{ GB}$** (`teconnex.zip`). | [Figshare 10.15131/shef.data.19299539](https://doi.org/10.15131/shef.data.19299539) | ✅ Descargable vía API de Figshare. |
| **`Mendeley Industrial`** | Planta de manufactura metalmecánica y prensas de inyección de plástico. | CCTV Full HD $1080\text{p}$ con 8 clases de comportamiento y zonas delimitadas. | **$14\text{ MB} - 33\text{ MB}$ por clip** ($1080\text{p}$). | [HuggingFace Voxel51 / Mendeley](https://doi.org/10.17632/xjmtb22pff.1) | 🚀 **Activo en el repo** (Clips `1_tr1`, `mendeley_walkway_violation`, `3_tr1`, `4_tr1` calibrados y evaluados en tiempo real). |

#### Análisis de Viabilidad y Alcance:
* **Limitaciones Técnicas:** Los datasets dedicados a celdas robóticas como `InHARD` ($24\text{ GB}$) y `HA4M` ($4.1\text{ TB}$) utilizan esquemas de empaquetado monolíticos o multipartición que impiden la descarga de un solo video atómico de muestra sin descargar decenas de gigabytes.
* **Alcance Actual del Proyecto:** Para mantener el repositorio ligero, modular y reproducible en entornos de CI/Edge sin transferencias masivas de datos, la suite de **`Mendeley Industrial Safety`** junto con **`PETS 2009`** y **`OpenVINO People`** proporciona la cobertura completa para validar homografía planar, estimación de pose en $1080\text{p}$, autómatas de seguridad ISO 13855 y filtrado cinemático.
* **Hoja de Ruta Futura:** En fases posteriores orientadas a Gemelos Digitales o reconocimiento de micro-acciones en robots manipuladores, se integrará un módulo de ingesta para desempaquetar las trazas BVH y cámaras multi-ángulo de `InHARD`.

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

### 3.6 Hallazgo 6: Semántica de Pasarelas Peatonales y Sensibilidad en Campo Lejano
* **Problema:** En el dataset `mendeley_walkway_violation`, el objetivo físico es detectar cuando un operario **se sale de la senda peatonal segura** demarcada con pintura en el suelo. El enfoque tradicional de "zona de peligro en la máquina" no modela la violación de pasarela, ya que la infracción ocurre al abandonar el corredor seguro hacia la calzada industrial general. Asimismo, en el plano lejano ($Y > 12\text{m}$), las personas ocupan menos de $80\text{ px}$ verticales, provocando pérdidas intermitentes de detección en YOLO11n-pose con umbrales $\text{conf} \ge 0.40$.
* **Estrategia de Evolución:**
  1. **Semántica de Inversión de Polígono (*Safe Corridor Inclusion*):** Permitir en `ZoneConfig` definir zonas donde el estado `SAFE` sea **estar dentro** del polígono de la pasarela y `DANGER/WARNING` sea cruzar sus límites exteriores hacia el galpón.
  2. **Ajuste de Umbral y Coasting en Campo Lejano:** Flexibilizar el umbral de confianza a $0.25 - 0.30$ en combinación con mayor inercia cinemática del Filtro de Kalman (`n_release=8`).
  3. **Estado Actual:** Registrado y documentado como caso de borde en el catálogo de benchmarks para futuras iteraciones del autómata espacial.

---

### 3.7 Discusión Técnica: Degradación Adaptativa por Escala — ¿Bounding Box Base vs. Keypoints en Campo Lejano?

Una de las conclusiones de ingeniería más ricas que surgen de la evaluación empírica de este metraje es la **tensión entre precisión de anclaje y estabilidad de detección**:

#### El Dilema Físico / Óptico:
* **Campo Cercano / Medio ($Y \le 10\text{m}$, Altura Persona $> 150\text{px}$):**
  * La estimación de pose COCO (17 keypoints) es insuperable: detectar los tobillos (`ankle_left`, `ankle_right`) elimina el error por postura (por ejemplo, si la persona está inclinada hacia adelante, los pies marcan el verdadero punto de apoyo en el suelo $Z=0$).
* **Campo Lejano ($Y > 12\text{m}$, Altura Persona $< 80\text{px}$):**
  * Las articulaciones del pie ocupan apenas $2 \times 2\text{ px}$ en el sensor. La red neuronal pierde confianza local en keypoints individuales ($\text{conf}_{\text{ankles}} < 0.30$) y el detector descarta la pose entera o introduce *jitter* angular.
  * **Sin embargo**, los mapas de características convolucionales de escala gruesa detectan el **Bounding Box global de la persona** con altísima confianza ($\text{conf}_{\text{box}} \ge 0.75$).

#### Patrón Arquitectónico Propuesto: Degradación Adaptativa por Escala
En lugar de forzar keypoints cuando la resolución no lo permite, el pipeline debe conmutar automáticamente su estrategia de anclaje en función de la altura aparente del objeto ($h_{\text{bbox}}$) y la distancia homográfica proyectada:

$$\text{Anchor}(t) = \begin{cases} 
\text{Midpoint}(\text{ankle}_L, \text{ankle}_R) & \text{si } h_{\text{bbox}} \ge 120\text{px} \land \text{conf}_{\text{ankles}} \ge 0.40 \quad (\text{Modo Alta Precisión}) \\
\text{BottomCenter}(\text{bbox}) & \text{si } h_{\text{bbox}} < 120\text{px} \lor \text{conf}_{\text{ankles}} < 0.40 \quad (\text{Modo Bounding Box Lejano})
\end{cases}$$

**Ventaja:** En campo lejano se asegura la continuidad ininterrumpida del tracking cinemático sin caídas de track, y a medida que el operario se aproxima a la zona crítica, el sistema conmuta suavemente a la precisión sub-centimétrica de los tobillos.

---

### 3.8 Discusión Técnica: Resolución Espacial de Inferencia vs. Alucinación en Estructuras Industriales (El Dilema 640p vs. 1280p)

Durante las pruebas de ingestión en `mendeley_walkway_violation`, se descubrió un fenómeno crucial de **percepción en visión artificial industrial**:

#### 1. El Mecanismo del Fallo a 640x640:
* **Submuestreo Espacial Severo:** En Full HD ($1920\times 1080$), los operarios en el pasillo lejano miden $\approx 130\text{ px}$ de alto. Al aplicar el preprocesamiento letterbox a $640\times 360$, la silueta humana se comprime a apenas **$43\text{ px}$ en el tensor de entrada**.
* **Límites del Campo Receptivo:** En las cabezas de detección profundas de YOLO ($P_4$ con stride 16 y $P_5$ con stride 32), una silueta de $43\text{ px}$ ocupa **menos de 2 celdas de convolución**. A esta escala, la red COCO no logra activar la clase `person` con confianza suficiente ($\text{conf} < 0.25$).
* **Alucinación por Falso Gradiente al Bajar el Umbral:** Si se reduce artificialmente el umbral a $\text{conf} = 0.15$ para intentar "forzar" la detección de las figuras lejanas, la red empieza a clasificar como personas las **columnas verticales, barandas y brazos robóticos metálicos** en el plano medio/cercano, debido a que sus gradientes lineales de alto contraste coinciden con los patrones de miembros corporales a baja activación.

#### 2. Evidencia Empírica Comparativa ($640\text{p}$ vs. $1280\text{p}$):
Ensayos comparativos directos sobre el Frame 50 y 150 del metraje:

| Configuración de Inferencia | Operarios Detectados | Confianza Persona | Falsos Positivos en Maquinaria |
| :--- | :--- | :--- | :--- |
| **`imgsz = 640` (ONNX Base)** | **0** | $< 0.25$ (Descartados) | Sí (al bajar umbral a $0.15$) |
| **`imgsz = 1280` (Alta Resolución)** | **2 (Ambos)** | **$0.66$ y $0.34$** | **0 (Cero falsos positivos)** |

> **Conclusión:** La red no tiene un problema fundamental de representación semántica, sino una limitación de **soporte espacial de píxeles**. A $1280\text{p}$, los operarios lejanos poseen suficientes píxeles para ser reconocidos limpiamente con alta confianza y sin alucinaciones.

---

### 3.9 Hoja de Ruta y Líneas de Investigación Futuras (Propuestas de Artículos Técnicos / Posts)

Este hallazgo abre tres líneas de trabajo y divulgación técnica de alto impacto:

#### 1. Post/Artículo 1: *«El Dilema de Escala en Edge AI: ¿Por qué tu modelo YOLO no ve humanos lejanos en plantas industriales?»*
* **Eje temático:** Análisis matemático de cómo el letterbox $1920 \to 640$ degrada el campo receptivo convolucional en cámaras industriales de focal amplia.
* **Demostración:** Comparativa visual y de tensores entre $640\text{p}$ y $1280\text{p}$, mostrando por qué bajar el umbral de confianza produce alucinaciones en tuberías y maquinaria.

#### 2. Post/Artículo 2: *«Inferencia por Parches (SAHI) vs. Escalado Global en Seguridad Industrial en Tiempo Real»*
* **Eje temático:** Arquitectura de inferencia híbrida: cómo procesar un recorte (crop) $640\times 640$ 1:1 enfocado en el corredor lejano en paralelo con el plano general, conservando el presupuesto de latencia de $16\text{ ms}$ en dispositivos embebidos.

#### 3. Post/Artículo 3: *«Fine-Tuning con Invarianza de Estructuras Industriales y Equipamiento EPP»*
* **Eje temático:** Entrenamiento especializado con datasets industriales (ropa de trabajo oscura, chalecos de alta visibilidad, cascos) y *hard negative mining* sobre maquinaria metálica para suprimir activaciones espurias a baja resolución.

---

## 4. Tabla Comparativa Integral de Rendimiento
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`synthetic_sequence_a`** | $1280 \times 720$ | $51.4\text{ FPS}$ | $16.24\text{ ms}$ | $24.68\text{ ms}$ | ✅ Ground truth exacto: incursión limpia |
| **`synthetic_sequence_b`** | $1280 \times 720$ | $36.5\text{ FPS}$ | $24.07\text{ ms}$ | $28.94\text{ ms}$ | ✅ Ground truth exacto: oclusión de pies |
| **`synthetic_sequence_c`** | $1280 \times 720$ | $37.4\text{ FPS}$ | $23.44\text{ ms}$ | $28.02\text{ ms}$ | ✅ Ground truth exacto: permanencia / dwell |
| **`mendeley_industrial`** | $1920 \times 1080$ | $37.5\text{ FPS}$ | $15.35\text{ ms}$ | $18.26\text{ ms}$ | ✅ Planta real: intervención no autorizada en máquina |
| **`mendeley_walkway_violation`** | $1920 \times 1080$ | $36.0\text{ FPS}$ | $16.32\text{ ms}$ | $21.52\text{ ms}$ | ✅ Pasarela industrial: cruce por corredor e incursión a celda |
| **`opencv_vtest`** | $768 \times 576$ | $40.8\text{ FPS}$ | $21.26\text{ ms}$ | $29.31\text{ ms}$ | ✅ CCTV urbano: intrusión en zona y enclave lockout |
| **`openvino_people`** | $1920 \times 1080$ | $36.7\text{ FPS}$ | $18.27\text{ ms}$ | $22.41\text{ ms}$ | ✅ Pasillo comercial: pose 1080p unletterboxed |
| **`pets2009_s2_l1`** | $768 \times 576$ | $40.6\text{ FPS}$ | $21.38\text{ ms}$ | $30.53\text{ ms}$ | ✅ Explanada: tracking multiobjetivo y oclusiones |
