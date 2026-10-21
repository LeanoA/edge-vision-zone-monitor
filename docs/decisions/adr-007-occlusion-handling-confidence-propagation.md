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

### 1. Jerarquía de Degradación Escalonada (`AnchorSource`)
1. **Nivel 1 (Fidelidad Plena - `AnchorSource.ANKLES_DUAL`):** Si ambos tobillos tienen $\text{conf} \ge \text{conf\_threshold}$ (por defecto $0.5$) y la altura de la caja satisface $h_{\text{bbox}} \ge \text{min\_ankle\_bbox\_height}$, se proyecta su punto medio con confianza media $\frac{c_{15}+c_{16}}{2} \times 1.0$ y covarianza de medición nominal ($1.0\times R$). Fuente: `AnchorSource.ANKLES_DUAL`.
2. **Nivel 2 (Fidelidad Monocular - `AnchorSource.ANKLE_SINGLE`):** Si un solo tobillo supera el umbral ($\text{conf} \ge 0.5$) y $h_{\text{bbox}} \ge \text{min\_ankle\_bbox\_height}$, se utiliza dicho tobillo como anclaje físico con confianza penalizada por $\times 0.75$ e inflación de covarianza $2.0\times R$. Fuente: `AnchorSource.ANKLE_SINGLE`.
3. **Nivel 3 (Proxy de Caja / Escala Lejana - `AnchorSource.BBOX_BOTTOM`):** Si ambos tobillos están ocluidos ($\text{conf} < 0.5$) o la caja se encuentra en campo lejano ($h_{\text{bbox}} < \text{min\_ankle\_bbox\_height}$), `extract_ground_anchor` proyecta el punto inferior central del bounding box $(\frac{x_1+x_2}{2}, y_2)$ con confianza penalizada por $\times 0.40$ e inflación de covarianza de medición $5.0\times R$ en la actualización de Joseph del filtro de Kalman. Fuente: `AnchorSource.BBOX_BOTTOM`.
4. **Nivel 4 (Filtro Cinemático / Coasting - `AnchorSource.TRACKER_PREDICTED`):** Si ocurre un *dropout* completo de detección (sin propuesta válida en el cuadro), el **MultiTargetKalmanTracker** retiene el track en modo `COASTING` extrapolando su estado cinemático $[X, Y, v_x, v_y]^T$ durante un máximo de $N_{\text{missed}} \le 5$ fotogramas con decaimiento exponencial de confianza $0.85^k$. Fuente: `AnchorSource.TRACKER_PREDICTED`.

### 2. Contrato de Estimación Métrica (Confidence Propagation)
Las coordenadas en metros e incertidumbres cinemáticas se encapsulan en `PositionEstimate` y `Track` (`src/core/kalman_filter.py`):

```python
class AnchorSource(str, Enum):
    ANKLES_DUAL = "ANKLES_DUAL"              # Tier 1: Midpoint of left and right ankles (conf * 1.0, 1.0x R)
    ANKLE_SINGLE = "ANKLE_SINGLE"            # Tier 2: Single detected ankle keypoint (conf * 0.75, 2.0x R)
    BBOX_BOTTOM = "BBOX_BOTTOM"              # Tier 3: Bounding box bottom-center proxy (score * 0.40, 5.0x R)
    TRACKER_PREDICTED = "TRACKER_PREDICTED"  # Tier 4: Dead reckoning via Kalman coasting (conf * 0.85^k)


@dataclass(frozen=True)
class PositionEstimate:
    xy_m: Tuple[float, float]                        # (x_m, y_m) on floor plane Zw = 0
    confidence: float                                # Normalized reliability in [0.0, 1.0]
    source: AnchorSource                             # "ANKLES_DUAL" | "ANKLE_SINGLE" | "BBOX_BOTTOM" | "TRACKER_PREDICTED"
    status: ObservationStatus = ObservationStatus.OBSERVED  # "OBSERVED" | "PREDICTED" | "STALE"
    covariance: Optional[np.ndarray] = None          # 2x2 spatial position error covariance matrix (m^2)
    missed_count: int = 0                            # Consecutive missed frames k (Track also exposes x_m, y_m, vx_m_s, vy_m_s)
```

## Consecuencias
- **Sin Puntos Ciegos:** Si un operario camina detrás de un pallet o máquina, el sistema mantiene el seguimiento métrico y el cálculo de intrusión mediante fallback `BBOX_BOTTOM` ($5.0\times R$) o *coasting* `TRACKER_PREDICTED` sin perder su historial de permanencia (*dwell time*).
- **Semántica Clara en Auditoría:** Un evento de alarma disparado con `source="ANKLES_DUAL"` tiene alta certeza geométrica; uno disparado con `source="BBOX_BOTTOM"` o `source="TRACKER_PREDICTED"` conserva trazabilidad explícita de su nivel de degradación.
- **Fail-Safe Temporal:** La ventana de coasting está acotada ($167\text{ ms}$, $k \le 5$); no se extrapola indefinidamente para evitar derivas cinemáticas.
