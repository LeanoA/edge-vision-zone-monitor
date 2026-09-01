# Tasks: Adaptive Scale Anchor Degradation and Visualizer Badging

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~90 lines |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Core pipeline scale switching, visualizer palette & tests | Single PR | `pytest tests/test_adaptive_anchor.py` | `python scripts/run_demo.py --no-display` | Revert changes in `src/pipeline/`, `src/utils/` and delete test file |

---

## Phase 1: Core Pipeline Enhancement

- [x] 1.1 Add `min_ankle_bbox_height: float = 0.0` parameter to `extract_ground_anchor` in `src/pipeline/safety_pipeline.py`. <!-- id: task-1.1-extract -->
- [x] 1.2 Update `SafetyPipeline.__init__` and `SafetyPipeline.process_frame` in `src/pipeline/safety_pipeline.py` to accept and pass `min_ankle_bbox_height`. <!-- id: task-1.2-pipeline -->

## Phase 2: Visualizer Color Palette and Badging

- [x] 2.1 Update `DualVisualizer` in `src/utils/visualizer.py` to define `ANCHOR_COLORS` mapping `AnchorSource` to BGR colors (`ANKLES_DUAL`: Cyan, `ANKLE_SINGLE`: Yellow, `BBOX_BOTTOM`: Magenta). <!-- id: task-2.1-palette -->
- [x] 2.2 Update perspective canvas rendering in `DualVisualizer` to draw anchor markers and text badges using `ANCHOR_COLORS`. <!-- id: task-2.2-perspective -->
- [x] 2.3 Update BEV canvas rendering in `DualVisualizer` to annotate tracks with anchor source provenance. <!-- id: task-2.3-bev -->

## Phase 3: Testing & Verification

- [x] 3.1 Create `tests/test_adaptive_anchor.py` covering unit tests for `min_ankle_bbox_height` switching and visualizer palette rendering. <!-- id: task-3.1-tests -->
- [x] 3.2 Execute complete regression test suite with `pytest tests/`. <!-- id: task-3.2-regression -->
