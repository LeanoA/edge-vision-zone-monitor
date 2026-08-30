# Tasks: End-to-End Safety Pipeline & Dual Visualization

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 480 - 560 lines |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Safety Pipeline) -> PR 2 (Dual Visualizer) |
| Delivery strategy | exception-ok |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Safety Pipeline Orchestrator | PR 1 | `pytest tests/test_pipeline.py` | Synthetic ONNX frame loop | `src/pipeline/safety_pipeline.py`, `tests/test_pipeline.py` |
| 2 | Dual Visualizer & Canvas Compositor | PR 2 | `pytest tests/test_visualizer.py` | Synthetic PipelineResult renderer | `src/utils/visualizer.py`, `tests/test_visualizer.py` |

## Phase 1: Foundation & Pipeline Dataclasses / Interfaces

- [x] 1.1 Define `StageLatencies`, `PoseDetection`, `PipelineResult`, and `LayoutMode` dataclasses in `src/pipeline/safety_pipeline.py`.
- [x] 1.2 Export pipeline contracts and visualizer symbols in `src/pipeline/__init__.py` and `src/utils/__init__.py`.

## Phase 2: Safety Pipeline Implementation (TDD)

- [x] 2.1 [RED] Write unit tests in `tests/test_pipeline.py` for letterbox preprocessing and un-letterboxing coordinates.
- [x] 2.2 [GREEN] Implement letterbox preprocessing, scaling, and un-letterbox coordinate mapping in `src/pipeline/safety_pipeline.py`.
- [x] 2.3 [RED] Write unit tests in `tests/test_pipeline.py` for ankle anchor extraction (midpoint kp 15/16, single fallback, low-conf drop).
- [x] 2.4 [GREEN] Implement ankle anchor extraction logic with confidence thresholding in `src/pipeline/safety_pipeline.py`.
- [x] 2.5 [RED] Write unit tests in `tests/test_pipeline.py` for 6-stage sequential loop, homography projection, Kalman update, and FSM evaluation.
- [x] 2.6 [GREEN] Implement `SafetyPipeline.process_frame()` coordinating all 6 stages and building `PipelineResult`.
- [x] 2.7 [RED] Write unit tests in `tests/test_pipeline.py` for sub-millisecond stage latency profiling ($t_1 \le 50.0\text{ ms}$) and fail-safe fault containment (`SafetyState.FAULT`, `trip=True`).
- [x] 2.8 [GREEN] Implement `perf_counter` profiling in `SafetyPipeline` and wrap execution in fail-safe exception containment.

## Phase 3: Dual Visualizer Implementation (TDD)

- [x] 3.1 [RED] Write unit tests in `tests/test_visualizer.py` for inverse homography $H^{-1}$ zone reprojection and perspective overlay rendering.
- [x] 3.2 [GREEN] Implement perspective drawing (reprojected polygons, skeletons, status banner) in `src/utils/visualizer.py`.
- [x] 3.3 [RED] Write unit tests in `tests/test_visualizer.py` for metric BEV canvas ($100\text{ px/m}$ grid, zones, track positions, velocity vectors, dwell tags).
- [x] 3.4 [GREEN] Implement metric BEV rendering with pre-rendered background cache in `src/utils/visualizer.py`.
- [x] 3.5 [RED] Write unit tests in `tests/test_visualizer.py` for `SIDE_BY_SIDE` and `PIP` compositing, plus headless bypass duration ($< 0.1\text{ ms}$).
- [x] 3.6 [GREEN] Implement `composite()` and `render()` with headless bypass fast-path in `src/utils/visualizer.py`.

## Phase 4: Integration Verification & Regression Tests

- [x] 4.1 [RED] Write end-to-end integration test in `tests/test_pipeline.py` executing full pipeline with synthetic ONNX model over 30 consecutive frames.
- [x] 4.2 [GREEN] Verify 100% pass rate across `pytest tests/test_pipeline.py tests/test_visualizer.py` and run full regression suite `pytest tests/`.
- [x] 4.3 Refactor typing and remove dead code in `src/pipeline/safety_pipeline.py` and `src/utils/visualizer.py`.

