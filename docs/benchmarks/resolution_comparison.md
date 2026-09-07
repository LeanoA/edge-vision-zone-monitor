## 📊 Comparative Resolution Benchmark (640 vs 960 on Walkway Video)

| Resolution / Mode | Size | Preprocess | Ingestion+Inference | Pipeline Latency ($T_1$) | $p95$ of $T_1$ | Wall Throughput | Total Detections | Far Detections ($Y_w > 6\text{m}$) | Budget ($T_1 \le 50\text{ms}$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **640p FP32 (Baseline)** | 11.30 MB | 0.88 ms | 17.87 ms | 18.84 ms | 20.31 ms | 49.1 FPS | **83** | **83** | ✅ PASS |
| **640p FP16** | 5.69 MB | 0.89 ms | 42.18 ms | 43.14 ms | 47.35 ms | 22.1 FPS | **76** | **76** | ✅ PASS |
| **960p FP32** | 11.58 MB | 1.83 ms | 40.83 ms | 42.86 ms | 45.79 ms | 22.5 FPS | **639** | **639** | ✅ PASS |
| **960p FP16** | 5.85 MB | 1.78 ms | 92.26 ms | 94.22 ms | 99.78 ms | 10.4 FPS | **624** | **624** | ❌ FAIL |
