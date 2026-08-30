# ADR-001: Selección de YOLO-Pose vs Bounding Box Centroid para Detección de Incursión

- **Estatus:** Aceptado
- **Fecha:** 2026-08-29

## Contexto
En sistemas de seguridad industrial y monitoreo de zonas restringidas, determinar el contacto físico o la posición exacta del trabajador sobre el suelo es crítico para calcular distancias de seguridad según la norma **ISO 13855:2024**.

## Opciones Consideradas

1. **Bounding Box Centroid / Bottom Center:**
   - *Pros:* Bajo costo computacional, compatible con detectores de objetos genéricos (YOLOv8/11 standard).
   - *Contras:* Alta susceptibilidad a oclusiones parciales, posturas inclinadas o brazos extendidos. El centroide del bounding box no representa el punto de contacto real con el suelo (los pies).

2. **YOLO-Pose (Extracción de Keypoints de Tobillos/Pies - Idx 15, 16):**
   - *Pros:* Proporciona la ubicación anatómica exacta del contacto con el suelo (tobillos/pies), permitiendo proyectar el punto real en el plano métrico independientemente de la postura del torso.
   - *Contras:* Ligero incremento en el tiempo de inferencia en comparación con detección pura de bounding boxes.

## Decisión Tomada
Se selecciona **YOLO-Pose** utilizando la media de los keypoints de los tobillos (`left_ankle: 15`, `right_ankle: 16`) como punto de contacto sobre el plano 2D. 

## Consecuencias
- **Precisión Geométrica:** Eliminación de falsos positivos causados por sombras o inclinación del torso.
- **Robustez en Homografía:** Los puntos proyectados al espacio 3D/métrico corresponden verdaderamente a la superficie donde camina el trabajador.
