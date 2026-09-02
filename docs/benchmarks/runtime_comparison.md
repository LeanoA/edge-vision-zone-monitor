## 📊 Comparative Runtime Engine Benchmark (YOLO11-Pose)

| Runtime Engine | Backend / Device | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Jitter $\sigma$ (ms) | Throughput (FPS) | Speedup vs CPU | ISO 13855 ($\le 30\text{ms}$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **PyTorch Eager (CPU)** | `PyTorch_CPU` | 70.80 | 69.86 | 75.11 | 75.91 | ±1.96 | 14.1 FPS | 1.00x | ❌ FAIL |
| **PyTorch Eager (MPS)** | `PyTorch_MPS` | 17.63 | 17.00 | 20.82 | 22.75 | ±1.67 | 56.7 FPS | **4.02x** | ✅ PASS |
| **ONNX Runtime (CPU)** | `CPUExecutionProvider` | 40.54 | 39.92 | 44.72 | 48.18 | ±2.04 | 24.7 FPS | **1.75x** | ❌ FAIL |
| **ONNX Runtime (CoreML/ANE)** | `CoreMLExecutionProvider` | 15.81 | 15.88 | 19.02 | 20.88 | ±1.79 | 63.3 FPS | **4.48x** | ✅ PASS |
