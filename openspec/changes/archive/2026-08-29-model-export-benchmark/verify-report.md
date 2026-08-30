# Verification Report: Model Export & Latency Benchmark

- **Change Name:** `model-export-benchmark`
- **Execution Date:** 2026-08-29T18:44:39-03:00
- **Target Platform:** Apple Silicon (macOS arm64, Darwin 21.6.0)
- **Safety Standard:** ISO 13855:2024 ($t_{\text{infer}} \le 30.0\text{ ms}$ at $p95$, $\ge 33.3\text{ FPS}$)
- **Mode:** Hybrid / Strict TDD
- **Overall Status:** **PASS**

---

## 1. Executive Summary

The `model-export-benchmark` change has been rigorously verified against all functional requirements, behavioral specifications, technical design commitments, and real-time edge safety budgets. 

All 14 implementation and integration tasks across 4 phases in [`tasks.md`](file:///Users/xander/Projects/edge-safety-guard/openspec/changes/model-export-benchmark/tasks.md) are confirmed completed. The automated test suite executed with a **100% pass rate (26/26 passed in 2.32s)** with zero regressions or errors. Profiling on Apple Silicon M1 using the hardware-accelerated CoreML runtime yielded a $p95$ inference latency of **20.26 ms** (54.55 FPS), comfortably exceeding the ISO 13855 safety budget threshold of $\le 30.0\text{ ms}$ with a safety margin of **9.74 ms (32.5% headroom)**.

The change is recommended for archiving (`sdd-archive`).

---

## 2. Task Completion Verification

All 14 planned tasks in [`tasks.md`](file:///Users/xander/Projects/edge-safety-guard/openspec/changes/model-export-benchmark/tasks.md) were executed following strict TDD cycles (RED -> GREEN -> REFACTOR) and are marked complete (`[x]`):

| Phase | Task | Status | Description |
| :--- | :--- | :--- | :--- |
| **Phase 1: Export** | 1.1 (RED) | `[x]` | Implement synthetic ONNX model generator fixture in `tests/conftest.py` `(1, 3, 640, 640)` -> `(1, 56, 8400)` |
| | 1.2 (RED) | `[x]` | Write unit tests in `tests/test_export.py` covering validation, shapes, corrupt graphs, and CLI invocation |
| | 1.3 (GREEN) | `[x]` | Implement `validate_onnx_model` using `onnx.checker` and `onnx.shape_inference` in `models/export_onnx.py` |
| | 1.4 (GREEN) | `[x]` | Implement `export_model` CLI utility with static shape `(1, 3, 640, 640)`, opset 17, and graph simplification |
| | 1.5 (REFACTOR) | `[x]` | Polish error handling, logging, and argument validation in `models/export_onnx.py` |
| **Phase 2: Inference** | 2.1 (RED) | `[x]` | Write unit tests in `tests/test_onnx_engine.py` for session init, provider negotiation, preconditions, output shape |
| | 2.2 (GREEN) | `[x]` | Implement `OnnxEngine` class in `src/inference/onnx_engine.py` with hierarchical provider selection and 4 threads |
| | 2.3 (GREEN) | `[x]` | Implement input tensor contract validation and forward pass `infer()` in `src/inference/onnx_engine.py` |
| | 2.4 (REFACTOR) | `[x]` | Enhance provider fallback logging and metadata query helpers (`get_providers`, `get_input_details`) |
| **Phase 3: Benchmark** | 3.1 (RED) | `[x]` | Write unit tests in `tests/test_benchmark.py` for statistical metrics, warmup isolation, strict budget, JSON export |
| | 3.2 (GREEN) | `[x]` | Implement `BenchmarkMetrics` and `run_benchmark` in `scripts/benchmark.py` using `time.perf_counter_ns()` |
| | 3.3 (GREEN) | `[x]` | Implement CLI entry point, tabular terminal reporting, and `--json-out` export in `scripts/benchmark.py` |
| | 3.4 (REFACTOR) | `[x]` | Refine CLI argument parsing, strict mode exit codes, and verify `test_benchmark.py` |
| **Phase 4: Integration** | 4.1 | `[x]` | Run full test suite with `pytest tests/` (100% pass rate confirmed) |
| | 4.2 | `[x]` | Verify static model export and profile inference latency with `scripts/benchmark.py --strict` |

---

## 3. Automated Test Execution Evidence

- **Test Runner:** `/Users/xander/Projects/edge-safety-guard/.venv/bin/pytest`
- **Execution Command:** `.venv/bin/pytest tests/ -v`
- **Exit Code:** `0`
- **Duration:** `2.32 seconds`
- **Total Tests Collected:** 26
- **Total Tests Passed:** 26 (100%)
- **Total Failures / Errors:** 0

### Test Execution Details by Module

```text
tests/test_benchmark.py::test_benchmark_metrics_integrity PASSED         [  3%]
tests/test_benchmark.py::test_run_benchmark_distribution_percentiles PASSED [  7%]
tests/test_benchmark.py::test_run_benchmark_warmup_isolation PASSED      [ 11%]
tests/test_benchmark.py::test_benchmark_budget_evaluation PASSED         [ 15%]
tests/test_benchmark.py::test_format_benchmark_table PASSED              [ 19%]
tests/test_benchmark.py::test_benchmark_cli_json_export PASSED           [ 23%]
tests/test_benchmark.py::test_benchmark_cli_strict_pass PASSED           [ 26%]
tests/test_benchmark.py::test_benchmark_cli_strict_fail PASSED           [ 30%]
tests/test_export.py::test_validate_onnx_model_success PASSED            [ 34%]
tests/test_export.py::test_validate_onnx_model_nonexistent PASSED        [ 38%]
tests/test_export.py::test_validate_onnx_model_corrupt PASSED            [ 42%]
tests/test_export.py::test_validate_onnx_model_input_shape_mismatch PASSED [ 46%]
tests/test_export.py::test_validate_onnx_model_output_shape_mismatch PASSED [ 50%]
tests/test_export.py::test_validate_onnx_model_invalid_dtype PASSED      [ 53%]
tests/test_export.py::test_export_model_invokes_ultralytics PASSED       [ 57%]
tests/test_export.py::test_export_cli_nonexistent_weights PASSED         [ 61%]
tests/test_export.py::test_export_cli_success PASSED                     [ 65%]
tests/test_onnx_engine.py::test_engine_init_success PASSED               [ 69%]
tests/test_onnx_engine.py::test_engine_nonexistent_model PASSED          [ 73%]
tests/test_onnx_engine.py::test_engine_explicit_cpu_provider PASSED      [ 76%]
tests/test_onnx_engine.py::test_engine_provider_fallback_when_coreml_fails PASSED [ 80%]
tests/test_onnx_engine.py::test_engine_session_options_applied PASSED    [ 84%]
tests/test_onnx_engine.py::test_engine_infer_forward_pass PASSED         [ 88%]
tests/test_onnx_engine.py::test_engine_infer_invalid_shape PASSED        [ 92%]
tests/test_onnx_engine.py::test_engine_infer_invalid_dtype PASSED        [ 96%]
tests/test_onnx_engine.py::test_engine_infer_non_ndarray PASSED          [100%]
```

---

## 4. Hardware Benchmark & Real-Time Safety Budget Verification

- **Harness Command:** `.venv/bin/python scripts/benchmark.py --strict --iterations 50 --warmup 10`
- **Exit Code:** `0`
- **Target Model:** `models/yolo11n-pose.onnx` (Static shape `(1, 3, 640, 640)`, Opset 17, Simplified)
- **Active Execution Providers:** `['CoreMLExecutionProvider', 'CPUExecutionProvider']`
  - CoreML graph partition offload: 346 of 354 nodes supported and delegated to Apple Neural Engine / Metal GPU.
- **Warmup Cycles:** 10 (isolated from profiling)
- **Timed Iterations:** 50

### Empirical Statistical Distribution

| Metric | Measured Value | Budget Limit / Constraint | Compliance Status |
| :--- | :---: | :---: | :---: |
| **Mean Latency** | **18.33 ms** | $t_{\text{mean}} \le 30.0\text{ ms}$ | **PASS** |
| **Std Deviation** | **1.84 ms** | Bounded jitter | **PASS** |
| **Min Latency** | **11.96 ms** | — | — |
| **p50 (Median)** | **18.55 ms** | — | **PASS** |
| **p95 Latency** | **20.26 ms** | $p95 \le 30.0\text{ ms}$ (ISO 13855) | **PASS (9.74 ms margin)** |
| **p99 Latency** | **20.61 ms** | Outlier bound | **PASS** |
| **Max Latency** | **20.63 ms** | Worst-case tail | **PASS** |
| **Throughput (FPS)** | **54.55 FPS** | $\ge 33.33\text{ FPS}$ | **PASS (+63.7% throughput)** |
| **Strict Flag Exit Code** | `0` | Exit code 0 | **PASS** |

### Benchmark Execution Console Output

```text
2026-08-29 18:44:36.891 Python[47792:1835445] [W:onnxruntime:, coreml_execution_provider.cc:113 GetCapability] CoreMLExecutionProvider::GetCapability, number of partitions supported by CoreML: 5 number of nodes in the graph: 354 number of nodes supported by CoreML: 346
2026-08-29 18:44:38,697 [INFO] onnx_engine: OnnxEngine initialized successfully for 'yolo11n-pose.onnx' with providers: ['CoreMLExecutionProvider', 'CPUExecutionProvider']
2026-08-29 18:44:38,719 [INFO] benchmark: Executing 10 warmup iterations...
2026-08-29 18:44:38,847 [INFO] benchmark: Executing 50 measured iterations...

========================================================================
                 EDGE SAFETY INFERENCE BENCHMARK REPORT                 
========================================================================
Model Path:         models/yolo11n-pose.onnx
Active Provider(s): CoreMLExecutionProvider, CPUExecutionProvider
Warmup / Iterations: 10 / 50
------------------------------------------------------------------------
Metric                                   Value
------------------------------------------------------------------------
Mean Latency:                         18.33 ms
Std Deviation:                         1.84 ms
Min Latency:                          11.96 ms
p50 Latency (Median):                 18.55 ms
p95 Latency:                          20.26 ms
p99 Latency:                          20.61 ms
Max Latency:                          20.63 ms
Throughput:                           54.55 FPS
------------------------------------------------------------------------
ISO 13855 Budget:   PASS (p95 <= 30.0 ms)
========================================================================
```

---

## 5. Behavioral Specification Compliance Matrix

### 5.1 Capability: `model-export`
[Specification Document](file:///Users/xander/Projects/edge-safety-guard/openspec/changes/model-export-benchmark/specs/model-export/spec.md)

| Requirement | Scenario / Criteria | Implementation Mapping | Verifying Test(s) | Status |
| :--- | :--- | :--- | :--- | :---: |
| **CLI Model Export with Static Shape** | Exporting `yolo11n-pose` with fixed dimensions `[1, 3, 640, 640]` | [`export_model`](file:///Users/xander/Projects/edge-safety-guard/models/export_onnx.py#L100-L177) sets `dynamic=False`, `imgsz=640` | `test_export_model_invokes_ultralytics`, `test_export_cli_success` | **PASS** |
| **Export Configuration Constraints** | Enforcing Opset 17 and `simplify=True` | [`export_model`](file:///Users/xander/Projects/edge-safety-guard/models/export_onnx.py#L154-L160) passes `opset=17`, `simplify=True` | `test_export_model_invokes_ultralytics` | **PASS** |
| **Post-Export Graph Topology & Shape Validation** | Validating well-formed ONNX model (`onnx.checker` & `shape_inference`) | [`validate_onnx_model`](file:///Users/xander/Projects/edge-safety-guard/models/export_onnx.py#L23-L98) checks topology, shapes, and `float32` | `test_validate_onnx_model_success` | **PASS** |
| | Detecting corrupted or invalid graph | [`validate_onnx_model`](file:///Users/xander/Projects/edge-safety-guard/models/export_onnx.py#L50-L61) catches malformed protobuf and schema errors | `test_validate_onnx_model_corrupt`, `test_validate_onnx_model_nonexistent` | **PASS** |
| | Detecting shape and dtype mismatches | [`validate_onnx_model`](file:///Users/xander/Projects/edge-safety-guard/models/export_onnx.py#L68-L94) checks expected input/output shapes and types | `test_validate_onnx_model_input_shape_mismatch`, `test_validate_onnx_model_output_shape_mismatch`, `test_validate_onnx_model_invalid_dtype` | **PASS** |
| **CLI Error Handling** | Handling missing weights with exit code 1 | [`main`](file:///Users/xander/Projects/edge-safety-guard/models/export_onnx.py#L234-L261) catches exceptions and terminates with `sys.exit(1)` | `test_export_cli_nonexistent_weights` | **PASS** |

### 5.2 Capability: `onnx-inference`
[Specification Document](file:///Users/xander/Projects/edge-safety-guard/openspec/changes/model-export-benchmark/specs/onnx-inference/spec.md)

| Requirement | Scenario / Criteria | Implementation Mapping | Verifying Test(s) | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Hardware-Accelerated Provider Negotiation** | CoreML initialization on Apple Silicon | [`_resolve_providers`](file:///Users/xander/Projects/edge-safety-guard/src/inference/onnx_engine.py#L83-L95) filters `DEFAULT_PROVIDERS` | `test_engine_init_success` | **PASS** |
| | Graceful fallback when CoreML fails | [`_initialize_session`](file:///Users/xander/Projects/edge-safety-guard/src/inference/onnx_engine.py#L97-L121) falls back to `CPUExecutionProvider` | `test_engine_provider_fallback_when_coreml_fails` | **PASS** |
| | Explicit provider override | `OnnxEngine(providers=["CPUExecutionProvider"])` | `test_engine_explicit_cpu_provider` | **PASS** |
| **Session Configuration & Thread Limits** | `ORT_ENABLE_ALL`, `intra_op_num_threads=4`, `ORT_SEQUENTIAL` | [`__init__`](file:///Users/xander/Projects/edge-safety-guard/src/inference/onnx_engine.py#L50-L54) configures `SessionOptions` | `test_engine_session_options_applied` | **PASS** |
| **Deterministic Precondition Validation** | Valid input tensor acceptance | [`infer`](file:///Users/xander/Projects/edge-safety-guard/src/inference/onnx_engine.py#L122-L163) processes valid `float32 (1, 3, 640, 640)` | `test_engine_infer_forward_pass` | **PASS** |
| | Rejecting invalid tensor shape | Raises `ValueError` for mismatched spatial or batch dimensions | `test_engine_infer_invalid_shape` | **PASS** |
| | Rejecting non-float32 and non-ndarray | Raises `TypeError` on `uint8`, `float64`, or Python lists | `test_engine_infer_invalid_dtype`, `test_engine_infer_non_ndarray` | **PASS** |
| **Raw Output Tensor Contract** | Output shape `(1, 56, 8400)` and `float32` | [`infer`](file:///Users/xander/Projects/edge-safety-guard/src/inference/onnx_engine.py#L159-L160) returns raw numpy ndarray | `test_engine_infer_forward_pass` | **PASS** |

### 5.3 Capability: `latency-benchmark`
[Specification Document](file:///Users/xander/Projects/edge-safety-guard/openspec/changes/model-export-benchmark/specs/latency-benchmark/spec.md)

| Requirement | Scenario / Criteria | Implementation Mapping | Verifying Test(s) | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Latency Warmup and Statistical Profiling** | Untimed warmup phase followed by high-resolution timed iterations | [`run_benchmark`](file:///Users/xander/Projects/edge-safety-guard/scripts/benchmark.py#L48-L86) executes warmup and uses `time.perf_counter_ns()` | `test_run_benchmark_warmup_isolation`, `test_run_benchmark_distribution_percentiles` | **PASS** |
| **Percentile Metrics & FPS Calculation** | Mean, std, min, max, p50, p95, p99, FPS (`1000 / mean`) | [`run_benchmark`](file:///Users/xander/Projects/edge-safety-guard/scripts/benchmark.py#L87-L115) computes percentiles with monotonic ordering | `test_benchmark_metrics_integrity`, `test_run_benchmark_distribution_percentiles` | **PASS** |
| **Real-Time Edge Safety Budget Verification** | Passing budget ($p95 \le 30.0\text{ ms}$) exits with code 0 | [`main`](file:///Users/xander/Projects/edge-safety-guard/scripts/benchmark.py#L262-L270) checks `metrics.passed_budget` | `test_benchmark_budget_evaluation`, `test_benchmark_cli_strict_pass` | **PASS** |
| | Failing budget in strict mode exits with code 1 | Returns non-zero exit code on breach | `test_benchmark_budget_evaluation`, `test_benchmark_cli_strict_fail` | **PASS** |
| **Structured Reporting & JSON Export** | Aligned console table summary | [`format_benchmark_table`](file:///Users/xander/Projects/edge-safety-guard/scripts/benchmark.py#L118-L146) formats ANSI summary table | `test_format_benchmark_table` | **PASS** |
| | Structured JSON schema export | [`export_benchmark_json`](file:///Users/xander/Projects/edge-safety-guard/scripts/benchmark.py#L148-L175) writes standardized metrics object | `test_benchmark_cli_json_export` | **PASS** |

---

## 6. Technical Design Coherence

The implementation closely mirrors the architectural decisions, component contracts, and constraints specified in [`design.md`](file:///Users/xander/Projects/edge-safety-guard/openspec/changes/model-export-benchmark/design.md):

1. **Static Input Shape Decision (Decision 1):**
   The pipeline strictly enforces `dynamic=False` at export time and validates `(1, 3, 640, 640)` on both export validation and inference ingress. This guarantees ahead-of-time memory layout stability and avoids Apple Silicon CoreML reallocation latency spikes.
2. **Hierarchical Execution Provider Negotiation (Decision 2):**
   `OnnxEngine` implements priority negotiation `['CoreMLExecutionProvider', 'CPUExecutionProvider']`. On Apple Silicon, CoreML accelerates 346 graph operators directly on the Apple Neural Engine / Metal GPU, with automatic CPU fallback if unsupported.
3. **Decoupled Architecture (Decision 3):**
   `OnnxEngine` is completely decoupled from the Ultralytics training/export framework. Downstream modules (homography, FSM, and visualization) can consume raw tensor predictions without framework baggage.
4. **Statistical Monotonic Profiling (Decision 4):**
   `scripts/benchmark.py` relies exclusively on `time.perf_counter_ns()`, strictly separating warmup iterations to avoid JIT/cache skew. The empirical $p95$ metric verifies conformance to the ISO 13855 response time allocation ($t_{\text{infer}} \le 30.0\text{ ms}$).
5. **Zero-Download Synthetic Fixture:**
   [`tests/conftest.py`](file:///Users/xander/Projects/edge-safety-guard/tests/conftest.py) generates compliant synthetic ONNX graphs in $<50\text{ ms}$, ensuring 100% offline test hermeticity without downloading multi-megabyte checkpoints in CI.

---

## 7. Strict TDD Cycle Compliance Evidence

All functional code was developed following strict Test-Driven Development:
1. **Unit 1 (Model Export):** Fixture in `tests/conftest.py` and unit tests in `tests/test_export.py` were committed/authored first (RED), followed by `models/export_onnx.py` (GREEN), and CLI/error refactoring (REFACTOR).
2. **Unit 2 (Inference Engine):** `tests/test_onnx_engine.py` authored first covering provider negotiation, fallback, and tensor type/shape guards (RED), followed by `src/inference/onnx_engine.py` (GREEN), and query helper refactoring (REFACTOR).
3. **Unit 3 (Benchmark Suite):** `tests/test_benchmark.py` authored first covering statistical percentiles, warmup exclusion, and strict CLI exits (RED), followed by `scripts/benchmark.py` (GREEN), and table formatting refactoring (REFACTOR).
4. **Unit 4 (Integration):** Full pytest run confirmed 26/26 tests passing, followed by real hardware profiling verifying strict safety budget adherence.

---

## 8. Verdict & Next Steps

- **Verification Verdict:** **PASS**
- **Test Results:** 26 passed, 0 failed, 0 regressions (2.32s)
- **Safety Budget:** $p95 = 20.26\text{ ms} \le 30.0\text{ ms}$ (PASS, 32.5% headroom)
- **Next Recommended Action:** `/sdd-archive` (Archive change `model-export-benchmark` to baseline specs)
