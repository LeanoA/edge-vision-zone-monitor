# Design: Runtime Engine Benchmarking Suite

## Architecture Overview

```
                      ┌────────────────────────────────────────┐
                      │      Comparative Benchmark Runner      │
                      │     scripts/benchmark_runtimes.py      │
                      └───────────────────┬────────────────────┘
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
     ┌─────────────────────────┐                     ┌─────────────────────────┐
     │       TorchEngine       │                     │       OnnxEngine        │
     │ src/inference/torch_... │                     │ src/inference/onnx_...  │
     ├─────────────────────────┤                     ├─────────────────────────┤
     │ • torch.inference_mode  │                     │ • CoreMLExecutionProv.  │
     │ • device="cpu"|"mps"    │                     │ • CPUExecutionProvider  │
     │ • returns np.ndarray    │                     │ • returns np.ndarray    │
     └─────────────────────────┘                     └─────────────────────────┘
```

## Detailed Design Decisions

### 1. Unified `TorchEngine` Abstraction (`src/inference/torch_engine.py`)
- Wraps `ultralytics.YOLO.model` or raw `torch.nn.Module`.
- Automatically loads `.pt` checkpoint and places model on target device (`cpu` or `mps` or `cuda`).
- Executes under `torch.inference_mode()` with `model.eval()`.
- Converts PyTorch output tensor back to contiguous CPU `np.ndarray` float32 to ensure fair measurement of end-to-end tensor transfer.
- Implements synchronization: on `mps` or `cuda`, calls `torch.mps.synchronize()` / `torch.cuda.synchronize()` inside timer bounds to guarantee accurate hardware timing without asynchronous lazy execution skewing results.

### 2. High-Resolution Statistical Measurement
- High precision nanosecond timing via `time.perf_counter_ns()`.
- Warmup isolation: untimed warmup iterations ensure JIT/graph compilation and shader caching are complete prior to measurement.
- Temporal Jitter computation:
  - $\text{Std} = \sqrt{\frac{1}{N-1}\sum (t_i - \bar{t})^2}$
  - $\text{IQR} = p75 - p25$
  - $\text{Variance} = \sigma^2$

### 3. Output Formats
- Pretty ASCII/Markdown tabular summary for terminal display and README/article embeds.
- Structured JSON with ISO 13855 compliance flag ($p95 \le 30\text{ ms}$).
