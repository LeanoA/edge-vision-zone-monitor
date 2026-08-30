# Proposal: End-to-End Safety Pipeline & Dual Visualization

## Intent
Integrate model inference, homography, Kalman tracking, and spatial FSM into an ISO 13855:2024 compliant pipeline ($t_1 \le 50$ ms, $\ge 20$ FPS) with synchronized camera and metric bird's-eye view (BEV) visualization.

## Scope

### In Scope
- **Safety Pipeline (`src/pipeline/safety_pipeline.py`)**: Orchestrator integrating letterbox preprocessing ($640\times640$), ONNX inference (`OnnxEngine`), ankle filtering (indices 15, 16), projection (`HomographyManager`), tracking (`MultiTargetKalmanTracker`), evaluation (`SpatialFSM`), and stage latency profiling.
- **Dual Visualizer (`src/utils/visualizer.py`)**: Perspective overlay (inverse homography $H^{-1}$ reprojection, skeletons, anchors, banners) and metric top-down BEV (grid, footprint, zones, tracks, velocity vectors, dwell times), with side-by-side or picture-in-picture compositing.
- **Unit Tests**: Test suites in `tests/test_pipeline.py` and `tests/test_visualizer.py`.

### Out of Scope
- RTSP camera ingestion and hardware GPIO/fieldbus relay switching.
- WebRTC or web streaming services.

## Capabilities

### New Capabilities
- `safety-pipeline`: Synchronous loop linking vision, projection, tracking, FSM evaluation, and sub-millisecond stage profiling.
- `dual-visualization`: Synchronized dual-stream rendering combining perspective overlay and metric BEV.

### Modified Capabilities
- None.

## Approach
1. **Pipeline Execution**: Sequential loop per frame: preprocess $\to$ ONNX $\to$ ankle filter $\to$ ground projection $\to$ Kalman tracking $\to$ FSM check. Profile stage latencies via monotonic clock.
2. **Dual-View Synthesis**:
   - *Perspective Overlay*: Reproject $P_{\text{danger}}$ and $P_{\text{release}}$ via $H^{-1}$; draw skeletons and status banner.
   - *Metric BEV*: Render orthogonal canvas ($100$ px/m) with grid, zones, positions, velocity vectors, and dwell tags.
   - *Compositing*: Side-by-side or picture-in-picture layouts.
3. **Verification**: Validate synthetic pipeline, latency budgets, trip determinism, and visualization via pytest.

## Affected Areas
| File | Change Type | Purpose |
| :--- | :--- | :--- |
| `src/pipeline/safety_pipeline.py` | New | Safety pipeline orchestrator & profiler |
| `src/utils/visualizer.py` | New | Camera overlay & metric BEV dual visualizer |
| `tests/test_pipeline.py` | New | Pipeline integration and trip unit tests |
| `tests/test_visualizer.py` | New | Visualizer and layout unit tests |

## Risks & Mitigation
- **Rendering Overhead**: Complex drawing risks exceeding 50 ms budget. Precompute $H^{-1}$ and static canvas geometries; support headless execution.
- **Ankle Occlusions**: Missing ankles disrupt tracking. Kalman coasting bridges dropouts; pipeline flags degraded confidence.

## Rollback Plan
Delete `src/pipeline/safety_pipeline.py`, `src/utils/visualizer.py`, and corresponding tests.

## Dependencies
- `numpy>=1.24.0`, `opencv-python>=4.8.0`, `shapely>=2.0.0`, `pytest>=7.0.0`, `onnxruntime>=1.15.0`.

## Success Criteria
- [ ] End-to-end latency $t_1 \le 50$ ms ($\ge 20$ FPS) on synthetic input.
- [ ] Latency profiler reports telemetry across all 6 stages.
- [ ] Inverse homography $H^{-1}$ accurately projects zones onto camera frames.
- [ ] Metric BEV renders grid, zones, track vectors, and dwell times.
- [ ] Fail-safe trip state asserted on zone intrusion.
- [ ] 100% test pass rate in `tests/test_pipeline.py` and `tests/test_visualizer.py`.
