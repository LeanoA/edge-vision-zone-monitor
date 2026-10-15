# Proposal: Adaptive Scale Anchor Degradation and Visualizer Badging

## Intent
Implement scale-adaptive ground anchor degradation (automatically falling back from ankle keypoints to bounding box bottom-center when targets are far/small) and enhance visualizer overlays with color-coded anchor provenance indicators and badges.

## Scope

### In Scope
- **Scale-Adaptive Anchor Extraction (`src/pipeline/safety_pipeline.py`)**: Add `min_ankle_bbox_height` parameter to `extract_ground_anchor` and `SafetyPipeline`. When $h_{\text{bbox}} < \text{min-ankle-bbox-height}$, dynamically switch to `BBOX_BOTTOM` anchor.
- **Visualizer Enhancement (`src/utils/visualizer.py`)**: Color-code perspective ground anchor markers and labels according to `AnchorSource` (`ANKLES_DUAL`: Cyan, `ANKLE_SINGLE`: Yellow, `BBOX_BOTTOM`: Magenta), and display anchor source in BEV track labels.
- **Unit & Integration Tests (`tests/test_adaptive_anchor.py`)**: Comprehensive test suite covering scale switching logic, confidence scaling, and visualizer rendering.

### Out of Scope
- Modifying Kalman Filter equations in `src/core/kalman_filter.py`.
- Modifying Spatial FSM logic in `src/core/spatial_fsm.py`.

## Capabilities

### New Capabilities
- `adaptive-scale-anchor-degradation`: Scale-aware ground anchor selection and color-coded visualizer badging.

### Modified Capabilities
- `safety-pipeline`: Support `min_ankle_bbox_height` in detection extraction loop.
- `dual-visualization`: Display anchor source colors and provenance indicators.

## Approach
1. Update `extract_ground_anchor` to accept `min_ankle_bbox_height: float = 0.0`. If $h_{\text{bbox}} > 0$ and $h_{\text{bbox}} < \text{min-ankle-bbox-height}$, bypass Tier 1/2 and use Tier 3 `BBOX_BOTTOM`.
2. Update `SafetyPipeline.__init__` and `process_frame` to propagate `min_ankle_bbox_height`.
3. Update `DualVisualizer` in `src/utils/visualizer.py` to map each `AnchorSource` to a distinct marker style and color.
4. Author comprehensive test suite in `tests/test_adaptive_anchor.py`.

## Affected Areas

| Area | Impact | Description |
| :--- | :--- | :--- |
| `src/pipeline/safety_pipeline.py` | Modified | Add `min_ankle_bbox_height` support to anchor extraction |
| `src/utils/visualizer.py` | Modified | Add color-coded anchor markers and provenance labels |
| `tests/test_adaptive_anchor.py` | New | Test suite for adaptive scale switching and visualizer |

## Risks

| Risk | Likelihood | Mitigation |
| :--- | :--- | :--- |
| Breaking backward compatibility | Low | Default `min_ankle_bbox_height=0.0` preserves unconditional keypoint logic by default |

## Rollback Plan
Revert changes in `src/pipeline/safety_pipeline.py` and `src/utils/visualizer.py` and remove `tests/test_adaptive_anchor.py`.

## Success Criteria
- [ ] `extract_ground_anchor` selects `BBOX_BOTTOM` when $h_{\text{bbox}} < \text{min-ankle-bbox-height}$.
- [ ] `DualVisualizer` renders distinct colors for `ANKLES_DUAL`, `ANKLE_SINGLE`, and `BBOX_BOTTOM`.
- [ ] 100% test pass in `tests/test_adaptive_anchor.py` and full regression suite.
