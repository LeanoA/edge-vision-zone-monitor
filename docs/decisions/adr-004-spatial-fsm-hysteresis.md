# ADR-004: Gestión de Oscilaciones Espaciales mediante Spatial FSM + Filtro Kalman

- **Estatus:** Aceptado
- **Fecha:** 2026-08-29

## Contexto
En aplicaciones de seguridad industrial, la activación de paradas de emergencia o alarmas sonoras no puede tolerar oscilaciones rápidas (*flickering* o *chattering*) cuando un operario camina o trabaja en el borde exacto de una zona restringida.

## Opciones Consideradas

1. **Evaluación Booleana Instantánea por Frame (Point-in-Polygon):**
   - *Pros:* Implementación trivial (`polygon.contains(point)`).
   - *Contras:* Ruido en la detección de keypoints ($\pm 10\text{–}30\text{ mm}$) hace que el estado de alarma conmute erráticamente de un fotograma a otro en los bordes, destruyendo contactores físicos o disparando falsos positivos.

2. **Doble Histéresis: Espacial (Doble Polígono) + Temporal (Ventana de Frames) + Filtro Kalman:**
   - *Pros:* 
     - **Filtro Kalman 2D:** Suaviza la trayectoria del trabajador en el plano métrico, absorbiendo vibraciones de keypoints y oclusiones instantáneas.
     - **Histéresis Espacial:** Define dos polígonos concéntricos: $P_{\text{danger}}$ (incursión) y $P_{\text{release}}$ (despeje) con una separación $\Delta d \in [150, 300]\text{ mm}$.
     - **Histéresis Temporal:** Requiere $N_{\text{confirm}} \ge 3\text{–}5$ fotogramas consecutivos de persistencia para cambiar de estado (`OUTSIDE` $\rightarrow$ `INTRUSION_ACTIVE`).
   - *Contras:* Introduce un pequeño retardo determinista temporal equivalente a $N_{\text{confirm}} \times \Delta t_{\text{frame}}$ (aprox. $60\text{–}90\text{ ms}$), el cual se compensa formalmente en el cálculo de distancia de seguridad $S$.

## Decisión Tomada
Se selecciona la **Máquina de Estados Finitos Espacial (Spatial FSM)** combinada con **Filtro Kalman 2D** y doble polígono concéntrico con histéresis espacial y temporal.

## Consecuencias
- **Determinismo y Estabilidad:** Supresión total del chattering en actuadores de relés de seguridad.
- **Trazabilidad:** Posibilidad de registrar tiempos de permanencia (*dwell time*) para advertencias graduadas antes de la parada crítica.
