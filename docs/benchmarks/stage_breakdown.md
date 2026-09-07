## 📊 Pipeline Granular Stage Latency Breakdown

| Pipeline Stage | Mean (ms) | Median p50 (ms) | p95 Critical (ms) | p99 Extreme (ms) | % of Pipeline ($T_1$) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Ingest & Frame Capture (Buffer)** | 1.46 ms | 1.20 ms | 1.67 ms | 7.85 ms | 7.9% |
| **2. Preprocessing (Letterbox / Norm)** | 0.87 ms | 0.86 ms | 0.93 ms | 0.96 ms | 4.7% |
| **3. YOLO11n-Pose Inference (CoreML)** | 16.97 ms | 16.98 ms | 18.74 ms | 20.48 ms | 92.1% |
| **4. Detection & Keypoint Parsing** | 0.21 ms | 0.20 ms | 0.27 ms | 0.31 ms | 1.1% |
| **5. Homography DLT Projection** | 0.08 ms | 0.08 ms | 0.09 ms | 0.10 ms | 0.4% |
| **6. Kalman Filter & Hungarian MOT** | 0.29 ms | 0.29 ms | 0.40 ms | 0.43 ms | 1.6% |
| **7. Spatial FSM & Dwell Statecharts** | 0.02 ms | 0.01 ms | 0.06 ms | 0.06 ms | 0.1% |
| **Total Vision Pipeline Latency (T1)** | 18.43 ms | 18.49 ms | 20.29 ms | 21.82 ms | 100.0% |
| **Total End-to-End System (T_system)** | 19.90 ms | 19.70 ms | 22.29 ms | 28.33 ms | 100.0% |
