## 📊 Comparative Quantization & Metric Precision Benchmark (YOLO11-Pose)

| Precision Mode | Model Size | Size Reduction | Mean Latency | Throughput | Pixel RMSE | Metric Ground RMSE | Max Drift | ISO 13855 Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **FP32 (Single Precision)** | 11.30 MB | 0.0% | 13.85 ms | 72.2 FPS | 0.00 px | 0.00 cm | 0.00 cm | ✅ PASS |
| **FP16 (Half Precision)** | 5.69 MB | 49.6% | 42.49 ms | 23.5 FPS | 0.45 px | 2.15 cm | 43.45 cm | ✅ PASS |
| **INT8 (Dynamic Quant)** | 3.27 MB | 71.1% | 97.50 ms | 10.3 FPS | 34.82 px | 275.12 cm | 3056.06 cm | ❌ FAIL |
