# Design: Adaptive Scale Anchor Degradation and Visualizer Badging

## Technical Approach
Enhance `extract_ground_anchor` in `src/pipeline/safety_pipeline.py` with bounding box height thresholding (`min_ankle_bbox_height`), enabling automatic switching between sub-centimeter ankle midpoint estimation in the foreground and robust bounding box bottom-center proxy in the far background. Enhance `DualVisualizer` in `src/utils/visualizer.py` to color-code anchor markers and display provenance indicators in both perspective and BEV views.

## Architecture Decisions

| Decision | Option Selected | Tradeoffs & Alternatives | Rationale |
| :--- | :--- | :--- | :--- |
| **Scale Thresholding Strategy** | Bounding box pixel height $(y2 - y1) < \text{min-ankle-bbox-height}$ | Alt: Distance in world coordinates $(Y_w > Y_{\text{thresh}})$ | Pixel height directly reflects sensor resolution and convolutional receptive field capacity without requiring prior homography inversion. |
| **Default Threshold Value** | `min_ankle_bbox_height = 0.0` (disabled by default) | Alt: Hardcoded `120.0` | Default of `0.0` ensures 100% backward compatibility for all existing tests and benchmarks, while allowing runtime/pipeline callers to pass e.g. `100.0` or `120.0`. |
| **Visualizer Palette** | Distinct BGR color coding per `AnchorSource` | Alt: Single color with text label only | Visual colors (`ANKLES_DUAL`: Cyan, `ANKLE_SINGLE`: Yellow, `BBOX_BOTTOM`: Magenta) provide instantaneous perceptual feedback at high frame rates without visual clutter. |

## Data Flow

```
Raw YOLO Output [Box, Keypoints, Conf]
            │
            ▼
    Height Check: (y2 - y1) < min_ankle_bbox_height ?
       ├── YES ──▶ Force Tier 3: BBOX_BOTTOM (Bottom-Center)
       └── NO  ──▶ Evaluate Tier 1 (Dual Ankles) / Tier 2 (Single Ankle)
            │
            ▼
    Anchor Point + AnchorSource Provenance
            │
            ▼
    DualVisualizer Rendering:
       ├── Perspective: Cyan / Yellow / Magenta Markers
       └── BEV: Orthogonal Track Badges with Source Indication
```

## File Changes

| File | Action | Description |
| :--- | :--- | :--- |
| `src/pipeline/safety_pipeline.py` | Modify | Update `extract_ground_anchor` and `SafetyPipeline` with `min_ankle_bbox_height` |
| `src/utils/visualizer.py` | Modify | Update `DualVisualizer` with anchor source color coding and labels |
| `tests/test_adaptive_anchor.py` | Create | Unit and integration test suite |

## Testing Strategy

| Layer | What to Test | Approach |
| :--- | :--- | :--- |
| **Unit** | `extract_ground_anchor` scale switching | Test small vs large bboxes with various ankle confidence levels |
| **Integration** | `SafetyPipeline` execution | Process frames with `min_ankle_bbox_height=120.0` and verify `PoseDetection.anchor_source` |
| **Visualizer** | `DualVisualizer` overlays | Test rendering of all `AnchorSource` variants in perspective and BEV |
| **Regression** | Full test suite | Run `pytest tests/` |

## Threat Matrix
`N/A — no routing, shell execution, subprocess parsing, VCS/PR automation, executable-file classification, or process-integration boundary.`

## Migration / Rollout
No migration required. Pure additive parameter with default value `0.0`.
