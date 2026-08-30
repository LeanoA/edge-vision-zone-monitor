# ADR-002: Proyección Homográfica 2D a Plano Métrico vs Estimación 3D Monocular

- **Estatus:** Aceptado
- **Fecha:** 2026-08-29
- **Módulo Asociado:** `src/core/homography.py` (`calibration-homography`)

## Contexto
Para auditar distancias de aproximación y zonificación en planta, los sistemas convencionales definen regiones de interés (*ROIs*) en el espacio de la imagen como polígonos de píxeles:
```
pixel ROI: [(327, 412), (598, 390), (620, 580), (280, 560)] px
```
Este enfoque sufre de distorsión proyectiva severa inducida por la inclinación de la cámara (ángulos picados/cenitales): la escala de píxel a metro no es lineal (10 px en primer plano $\ne$ 10 px cerca del horizonte), lo que impide calcular distancias euclidianas reales, velocidades cinemáticas o distancias a máquinas.

Se requería una solución para traducir las observaciones de la cámara a un marco físicamente interpretable.

## Opciones Consideradas

1. **Estimación de Pose 3D Monocular / Redes de Profundidad (ej. Depth-Anything, Monodepth):**
   - *Pros:* No requiere asumir que la escena es estrictamente planar; infiere coordenadas en volumen tridimensional.
   - *Contras:* Computacionalmente pesado en hardware Edge, escala métrica indeterminada o ruidosa (requiere calibración métrica compleja), latencia no determinista ($>60\text{ ms}$) y consumo excesivo de memoria.

2. **Proyección Homográfica Planar 2D (Direct Linear Transformation - DLT):**
   - *Pros:* Operación matricial $3 \times 3$ ultraligera ($<0.1\text{ ms}$ por punto proyectado), determinista, y matemáticamente exacta para puntos en contacto con el suelo ($Z_w=0$).
   - *Transformación Conceptual:* Convierte un polígono arbitrario en píxeles en una zona métrica real:
     ```
     camera image -> pixel coordinates (u, v) -> [ H ] -> ground coordinates (X, Y) [m]
     ```
     Permite definir la zona peligrosa como $X \in [1.0, 2.5]\text{ m}, Y \in [0.5, 2.0]\text{ m}$, habilitando el cálculo de distancias reales a máquinas, velocidad cinemática $[\dot{X}, \dot{Y}]$, dwell distance y zonas concéntricas.
   - *Contras:* Asume que el piso es aproximadamente planar ($Z=0$); requiere al menos 4 puntos de calibración en planta.

## Decisión Tomada
Se selecciona la **Transformación Homográfica Planar ($H \in \mathbb{R}^{3 \times 3}$)** mediante el algoritmo DLT con anclaje en el punto medio de los tobillos del operario.

Dado que el contacto del operario con el piso ocurre en $Z=0$, la matriz de proyección de cámara colapsa a una transformación proyectiva biyectiva invertible $H$:
$$\hat{P}_{\text{world}} = H(\hat{p}_{\text{feet}})$$

### Cadena de Propagación de Errores e Incertidumbre
Una coordenada estimada en metros $\hat{P}_{\text{world}}$ no implica conocimiento exacto de la posición real. En ella convergen cinco fuentes de incertidumbre:
```
pose estimation error (detección de keypoints de tobillos)
        +
pixel quantization (discretización del sensor)
        +
camera calibration error (incertidumbre en puntos DLT ground-truth)
        +
ground-plane assumption (desniveles del suelo Z ≠ 0)
        +
homography numerical error (número de condición matricial κ(H))
```

Por ende, reportar que un trabajador se encuentra a "$0.93\text{ m}$ del peligro" representa una estimación sobre el plano del suelo con tolerancia finita ($\pm \epsilon$). No debe asumirse precisión centimétrica sin una calibración geométrica rigurosa y un análisis de condicionamiento $\kappa(H)$.

## Consecuencias
- **Físicamente Interpretable:** Las zonas y distancias se expresan en metros reales del taller, posibilitando telemetría industrial y auditoría de velocidades.
- **Latencia Mínima:** La proyección métrica toma $< 0.05\text{ ms}$ en CPU, preservando el presupuesto de latencia ($T_1$).
- **Determinismo Matemático:** Álgebra lineal sin fluctuaciones estocásticas de profundidad generadas por redes neuronales.
