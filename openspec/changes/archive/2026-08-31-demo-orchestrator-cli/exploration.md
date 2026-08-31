## Exploration: End-to-End Demo Orchestrator CLI (`scripts/run_demo.py`)

### Current State
- The core analytical stack is fully implemented and tested:
  - [`OnnxEngine`](file:///Users/xander/Projects/edge-safety-guard/src/inference/onnx_engine.py): YOLO-Pose inference via ONNX Runtime (`CoreMLExecutionProvider` / `CPUExecutionProvider`).
  - [`HomographyManager`](file:///Users/xander/Projects/edge-safety-guard/src/core/homography.py): Planar DLT metric mapping $(u, v) \leftrightarrow (X_w, Y_w)$.
  - [`MultiTargetKalmanTracker`](file:///Users/xander/Projects/edge-safety-guard/src/core/kalman_filter.py): 2D kinematic tracking with 3 epistemological states (`OBSERVED`, `PREDICTED`, `STALE`).
  - [`SpatialFSM`](file:///Users/xander/Projects/edge-safety-guard/src/core/spatial_fsm.py): Dual spatial/temporal hysteresis, ISO 13855 approach speed bypass ($v_n \ge 1.6\text{ m/s}$), asymmetric de-escalation gating, and dwell time monitoring.
  - [`SafetyPipeline`](file:///Users/xander/Projects/edge-safety-guard/src/pipeline/safety_pipeline.py): Synchronous 6-stage frame orchestrator with fail-safe exception containment.
  - [`DualVisualizer`](file:///Users/xander/Projects/edge-safety-guard/src/utils/visualizer.py): Side-by-Side and PiP compositor for perspective frame + orthogonal BEV canvas.
  - [`SyntheticVideoGenerator`](file:///Users/xander/Projects/edge-safety-guard/src/utils/synthetic_generator.py): Deterministic sample videos in `data/samples/`.
- Currently, execution requires calling internal Python modules directly; there is no top-level user-facing CLI runner to demonstrate the live system on video files, webcams, or streams.

### Affected Areas
- `scripts/run_demo.py` (New): CLI entrypoint orchestrating video capture, pipeline execution, real-time GUI display, recording, and telemetry export.
- `openspec/specs/demo-orchestrator/spec.md` (New): Canonical OpenSpec specification defining CLI behavior, argument contracts, telemetry schema, and exit metrics.
- `tests/test_demo_runner.py` (New): Unit and integration tests validating argument parsing, stream decoding, headless processing, video export, and telemetry logging.
- `README.md` (Modified): Mark Paso 7 complete in roadmap and document CLI usage examples.

---

### Comparison of Approaches

| Approach | Pros | Cons | Complexity |
| :--- | :--- | :--- | :--- |
| **Approach 1: Monolithic Script**<br>Procedural script in `scripts/run_demo.py` with top-level while loop. | Quick to write. | Hard to unit-test; global state pollution; tight coupling between I/O and display. | Low |
| **Approach 2: Modular `DemoRunner` Class (Recommended)**<br>Encapsulates stream lifecycle (`initialize`, `process_frame`, `run`, `close`, `get_summary_metrics`) with CLI entrypoint. | Highly testable in CI; clean separation of stream ingestion, display, and telemetry serialization; easily scriptable as a Python API. | Slightly more initial code structure. | Medium |
| **Approach 3: Asynchronous Multi-Threaded Runner**<br>Producer-consumer architecture with separate frame decoding, inference, and display threads. | Maximizes multi-core throughput. | Over-engineered for single-stream MVP; introduces thread race conditions and jitter in latency profiling metrics ($T_1$). | High |

---

### Recommendation: Approach 2 (Modular `DemoRunner` Class + CLI Wrapper)
- Implement `DemoRunner` inside `scripts/run_demo.py` (or imported helper):
  - **Source Decoding:** Automatically handles integer camera index (`0`, `1`), video file path (`.mp4`, `.avi`, `.mkv`), or stream URL (`rtsp://`, `http://`).
  - **Interactive Display:** OpenCV window with side-by-side or PiP layout, pause/resume (`SPACE`), step, screenshot (`s`), and quit (`q`/`ESC`).
  - **Headless Mode:** `--no-display` flag enabling deterministic execution in CI or server environments without X11/Wayland display.
  - **Video Writer:** Optional `--output-video` writing annotated dual compositions with `mp4v` codec.
  - **Telemetry Logger:** Optional `--output-events` writing structured JSONL entries per frame containing timestamp, safety state, contactor trip status, active tracks, and $T_1$ stage latency breakdown.
  - **Summary Metrics:** At stream completion, computes and prints aggregate stats (processed frames, average FPS, mean/p50/p95/p99 latency, and safety violation counts).

### Risks & Mitigations
1. **Headless Environment Crashes:** Calling `cv2.imshow` in headless CI triggers `cv2.error: The function is not implemented` or `cannot connect to X server`.
   - *Mitigation:* Ensure `--no-display` completely suppresses all GUI window calls.
2. **Video Writer Codec Incompatibilities:** Certain OS platforms fail on specific fourcc codes.
   - *Mitigation:* Use cross-platform `mp4v` fourcc and wrap `VideoWriter` initialization with verification check.
3. **Live Stream vs File Frame Timing:** File playback can run much faster than real-time if not rate-limited.
   - *Mitigation:* Provide `--realtime` flag to sleep according to source FPS, and max-throughput mode by default for rapid processing.

### Ready for Proposal / Design
Yes. We are ready to proceed to `/sdd-propose`, `/sdd-design`, and `/sdd-spec`.
