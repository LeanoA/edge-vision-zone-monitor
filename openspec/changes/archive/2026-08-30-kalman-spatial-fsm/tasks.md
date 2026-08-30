# Tasks: Metric Kalman Tracking & Spatial FSM with Dual Hysteresis

## Review Workload Forecast
Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

## Suggested Work Units
- **Unit 1: Metric Kalman Filter & Multi-Target Tracker**
  - Files: `src/core/kalman_filter.py`, `tests/test_kalman.py`
  - Focused test command: `pytest tests/test_kalman.py`
  - Runtime harness: Python 3.10+ / NumPy vectorization
  - Rollback boundary: Delete `src/core/kalman_filter.py`, `tests/test_kalman.py`
- **Unit 2: Spatial Safety FSM & Dual Hysteresis Engine**
  - Files: `src/core/spatial_fsm.py`, `tests/test_fsm.py`
  - Focused test command: `pytest tests/test_fsm.py`
  - Runtime harness: Shapely 2.0+ prepared geometries & Python dataclasses
  - Rollback boundary: Delete `src/core/spatial_fsm.py`, `tests/test_fsm.py`

## Implementation Tasks

### Phase 1: Metric Kalman Filter Kinematics (Unit 1)
- [x] 1.1 (RED) Write unit tests in `tests/test_kalman.py` for `MetricKalmanFilter` covering parameter validation, CV prediction ($F$), covariance reduction on update ($H, R$), analytical $2 \times 2$ innovation inverse, Joseph form covariance stabilization, speed magnitude ($v = \|\vec{v}\|_2$), heading angle, and $\ge 70\%$ jitter attenuation under $\sigma = 15\text{ mm}$ noise.
- [x] 1.2 (GREEN) Implement `MetricKalmanFilter` in `src/core/kalman_filter.py` with 4D state vector $[X, Y, v_x, v_y]^T$, discrete CV kinematics, analytical $S^{-1}$, Joseph form update, and velocity vector properties.
- [x] 1.3 (REFACTOR) Optimize array allocations, enforce strict typing, and verify with `pytest tests/test_kalman.py -k "filter"`.

### Phase 2: Track Lifecycle & Multi-Target Association (Unit 1)
- [x] 2.1 (RED) Write unit tests in `tests/test_kalman.py` for `TrackState` lifecycle (`TENTATIVE`, `CONFIRMED`, `COASTING`, `DELETED`), coast mode covariance growth across 4 missed frames, recovery on frame 5, track expiration at `max_missed > 5`, greedy Euclidean distance gating ($d_{\text{gate}} = 1.0\text{ m}$), empty detection frames, and multi-target tracking continuity.
- [x] 2.2 (GREEN) Implement `Track` dataclass and `MultiTargetKalmanTracker` in `src/core/kalman_filter.py` supporting greedy spatial association, track confirmation ($N_{\text{init}} \ge 2$), coasting prediction, and pruning.
- [x] 2.3 (REFACTOR) Profile greedy association latency ($< 0.05\text{ ms}$) and verify with `pytest tests/test_kalman.py`.

### Phase 3: Spatial Safety FSM & Dual Hysteresis (Unit 2)
- [x] 3.1 (RED) Write unit tests in `tests/test_fsm.py` for 6-state transitions (`SAFE`, `WARNING_APPROACH`, `DANGER_INTRUSION`, `MUTED`, `FAULT`, `LOCKOUT`), fail-safe startup (`trip == True`), concentric boundary buffering ($\Delta d = 0.20\text{ m}$), chattering suppression in $[P_{\text{danger}}, P_{\text{release}}]$, debounce counters ($N_{\text{confirm}} \ge 3$, $N_{\text{release}} \ge 5$), ISO 13855 approach velocity ($v_n \ge 1.6\text{ m/s}$ bypass), warning dwell time, and authorized manual reset.
- [x] 3.2 (GREEN) Implement `ZoneConfig`, `SafetyState`, `SafetyOutput`, and `SpatialFSM` in `src/core/spatial_fsm.py` with precomputed Shapely `prep()` geometries for $P_{\text{danger}}$ and $P_{\text{release}}$.
- [x] 3.3 (GREEN) Implement temporal debounce counters, ISO 13855 boundary-normal approach speed checks, dwell time monitor, and fail-safe trip output contract.
- [x] 3.4 (REFACTOR) Benchmark prepared geometry containment ($< 0.1\text{ ms}$ for 10 targets) and verify with `pytest tests/test_fsm.py`.

### Phase 4: Integration Verification & Regression Gate
- [x] 4.1 Run combined test suite with `pytest tests/test_kalman.py tests/test_fsm.py` to confirm 100% pass rate across all kinematic tracking and safety FSM scenarios.
- [x] 4.2 Run full project test suite with `pytest tests/` to confirm zero regression against existing homography and model export capabilities.
