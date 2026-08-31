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
Se selecciona la **Máquina de Estados Finitos Espacial (Spatial FSM)** combinada con **Filtro Kalman 2D** y doble polígono concéntrico con histéresis espacial y temporal asimétrica.

```
════════════════════════════════════════════════════════════════════════════════
              SCHMITT TRIGGER ESPACIAL Y ASIMETRÍA ENTRY / EXIT
════════════════════════════════════════════════════════════════════════════════

                      P_release (Límite de Liberación)
                   ┌───────────────────────────────────┐
                   │       Banda de Histéresis         │
                   │       (Δd = 200 mm)               │
                   │    P_danger (Límite de Peligro)   │
                   │   ┌───────────────────────────┐   │
                   │   │                           │   │
                   │   │          MÁQUINA          │   │
                   │   │                           │   │
                   │   └───────────────────────────┘   │
                   │                                   │
                   └───────────────────────────────────┘

1. ENTRY POLICY: CONSERVATIVE & FAST
   • Aproximación normal (vn < 1.6 m/s) : Debounce de N_confirm = 3 cuadros.
   • Aproximación rápida (vn >= 1.6 m/s): Bypass instantáneo (N_confirm = 1) en cuadro 1 (ISO 13855).

2. EXIT POLICY: HYSTERETIC & STRICT
   • Debounce de salida: Exige N_release = 5 cuadros consecutivos fuera de P_release.
   • Salvaguarda asimétrica (ADR-008): Desescalada permitida estrictamente con fotones reales (OBSERVED).
     Si el objetivo queda ocluido (PREDICTED / STALE), la salida se bloquea y el relé permanece abierto.
════════════════════════════════════════════════════════════════════════════════
```

## Consecuencias
- **Determinismo y Estabilidad:** Supresión total del chattering en actuadores de relés de seguridad.
- **Seguridad Fail-Safe:** Eliminación de demoras peligrosas en la entrada ante velocidades críticas, manteniendo máxima robustez en la salida.
- **Trazabilidad:** Posibilidad de registrar tiempos de permanencia (*dwell time*) para advertencias graduadas antes de la parada crítica.
