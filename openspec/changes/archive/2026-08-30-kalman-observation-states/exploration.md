# Exploration: Epistemological Observation States, Noise Modeling & Prediction Horizons in Metric Safety Tracking

**Change ID:** `kalman-observation-states`  
**Date:** 2026-08-30  
**Status:** In Review (Exploration)  
**Associated Proposed ADR:** `docs/decisions/adr-008-kalman-observation-states.md`  
**Applicable Standards:** ISO 13855:2024, ISO 13849-1 (PL d/e), IEC 61508 (SIL 2/3)  

---

## 1. Context & Problem Statement

In vision-based industrial safety monitoring (ISO 13855:2024), real-time perception models (such as YOLO Pose coupled with homography projection) produce metric ground-plane coordinates $(X_w, Y_w)$ of workers in the factory plane ($Z_w = 0$). To prevent boundary chattering, filter keypoint jitter, estimate approach velocities, and maintain track continuity during lower-limb occlusions (e.g. behind pallets, machinery skirts, or mobile equipment), the pipeline routes observations through a 2D Metric Kalman Filter (`src/core/kalman_filter.py`) before spatial containment evaluation in a finite state machine (`src/core/spatial_fsm.py`).

In the current implementation:
1. **Epistemic Conflation**:
   - `Track` maintains a lifecycle state machine (`TrackState`: `TENTATIVE`, `CONFIRMED`, `COASTING`, `DELETED`).
   - Ground positions are packaged into `PositionEstimate(xy_m, confidence, source, covariance)`.
   - However, the system conflates **track identity lifecycle** with the **epistemological validity of the current frame's position**. When a track is in `COASTING`, its source is set to `AnchorSource.TRACKER_PREDICTED` and confidence decays ($c = c_0 \cdot 0.85^k$). But downstream components have no first-class indicator of whether the estimate is:
     - Directly validated by fresh optical photons (`OBSERVED`),
     - Projected by dead reckoning within a mathematically safe temporal window (`PREDICTED`), or
     - Reaching the limits of physical credibility where unobserved human maneuvering invalidates the kinematic prior (`STALE`).
2. **Blind Consumption in Spatial FSM**:
   - `SpatialFSM.update` accepts `tracks: List[Track]`. It unpacks `trk.position`, `trk.velocity`, and `trk.speed`.
   - It **does not inspect** `trk.state`, `trk.source`, `trk.confidence`, `trk.missed_count`, or `trk.estimate`.
   - A track coasting for 5 frames ($167\text{ ms}$) without any physical observation is treated with identical epistemic authority as a track with dual-ankle verification.
3. **Critical Safety Asymmetry in Hazard De-escalation & Dwell Time**:
   - **Hazard Escalation (Fail-Safe)**: If an occluded track coasts into $P_{\text{danger}}$, `danger_count` increments and trips the safety relay. Tripping on prediction is conservative and safe.
   - **Hazard De-escalation (Hazardous)**: If a track currently violating $P_{\text{danger}}$ coasts outward into $P_{\text{safe}}$, `clean_count` increments. If it coasts outside for $N_{\text{release}} = 5$ frames, the FSM de-escalates and releases the trip **without any positive optical proof that the worker has exited the hazard zone**!
   - **Dwell Time Accumulation**: While coasting in $P_{\text{warning}}$, `dwell_time_s` continues accumulating monotonically against real wall-clock time, blurring the distinction between physically verified presence and dead-reckoning extrapolation.

This exploration establishes the mathematical, kinematic, and functional justification for distinguishing observation states, bounding prediction duration, tuning noise covariances ($Q$ vs $R$), and enforcing fail-safe de-escalation invariants.

---

## 2. Current State Analysis

### 2.1 Track Lifecycle vs Observation Provenance (`src/core/kalman_filter.py`)

#### `TrackState` vs `AnchorSource`
The codebase currently defines:
```python
class TrackState(str, Enum):
    TENTATIVE = "TENTATIVE"    # Initial detection, hits < n_confirm
    CONFIRMED = "CONFIRMED"    # Fully confirmed kinematic target
    COASTING = "COASTING"      # Active track with missing detection (missed <= max_missed)
    DELETED = "DELETED"        # Expired track (missed > max_missed)

class AnchorSource(str, Enum):
    ANKLES_DUAL = "ANKLES_DUAL"          # Tier 1: Midpoint of left and right ankles
    ANKLE_SINGLE = "ANKLE_SINGLE"        # Tier 2: Single detected ankle keypoint
    BBOX_BOTTOM = "BBOX_BOTTOM"          # Tier 3: Bounding box bottom-center proxy
    TRACKER_PREDICTED = "TRACKER_PREDICTED"  # Tier 4: Dead reckoning via Kalman prediction
```

#### Track Update Cycle
When a detection is associated (`Track.update`):
```python
self._filter.update(measurement, R=R)
self._hits += 1
self._missed_count = 0
self._source = source
self._confidence = float(confidence)
self._last_confirmed_confidence = float(confidence)
if self._state == TrackState.TENTATIVE and self._hits >= self._n_confirm:
    self._state = TrackState.CONFIRMED
elif self._state == TrackState.COASTING:
    self._state = TrackState.CONFIRMED
```

#### Track Miss Cycle
When a detection is missed (`Track.mark_missed`):
```python
self._missed_count += 1
self._source = AnchorSource.TRACKER_PREDICTED
self._confidence = self._last_confirmed_confidence * (0.85 ** self._missed_count)

if self._state == TrackState.TENTATIVE:
    self._state = TrackState.DELETED
elif self._state in (TrackState.CONFIRMED, TrackState.COASTING):
    if self._missed_count > self._max_missed:
        self._state = TrackState.DELETED
    else:
        self._state = TrackState.COASTING
```

#### Tracker Output
`MultiTargetKalmanTracker.confirmed_tracks` exports both `CONFIRMED` and `COASTING` tracks:
```python
@property
def confirmed_tracks(self) -> List[Track]:
    """Return all CONFIRMED and active COASTING tracks."""
    return [t for t in self._tracks if t.is_confirmed() or t.is_coasting()]
```
`max_missed` is default 5 frames ($\approx 166.7\text{ ms}$ at $30\text{ fps}$). While coasting, the track's position error covariance $P$ grows strictly by $F P F^T + Q$, and confidence decays by $0.85^k$ ($0.85 \to 0.72 \to 0.61 \to 0.52 \to 0.44$).

---

### 2.2 Spatial FSM Consumption (`src/core/spatial_fsm.py`)

In `SpatialFSM.update`:
1. **Uniform Track Consumption**:
   `SpatialFSM.evaluate_containment(tracks)` extracts positions from `trk.position` using `shapely.contains_xy`.
   Neither `trk.source`, `trk.state`, nor `trk.confidence` is evaluated.
2. **Debounce Logic**:
   - In Danger: `record.danger_count += 1`, `record.clean_count = 0`.
     If fast approach ($v_n \ge 1.6\text{ m/s}$), bypass debounce: `danger_count = max(danger_count + 1, n_confirm)`.
   - In Release: `record.clean_count = 0`. If not violating, `danger_count = 0`.
   - In Outside: `record.clean_count += 1`, `record.danger_count = 0`.
   - Violation Escalation: If `record.danger_count >= n_confirm`, target ID added to `_violating_track_ids`.
   - Violation De-escalation: If `not in_release and record.clean_count >= n_release`, target ID removed from `_violating_track_ids`.
3. **Disappearance Cleanup**:
   If a violating track is deleted (`missed > max_missed`), it disappears from `tracks`. The FSM loop at lines 453-457 increments `clean_count` on the missing track record. After $N_{\text{release}} = 5$ frames, the violation is discarded and the system returns to `SAFE`!

---

## 3. Mathematical & Kinematic Justification

### 3.1 Spectral Decomposition of Measurement Noise

Metric ground coordinates obtained via camera pose estimation are subject to three distinct noise sources:

$$\tilde{z}_k = z_k + \eta_{\text{jitter}} + \eta_{\text{quant}} + \eta_{\text{parallax}}$$

| Noise Source | Magnitude | Frequency Spectrum | Physical Origin |
| :--- | :--- | :--- | :--- |
| **Keypoint Jitter ($\eta_{\text{jitter}}$)** | $\pm 15\text{–}25\text{ mm}$ ($\sigma \approx 0.015\text{ m}$) | High frequency ($10\text{–}30\text{ Hz}$) | Neural network heatmap argmax regression, garment flutter, subtle illumination shifts |
| **Pixel Discretization ($\eta_{\text{quant}}$)** | $\pm 10\text{–}40\text{ mm}$ ($\sigma \approx \Delta / \sqrt{12}$) | High frequency | Finite sensor resolution ($640 \times 640$ letterbox), pixel grid quantization |
| **Bounding Box Parallax ($\eta_{\text{parallax}}$)** | $\pm 50\text{–}250\text{ mm}$ | Mid frequency ($2\text{–}5\text{ Hz}$) | Torso sway, arm articulation, low-angle projection geometry |
| **Human Center of Mass Motion** | Up to $1.6\text{–}2.5\text{ m/s}$ | Low frequency ($0\text{–}2\text{ Hz}$) | Intentional human walking, turning, acceleration |

#### Why Finite Differences ($\Delta x / \Delta t$) Fail
If velocity were computed directly via backward differences $\hat{v}_k = (z_k - z_{k-1}) / \Delta t$ at $30\text{ fps}$ ($\Delta t = 0.0333\text{ s}$):

$$\sigma_v = \frac{\sqrt{2} \sigma_{\text{pos}}}{\Delta t} = \frac{\sqrt{2} \times 0.015\text{ m}}{0.0333\text{ s}} \approx 0.637\text{ m/s} \quad (2.29\text{ km/h})$$

A $3\sigma$ fluctuation yields fictitious velocity spikes of $\approx 1.91\text{ m/s}$. Because ISO 13855 approach speed threshold is $K = 1.6\text{ m/s}$, **raw numerical differentiation falsely triggers the emergency dynamic bypass continuously on stationary operators**.

---

### 3.2 Why Constant Velocity (CV) is Sufficient at 30 fps

#### Discrete Constant Velocity (CV) Model
State vector $x = [X, Y, v_x, v_y]^T \in \mathbb{R}^4$:

$$x_k = F x_{k-1} + w_k, \quad F = \begin{bmatrix} 1 & 0 & \Delta t & 0 \\ 0 & 1 & 0 & \Delta t \\ 0 & 0 & 1 & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix}, \quad H = \begin{bmatrix} 1 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 \end{bmatrix}$$

#### Kinematic Discrepancy under Maximum Human Acceleration
In factory operations, maximum human acceleration during rapid walking or emergency stopping is bounded by friction and biomechanics:

$$a_{\text{max}} \approx 2.5\text{–}3.5\text{ m/s}^2$$

Over a single frame interval $\Delta t = 0.0333\text{ s}$:
1. **Velocity Delta**:
   $$\Delta v = a_{\text{max}} \Delta t \le 3.5 \times 0.0333 \approx 0.117\text{ m/s}$$
2. **Positional Displacement due to Acceleration**:
   $$\Delta x_{\text{acc}} = \frac{1}{2} a_{\text{max}} (\Delta t)^2 \le \frac{1}{2} (3.5) (0.0333)^2 \approx 0.00194\text{ m} = \mathbf{1.94\text{ mm}}$$

#### Comparison with Noise Floor
- Acceleration displacement per frame: $\mathbf{1.94\text{ mm}}$
- Measurement jitter noise floor: $\mathbf{15.0\text{ mm}}$
- Ratio: $\frac{\sigma_{\text{jitter}}}{\Delta x_{\text{acc}}} \approx \mathbf{7.7\times}$

The true physical displacement caused by human acceleration is an order of magnitude smaller than the sensor measurement noise. It is physically and mathematically impossible to estimate acceleration within a single $33\text{ ms}$ sample without severe noise amplification.

#### Why Constant Acceleration (CA) Fails (Noise Amplification)
If a Constant Acceleration (CA) model is adopted ($x = [X, Y, v_x, v_y, a_x, a_y]^T \in \mathbb{R}^6$), acceleration is inferred from the second difference of position:

$$\hat{a}_k \approx \frac{z_k - 2z_{k-1} + z_{k-2}}{\Delta t^2}$$

The estimation variance of acceleration is:

$$\text{Var}(\hat{a}) = \frac{1 + 4 + 1}{\Delta t^4} \sigma_{\text{pos}}^2 = \frac{6}{\Delta t^4} \sigma_{\text{pos}}^2$$

For $\Delta t = 0.0333\text{ s}$ ($\Delta t^4 \approx 1.23 \times 10^{-6}\text{ s}^4$) and $\sigma_{\text{pos}} = 0.015\text{ m}$:

$$\text{Var}(\hat{a}) = \frac{6 \times 2.25 \times 10^{-4}}{1.23 \times 10^{-6}} \approx 1097\text{ m}^2/\text{s}^4 \implies \sigma_a \approx \mathbf{33.1\text{ m/s}^2 \ (> 3.3\text{ g})}$$

**Result**: A CA filter generates massive false acceleration oscillations, destabilizing state estimation, inducing lag, and destroying boundary containment reliability. CV with process noise representing maneuverability is mathematically optimal.

---

### 3.3 Process Noise $Q$ vs Measurement Noise $R$

The filter balances confidence in the physical model ($Q$) against confidence in the optical sensor ($R$).

#### Measurement Noise Covariance $R$
$R = \text{diag}([r_{\text{pos}}, r_{\text{pos}}])$ with adaptive scaling by provenance tier:
- **`ANKLES_DUAL`** ($1.0\times$): $r_{\text{pos}} = 0.05\text{ m}^2$ ($\sigma_{\text{eff}} \approx 0.22\text{ m}$, incorporating calibration and homography condition number $\kappa(H)$).
- **`ANKLE_SINGLE`** ($2.0\times$): $r_{\text{pos}} = 0.10\text{ m}^2$ (accommodates stance-phase lateral offset up to $0.30\text{ m}$).
- **`BBOX_BOTTOM`** ($5.0\times$): $r_{\text{pos}} = 0.25\text{ m}^2$ (dampens Kalman gain against low-lying obstacle parallax).

#### Process Noise Covariance $Q$
Human deviations from constant velocity are modeled as zero-mean white noise acceleration $w_a \sim \mathcal{N}(0, \sigma_a^2)$.
Under the Discrete White Noise Acceleration (DWNA) formulation:

$$Q = \begin{bmatrix} \frac{\Delta t^3}{3} \sigma_a^2 & 0 & \frac{\Delta t^2}{2} \sigma_a^2 & 0 \\ 0 & \frac{\Delta t^3}{3} \sigma_a^2 & 0 & \frac{\Delta t^2}{2} \sigma_a^2 \\ \frac{\Delta t^2}{2} \sigma_a^2 & 0 & \Delta t \sigma_a^2 & 0 \\ 0 & \frac{\Delta t^2}{2} \sigma_a^2 & 0 & \Delta t \sigma_a^2 \end{bmatrix}$$

For human walking with $\sigma_a \approx 2.0\text{ m/s}^2$ and $\Delta t = 0.0333\text{ s}$:
- Position process variance: $Q_{\text{pos}} = \frac{(0.0333)^3}{3} (4.0) \approx 4.9 \times 10^{-5}\text{ m}^2$
- Velocity process variance: $Q_{\text{vel}} = 0.0333 \times 4.0 \approx 0.133\text{ (m/s)}^2$

Our implementation's default diagonal $Q = \text{diag}([0.01, 0.01, 0.10, 0.10])$ provides conservative responsiveness to turns while suppressing velocity estimation jitter.

---

### 3.4 Bounding Prediction-Only Duration: The Horizon of Safe Extrapolation

When visual detections drop ($z_k = \emptyset$), the filter operates open-loop (dead reckoning):

$$\hat{x}_k = F^k \hat{x}_0, \quad P_k = F^k P_0 (F^k)^T + \sum_{j=0}^{k-1} F^j Q (F^j)^T$$

#### Kinematic Divergence Under Maneuvering
During open-loop prediction, the true operator may execute an unexpected maneuver (e.g. pivoting $90^\circ$, stopping suddenly, or accelerating toward the hazard).
The maximum position divergence between the true position $p_k$ and the dead-reckoned prediction $\hat{p}_k$ is:

$$\|\Delta p(t)\| \le \frac{1}{2} a_{\text{max}} t^2 + v_0 t (1 - \cos \theta)$$

Evaluating across consecutive missed frames at $30\text{ fps}$ ($\Delta t = 33.3\text{ ms}$, $v_0 = 1.6\text{ m/s}$, $a_{\text{max}} = 3.0\text{ m/s}^2$):

| Missed Frames ($k$) | Extrapolated Time ($t$) | Trajectory Overshoot ($v_0 t$) | Maneuver Divergence ($\frac{1}{2} a t^2$) | Total Max Divergence | Relation to Hysteresis Buffer ($\Delta d = 200\text{ mm}$) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1 frame** | $33.3\text{ ms}$ | $53\text{ mm}$ | $1.7\text{ mm}$ | $\approx 55\text{ mm}$ | Well inside buffer ($27.5\%$) |
| **2 frames** | $66.7\text{ ms}$ | $107\text{ mm}$ | $6.7\text{ mm}$ | $\approx 113\text{ mm}$ | Inside buffer ($56.5\%$) |
| **3 frames** | $100.0\text{ ms}$ | $160\text{ mm}$ | $15.0\text{ mm}$ | $\approx 175\text{ mm}$ | Approaching buffer limit ($87.5\%$) |
| **4 frames** | $133.3\text{ ms}$ | $213\text{ mm}$ | $26.7\text{ mm}$ | $\approx 240\text{ mm}$ | **Exceeds buffer** ($120\%$) |
| **5 frames** | $166.7\text{ ms}$ | $267\text{ mm}$ | $41.7\text{ mm}$ | $\approx 308\text{ mm}$ | **Grossly exceeds buffer** ($154\%$) |

#### Covariance Expansion
Under open-loop prediction, positional covariance grows cubically with time:

$$\text{Tr}(P_{\text{pos}}(k)) \approx \text{Tr}(P_{\text{pos}}(0)) + 2 k q_{\text{pos}} + \frac{2 k^3 \Delta t^2}{3} q_{\text{vel}}$$

By frame 4–5, the $3\sigma$ positional confidence ellipse exceeds $0.60\text{ m}$ in diameter.

#### Epistemological Categorization
1. **$k = 0$ (`OBSERVED`)**: Optical confirmation. Innovation $y = z - Hx$ assimilated. High epistemic certainty.
2. **$1 \le k \le 3$ ($\le 100\text{ ms}$) (`PREDICTED`)**: Valid dead reckoning. Divergence is strictly contained within the spatial hysteresis buffer ($\Delta d = 200\text{ mm}$). Valid for proactive danger tripping and continuous tracking.
3. **$4 \le k \le 5$ ($133\text{–}167\text{ ms}$) (`STALE`)**: Kinematic divergence exceeds the hysteresis margin. Position is speculative.
   - **Allowed**: Sustaining an existing trip, triggering a proactive danger trip if trajectory points inward.
   - **Prohibited**: De-escalating from danger, releasing trips, or resetting dwell timers.
4. **$k > 5$ ($> 167\text{ ms}$) (`EXPIRED` / `DELETED`)**: Prediction ceases to have physical meaning. Track must be deleted. If deleted while inside the danger zone, the system must trigger a safety fault or latch lockout until physical manual verification is performed.

---

## 4. Epistemological Observation States & Proposed Architecture

### 4.1 New Contract: `ObservationStatus`

```python
class ObservationStatus(str, Enum):
    """Epistemological validity of a metric position estimate in the current frame."""
    OBSERVED = "OBSERVED"      # Supported by direct sensory measurement in current frame
    PREDICTED = "PREDICTED"    # Kinematically extrapolated within safe horizon (1 <= missed <= 3)
    STALE = "STALE"            # Degraded dead reckoning nearing expiry (4 <= missed <= max_missed)
```

### 4.2 Enriched `PositionEstimate` and `Track` Properties

```python
@dataclass(frozen=True)
class PositionEstimate:
    xy_m: Tuple[float, float]
    confidence: float
    source: AnchorSource
    status: ObservationStatus = ObservationStatus.OBSERVED
    covariance: Optional[np.ndarray] = None
    missed_count: int = 0
```

In `Track`:
```python
@property
def observation_status(self) -> ObservationStatus:
    """Current epistemological observation status."""
    if self._missed_count == 0:
        return ObservationStatus.OBSERVED
    elif self._missed_count <= 3:
        return ObservationStatus.PREDICTED
    else:
        return ObservationStatus.STALE

@property
def estimate(self) -> PositionEstimate:
    return PositionEstimate(
        xy_m=self.position,
        confidence=self._confidence,
        source=self._source,
        status=self.observation_status,
        covariance=self._filter.covariance[:2, :2].copy(),
        missed_count=self._missed_count,
    )
```

---

## 5. Fail-Safe Invariants for Spatial FSM

To guarantee compliance with IEC 61508 / ISO 13849-1 fail-safe principles, the Spatial FSM must enforce the following state transition matrix:

```
                  ┌─────────────────────────────────────────────────────────┐
                  │                 OBSERVATION STATUS                      │
┌─────────────────┼───────────────────┬───────────────────┬─────────────────┤
│ SAFETY ACTION   │     OBSERVED      │     PREDICTED     │      STALE      │
├─────────────────┼───────────────────┼───────────────────┼─────────────────┤
│ Trip Danger     │ YES (Immediate    │ YES (Proactive    │ YES (Safety     │
│ (Escalation)    │  or Debounce)     │  Fail-Safe)       │  Preservation)  │
├─────────────────┼───────────────────┼───────────────────┼─────────────────┤
│ Clear Danger    │ YES (Requires     │ NO (NEVER clear   │ NO (NEVER clear │
│ (De-escalation) │  N_release hits)  │  on prediction)   │  on dead reck.) │
├─────────────────┼───────────────────┼───────────────────┼─────────────────┤
│ Dwell Accrual   │ YES (Monotonic    │ FREEZE (Preserve  │ FREEZE (Flag as │
│                 │  wall-clock)      │  last observed)   │  unverified)    │
├─────────────────┼───────────────────┼───────────────────┼─────────────────┤
│ Track Lost in   │ N/A               │ N/A               │ LOCKOUT / FAULT │
│ Hazard Zone     │                   │                   │ (Cannot assume) │
└─────────────────┴───────────────────┴───────────────────┴─────────────────┘
```

### Critical Rules
1. **Asymmetric De-escalation Rule**: A track can only increment `clean_count` if `track.observation_status == ObservationStatus.OBSERVED`. A coasting track (`PREDICTED` or `STALE`) drifting out of $P_{\text{danger}}$ or disappearing cannot de-escalate a hazard.
2. **Missing Target Latch Rule**: If a track that is currently marked violating (`tid in _violating_track_ids`) expires (`missed > max_missed`), the FSM must **NOT** automatically release after $N_{\text{release}}$ blank frames. It must latch into `LOCKOUT` or require an authorized physical reset (`SpatialFSM.reset()`), preventing a scenario where an occluded injured worker inside a cell causes the machine to restart.
3. **Dwell Time Freezing**: While a track is `PREDICTED` or `STALE`, its `dwell_time_s` does not accumulate false presence duration; it is frozen at the last physically observed timestamp, or tagged with a `dwell_observed` flag.

---

## 6. Comparison of Implementation Approaches

| Approach | Architectural Strategy | Pros | Cons | Effort |
| :--- | :--- | :--- | :--- | :---: |
| **Approach 1: Minimal Documentation Only** | Write ADR-008 and Q&A explaining the math without changing code. | Zero code risk, 100% backward compatible. | FSM de-escalation safety loophole remains active in code. | Low (1-2 h) |
| **Approach 2: Pure Contract Enrichment (`kalman_filter.py`)** | Add `ObservationStatus` enum, enrich `PositionEstimate` and `Track.observation_status`. Keep `SpatialFSM` as-is. | Provides typed contracts for pipeline and telemetry; zero breaking changes in FSM. | Does not enforce the asymmetric de-escalation invariant in FSM. | Low-Med (2-3 h) |
| **Approach 3: End-to-End Epistemological Safeguarding (Recommended)** | Enrich `kalman_filter.py` with `ObservationStatus`, update `SpatialFSM` to enforce asymmetric de-escalation and freeze coasting dwell time, document in ADR-008 and Q&A. | Mathematically rigorous, closes critical safety loopholes, fully compliant with ISO 13849/13855 fail-safe logic. | Requires updating existing FSM test cases that assumed de-escalation during track expiration. | Medium (4-6 h) |

---

## 7. Recommended Action Plan & Next Steps

1. **Adopt Approach 3 (End-to-End Epistemological Safeguarding)** in the upcoming design and implementation phases.
2. **Deliverables for Change `kalman-observation-states`**:
   - `openspec/changes/kalman-observation-states/proposal.md`
   - `openspec/changes/kalman-observation-states/specs/kalman-tracking/spec.md` (delta)
   - `openspec/changes/kalman-observation-states/specs/spatial-fsm/spec.md` (delta)
   - `openspec/changes/kalman-observation-states/design.md`
   - `openspec/changes/kalman-observation-states/tasks.md`
   - `docs/decisions/adr-008-kalman-observation-states.md`
   - `docs/architecture/preguntas-y-respuestas-arquitectura.md` (Q16 & Q17 additions)
   - `README.md` & `docs/decisions/README.md` updates
   - Code updates in `src/core/kalman_filter.py` and `src/core/spatial_fsm.py`
   - Comprehensive test suite additions in `tests/test_kalman.py` and `tests/test_fsm.py`.
