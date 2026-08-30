# ADR-007: Gestión de Oclusiones en Extremidades Inferiores y Propagación de Confianza

- **Estatus:** Aceptado
- **Fecha:** 2026-08-30
- **Módulo Asociado:** `src/pipeline/safety_pipeline.py`, `src/core/kalman_filter.py`

## Contexto
En un entorno industrial, la oclusión de las extremidades inferiores es el modo de fallo primario más común: maquinaria baja, pallets, carretillas elevadoras, herramientas o el propio borde inferior del sensor ocultan los pies de un trabajador cuyo torso permanece perfectamente visible:

```
camera
   ↓
┌──────────── frame
│
│   O
│  /|\
│  / \
│
│──────── maquinaria / obstáculo (oclusión)
│
└────────────
```

Bajo este escenario, el estimador de pose reporta baja confianza o ausencia total de keypoints en tobillos:
`conf(left_ankle) = 0.12`, `conf(right_ankle) = 0.08` frente a un umbral $T_{\text{conf}} = 0.5$.

Una arquitectura ingenua tiene dos extremos peligrosos:
1. **Descartar la observación en silencio:** Deja de monitorear al trabajador mientras penetra la zona de peligro.
2. **Usar puntos de baja confianza:** Proyecta ruido estocástico masivo en el plano métrico, provocando falsas alarmas o cálculos cinemáticos disparatados.

## Análisis de Alternativas ante Oclusión

| Alternativa | Descripción | Ventajas | Desventajas |
| :--- | :--- | :--- | :--- |
| **A) Rechazar observación** | Ignorar al trabajador si no hay tobillos válidos | Cero mediciones ruidosas en homografía | Peligro ciego: el trabajador existe pero el sistema no lo monitorea |
| **B) Anclaje en un solo tobillo** | Si un tobillo tiene $conf \ge 0.5$, usarlo | No requiere cajas ni modelos externos | Sesgo lateral de hasta $30\text{ cm}$ según la apertura de piernas |
| **C) Fallback a Bbox Bottom-Center** | Proyectar $((x_{\min}+x_{\max})/2, y_{\max})$ de la caja | Preserva presencia continua aunque los pies no se vean | Asume que la base del obstáculo coincide con el suelo |
| **D) Predicción vía Tracker (Coasting)** | El Filtro Kalman proyecta la trayectoria cinemática previa | Suave, determinista, sin saltos espaciales espurios | Válido solo por ventana corta ($N_{\text{missed}} \le 5$ frames $\approx 160\text{ ms}$) |
| **E) Declarar Incertidumbre Explícita** | Etiquetar la estimación con fuente y confianza | La FSM y el visualizador conocen la calidad del dato | Requiere propagación de contratos tipados en todo el pipeline |

## Decisión Tomada

Se adopta una **política de degradación escalonada (Graceful Degradation Hierarchy)** combinada con el concepto de **Propagación de Confianza (Confidence Propagation)**:

### 1. Jerarquía de Degradación Escalonada
1. **Nivel 1 (Fidelidad Plena - Dual Ankles):** Si ambos tobillos tienen $conf \ge 0.5$, se proyecta su punto medio. Fuente: `SourceType.ANKLES_DUAL`.
2. **Nivel 2 (Fidelidad Monocular - Single Ankle):** Si un solo tobillo supera el umbral, se utiliza dicho tobillo como anclaje físico. Fuente: `SourceType.ANKLE_SINGLE`.
3. **Nivel 3 (Filtro Cinemático - Coasting):** Si ambos tobillos caen por debajo del umbral, el pipeline no proyecta un punto nuevo a homografía; en su lugar, el **MultiTargetKalmanTracker** retiene el track en modo `COASTING` extrapolando su velocidad $[\dot{X}, \dot{Y}]$ durante un máximo de $N_{\text{missed}} = 5$ fotogramas. Fuente: `SourceType.TRACKER_PREDICTED`.
4. **Nivel 4 (Pérdida Crítica / Fallback):** Si la oclusión persiste más de $N_{\text{missed}}$ fotogramas o se trata de una pista no confirmada, se habilita el fallback a `BBOX_BOTTOM_CENTER` con penalización de confianza, o se marca el track como `DELETED`.

### 2. Contrato de Estimación Métrica (Confidence Propagation)
Las coordenadas en metros no deben tratarse como valores escalares idénticos. Representan el tipo conceptual:

```python
@dataclass(frozen=True)
class PositionEstimate:
    xy_m: Tuple[float, float]
    confidence: float
    source: str  # "ankles_dual" | "ankle_single" | "bbox_bottom" | "tracker_predicted"
    covariance: Optional[np.ndarray] = None
```

## Consecuencias
- **Sin Puntos Ciegos:** Si un operario camina detrás de un pallet o máquina, el sistema mantiene el seguimiento métrico y el cálculo de intrusión mediante *coasting* sin perder su historial de permanencia (*dwell time*).
- **Semántica Clara en Auditoría:** Un evento de alarma disparado con `source="ankles_dual"` tiene alta certeza geométrica; uno disparado con `source="tracker_predicted"` indica que el trabajador ya venía en trayectoria de incursión antes de ocluirse.
- **Fail-Safe Temporal:** La ventana de coasting está acotada ($160\text{ ms}$); no se extrapola indefinidamente para evitar derivas cinemáticas.
