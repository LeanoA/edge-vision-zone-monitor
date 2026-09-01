# Datasets de Referencia y Validación Experimental (Ground-Truth Datasets)

Este documento centraliza las fuentes de datos, secuencias de referencia y especificaciones métricas para validar los algoritmos de visión por computador en seguridad industrial del proyecto (**Detección de Intrusiones**, **Homografía Planar**, **Oclusiones de Extremidades Inferiores**, **Filtro de Kalman Cinemático** y **Tiempos de Permanencia / Dwell Time**).

---

## 1. Criterios de Selección Metrológica (ISO 13855 / VBPD)

Para evaluar rigurosamente el pipeline de seguridad, las secuencias de video deben cumplir con los siguientes requisitos físicos y ópticos:

1. **Cámara Fija en Altura:** Montaje cenital o angular ($2.5\text{ a }4.0\text{ m}$ de altura, ángulo de inclinación / *pitch* entre $25^\circ$ y $45^\circ$). Sin paneo, tilt ni zoom dinámico para garantizar la invariancia de la matriz de homografía $H \in \mathbb{R}^{3 \times 3}$.
2. **Plano de Suelo Calibrable ($Z_w \approx 0$):** Baldosas, adoquines, cuadrículas o marcas físicas identificables para calibración DLT (*Direct Linear Transformation*) con 4 o más puntos coplanares.
3. **Casos de Borde de Seguridad:**
   - **Incursión Limpia y Cruce Rectilíneo:** Velocidad constante sin oclusión para medir latencia de disparo y error de estimación de velocidad $\vec{v} = [\dot{X}, \dot{Y}]$.
   - **Oclusión Parcial Inferior (Pies Ocultos):** Tránsito detrás de obstáculos bajos (pallets, cajas, barandas) para evaluar el modo *coasting* del filtro de Kalman y la degradación controlada (`ankles_dual` $\to$ `ankle_single` $\to$ `tracker_predicted` $\to$ `bbox_bottom`).
   - **Permanencia y Merodeo (*Loitering*):** Sujetos detenidos dentro de la zona protegida para verificar los temporizadores $T_{\text{warn}}$ y $T_{\text{violation}}$.

---

## 2. Conjuntos de Referencia Públicos

| Dataset | Resolución | Puntos de Referencia en Suelo | Caso de Prueba Primario | Licencia / Acceso |
| :--- | :--- | :--- | :--- | :--- |
| **PETS 2009 (S2.L1)** | $768 \times 576$ / $720\text{p}$ | Cuadrícula de adoquines / esquinas de acera | Incursión limpia y seguimiento de velocidad cinemática | Académica / Abierta |
| **INRIA CAVIAR** | $720\text{p}$ / $288\text{p}$ | Baldosas cuadradas de piso interior | Oclusión de pies y propagación de confianza | Abierta (INRIA / Univ. Edinburgh) |
| **Oxford TownCentre** | $1920 \times 1080$ ($1080\text{p}$) | Líneas de adoquines y esquinas de bancas | Permanencia en zona protegida y cruce de límites | Académica / Abierta (Oxford) |

---

### Secuencia A: Incursión Limpia y Cruce Rectilíneo
* **Dataset / Fuente:** PETS 2009 Benchmark (Sequence `S2.L1` – View 001).
* **Escenario:** Vista cenital angular (montada a $\approx 3.5\text{ m}$ de altura) sobre explanada plana con marcas de adoquines/cuadrícula. Sujetos ingresan y cruzan el plano de visualización a velocidad constante sin interferencias severas.
* **Propiedades Técnicas:** 25 FPS, cámara fija con matriz de calibración Tsai incluida (coordenadas intrínsecas/extrínsecas y homografía de plano de suelo directa).
* **Utilidad en el Pipeline:** Calibración de los 4 puntos de homografía `cv2.findHomography` / `cv2.warpPerspective`, proyección de los pies al plano $Z=0$ y cálculo de velocidad en $\text{m/s}$.
* **Enlaces de Descarga:**
  * [PETS 2009 – Repositorio Abierto en GitLab / TU Clausthal](https://gitlab.tu-clausthal.de/)
  * [Espejo de secuencias PETS 2009 en Kaggle](https://www.kaggle.com/)

---

### Secuencia B: Oclusión Parcial Inferior (Pies Ocultos)
* **Dataset / Fuente:** INRIA CAVIAR Dataset (Secuencias: `Browse_While_Waiting1` / `LeftBag`).
* **Escenario:** Cámara de seguridad fija montada en ángulo superior (hall/lobby de laboratorio y centro comercial). El piso tiene baldosas cuadradas continuas ideales para homografía. Personas caminan pasando detrás de columnas, barandas y asientos bajos donde los pies desaparecen momentáneamente del detector.
* **Propiedades Técnicas:** 25 FPS, compresión directa H.264/MP4 disponible. Incluye anotación de bounding box y posición de pies/cabeza.
* **Utilidad en el Pipeline:** Prueba de robustez del filtro de Kalman cuando el punto inferior de contacto con el suelo se pierde temporalmente por un obstáculo bajo ([ADR-007](file:///Users/xander/Projects/edge-safety-guard/docs/decisions/adr-007-occlusion-handling-confidence-propagation.md) y [ADR-008](file:///Users/xander/Projects/edge-safety-guard/docs/decisions/adr-008-kalman-epistemology-noise-divergence.md)).
* **Enlaces de Descarga:**
  * [CAVIAR Test Case Scenarios – INRIA / University of Edinburgh](http://homepages.inf.ed.ac.uk/rbf/CAVIARDATA1/)

---

### Secuencia C: Permanencia / Merodeo (Loitering) y Cruce de Líneas Críticas
* **Dataset / Fuente:** Oxford TownCentre Dataset (1080p Full HD).
* **Escenario:** Cámara fija CCTV a $\approx 4\text{ m}$ de altura con pitch de $\approx 35^\circ$ observando un área peatonal con cuadrícula de adoquines claramente visible. Sujetos caminan, algunos se detienen por más de 5–15 segundos y otros bordean los límites.
* **Propiedades Técnicas:** $1920 \times 1080$ @ 25 FPS, vídeo sin movimiento de cámara, alta nitidez para estimación precisa de pose y pies.
* **Utilidad en el Pipeline:** Validación de lógica de zonas poligonales de peligro (Shapely / `prep(polygon)`), temporizadores de permanencia (*dwell time*) y bypass dinámico por velocidad de aproximación.
* **Enlaces de Descarga:**
  * [Oxford TownCentre Dataset en Kaggle (1080p MP4 + Ground Truth)](https://www.kaggle.com/)

---

## 3. Generación y Uso de Muestras Sintéticas Locales

Para pruebas automatizadas en CI y desarrollo local sin descargas externas, el proyecto incluye un generador determinista (`src/utils/synthetic_generator.py` y `scripts/generate_samples.py`) que reproduce la geometría planar, la calibración DLT y la cinemática de estos 3 escenarios:

```bash
# Generar las tres secuencias de prueba en data/samples/
python scripts/generate_samples.py --output-dir data/samples --fps 30
```

---

## 4. Herramientas Modulares de Descarga e Ingesta Real

Para evaluar el modelo y pipeline sobre secuencias reales sin modificar el código *core*, el repositorio proporciona un gestor de descarga y un arnés de pruebas desacoplado.

### 4.1 Catálogo y Descarga de Datasets (`scripts/download_datasets.py`)

El script cuenta con un registro centralizado, verificación de presencia local y failover automático entre múltiples *mirrors*:

```bash
# 1. Listar datasets registrados y su estado local
python scripts/download_datasets.py --list

# 2. Descargar la secuencia limpia de prueba primaria (OpenCV vtest)
python scripts/download_datasets.py --dataset opencv_vtest

# 3. Descargar la secuencia peatonal 1080p (OpenVINO people)
python scripts/download_datasets.py --dataset openvino_people
```

### 4.2 Arnés de Evaluación Desacoplado (`scripts/run_dataset_test.py`)

Ejecuta el pipeline completo de seguridad (`SafetyPipeline`) contra el video descargado y su archivo de calibración/zona YAML en `configs/datasets/`:

```bash
# Ejecutar evaluación de 75 frames en modo headless
python scripts/run_dataset_test.py --dataset opencv_vtest --max-frames 75 --no-display

# Ejecutar evaluación interactiva con ventana visual (OpenCV GUI)
python scripts/run_dataset_test.py --dataset opencv_vtest --display
```

### 4.3 Resultados y Métricas de Validación Baseline

Las corridas generan automáticamente los siguientes artefactos en `data/results/<dataset_name>/`:
* `annotated_<dataset_name>.mp4`: Video compuesto (perspectiva + BEV) con seguimiento de poses, matriz $H$ y disparos de zonas FSM.
* `events.jsonl`: Telemetría estructurada frame a frame con latencias por etapa ($T_1$), identificadores de track y tiempos de permanencia.
* `summary.json`: Resumen cuantitativo de rendimiento (FPS, latencias $p50/p95/p99$ y transiciones de estado).

| Dataset | Resolución | FPS Medido | Latencia Media ($T_1$) | $p95$ Latencia | Estado de Prueba |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`mendeley_industrial`** | $1920 \times 1080$ | $34.8\text{ FPS}$ | $17.74\text{ ms}$ | $24.42\text{ ms}$ | ✅ Validado (CCTV en planta de manufactura / pasillo de seguridad) |
| **`opencv_vtest`** | $768 \times 576$ | $40.8\text{ FPS}$ | $21.26\text{ ms}$ | $29.31\text{ ms}$ | ✅ Validado (Detección de intrusión e inmovilización) |
| **`openvino_people`** | $1920 \times 1080$ | $36.7\text{ FPS}$ | $18.27\text{ ms}$ | $22.41\text{ ms}$ | ✅ Validado (Tránsito en pasillo comercial 1080p) |
| **`pets2009_s2_l1`** | $768 \times 576$ | $40.6\text{ FPS}$ | $21.38\text{ ms}$ | $30.53\text{ ms}$ | ✅ Validado (Seguimiento multi-objetivo y zona de plaza) |



