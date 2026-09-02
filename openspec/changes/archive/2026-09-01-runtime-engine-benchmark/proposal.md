# Proposal: Runtime Engine Comparative Benchmarking Suite

## Problem Statement
The Edge Safety Guard pipeline relies on low latency and minimal jitter for ISO 13855 safety compliance. While [ADR-003](docs/decisions/adr-003-onnx-runtime-coreml.md) asserts that ONNX Runtime with CoreML is superior to PyTorch eager execution, the codebase lacks an automated, reproducible comparative benchmark harness that measures all 4 execution runtimes side-by-side with identical inputs and statistically rigorous metrics.

## Proposed Solution
1. **Modular `TorchEngine`**: Implement a PyTorch inference wrapper in `src/inference/torch_engine.py` matching the `.infer(tensor)` and `.get_device()` interface of `OnnxEngine`.
2. **Unified Benchmark Core**: Enhance benchmark execution to support any engine conforming to the inference interface, measuring:
   - Central tendency: Mean, Median ($p50$).
   - Tail latency: $p95$, $p99$, Max.
   - Temporal stability / Jitter: Standard deviation $\sigma$, Interquartile Range ($IQR$), variance $\sigma^2$.
   - Throughput & Speedup: $\text{FPS}$ and relative acceleration factor vs PyTorch CPU baseline.
3. **Multi-Engine Comparison CLI (`scripts/benchmark_runtimes.py`)**: A dedicated comparison CLI that runs all 4 engines (`pytorch_cpu`, `pytorch_mps`, `onnx_cpu`, `onnx_coreml`), formats a Markdown/ASCII comparative table, and exports structured JSON for CI/CD and technical articles.

## Impact & Scope
- **Files added**: `src/inference/torch_engine.py`, `scripts/benchmark_runtimes.py`, `tests/test_torch_engine.py`, `tests/test_runtime_benchmarks.py`.
- **Files updated**: `scripts/benchmark.py`, `tests/test_benchmark.py`.
- **Breaking changes**: None. Fully backward-compatible.
