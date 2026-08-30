# ADR-001: Estimación de Contacto con el Suelo: Ankle Keypoints (YOLO-Pose) vs Bounding Box Bottom-Center

- **Estatus:** Aceptado (Hipótesis Primaria sujeta a Benchmark Experimental)
- **Fecha:** 2026-08-29 (Revisado: 2026-08-30)
- **Módulo Asociado:** `src/pipeline/safety_pipeline.py` (`safety-pipeline`)

## Contexto
Para proyectar la posición métrica de un operario mediante homografía planar ($Z_w = 0$), el sistema necesita estimar el punto de contacto físico entre la persona y el suelo ($\hat{p}_{\text{ground}}$).

El baseline razonable en visión computacional **no es el centroide 2D de la caja**, sino el **borde inferior central (*bottom-center*)**:
$$p_{\text{ground\_bbox}} = \left( \frac{x_{\min} + x_{\max}}{2}, \, y_{\max} \right)$$

Frente a esto, un modelo de estimación de pose infiere keypoints anatómicos y calcula:
$$p_{\text{ground\_pose}} = \text{mean}\left(\text{valid\_ankles}(k_{15}, k_{16})\right)$$

Ambos enfoques intentan resolver exactamente el mismo problema geométrico: estimar el punto de apoyo en el suelo. La pregunta de arquitectura no es si Pose es "superior", sino: **¿justifican los keypoints de tobillo el costo computacional adicional frente a usar el borde inferior de una bounding box?**

## Opciones Consideradas y Trade-Offs

1. **Detector Estándar (Bounding Box Bottom-Center):**
   * *Mecanismo:* Inferencia de detección estándar (ej. YOLOv8n / YOLO11n). Punto en $( (x_{\min} + x_{\max})/2, y_{\max} )$.
   * *Ventajas:* Menor costo computacional ($\approx 30\text{–}40\%$ menos FLOPs y menor latencia), topología de red más simple y menor consumo de memoria. Inmune a la oclusión específica de pies (mientras detecte el cuerpo, infiere la base).
   * *Desventajas:* Si el operario se agacha, salta, se sienta, o sus pies no están alineados con la base del bbox, $y_{\max}$ introduce un sesgo proyectivo sistemático.
   * *Hipótesis:* Mayor velocidad, pero potencial ruido en posturas no bípedas.

2. **Estimador de Pose (Ankle Keypoints):**
   * *Mecanismo:* Inferencia de Pose (ej. YOLO11n-pose). Punto medio entre tobillo izquierdo (`idx 15`) y tobillo derecho (`idx 16`) condicionado por umbral de confianza ($conf \ge 0.5$).
   * *Ventajas:* Semántica anatómica real: mide dónde tocan efectivamente los pies el suelo, independientemente de que el operario esté inclinado hacia adelante o levantando un brazo.
   * *Desventajas:* Mayor latencia de inferencia y post-procesamiento. Vulnerable a oclusiones frecuentes en planta (pallets, maquinaria baja, indumentaria holgada o calzado cubierto) y a pérdida de confianza cuando los pies quedan en el borde inferior del encuadre.

## Decisión Tomada
Se adopta **YOLO-Pose (Ankle Keypoints)** como **hipótesis arquitectónica primaria**, implementando una política de degradación controlada (*fallback*):
1. Si ambos tobillos son válidos ($conf \ge 0.5$): promedio de tobillos.
2. Si un solo tobillo es visible: anclaje en el tobillo visible.
3. Si ambos tobillos están ocluidos: el filtro de Kalman cinemático 2D extrapola la trayectoria en espacio métrico (*coasting*).

Asimismo, se formula la comparación empírica **YOLO-Pose vs Bbox Bottom-Center** como un estudio experimental prioritario en el roadmap secundario.

## Consecuencias y Pregunta Experimental
- **Trade-Off Crítico:** Se asume un incremento de latencia a cambio de fidelidad anatómica en el punto de contacto.
- **Validación Experimental Pendiente:** Contrastar si la ganancia en estabilidad espacial de los tobillos compensa la pérdida de rendimiento frente al detector de cajas estándar bajo oclusiones industriales reales.
