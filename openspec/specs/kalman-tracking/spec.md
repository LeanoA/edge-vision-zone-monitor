# Specification: Metric Kalman Tracking (`kalman-tracking`)

## Overview
The `kalman-tracking` capability provides real-time 2D metric state estimation, velocity vector tracking, and occlusion coasting for industrial edge safety monitoring. Operating on ground-plane metric coordinates $(X_w, Y_w)$ in meters ($Z_w = 0$), it eliminates high-frequency keypoint jitter ($\pm 15\text{ mm}$), estimates instantaneous velocity $(v_x, v_y)$ in $\text{m/s}$, and maintains target continuity through temporary visual dropouts up to `max_missed` frames. Implemented via `MetricKalmanFilter` and `MultiTargetKalmanTracker` (`src/core/kalman_filter.py`), this capability guarantees deterministic kinematic filtering required for ISO 13855 approach speed calculation and spatial hazard boundary evaluation.

## ADDED Requirements

### Requirement: Metric State Representation and Kinematic Model Initialization
The `MetricKalmanFilter` MUST represent target kinematics using a 4-dimensional state vector $x = [X, Y, v_x, v_y]^T \in \mathbb{R}^4$, where $(X, Y)$ denote 2D ground-plane coordinates in meters and $(v_x, v_y)$ denote velocity components in meters per second ($\text{m/s}$). The filter MUST initialize with user-provided initial metric position $(X_0, Y_0)$, zero initial velocity $(v_{x0} = 0.0, v_{y0} = 0.0)$, an initial error covariance matrix $P_0 \in \mathbb{R}^{4 \times 4}$, process noise covariance $Q \in \mathbb{R}^{4 \times 4}$, and measurement noise covariance $R \in \mathbb{R}^{2 \times 2}$. The measurement matrix $H \in \mathbb{R}^{2 \times 4}$ MUST map state space to 2D measurement space via:
$$H = \begin{bmatrix} 1 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 \end{bmatrix}$$

#### Scenario: Successful initialization with valid metric ground-plane coordinates
- **GIVEN** initial ground-plane coordinates $(X_0 = 1.5\text{ m}, Y_0 = 3.0\text{ m})$
- **WHEN** `MetricKalmanFilter` is instantiated with these coordinates
- **THEN** the state vector $x$ SHALL be initialized to $[1.5, 3.0, 0.0, 0.0]^T$
- **AND** the covariance matrix $P$ SHALL be initialized as a $4 \times 4$ positive-definite matrix
- **AND** measurement matrix $H$ SHALL have dimensions $(2, 4)$ with unit diagonal for position states.

#### Scenario: Rejecting invalid or non-numeric initial coordinates
- **GIVEN** initial coordinate inputs containing `NaN`, infinity, or non-numerical values
- **WHEN** `MetricKalmanFilter` initialization is attempted
- **THEN** the constructor SHALL raise a `ValueError` indicating that initial coordinates must be finite real numbers.

#### Scenario: Validating covariance matrix dimensions and positive definiteness
- **GIVEN** covariance matrices $P, Q, R$ supplied to `MetricKalmanFilter`
- **WHEN** the filter validates initialization parameters
- **THEN** $P$ and $Q$ MUST have shape $(4, 4)$ and $R$ MUST have shape $(2, 2)$
- **AND** any non-symmetric or non-positive semi-definite matrix SHALL raise a `ValueError`.

---

### Requirement: Predict and Update Execution with Discrete Time Interval ($\Delta t$)
The `MetricKalmanFilter` MUST execute discrete-time constant velocity (CV) prediction and Kalman measurement update cycles. The prediction cycle MUST project state and covariance forward by time step $\Delta t > 0$:
$$F(\Delta t) = \begin{bmatrix} 1 & 0 & \Delta t & 0 \\ 0 & 1 & 0 & \Delta t \\ 0 & 0 & 1 & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix}$$
$$x_{k|k-1} = F x_{k-1|k-1}$$
$$P_{k|k-1} = F P_{k-1|k-1} F^T + Q(\Delta t)$$
The update cycle MUST incorporate measured ground-plane coordinates $z = [X_m, Y_m]^T \in \mathbb{R}^2$ via:
$$y = z - H x_{k|k-1}$$
$$S = H P_{k|k-1} H^T + R$$
$$K = P_{k|k-1} H^T S^{-1}$$
$$x_{k|k} = x_{k|k-1} + K y$$
$$P_{k|k} = (I - K H) P_{k|k-1}$$

#### Scenario: Predict step with fixed time step
- **GIVEN** an active filter with state $x = [2.0, 1.0, 1.0, -0.5]^T$ and $\Delta t = 0.1\text{ s}$
- **WHEN** `predict(dt=0.1)` is executed
- **THEN** the predicted position SHALL equal $X = 2.0 + 1.0 \times 0.1 = 2.1\text{ m}$ and $Y = 1.0 - 0.5 \times 0.1 = 0.95\text{ m}$
- **AND** predicted velocities SHALL remain $v_x = 1.0\text{ m/s}$ and $v_y = -0.5\text{ m/s}$
- **AND** error covariance $P$ SHALL incorporate process noise $Q(\Delta t)$.

#### Scenario: Update step with noisy measurement reducing variance
- **GIVEN** a predicted filter state and a new metric measurement $z = [2.12, 0.94]^T$
- **WHEN** `update(z)` is executed
- **THEN** the state vector $x_{k|k}$ SHALL be updated towards measurement $z$ weighted by Kalman gain $K$
- **AND** the trace of error covariance matrix $\text{Tr}(P_{k|k})$ SHALL be strictly less than $\text{Tr}(P_{k|k-1})$.

#### Scenario: Attenuation of high-frequency keypoint jitter
- **GIVEN** a stationary operator keypoint trajectory corrupted with zero-mean Gaussian noise $\sigma = 0.015\text{ m}$ ($\pm 15\text{ mm}$)
- **WHEN** the filter processes 30 consecutive measurement updates
- **THEN** the root mean square error (RMSE) of the filtered trajectory relative to the true ground truth position SHALL be reduced by at least $70\%$ compared to raw measurement RMSE.

#### Scenario: Rejecting invalid non-positive time interval dt
- **GIVEN** an initialized `MetricKalmanFilter`
- **WHEN** `predict(dt)` is invoked with $\Delta t \le 0$
- **THEN** the method SHALL raise a `ValueError` requiring $\Delta t > 0$.

---

### Requirement: Adaptive Measurement Noise Scaling
The `MetricKalmanFilter` and `MultiTargetKalmanTracker` MUST support adaptive measurement noise scaling based on the ground anchor provenance source:
1. `MetricKalmanFilter.update(measurement, R=None)` MUST accept an optional measurement noise covariance override $R \in \mathbb{R}^{2 \times 2}$. If $R$ is `None`, the filter's nominal configured covariance $R_0 = \text{diag}([r_{\text{pos}}, r_{\text{pos}}])$ MUST be used.
2. The `MultiTargetKalmanTracker` MUST scale measurement noise covariance $R$ for associated detections according to their `AnchorSource`:
   - **`ANKLES_DUAL`**: $R = R_0 = \text{diag}([r_{\text{pos}}, r_{\text{pos}}])$ (nominal scale factor $1.0\times$).
   - **`ANKLE_SINGLE`**: $R = 2.0 \times R_0 = \text{diag}([2 \cdot r_{\text{pos}}, 2 \cdot r_{\text{pos}}])$ (scale factor $2.0\times$, reflecting stance lateral uncertainty).
   - **`BBOX_BOTTOM`**: $R = 5.0 \times R_0 = \text{diag}([5 \cdot r_{\text{pos}}, 5 \cdot r_{\text{pos}}])$ (scale factor $5.0\times$, dampening Kalman gain against obstacle vertical parallax).
3. The Euclidean distance gating threshold $d_{\text{gate}} = 1.0\text{ m}$ MUST reject candidate detections whose distance from the track's predicted state exceeds $d_{\text{gate}}$, preventing severe bounding box parallax jumps from corrupting active tracks and forcing degraded observations into coast mode.

#### Scenario: Nominal measurement noise update for dual ankles
- **GIVEN** a predicted filter state with nominal $R_0 = \text{diag}([0.05, 0.05])$
- **WHEN** `update` is executed with an `ANKLES_DUAL` measurement ($R = R_0$)
- **THEN** the filter SHALL use $R = \text{diag}([0.05, 0.05])$
- **AND** the resulting state innovation weighting SHALL follow nominal Kalman gain $K_0 = P H^T (H P H^T + R_0)^{-1}$.

#### Scenario: Dampened update with single ankle measurement
- **GIVEN** a predicted filter state with nominal $R_0 = \text{diag}([0.05, 0.05])$
- **WHEN** `update` is executed with an `ANKLE_SINGLE` measurement ($R = 2.0 \times R_0$)
- **THEN** the filter SHALL incorporate measurement noise $R = \text{diag}([0.10, 0.10])$
- **AND** the resulting Kalman gain $K$ SHALL be strictly smaller than $K_0$.

#### Scenario: Strongly dampened update with bounding box bottom measurement
- **GIVEN** a predicted filter state and an associated `BBOX_BOTTOM` measurement within $1.0\text{ m}$
- **WHEN** `update` is executed with $R = 5.0 \times R_0 = \text{diag}([0.25, 0.25])$
- **THEN** the filter SHALL incorporate $R = \text{diag}([0.25, 0.25])$
- **AND** the state adjustment along each axis SHALL be attenuated compared to dual ankle updates.

#### Scenario: Gating rejection of distant bbox bottom measurement
- **GIVEN** an active track at predicted ground position $(2.0, 3.0)\text{ m}$
- **AND** a candidate `BBOX_BOTTOM` detection projected to $(2.0, 4.2)\text{ m}$ ($d = 1.2\text{ m} > d_{\text{gate}} = 1.0\text{ m}$)
- **WHEN** `tracker.update` executes association
- **THEN** the measurement SHALL be rejected by spatial gating
- **AND** the active track SHALL NOT update with this measurement and SHALL transition to coast mode.

---

### Requirement: Velocity Estimation and Metric Vector Magnitude
The `MetricKalmanFilter` MUST continuously compute the 2D velocity vector $\vec{v} = [v_x, v_y]^T$ and its scalar speed magnitude $v = \|\vec{v}\|_2 = \sqrt{v_x^2 + v_y^2}$ in $\text{m/s}$. The filter SHALL also provide the heading angle $\theta = \text{atan2}(v_y, v_x)$ in radians.

#### Scenario: Velocity convergence during constant speed linear translation
- **GIVEN** a target moving along the X-axis at constant velocity $v_x = 1.6\text{ m/s}$ (ISO 13855 walking speed) with measurement noise $\sigma = 0.01\text{ m}$
- **WHEN** the filter processes 15 consecutive frames at $\Delta t = 0.033\text{ s}$ ($30\text{ fps}$)
- **THEN** the estimated velocity $v_x$ SHALL converge to $1.6\text{ m/s}$ within an error margin of $\pm 0.1\text{ m/s}$
- **AND** estimated orthogonal velocity $v_y$ SHALL remain within $\pm 0.08\text{ m/s}$ of zero
- **AND** scalar speed magnitude $v$ SHALL equal $\sqrt{v_x^2 + v_y^2}$.

#### Scenario: Stationary target velocity estimation
- **GIVEN** a stationary target with true velocity $0.0\text{ m/s}$ subjected to measurement noise
- **WHEN** the filter processes 20 frames of static measurements
- **THEN** the estimated speed magnitude $v$ SHALL be less than $0.05\text{ m/s}$.

---

### Requirement: Occlusion Coast Mode and Track Continuity
The `MetricKalmanFilter` and tracker MUST support an occlusion coast mode. When a target is temporarily not detected (due to occlusion, keypoint dropout, or camera blind spots), the filter MUST execute the prediction step using the kinematic model without performing a measurement update. The tracker MUST maintain track continuity without dropping the track for up to `max_missed` consecutive frames (default: 5 frames).

#### Scenario: Coasting through transient occlusion up to max_missed frames
- **GIVEN** an active track with `max_missed = 5` and valid initial velocity $\vec{v} = [1.0, 0.0]\text{ m/s}$
- **WHEN** no detection measurements are associated for 4 consecutive frames
- **THEN** the filter SHALL execute `predict()` at each frame without calling `update()`
- **AND** the missed frame counter SHALL increment from 0 to 4
- **AND** the track status SHALL remain active (coasting)
- **AND** the error covariance $P$ diagonal elements SHALL monotonically increase reflecting growing positional uncertainty.

#### Scenario: Immediate track recovery upon measurement reappearance
- **GIVEN** a track coasting at missed frame counter equal to 3
- **WHEN** a valid measurement is detected and associated with the track on the subsequent frame
- **THEN** `update(z)` SHALL be executed
- **AND** the missed frame counter SHALL be reset to 0
- **AND** the track status SHALL return to confirmed/active
- **AND** positional uncertainty in $P$ SHALL decrease immediately.

#### Scenario: Track expiration upon exceeding max_missed frames
- **GIVEN** a track coasting with missed frame counter equal to `max_missed` (5 frames)
- **WHEN** another frame elapses without an associated measurement
- **THEN** the tracker MUST mark the track as terminated/expired
- **AND** the track SHALL be purged from the active tracker list on the next cleanup cycle.

---

### Requirement: Track PositionEstimate Exposure and Kinematic Confidence Decay
The `Track` class MUST encapsulate metric uncertainty and provenance, exposing a typed `PositionEstimate` property, and MUST decay confidence exponentially during occlusion coasting:
1. **Contract Definition**: The system MUST define:
   - `AnchorSource(str, Enum)` with members `ANKLES_DUAL`, `ANKLE_SINGLE`, `BBOX_BOTTOM`, `TRACKER_PREDICTED`.
   - `PositionEstimate(frozen=True)` with fields `xy_m: Tuple[float, float]`, `confidence: float`, `source: AnchorSource`, and optional `covariance: Optional[np.ndarray] = None` representing the $2 \times 2$ position error covariance submatrix $P_{0:2, 0:2}$.
2. **Track Properties**: `Track` MUST expose:
   - `estimate -> PositionEstimate`: current state estimate tuple, confidence, source, and 2x2 covariance.
   - `confidence -> float`: current confidence scalar $\in [0.0, 1.0]$.
   - `source -> AnchorSource`: current provenance source.
3. **Kinematic Confidence Decay during Coasting**:
   - When a track is updated via matched measurement, `confidence` MUST be set to the measurement confidence $c_{\text{meas}}$ and `source` MUST match the measurement source.
   - When a track misses association and enters or remains in `COASTING` state (`mark_missed`):
     - `source` MUST be set to `AnchorSource.TRACKER_PREDICTED`.
     - `confidence` MUST decay exponentially as a function of consecutive missed frames:
       $$c_k = c_{\text{last\_confirmed}} \times (0.85)^{\text{missed\_count}}$$
       where $c_{\text{last\_confirmed}}$ is the confidence value at the last successful measurement update, and $\text{missed\_count} \in [1, \text{max\_missed}]$.
4. **Confidence Recovery upon Re-detection**:
   - When a coasting track is re-associated with a new measurement, `missed_count` MUST reset to 0, `confidence` MUST restore to the incoming measurement's confidence $c_{\text{meas}}$, and `source` MUST be updated to the measurement's `AnchorSource`.
5. **Backward Compatibility**: `Track.position` MUST continue returning `Tuple[float, float]` and `Track.velocity` MUST continue returning `Tuple[float, float]`. `MultiTargetKalmanTracker.update` MUST accept both legacy 2D coordinate arrays and typed `PositionEstimate` sequences.

#### Scenario: Track confidence decay across coasting frames
- **GIVEN** a confirmed track with last confirmed confidence $c_{\text{last}} = 0.90$ and source `AnchorSource.ANKLES_DUAL`
- **WHEN** no measurements associate with the track for 3 consecutive frames
- **THEN** on missed frame 1, `track.is_coasting()` SHALL be `True`, `track.source` SHALL be `AnchorSource.TRACKER_PREDICTED`, and `track.confidence` SHALL equal $0.90 \times 0.85 = 0.765$
- **AND** on missed frame 2, `track.confidence` SHALL equal $0.90 \times 0.85^2 = 0.65025$
- **AND** on missed frame 3, `track.confidence` SHALL equal $0.90 \times 0.85^3 \approx 0.5527$
- **AND** `track.estimate.covariance` SHALL reflect the inflated $2\times2$ position covariance from Kalman prediction.

#### Scenario: Recovery of confidence upon re-detection
- **GIVEN** a track coasting with `missed_count = 2` and decaying confidence
- **WHEN** a new detection with `AnchorSource.ANKLE_SINGLE` and confidence $0.60$ is associated with the track
- **THEN** `track.missed_count` SHALL reset to $0$
- **AND** `track.state` SHALL return to `TrackState.CONFIRMED`
- **AND** `track.source` SHALL equal `AnchorSource.ANKLE_SINGLE`
- **AND** `track.confidence` SHALL equal $0.60$
- **AND** `track.estimate.covariance` trace SHALL strictly decrease compared to the coasting covariance.

#### Scenario: Backward compatibility for track properties and raw inputs
- **GIVEN** existing test code accessing `track.position` and `track.velocity`
- **WHEN** tracking updates execute using raw `np.ndarray` of shape `(N, 2)`
- **THEN** `track.position` SHALL return a 2-tuple of floats
- **AND** `track.velocity` SHALL return a 2-tuple of floats
- **AND** `track.estimate.xy_m` SHALL match `track.position`.

---

### Requirement: Multi-Target Lifecycle Management and Spatial Association
The `MultiTargetKalmanTracker` MUST manage simultaneous tracking of multiple targets across consecutive video frames. It MUST handle the complete lifecycle of targets: birth (track creation), update (measurement association), coasting (unmatched tracks), and deletion (expired tracks). Association between existing track predictions and incoming metric ground-plane detections MUST use Euclidean distance gating with maximum association distance threshold $d_{\text{gate}}$ (default: $1.0\text{ m}$).

#### Scenario: Associating multiple detections to existing tracks
- **GIVEN** 2 active tracks at predicted coordinates $(1.0, 2.0)$ and $(4.0, 5.0)$
- **WHEN** 2 new detection coordinates $(1.05, 1.98)$ and $(3.95, 5.02)$ are passed to `tracker.update(detections)`
- **THEN** the tracker SHALL correctly associate detection 1 with track 1 and detection 2 with track 2
- **AND** both tracks SHALL have their Kalman filters updated with zero missed frames.

#### Scenario: Target birth for unassociated detections
- **GIVEN** an active tracker and a new detection coordinate that is not within $d_{\text{gate}}$ of any existing track
- **WHEN** `tracker.update(detections)` is invoked
- **THEN** the tracker SHALL instantiate a new `MetricKalmanFilter` for the detection
- **AND** a new unique monotonic integer track ID SHALL be assigned
- **AND** the new track SHALL be added to the active track dictionary.

#### Scenario: Target gating rejecting distant false associations
- **GIVEN** an existing track at predicted position $(1.0, 1.0)$ and a detection at $(5.0, 5.0)$ exceeding $d_{\text{gate}} = 1.0\text{ m}$
- **WHEN** association matching executes
- **THEN** the distant detection SHALL NOT be matched to the existing track
- **AND** the existing track SHALL transition to coast mode (missed counter incremented)
- **AND** a new separate track SHALL be spawned for the detection.

#### Scenario: Handling empty detection frames
- **GIVEN** an active tracker managing 3 confirmed tracks
- **WHEN** an empty detection list `[]` is passed to `tracker.update([])`
- **THEN** all 3 tracks SHALL execute `predict()`
- **AND** each track's missed counter SHALL increment by 1
- **AND** no exceptions SHALL be raised.

#### Scenario: Multi-target tracker output structure
- **GIVEN** an active tracker with confirmed and coasting tracks
- **WHEN** `tracker.get_tracks()` or `tracker.update()` returns results
- **THEN** the output SHALL contain a list or dictionary of track objects or records
- **AND** each record SHALL include `track_id`, metric position `(X, Y)`, velocity `(vx, vy)`, speed magnitude `v`, `is_coasting` boolean flag, and typed `estimate` (`PositionEstimate`).
