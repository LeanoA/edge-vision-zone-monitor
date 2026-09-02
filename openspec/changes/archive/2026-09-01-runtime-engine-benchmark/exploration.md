# Exploration: Runtime Engine Benchmark (PyTorch vs ONNX vs CoreML)

## 1. Context & Objective
In industrial edge safety guarding (ISO 13855 / IEC 61496), perception latency and jitter must be strictly bounded ($T_1 \le 50\text{ ms}$, target $T_1 \le 30\text{ ms}$).
To provide empirical evidence for architecture decisions and technical articles, we need a unified benchmarking harness to compare:
1. **PyTorch Eager (CPU)**: Baseline Python runtime with `torch.inference_mode()`.
2. **PyTorch Eager (MPS)**: Apple Silicon GPU acceleration via Metal Performance Shaders.
3. **ONNX Runtime (CPUExecutionProvider)**: Optimized static graph inference with multi-threaded CPU execution.
4. **ONNX Runtime (CoreMLExecutionProvider)**: Optimized static graph inference compiled for Apple Neural Engine (ANE) and GPU.

## 2. Existing Code & Assets
- `models/yolo11n-pose.pt` ($6.26\text{ MB}$): Native PyTorch weights.
- `models/yolo11n-pose.onnx` ($11.85\text{ MB}$): Static shape ($1, 3, 640, 640$) exported ONNX graph.
- `src/inference/onnx_engine.py`: Encapsulates `onnxruntime.InferenceSession` with dynamic provider fallback.
- `scripts/benchmark.py`: Single-engine ONNX benchmark script.
- `tests/test_benchmark.py`: Unit tests for benchmark metrics.

## 3. Architecture Exploration
We should introduce a clean modular design:
- `src/inference/torch_engine.py`: `TorchEngine` wrapper providing a consistent `.infer(img)` API matching `OnnxEngine` for PyTorch models (supporting CPU and MPS devices).
- `src/inference/benchmark.py`: Core benchmark runner supporting multiple engine types with statistical profiling (Mean, Std, Min, Max, p50, p95, p99, IQR, Jitter $\sigma^2$, FPS, Speedup factor vs baseline).
- `scripts/benchmark_runtimes.py`: CLI multi-runtime comparator that runs all engines sequentially on the same synthetic/real input distributions and generates markdown + JSON comparative tables.
- Updates to `scripts/benchmark.py` and `tests/test_benchmark.py` to support comprehensive multi-engine validation.
