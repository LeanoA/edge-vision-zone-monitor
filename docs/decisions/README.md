# Registro de Decisiones de Arquitectura (ADR)

Este directorio contiene las decisiones clave de ingeniería y arquitectura adoptadas a lo largo del desarrollo del proyecto.

## Estructura de un ADR

Cada documento debe seguir el formato estándar:

1. **Título y Contexto:** Problema o necesidad técnica identificada.
2. **Opciones Consideradas:** Alternativas analizadas con sus pros y contras.
3. **Decisión Tomada:** La solución elegida y los motivos técnicos de la elección.
4. **Consecuencias e Impacto:** Compensaciones (*trade-offs*), rendimiento y mantenibilidad.

---

## Índice de Decisiones

| ADR ID | Título | Estado | Fecha |
| :--- | :--- | :--- | :--- |
| [ADR-001](adr-001-yolo-pose-vs-bbox.md) | Estimación de Contacto con el Suelo: Ankle Keypoints (YOLO-Pose) vs Bbox Bottom-Center | Aceptado | 2026-08-29 |
| [ADR-002](adr-002-homography-vs-monocular-3d.md) | Proyección Homográfica 2D a Plano Métrico vs Estimación 3D Monocular | Aceptado | 2026-08-29 |
| [ADR-003](adr-003-onnx-runtime-coreml.md) | Runtime de Inferencia: ONNX Runtime (CoreML Provider) vs PyTorch Nativo | Aceptado | 2026-08-29 |
| [ADR-004](adr-004-spatial-fsm-hysteresis.md) | Gestión de Oscilaciones Espaciales mediante Spatial FSM + Filtro Kalman | Aceptado | 2026-08-29 |
| [ADR-005](adr-005-homography-vectorization-geometric-validation.md) | Validación Geométrica Preventiva y Proyección Vectorizada en Homografía Planar | Aceptado | 2026-08-29 |
| [ADR-006](adr-006-prepared-geometries-dynamic-debounce-bypass.md) | Geometrías Preparadas y Bypass Dinámico de Debounce en FSM de Seguridad (ISO 13855) | Aceptado | 2026-08-30 |
| [ADR-007](adr-007-occlusion-handling-confidence-propagation.md) | Gestión de Oclusiones en Extremidades Inferiores y Propagación de Confianza | Aceptado | 2026-08-30 |
| [ADR-008](adr-008-kalman-epistemology-noise-divergence.md) | Epistemología de Estados de Observación Kalman, Ruido Espectral y Desescalada Asimétrica | Aceptado | 2026-08-30 |
| [ADR-009](adr-009-decoupled-spatial-dwell-statecharts.md) | Desacoplamiento de Autómata Espacial y Clasificación Temporal de Dwell en Regiones Ortogonales | Aceptado | 2026-08-31 |
| [ADR-010](adr-010-dual-latency-profiling-iso13855.md) | Doble Horizonte Temporal de Latencia en Edge AI Industrial (ISO 13855 / IEC 61496) | Aceptado | 2026-08-31 |
| [ADR-011](adr-011-mahalanobis-hungarian-mot.md) | Bayesian Validation Gating (Mahalanobis $\chi^2$), Asignación Global Húngara y Spatial Birth NMS | Aceptado | 2026-09-01 |
| [ADR-012](adr-012-synthetic-yolo-video-generation.md) | Generación de Videos Sintéticos Fotorrealistas con Escala Pinhole e Identidad Única | Aceptado | 2026-09-02 |
| [ADR-013](adr-013-foveated-far-field-roi-inference.md) | Inferencia Foveada por Región de Interés en Campo Lejano (Foveated Far-Field ROI) y Delimitación Física de Senda Peatonal | Aceptado | 2026-10-21 |

