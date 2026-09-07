## 📊 Comparative Resolution Benchmark (640 vs 960 on Walkway Video)

| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
## 3. Resolution & Far-Field Walkway Detection (348 Frames)
| Resolution / Mode | Size | Preprocess | Ingestion+Inference | Pipeline Latency ($T_1$) | $p95$ of $T_1$ | Wall Throughput | Total Detections | Far Detections ($Y_w > 6\text{m}$) | Budget ($T_1 \le 50\text{ms}$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **640p FP32 (Baseline)** | 11.30 MB | 0.94 ms | 18.77 ms | 19.80 ms | 22.35 ms | 46.9 FPS | **83** | **83** | ✅ PASS |
| **640p FP16** | 5.69 MB | 0.91 ms | 42.90 ms | 43.88 ms | 48.74 ms | 22.0 FPS | **76** | **76** | ✅ PASS |
| **960p FP32** | 11.58 MB | 1.88 ms | 40.44 ms | 42.54 ms | 45.34 ms | 22.6 FPS | **639** | **639** | ✅ PASS |
| **960p FP16** | 5.85 MB | 1.86 ms | 95.38 ms | 97.44 ms | 113.47 ms | 10.1 FPS | **624** | **624** | ❌ FAIL |
| :--- | :---: | :---: | :---: | :---: | :---: |
