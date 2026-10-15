# Specification Delta: Metric Kalman Tracking (`kalman-tracking`)

## MODIFIED Requirements

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
       $$c_k = c_{\text{last-confirmed}} \times (0.85)^{\text{missed-count}}$$
       where $c_{\text{last-confirmed}}$ is the confidence value at the last successful measurement update, and $\text{missed-count} \in [1, \text{max-missed}]$.
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
