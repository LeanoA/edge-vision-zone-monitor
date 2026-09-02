## 📊 Comparative Quantization & Metric Precision Benchmark (YOLO11-Pose)

| Precision Mode | Model Size | Size Reduction | Mean Latency | Throughput | Pixel RMSE | Metric Ground RMSE | Max Drift | ISO 13855 Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **FP32 (Single Precision)** | 11.30 MB | 0.0% | 17.68 ms | 56.6 FPS | 0.00 px | 0.00 cm | 0.00 cm | ✅ PASS |
| **FP16 (Half Precision)** | 5.69 MB | 49.6% | 42.40 ms | 23.6 FPS | 0.31 px | 1.37 cm | 34.88 cm | ✅ PASS |
| **INT8 (Dynamic Quant)** | 3.27 MB | 71.1% | 97.85 ms | 10.2 FPS | 23.84 px | 156.70 cm | 2179.88 cm | ❌ FAIL |
