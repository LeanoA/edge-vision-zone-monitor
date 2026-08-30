# Proposal: Metric Kalman Tracking & Spatial FSM with Dual Hysteresis

## Intent
Eliminate boundary chattering, keypoint jitter ($\pm 15\text{ mm}$), and transient occlusions via 2D metric Kalman tracking and a 6-state safety FSM with dual spatial-temporal hysteresis for deterministic industrial safeguarding.

## Scope

### In Scope
- **Kalman Tracker (`src/core/kalman_filter.py`)**: `MetricKalmanFilter` ($[X, Y, v_x, v_y]^T$, CV model, $P/Q/R$ covariance, velocity vector, coasting) and `MultiTargetKalmanTracker`.
- **Spatial FSM (`src/core/spatial_fsm.py`)**: `SpatialFSM` with 6 discrete states (`SAFE`, `WARNING_APPROACH`, `DANGER_INTRUSION`, `MUTED`, `FAULT`, `LOCKOUT`), dual concentric polygons ($P_{\text{danger}}$, $P_{\text{release}}$ via Shapely buffer $\Delta d \in [150, 300]\text{ mm}$), temporal debounce ($N_{\text{confirm}} \ge 3$, $N_{\text{release}} \ge 5$), ISO 13855 approach speed ($K$), dwell time, and trip outputs.
- **Unit Tests**: Test suites in `tests/test_kalman.py` and `tests/test_fsm.py`.

### Out of Scope
- RTSP video ingestion and visual overlays.
- Physical GPIO relay hardware and industrial fieldbus protocols.

## Capabilities

### New Capabilities
- `kalman-tracking`: 2D ground-plane tracking, velocity estimation, and occlusion coasting.
- `spatial-fsm`: 6-state safety automaton with spatial-temporal hysteresis and trip generation.

### Modified Capabilities
- None.

## Approach
1. **Tracking**: Discrete CV state-space matrices ($F, H$) estimate position $(X, Y)$ and velocity $(v_x, v_y)$. Maintain track IDs with coasting during missing detections.
2. **Zones**: Precompute $P_{\text{release}}$ buffer ($\Delta d = 0.2\text{ m}$) from $P_{\text{danger}}$ using Shapely.
3. **FSM Logic**: Enforce $N_{\text{confirm}}$ consecutive violations for intrusion and $N_{\text{release}}$ clear frames for safe return. Evaluate velocity along boundary normal.
4. **Safety Interface**: Output fail-safe trip boolean (`True` on intrusion/fault/lockout) and telemetry.

## Affected Areas
| File | Change Type | Purpose |
| :--- | :--- | :--- |
| `src/core/kalman_filter.py` | New | Kalman filter and multi-target tracker |
| `src/core/spatial_fsm.py` | New | Safety FSM with dual hysteresis |
| `tests/test_kalman.py` | New | Kalman unit test suite |
| `tests/test_fsm.py` | New | Spatial FSM unit test suite |

## Risks & Mitigation
- **Coast Mode Drift**: Prolonged occlusion causes inaccurate extrapolation. Hard cap `max_missed` frames before track termination.
- **Geometric Overhead**: Dynamic polygon operations add latency. Precompute $P_{\text{release}}$ and prepare geometries for point containment.

## Rollback Plan
Remove `src/core/kalman_filter.py`, `src/core/spatial_fsm.py`, `tests/test_kalman.py`, and `tests/test_fsm.py`.

## Dependencies
- `numpy>=1.24.0`
- `shapely>=2.0.0`
- `pytest>=7.0.0`

## Success Criteria
- [ ] Trajectory jitter reduced by $\ge 70\%$ vs raw projections.
- [ ] Coast mode maintains track continuity across 5 missed frames.
- [ ] Boundary chattering eliminated within hysteresis margin $\Delta d$.
- [ ] Debounce enforces $N_{\text{confirm}} \ge 3$ and $N_{\text{release}} \ge 5$ frames.
- [ ] Trip signal asserts `True` on intrusion, fault, or lockout in $< 1\text{ ms}$.
- [ ] 100% test pass rate in `tests/test_kalman.py` and `tests/test_fsm.py`.
