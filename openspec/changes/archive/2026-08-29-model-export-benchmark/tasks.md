# Tasks: Model Export & Latency Benchmark

## Review Workload Forecast
Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: Medium

## Suggested Work Units
- **Unit 1: Model Export Pipeline**
  - Files: `models/export_onnx.py`, `tests/conftest.py`, `tests/test_export.py`
  - Focused test command: `pytest tests/test_export.py`
  - Runtime harness: Python 3.10+ / synthetic ONNX graph generator
  - Rollback boundary: Delete `models/export_onnx.py`, `tests/test_export.py`, `tests/conftest.py`
- **Unit 2: ONNX Inference Engine**
  - Files: `src/inference/onnx_engine.py`, `tests/test_onnx_engine.py`
  - Focused test command: `pytest tests/test_onnx_engine.py`
  - Runtime harness: ONNX Runtime with CoreML / CPU provider negotiation
  - Rollback boundary: Delete `src/inference/onnx_engine.py`, `tests/test_onnx_engine.py`
- **Unit 3: Latency Benchmark Suite**
  - Files: `scripts/benchmark.py`, `tests/test_benchmark.py`
  - Focused test command: `pytest tests/test_benchmark.py`
  - Runtime harness: Monotonic high-resolution timer (`time.perf_counter_ns`)
  - Rollback boundary: Delete `scripts/benchmark.py`, `tests/test_benchmark.py`

## Implementation Tasks

### Phase 1: Test Fixtures & Model Export
- [x] 1.1 (RED) Implement synthetic ONNX model generator fixture in `tests/conftest.py` producing shape `(1, 3, 640, 640)` -> `(1, 56, 8400)`.
- [x] 1.2 (RED) Write unit tests in `tests/test_export.py` covering `validate_onnx_model`, shape assertions, error handling on corrupted graphs, and mocked `export_model` CLI invocation.
- [x] 1.3 (GREEN) Implement `validate_onnx_model` using `onnx.checker` and `onnx.shape_inference` in `models/export_onnx.py`.
- [x] 1.4 (GREEN) Implement `export_model` CLI utility with static shape `(1, 3, 640, 640)`, opset 17, and graph simplification in `models/export_onnx.py`.
- [x] 1.5 (REFACTOR) Polish error handling, logging, and argument validation in `models/export_onnx.py`. Run `pytest tests/test_export.py`.

### Phase 2: Hardware-Accelerated ONNX Inference Engine
- [x] 2.1 (RED) Write unit tests in `tests/test_onnx_engine.py` testing session initialization, provider negotiation (`CoreMLExecutionProvider` -> `CPUExecutionProvider`), input validation (`float32`, shape `(1, 3, 640, 640)`), and output tensor shape `(1, 56, 8400)`.
- [x] 2.2 (GREEN) Implement `OnnxEngine` class in `src/inference/onnx_engine.py` with hierarchical provider selection and thread pool configuration (`num_threads=4`).
- [x] 2.3 (GREEN) Implement input tensor contract validation and forward pass `infer()` in `src/inference/onnx_engine.py`.
- [x] 2.4 (REFACTOR) Enhance provider fallback logging and metadata query helpers (`get_providers`, `get_input_details`). Run `pytest tests/test_onnx_engine.py`.

### Phase 3: Latency Benchmark Suite
- [x] 3.1 (RED) Write unit tests in `tests/test_benchmark.py` for statistical metrics calculation (mean, std, p50, p95, p99, FPS), warmup exclusions, strict budget enforcement ($p95 \le 30.0\text{ ms}$), and JSON output.
- [x] 3.2 (GREEN) Implement `BenchmarkMetrics` and `run_benchmark` in `scripts/benchmark.py` using `time.perf_counter_ns()`.
- [x] 3.3 (GREEN) Implement CLI entry point, tabular terminal reporting, and `--json-out` export in `scripts/benchmark.py`.
- [x] 3.4 (REFACTOR) Refine CLI argument parsing, strict mode exit codes, and run `pytest tests/test_benchmark.py`.

### Phase 4: Integration Verification
- [x] 4.1 Run full test suite with `pytest tests/` to confirm 100% pass rate.
- [x] 4.2 Verify static model export and profile inference latency with `python scripts/benchmark.py --strict` to ensure compliance with ISO 13855 safety budget ($p95 \le 30.0\text{ ms}$).
