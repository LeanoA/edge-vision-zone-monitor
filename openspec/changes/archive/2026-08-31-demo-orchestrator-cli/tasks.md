# Tasks: End-to-End Demo Orchestrator CLI (`scripts/run_demo.py`)

## Review Workload Forecast

| Field | Value |
| :--- | :--- |
| Estimated changed lines | ~300 lines |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Demo CLI runner, telemetry logging & test suite | PR 1 | `pytest tests/test_demo_runner.py` | `python scripts/run_demo.py --source data/samples/sequence_a_clean_incursion.mp4 --no-display` | `scripts/run_demo.py`, `tests/test_demo_runner.py` |

---

## Phase 1: Data Contracts & CLI Parsing

- [x] 1.1 Create `DemoRunnerConfig` and `DemoSummary` dataclasses in `scripts/run_demo.py` with strict type hints.
- [x] 1.2 Implement `parse_args()` in `scripts/run_demo.py` with arguments for `--source`, `--model`, `--config`, `--layout`, `--no-display`, `--realtime`, `--output-video`, `--output-events`, `--conf-threshold`, and `--max-frames`.

## Phase 2: Core Orchestrator Implementation (`scripts/run_demo.py`)

- [x] 2.1 Implement `DemoRunner._resolve_source()` to handle webcam integers, video files, and RTSP stream URLs.
- [x] 2.2 Implement `DemoRunner.initialize()` to instantiate `SafetyPipeline` (with `OnnxEngine`, `HomographyManager`, `MultiTargetKalmanTracker`, `SpatialFSM`) and `DualVisualizer`.
- [x] 2.3 Implement `DemoRunner.process_frame()` to execute the 6-stage pipeline, write video frames, and append JSONL telemetry.
- [x] 2.4 Implement `DemoRunner.run()` execution loop with headless bypass, interactive keyboard handling (`q`/`ESC`, `SPACE`, `s`), and frame-rate pacing.
- [x] 2.5 Implement `DemoRunner.get_summary()` to compute latency percentiles (mean, p50, p95, p99) and format terminal telemetry table.
- [x] 2.6 Implement `main()` entrypoint with clean exception handling and summary logging.

## Phase 3: Automated Test Suite (`tests/test_demo_runner.py`)

- [x] 3.1 Write unit tests for `parse_args` validating default values, type conversions, and layout options.
- [x] 3.2 Write unit tests for `DemoSummary` verifying accurate percentile calculations against known latency series.
- [x] 3.3 Write integration test for `DemoRunner` running headless (`no_display=True`) on `data/samples/sequence_a_clean_incursion.mp4` with synthetic ONNX model.
- [x] 3.4 Write integration test validating `.mp4` video creation and `.jsonl` schema completeness.

## Phase 4: Canonical Spec & Documentation

- [x] 4.1 Create canonical OpenSpec specification file in `openspec/specs/demo-orchestrator/spec.md`.
- [x] 4.2 Update `README.md` Roadmap (check Paso 7) and document CLI demo execution commands.
