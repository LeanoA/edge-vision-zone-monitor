# Proposal: Quantization & Metric Precision Benchmarking Suite

## Problem Statement
Quantizing deep learning models for edge hardware (FP16 / INT8) accelerates inference and cuts RAM usage, but its impact on geometric accuracy in metric-space safety monitoring is unquantified. We need a reproducible evaluation harness measuring both inference throughput and metric projection drift ($RMSE_{XY}$ in cm) on real and synthetic validation datasets.

## Proposed Solution
1. **Automated Quantization Pipeline**:
   - Add export utilities to generate FP16 and INT8 ONNX models with validation checks.
2. **Metric Precision Evaluator (`src/inference/precision_evaluator.py` / `scripts/benchmark_quantization.py`)**:
   - Compare predictions from FP32 (reference ground truth) against FP16 and INT8 models on dataset frames.
   - Decode detections (bounding boxes, ankle keypoints, confidence scores).
   - Project detections to metric ground coordinates $(X_w, Y_w)$ via `HomographyManager`.
   - Calculate Mean Pixel Error ($E_{\text{px}}$), Metric RMSE ($RMSE_{\text{metric}}$ in cm), Maximum Metric Drift ($E_{\max}$ in cm), and Inference Latency / Throughput.
3. **Comparative Export**:
   - Generate comparative tables in Markdown and structured JSON for documentation and post-publication.
