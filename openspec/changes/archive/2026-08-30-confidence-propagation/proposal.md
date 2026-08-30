# Proposal: Lower-Limb Occlusion Degradation & Confidence Propagation

## Intent
Eliminate blind spots when ankles are occluded by implementing a 4-tier graceful degradation anchor extraction hierarchy and typed confidence propagation (`PositionEstimate`) throughout the perception-tracking-FSM chain.

## Scope

### In Scope
- **`PositionEstimate` & `AnchorSource`**: Typed model (`ANKLES_DUAL`, `ANKLE_SINGLE`, `BBOX_BOTTOM`, `TRACKER_PREDICTED`) with covariance.
- **Anchor Degradation Hierarchy**: Implement `extract_ground_anchor` with fallback from dual ankles to single ankle and bbox bottom-center. Retain `extract_ankle_anchor`.
- **Kinematic Confidence Decay**: Add `Track.estimate` with exponential decay ($0.85^{\text{missed}}$) during coasting.
- **Adaptive Kalman Measurement Noise**: Scale measurement noise $R$ by source in `MetricKalmanFilter.update`.
- **Backward-Compatible Metadata**: Propagate `PositionEstimate` through `PoseDetection` and `PipelineResult`.

### Out of Scope
- Multi-camera fusion and spatial cross-view aggregation.
- 3D body mesh reconstruction.
- Neural network model retraining.

## Capabilities

### Modified Capabilities
- `safety-pipeline`: Add ground anchor fallback hierarchy and `PositionEstimate` metadata propagation.
- `kalman-tracking`: Add confidence decay during coasting and adaptive measurement noise scaling.

### New Capabilities
- None.

## Approach
Implement Option 2 from exploration:
1. **Typed Contract**: Define `AnchorSource` and frozen `PositionEstimate` in `src/core/kalman_filter.py`, re-exported in `src/pipeline/safety_pipeline.py`.
2. **Anchor Extraction Hierarchy**: Implement `extract_ground_anchor` with fallback logic: Tier 1 dual ankles ($R_0$), Tier 2 single ankle ($2R_0$), Tier 3 bbox bottom ($5R_0$).
3. **Adaptive Tracking**: Support per-measurement $R$ in `MetricKalmanFilter.update`; apply spatial gating ($1.0\text{ m}$) against parallax; decay confidence in coast mode (Tier 4).
4. **End-to-End Propagation**: Pass `PositionEstimate` through homography and tracking while preserving `Track.position` and `det.anchor` tuple compatibility.

## Affected Areas
| File | Change Type | Purpose |
| :--- | :--- | :--- |
| `src/core/kalman_filter.py` | Modified | Add `AnchorSource`, `PositionEstimate`, adaptive $R$, confidence decay |
| `src/pipeline/safety_pipeline.py` | Modified | Add `extract_ground_anchor`, enrich `PoseDetection` |
| `tests/test_kalman.py` | Modified | Unit tests for adaptive $R$ and confidence decay |
| `tests/test_pipeline.py` | Modified | Unit tests for anchor fallback hierarchy |

## Risks & Mitigation
- **Bbox Parallax Jumps**: Waist occlusions shift reprojected ground positions. *Mitigation*: Gating ($1.0\text{ m}$) rejects jumps; $5\times R_0$ dampens gain; low confidence ($c \le 0.40$) flags degraded integrity.
- **Latency Budget Overhead**: Extra object creation. *Mitigation*: Frozen dataclass instantiation takes $< 50\text{ ns}$, well within the $50\text{ ms}$ budget.

## Rollback Plan
Revert modified files via `git checkout` to restore binary ankle extraction and unweighted Kalman tracking.

## Success Criteria
- [ ] 4-tier anchor hierarchy extracts dual ankles, single ankle, and bbox bottom.
- [ ] `Track.estimate` exposes typed `PositionEstimate` with source and decaying confidence.
- [ ] Adaptive $R$ weights measurements based on source fidelity.
- [ ] 100% backward compatibility maintained for existing APIs and tests.
- [ ] Pipeline loop latency satisfies $t_1 \le 50\text{ ms}$.
- [ ] 100% test pass rate across `tests/test_kalman.py` and `tests/test_pipeline.py`.
