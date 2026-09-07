# ADR-012: Generación de Videos Sintéticos Fotorrealistas con Escala Pinhole e Identidad Única

## Estado
Aceptado

## Contexto
Para validar de forma determinista y reproducible el pipeline de seguridad industrial (incursión limpia, oclusión de extremidades inferiores y tiempo de permanencia / *dwell time*), se diseñó un generador sintético de video (`src/utils/synthetic_generator.py`).

Sin embargo, las implementaciones iniciales sufrieron dos problemas fundamentales:
1. **Falta de Detección en YOLO (Synthetic Domain Gap):** Los humanoides dibujados con primitivas geométricas vectoriales planas (`cv2.line`, `cv2.rectangle`) carecían de los gradientes, texturas fotográficas y anatomía orgánica que activan los feature maps convolucionales de los modelos YOLO pre-entrenados en COCO ($conf = 0.00$, 0% detección).
2. **Inconsistencia de Identidad y Escala (*Identity Flickering & Underscaling*):** 
   - El muestreo discontinuo de candidatos causaba que el operario cambiara de vestimenta y silueta cada 3 fotogramas.
   - El escalado de altura por delta local sub-escalaba al sujeto en el fondo ($Y \ge 4.0\text{ m}$) a menos de 90 píxeles, provocando pérdida de detección por tamaño diminuto.
   - Los textos del generador colisionaban en la coordenada $y=50\text{ px}$ con el banner del HUD de seguridad.

## Decisión
Se decide implementar una arquitectura de renderizado sintético 2.5D basada en:
1. **Extracción y Normalización de Tracklet de Identidad Única:**
   - Un único sujeto continuo trackeado en video real mediante IoU es segmentado con `yolo11n-seg` y normalizado en un lienzo canónico de $160 \times 320\text{ RGBA}$ con alpha-feathering suave y anclaje de pies en el borde inferior.
2. **Escalado Perspectivo Pinhole Calibrado:**
   - La altura en píxeles del actor a cualquier profundidad métrica $Y \in [0.0, 6.0]\text{ m}$ sigue estrictamente la proyección de cámara estenopeica (*pinhole*):
     $$h_{px}(Y) = \frac{480.0}{1.0 + 0.165 \cdot Y}$$
     Garantizando $h \in [240, 480]\text{ px}$ y manteniendo al sujeto siempre dentro del rango óptimo de detección de YOLO.
3. **Sombra de Contacto Direccional Gaussiana:**
   - Proyección de elipse difusa con desenfoque Gaussiano bajo los pies del actor para integración visual sobre el piso industrial.
4. **Desacoplamiento Estricto de Capas de UI:**
   - El HUD del pipeline de seguridad se confina al banner superior (56px) con pastillas de alto contraste, mientras que la metadata de simulación se dibuja en un badge inferior ($y=1040\text{ px}$), evitando cualquier colisión textual.

## Consecuencias
### Positivas
* **100% de Tasa de Detección:** Cobertura total en las 3 secuencias de prueba (`sequence_a`, `sequence_b`, `sequence_c`).
* **Alta Confianza:** Confianza promedio de YOLO elevada a **0.835 - 0.861**.
* **Continuidad Temporal:** Cero saltos de vestimenta o silueta; el filtro de Kalman trackea un único sujeto continuo.
* **Trazabilidad Criptográfica & Invariantes:** Metadatos de ejecución integrados (SHA256, Git commit, perfiles de zona en `configs/datasets/` con `dwell_violation_s: 5.0`) y suite de aserciones automatizadas (`tests/test_benchmark_traceability.py`).
* **Legibilidad Industrial:** UI ultra-nítida con pastillas de contraste y badges de telemetría desacoplados.

### Negativas / Mitigaciones
* Requiere empaquetar una biblioteca liviana de sprites RGBA curados en `data/assets/sprites/worker/` (~200 KB).
