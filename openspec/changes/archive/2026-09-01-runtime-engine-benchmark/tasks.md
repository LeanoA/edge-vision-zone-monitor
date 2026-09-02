# Tasks: runtime-engine-benchmark

## Phase 1: Modular Engine & TDD Tests
- [x] 1.1 [RED] Write failing tests in `tests/test_torch_engine.py` verifying `TorchEngine` initialization, device placement (`cpu`, `mps`), inference output shape, and tensor conversions.
- [x] 1.2 [GREEN] Implement `TorchEngine` in `src/inference/torch_engine.py` with device synchronization and `.infer()` API.

## Phase 2: Multi-Runtime Benchmark Engine & CLI
- [x] 2.1 [RED] Write failing tests in `tests/test_runtime_benchmarks.py` testing statistical metric calculations, multi-runtime comparison orchestrator, speedup calculation, and markdown/JSON formatting.
- [x] 2.2 [GREEN] Implement comparative benchmarking logic in `scripts/benchmark_runtimes.py` and enhance `scripts/benchmark.py` with multi-engine compatibility.

## Phase 3: Execution, Empirical Profiling & Verification
- [x] 3.1 [VERIFY] Run unit test suite ensuring all tests pass (`pytest tests/test_torch_engine.py tests/test_runtime_benchmarks.py tests/test_benchmark.py`).
- [x] 3.2 [VERIFY] Execute `scripts/benchmark_runtimes.py` generating live empirical benchmark metrics across PyTorch CPU, PyTorch MPS, ONNX CPU, and ONNX CoreML.
- [x] 3.3 [VERIFY] Export comparative markdown and JSON reports to `docs/benchmarks/` and verify the full repo test suite passes with 0 regressions.
