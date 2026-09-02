# Design: Quantization & Metric Precision Benchmarking Suite

## Architecture Overview

```
                      ┌────────────────────────────────────────┐
                      │    Quantization Benchmark Runner       │
                      │    scripts/benchmark_quantization.py   │
                      └───────────────────┬────────────────────┘
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  ▼                       ▼                       ▼
     ┌─────────────────────────┐ ┌────────────────────────┐ ┌────────────────────────┐
     │      FP32 Baseline      │ │      FP16 Model        │ │       INT8 Model       │
     │ models/yolo11n-pose.onnx│ │ models/...-fp16.onnx   │ │ models/...-int8.onnx   │
     └────────────┬────────────┘ └───────────┬────────────┘ └───────────┬────────────┘
                  │                          │                          │
                  └───────────────────────┐  │  ┌───────────────────────┘
                                          ▼  ▼  ▼
                             ┌──────────────────────────────┐
                             │  Precision & Metric Drift    │
                             │  Evaluator (Homography H)    │
                             │  • Pixel RMSE (px)           │
                             │  • Ground RMSE (cm)          │
                             │  • Max Metric Drift (cm)     │
                             └──────────────────────────────┘
```

## Detailed Design Decisions

### 1. Spatial Matching & Keypoint Association
- For each frame, run FP32 reference model to detect persons and extract baseline keypoint arrays $K_{\text{ref}} \in \mathbb{R}^{M \times 17 \times 3}$.
- Run candidate quantized model (FP16 or INT8) to extract candidate keypoint arrays $K_{\text{cand}} \in \mathbb{R}^{N \times 17 \times 3}$.
- Match detected persons by bounding box IoU ($\text{IoU} \ge 0.5$).
- For matched persons, compute keypoint error $\Delta p_k = \|(u_{\text{cand}, k}, v_{\text{cand}, k}) - (u_{\text{ref}, k}, v_{\text{ref}, k})\|_2$.
- Project ankle anchors ($k=15, 16$ or midpoint) through `HomographyManager.project(u, v)` to get $(X_w, Y_w)_{\text{ref}}$ and $(X_w, Y_w)_{\text{cand}}$.
- Compute metric distance $\Delta D = 100.0 \times \sqrt{(X_{\text{cand}} - X_{\text{ref}})^2 + (Y_{\text{cand}} - Y_{\text{ref}})^2}$ in centimeters.

### 2. Output Formats
- Generates a clear Markdown table and JSON file in `docs/benchmarks/` comparing:
  - Precision mode, File Size (MB), Latency (ms), Throughput (FPS), Pixel Error (px), Metric RMSE (cm), Max Drift (cm), and Safety Status ($RMSE \le 15\text{ cm}$).
