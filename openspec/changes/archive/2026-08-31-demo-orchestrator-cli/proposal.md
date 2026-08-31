# Proposal: End-to-End Demo Orchestrator CLI (`scripts/run_demo.py`)

## Intent
Provide a unified CLI runner (`scripts/run_demo.py`) to execute the industrial safety monitoring pipeline across recorded video files, live webcams, and RTSP streams with interactive dual-stream visualization, headless CI execution, annotated video recording, and structured JSONL telemetry.

## Scope

### In Scope
- **Input Source Decoding**: Ingest video files (`.mp4`, `.avi`, `.mkv`), webcams (`/dev/videoX` or device indices `0`, `1`), or RTSP/HTTP URLs.
- **Pipeline Execution**: Synchronous frame evaluation via `SafetyPipeline` with high-resolution $T_1$ stage latency breakdown.
- **Dual Visualizer Composition**: Perspective overlay + orthogonal BEV canvas in Side-by-Side or Picture-in-Picture layout.
- **Interactive UI & Keyboard Controls**: OpenCV `imshow` display with `q`/`ESC` (quit), `SPACE` (pause/resume), and `s` (save snapshot).
- **Headless & Recording Flags**: `--no-display` flag to suppress all GUI calls for CI/servers, `--output-video` (MP4 export), and `--output-events` (structured JSONL telemetry export).
- **Exit Telemetry Summary**: Aggregate runtime metrics (FPS, total frames, mean/p50/p95/p99 $T_1$ reaction time, violation counts).
- **Automated Test Suite**: Unit and integration tests in `tests/test_demo_runner.py`.

### Out of Scope
- Multi-camera distributed spatial fusion.
- Web browser streaming server (WebRTC/WebSocket).

## Capabilities

### New Capabilities
- `demo-orchestrator`: End-to-end CLI execution, video stream decoding, interactive display window, video writer, and structured telemetry export.

### Modified Capabilities
- None.

## Approach
Implement a modular `DemoRunner` class inside `scripts/run_demo.py` paired with an `argparse` CLI wrapper:
1. `DemoRunner.initialize()`: Validates input source, opens `cv2.VideoCapture`, instantiates `SafetyPipeline` and `DualVisualizer`.
2. `DemoRunner.process_frame()`: Dispatches frames through the 6-stage pipeline, updates metrics, writes video/JSONL.
3. `DemoRunner.run()`: Main playback loop with pause/resume and headless safety bypass.
4. `DemoRunner.get_summary()`: Compiles latency percentiles (numpy `percentile`) and safety transition metrics.

## Affected Areas

| Area | Impact | Description |
| :--- | :--- | :--- |
| `scripts/run_demo.py` | New | Modular `DemoRunner` class and executable CLI entrypoint |
| `openspec/specs/demo-orchestrator/spec.md` | New | Canonical specification for demo CLI runner |
| `tests/test_demo_runner.py` | New | Automated test suite for CLI arguments, headless run, and telemetry |
| `README.md` | Modified | Update Roadmap (Paso 7) and add CLI usage guide |

## Risks

| Risk | Likelihood | Mitigation |
| :--- | :--- | :--- |
| Headless CI crashes on `cv2.imshow` | High | `--no-display` flag suppresses all GUI calls completely |
| VideoWriter codec incompatibility | Medium | Use cross-platform `'mp4v'` fourcc and verify `writer.isOpened()` |
| High-speed file playback desync | Low | Provide `--realtime` flag to pace playback to source FPS |

## Rollback Plan
Remove `scripts/run_demo.py`, `tests/test_demo_runner.py`, and `openspec/specs/demo-orchestrator/spec.md`.

## Success Criteria
- [ ] `python scripts/run_demo.py --source data/samples/sequence_a_clean_incursion.mp4 --no-display` runs to completion.
- [ ] Annotated `.mp4` video created when `--output-video` is specified.
- [ ] Valid `.jsonl` telemetry generated when `--output-events` is specified.
- [ ] 100% test pass rate in `tests/test_demo_runner.py` and overall test suite.
