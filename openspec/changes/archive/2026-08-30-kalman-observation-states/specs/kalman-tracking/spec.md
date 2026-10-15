# Specification Delta: Metric Kalman Tracking (`kalman-tracking`)

## MODIFIED Requirements

### Requirement: Epistemological Observation States and Prediction Horizon Classification
The `MetricKalmanFilter` and `Track` domain models MUST formalize the epistemological validity of metric position estimates, distinguishing between direct sensory confirmation and kinematic extrapolation across prediction horizons:
1. **`ObservationStatus` Enumeration**: The system MUST define an enumeration `ObservationStatus(str, Enum)` with three discrete states:
   - `OBSERVED`: Supported by direct sensory measurement in the current frame ($k = 0$, where $k$ is the consecutive missed frame count). High epistemic certainty.
   - `PREDICTED`: Kinematically extrapolated via dead reckoning within the safe bounded horizon where divergence remains contained within the spatial hysteresis margin ($\Delta d = 200\text{ mm}$), specifically $1 \le k \le 3$ consecutive missed frames ($33.3\text{ ms} \le t \le 100.0\text{ ms}$ at $30\text{ fps}$).
   - `STALE`: Degraded dead reckoning nearing track deletion where kinematic maneuver divergence exceeds the spatial hysteresis margin ($4 \le k \le \text{max-missed}$, default $4 \le k \le 5$). Position estimates are speculative.
2. **Track Epistemological Status**: The `Track` class MUST expose an `observation_status -> ObservationStatus` property returning:
   - `ObservationStatus.OBSERVED` when `self.missed_count == 0`
   - `ObservationStatus.PREDICTED` when $1 \le \text{self.missed-count} \le 3$
   - `ObservationStatus.STALE` when $\text{self.missed-count} \ge 4$.
3. **Re-detection Transition**: Upon association with a fresh measurement, `missed_count` MUST immediately reset to 0, instantly transitioning `observation_status` back to `ObservationStatus.OBSERVED`.

#### Scenario: Fresh observation yields OBSERVED status
- **GIVEN** an active track receiving a matching measurement on the current frame
- **WHEN** `track.update(measurement)` is executed
- **THEN** `track.missed_count` SHALL equal `0`
- **AND** `track.observation_status` SHALL equal `ObservationStatus.OBSERVED`
- **AND** `track.estimate.status` SHALL equal `ObservationStatus.OBSERVED`.

#### Scenario: Coasting frames 1 to 3 yield PREDICTED status
- **GIVEN** an active track with an initial confirmed observation
- **WHEN** no detection measurements are associated for 1, 2, or 3 consecutive frames
- **THEN** for `missed_count` equal to 1, 2, and 3, `track.is_coasting()` SHALL be `True`
- **AND** `track.observation_status` SHALL equal `ObservationStatus.PREDICTED`
- **AND** `track.estimate.status` SHALL equal `ObservationStatus.PREDICTED`.

#### Scenario: Coasting frames 4 to 5 yield STALE status
- **GIVEN** an active track coasting with `missed_count = 3`
- **WHEN** missed frames continue to accrue for frames 4 and 5 (up to `max_missed = 5`)
- **THEN** for `missed_count` equal to 4 and 5, `track.is_coasting()` SHALL remain `True`
- **AND** `track.observation_status` SHALL equal `ObservationStatus.STALE`
- **AND** `track.estimate.status` SHALL equal `ObservationStatus.STALE`.

#### Scenario: Re-detection immediately restores OBSERVED status
- **GIVEN** a track in `STALE` status with `missed_count = 4`
- **WHEN** a valid measurement is associated on the subsequent frame via `track.update(...)`
- **THEN** `track.missed_count` SHALL reset to `0`
- **AND** `track.observation_status` SHALL immediately transition to `ObservationStatus.OBSERVED`
- **AND** `track.estimate.status` SHALL equal `ObservationStatus.OBSERVED`.

---

### Requirement: Track PositionEstimate Exposure and Kinematic Confidence Decay
The `Track` class MUST encapsulate metric uncertainty, provenance, and epistemological status, exposing a typed `PositionEstimate` property, and MUST decay confidence exponentially during occlusion coasting:
1. **Contract Definition**: The system MUST define:
   - `AnchorSource(str, Enum)` with members `ANKLES_DUAL`, `ANKLE_SINGLE`, `BBOX_BOTTOM`, `TRACKER_PREDICTED`.
   - `ObservationStatus(str, Enum)` with members `OBSERVED`, `PREDICTED`, `STALE`.
   - `PositionEstimate(frozen=True)` with fields:
     - `xy_m: Tuple[float, float]`
     - `confidence: float`
     - `source: AnchorSource`
     - `status: ObservationStatus = ObservationStatus.OBSERVED`
     - `covariance: Optional[np.ndarray] = None` (representing the $2 \times 2$ position error covariance submatrix $P_{0:2, 0:2}$)
     - `missed_count: int = 0`.
2. **Track Properties**: `Track` MUST expose:
   - `estimate -> PositionEstimate`: current state estimate tuple, confidence, source, `status`, `covariance`, and `missed_count`.
   - `observation_status -> ObservationStatus`: current epistemological status.
   - `confidence -> float`: current confidence scalar $\in [0.0, 1.0]$.
   - `source -> AnchorSource`: current provenance source.
   - `missed_count -> int`: consecutive missed frame counter.
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

#### Scenario: Track estimate reflects status and missed_count during coasting
- **GIVEN** a confirmed track with `c_last = 0.90`
- **WHEN** 2 consecutive frames elapse without measurement association
- **THEN** `track.missed_count` SHALL equal 2
- **AND** `track.estimate.status` SHALL equal `ObservationStatus.PREDICTED`
- **AND** `track.estimate.missed_count` SHALL equal 2
- **AND** `track.estimate.source` SHALL equal `AnchorSource.TRACKER_PREDICTED`.

#### Scenario: PositionEstimate default status validation
- **GIVEN** instantiation of `PositionEstimate(xy_m=(1.0, 2.0), confidence=0.8, source=AnchorSource.ANKLES_DUAL)`
- **WHEN** no explicit `status` or `missed_count` is passed
- **THEN** `estimate.status` SHALL default to `ObservationStatus.OBSERVED`
- **AND** `estimate.missed_count` SHALL default to `0`.
