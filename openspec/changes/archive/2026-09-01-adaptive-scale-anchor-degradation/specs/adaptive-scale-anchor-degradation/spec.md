# Specification: Adaptive Scale Anchor Degradation (`adaptive-scale-anchor-degradation`)

## NEW Capabilities

### Capability: Scale-Aware Dynamic Ground Anchor Selection
The pipeline MUST support scale-adaptive ground anchor extraction based on bounding box height:

1. **Parameter Definition**:
   - `extract_ground_anchor` and `SafetyPipeline` MUST support `min_ankle_bbox_height: float = 0.0`.
   - When `min_ankle_bbox_height > 0.0` and a valid bounding box `(x1, y1, x2, y2)` has height $(y2 - y1) < \text{min\_ankle\_bbox\_height}$, the extractor MUST bypass Tier 1 (`ANKLES_DUAL`) and Tier 2 (`ANKLE_SINGLE`) and fallback directly to Tier 3 (`BBOX_BOTTOM`).
   - When $(y2 - y1) \ge \text{min\_ankle\_bbox\_height}$ (or `min_ankle_bbox_height == 0.0`), the extractor MUST evaluate Tier 1 and Tier 2 normally.

2. **Confidence Computation**:
   - When `BBOX_BOTTOM` is selected via scale degradation, the confidence MUST be computed as $\text{det\_score} \times 0.40$.

3. **Visualizer Palette and Provenance Badging**:
   - `DualVisualizer` in perspective mode MUST render ground anchors using distinct color coding:
     - `AnchorSource.ANKLES_DUAL`: Cyan `(255, 255, 0)` marker.
     - `AnchorSource.ANKLE_SINGLE`: Yellow `(0, 255, 255)` marker.
     - `AnchorSource.BBOX_BOTTOM`: Magenta `(255, 0, 255)` marker.
   - `DualVisualizer` in BEV mode MUST include the anchor source indicator in the track annotation if available.

#### Scenario: Far-Field Small Detection Falls Back to Bounding Box Bottom
- **GIVEN** a detection with bounding box height $h = 80\text{px}$ and valid ankle keypoints with confidence $0.85$
- **WHEN** `extract_ground_anchor` is called with `min_ankle_bbox_height=120.0`
- **THEN** the returned anchor source SHALL be `AnchorSource.BBOX_BOTTOM`
- **AND** the anchor coordinates SHALL be the bottom-center of the bounding box.

#### Scenario: Near-Field Large Detection Uses Ankle Keypoints
- **GIVEN** a detection with bounding box height $h = 200\text{px}$ and valid ankle keypoints with confidence $0.85$
- **WHEN** `extract_ground_anchor` is called with `min_ankle_bbox_height=120.0`
- **THEN** the returned anchor source SHALL be `AnchorSource.ANKLES_DUAL`
- **AND** the anchor coordinates SHALL be the midpoint between left and right ankles.
