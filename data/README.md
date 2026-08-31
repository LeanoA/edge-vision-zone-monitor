# Data & Samples Directory

Este directorio almacena las muestras de video y calibraciones para validación experimental.

Para más detalles sobre los datasets públicos recomendados (PETS 2009, INRIA CAVIAR, Oxford TownCentre), consultar [docs/data/datasets.md](../docs/data/datasets.md).

## Generación de Muestras Sintéticas

Puedes generar las tres secuencias de prueba deterministas (`sequence_a_clean_incursion.mp4`, `sequence_b_occlusion_coasting.mp4`, `sequence_c_dwell_loitering.mp4`) ejecutando:

```bash
python scripts/generate_samples.py --output-dir data/samples
```
