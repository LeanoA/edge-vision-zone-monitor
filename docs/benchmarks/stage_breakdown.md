## 📊 Pipeline Granular Stage Latency Breakdown

| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **FP32 (Single Precision)** | 11.30 MB | 0.0% | 15.79 ms | 63.3 FPS | 26.50 px | **33.32 cm** | 67.85 cm | 27.05 cm | 41.60 cm | ❌ FAIL |
| **FP16 (Half Precision)** | 5.69 MB | 49.7% | 42.18 ms | 23.7 FPS | 26.51 px | **33.35 cm** | 66.90 cm | 27.07 cm | 41.67 cm | ❌ FAIL |
| **INT8 (Dynamic Quant)** | 3.27 MB | 71.1% | 91.58 ms | 10.9 FPS | 18.30 px | **18.96 cm** | 88.03 cm | 19.20 cm | 17.51 cm | ❌ FAIL |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **640p FP32 (Baseline)** | 11.30 MB | 0.94 ms | 18.77 ms | 19.80 ms | 22.35 ms | 46.9 FPS | **83** | **83** | ✅ PASS |
| **640p FP16** | 5.69 MB | 0.91 ms | 42.90 ms | 43.88 ms | 48.74 ms | 22.0 FPS | **76** | **76** | ✅ PASS |
| **960p FP32** | 11.58 MB | 1.88 ms | 40.44 ms | 42.54 ms | 45.34 ms | 22.6 FPS | **639** | **639** | ✅ PASS |
| **960p FP16** | 5.85 MB | 1.86 ms | 95.38 ms | 97.44 ms | 113.47 ms | 10.1 FPS | **624** | **624** | ❌ FAIL |
## 4. Pipeline Granular Stage Latency Breakdown
| Pipeline Stage | Mean (ms) | Median p50 (ms) | p95 Critical (ms) | p99 Extreme (ms) | % of Pipeline ($T_1$) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Ingest & Frame Capture (Buffer)** | 1.66 ms | 1.32 ms | 2.52 ms | 7.55 ms | 9.2% |
| **2. Preprocessing (Letterbox / Norm)** | 0.90 ms | 0.87 ms | 1.04 ms | 1.19 ms | 5.0% |
| **3. YOLO11n-Pose Inference (CoreML)** | 16.42 ms | 17.08 ms | 18.52 ms | 19.55 ms | 91.6% |
| **4. Detection & Keypoint Parsing** | 0.21 ms | 0.21 ms | 0.29 ms | 0.32 ms | 1.2% |
| **5. Homography DLT Projection** | 0.08 ms | 0.08 ms | 0.10 ms | 0.13 ms | 0.4% |
| **6. Kalman Filter & Hungarian MOT** | 0.29 ms | 0.30 ms | 0.43 ms | 0.44 ms | 1.6% |
| **7. Spatial FSM & Dwell Statecharts** | 0.02 ms | 0.01 ms | 0.06 ms | 0.07 ms | 0.1% |
| **Total Vision Pipeline Latency (T1)** | 17.92 ms | 18.53 ms | 20.16 ms | 21.42 ms | 100.0% |
| **Total End-to-End System (T_system)** | 19.58 ms | 19.88 ms | 22.22 ms | 26.13 ms | 100.0% |
