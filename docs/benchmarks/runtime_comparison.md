## Comparative Runtime Engine Benchmark (YOLO11-Pose @ 640x640)

| Runtime Engine | Backend / Device | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Std (ms) | Pure Inference FPS | Speedup vs CPU | Internal Budget (p95 $\le$ 30ms) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **PyTorch Eager (CPU)** | `PyTorch_CPU` | 77.80 | 73.80 | 98.32 | 120.10 | ±10.73 | 12.9 FPS | **1.00x** | ❌ FAIL |
| **ONNX Runtime (CPU)** | `CPUExecutionProvider` | 47.33 | 45.24 | 60.07 | 76.57 | ±8.03 | 21.1 FPS | **1.64x** | ❌ FAIL |
| **PyTorch Eager (MPS)** | `PyTorch_MPS` | 20.57 | 19.94 | 25.01 | 27.67 | ±2.90 | 48.6 FPS | **3.78x** | ✅ PASS |
| **ONNX Runtime (CoreML)** | `CoreMLExecutionProvider` | 17.83 | 17.76 | 20.80 | 21.95 | ±1.75 | 56.1 FPS | **4.36x** | ✅ PASS |
