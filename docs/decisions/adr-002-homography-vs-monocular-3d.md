# ADR-002: Proyección Homográfica 2D a Plano Métrico vs Estimación 3D Monocular

- **Estatus:** Aceptado
- **Fecha:** 2026-08-29

## Contexto
Para validar distancias de separación según la norma **ISO 13855:2024**, el sistema requiere traducir coordenadas en píxeles de la cámara $(u, v)$ a posiciones métricas reales en el plano de planta $(X_w, Y_w)$ en metros.

## Opciones Consideradas

1. **Estimación de Pose 3D Monocular / Redes de Profundidad (ej. Depth-Anything, Monodepth):**
   - *Pros:* No requiere asumir que la escena es estrictamente planar; infiere coordenadas en volumen tridimensional.
   - *Contras:* Computacionalmente pesado en hardware Edge, escala métrica indeterminada o ruidosa (requiere calibración métrica compleja), latencia no determinista ($>60\text{ ms}$).

2. **Proyección Homográfica Planar 2D (Direct Linear Transformation - DLT):**
   - *Pros:* Operación matricial $3 \times 3$ ultraligera ($<0.1\text{ ms}$ por punto proyectado), determinista, y matemáticamente exacta para puntos que tocan el suelo (pies/tobillos del operario).
   - *Contras:* Asume que el piso es un plano coplanar ($Z=0$); requiere 4 o más puntos de calibración en la escena.

## Decisión Tomada
Se selecciona la **Transformación Homográfica Planar ($H \in \mathbb{R}^{3 \times 3}$)** calculada mediante el algoritmo DLT con calibración en 4 puntos de referencia en suelo. Dado que el contacto con el piso ocurre en $Z=0$, la transformación homográfica es biyectiva y elimina el overhead computacional de modelos 3D.

## Consecuencias
- **Latencia Mínima:** La proyección métrica consume tiempo despreciable en CPU, protegiendo el presupuesto temporal global ($t_1 \le 50\text{ ms}$).
- **Determinismo Matemático:** Sin fluctuaciones estocásticas de profundidad generada por redes neuronales.
