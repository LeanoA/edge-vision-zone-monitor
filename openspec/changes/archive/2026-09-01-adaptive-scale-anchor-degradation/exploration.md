# Exploration: Adaptive Scale Anchor Degradation and Visualizer Badging

## Current State
The system currently provides ground anchor extraction via `extract_ground_anchor` in `src/pipeline/safety_pipeline.py` with 4 degradation tiers (`ANKLES_DUAL`, `ANKLE_SINGLE`, `BBOX_BOTTOM`, and `None`).
However:
1. **No Scale / Bounding Box Height Awareness**: `extract_ground_anchor` attempts ankle keypoint extraction unconditionally, regardless of the target's apparent scale. For far-field workers ($h_{\text{bbox}} < 120\text{px}$, $Y > 12\text{m}$), noisy keypoints with marginal confidence cause keypoint jitter, or drop to None when ankle confidence fluctuates just below threshold.
2. **Generic Visualizer Marker**: `DualVisualizer` in `src/utils/visualizer.py` renders all ground anchors identically using a static red tilted cross (`MARKER_TILTED_CROSS`), without visually distinguishing whether the anchor was derived from dual ankles, single ankle, bounding box bottom, or coasting track.
3. **BEV Track Labels**: The BEV orthogonal canvas displays track ID and speed, but does not indicate anchor source provenance.

## Affected Areas
- `src/pipeline/safety_pipeline.py`:
  - Enhance `extract_ground_anchor` with `min_ankle_bbox_height: float = 120.0` (configurable parameter).
  - When $h_{\text{bbox}} < \text{min\_ankle\_bbox\_height}$, dynamically route anchor selection to `BBOX_BOTTOM` (Tier 3) with confidence proportional to detection score.
- `src/utils/visualizer.py`:
  - Color-code perspective ground anchor markers and badges based on `AnchorSource`:
    - `ANKLES_DUAL`: Cyan `(255, 255, 0)` marker + badge.
    - `ANKLE_SINGLE`: Yellow `(0, 255, 255)` marker + badge.
    - `BBOX_BOTTOM`: Magenta `(255, 0, 255)` marker + badge.
  - Update BEV canvas rendering to show anchor source in track badge.
- `tests/test_adaptive_anchor.py`: Dedicated unit and integration tests verifying scale-adaptive switching and visualizer rendering.

## Approaches

### 1. Scale-Aware Dynamic Degradation in `extract_ground_anchor` + Visualizer Palette (Recommended)
- **Description**: Add `min_ankle_bbox_height` parameter to `extract_ground_anchor` and `SafetyPipeline`. When bounding box height is below threshold, automatically select `BBOX_BOTTOM` if available. Update `DualVisualizer` to render color-coded anchor markers and provenance badges.
- **Pros**:
  - Robust tracking for small/far targets without jitter or dropped frames.
  - Full transparency in operator visualization (visual cue of anchor provenance).
  - 100% backward compatible (default values preserve existing behavior when scale threshold is met).
- **Cons**: Minor addition of visualization logic in `DualVisualizer`.
- **Effort**: Low.

## Recommendation
Proceed with **Approach 1**.

## Risks
- Regression in existing synthetic or empirical benchmarks: Mitigated by default `min_ankle_bbox_height=0.0` or sensible default ($100-120\text{px}$) with full regression testing.

## Ready for Proposal
Yes.
