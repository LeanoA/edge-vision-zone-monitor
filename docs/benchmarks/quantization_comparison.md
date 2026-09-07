## 📊 Comparative Quantization & Metric Precision Benchmark (YOLO11-Pose)

| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
## 2. Numerical Precision & Quantization Drift
| Precision Mode | Model Size | Reduction | Mean Latency | Throughput | Pixel RMSE | Metric Ground RMSE | Max Drift | Near ($<2.5\text{m}$) | Far ($>4.0\text{m}$) | Tolerance ($\le 15\text{cm}$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **FP32 (Single Precision)** | 11.30 MB | 0.0% | 15.79 ms | 63.3 FPS | 26.50 px | **33.32 cm** | 67.85 cm | 27.05 cm | 41.60 cm | ❌ FAIL |
| **FP16 (Half Precision)** | 5.69 MB | 49.7% | 42.18 ms | 23.7 FPS | 26.51 px | **33.35 cm** | 66.90 cm | 27.07 cm | 41.67 cm | ❌ FAIL |
| **INT8 (Dynamic Quant)** | 3.27 MB | 71.1% | 91.58 ms | 10.9 FPS | 18.30 px | **18.96 cm** | 88.03 cm | 19.20 cm | 17.51 cm | ❌ FAIL |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| :--- | :---: | :---: | :---: | :---: | :---: |
