# Tasks: quantization-precision-benchmark

## Phase 1: Precision Evaluator & TDD Tests
- [x] 1.1 [RED] Write failing tests in `tests/test_quantization_benchmarks.py` validating precision metric data structures, keypoint displacement RMSE calculation, and homography ground-projection error computation.
- [x] 1.2 [GREEN] Implement `PrecisionMetrics`, `compute_geometric_drift`, and `run_quantization_precision_benchmark` in `scripts/benchmark_quantization.py`.

## Phase 2: Live Empirical Profiling & CLI Export
- [x] 2.1 [GREEN] Implement CLI interface in `scripts/benchmark_quantization.py` with Markdown and JSON export.
- [x] 2.2 [VERIFY] Execute live empirical benchmark comparing FP32, FP16, and INT8 models across `openvino_people` / `pets2009_s2_l1` frames and synthetic inputs.
- [x] 2.3 [VERIFY] Export comparative markdown and JSON reports to `docs/benchmarks/quantization_comparison.md` and `docs/benchmarks/quantization_comparison.json`.

## Phase 3: Full Verification & Archive
- [x] 3.1 [VERIFY] Run full test suite (`pytest tests/`) ensuring 100% pass rate.
- [x] 3.2 [ARCHIVE] Update `docs/benchmarks/experiments-plan.md` with Ensayo 2 empirical results and engineering discussion.
