# Specification: Quantization and Geometric Precision Benchmarking (`quantization-precision`)

## Purpose
Define the formal behavioral requirements and acceptance thresholds for measuring inference latency and metric geometric error across numerical quantization modes (FP32, FP16, INT8).

---

### Requirement: Quantitative Precision Profiling
The quantization evaluation suite MUST profile candidate models against a baseline FP32 model:
1. **Model Size and Footprint**: Report file size in MB and storage reduction percentage.
2. **Inference Latency & Throughput**: Report mean latency (ms), p95 latency (ms), and FPS under identical hardware backends.
3. **Keypoint Pixel Drift**: Calculate average Euclidean pixel error $E_{\text{px}} = \sqrt{(\Delta u)^2 + (\Delta v)^2}$ across all detected anatomical keypoints with confidence $\ge 0.5$.
4. **Metric Ground Projection Drift**: Project detected ankle anchors to metric world plane $(X_w, Y_w)$ via $H$, computing $RMSE_{XY} = \sqrt{\frac{1}{N}\sum (\Delta X)^2 + (\Delta Y)^2}$ in centimeters.
5. **Safety Tolerance Threshold**: For industrial safeguarding under ISO 13855, the metric $RMSE_{XY}$ for high-confidence detections ($\text{conf} \ge 0.5$) in the working zone ($Y_w \le 10\text{m}$) MUST NOT exceed $15.0\text{ cm}$.

#### Scenario: Evaluating FP16 model precision
- **GIVEN** an FP32 reference model and an FP16 candidate model
- **WHEN** precision evaluation executes across validation frames
- **THEN** $RMSE_{XY}$ SHALL be strictly less than $5.0\text{ cm}$
- **AND** the inference latency SHALL be equal to or lower than the FP32 baseline.

#### Scenario: Evaluating INT8 model precision
- **GIVEN** an FP32 reference model and an INT8 dynamically quantized model
- **WHEN** precision evaluation executes across validation frames
- **THEN** model size reduction SHALL exceed $50\%$
- **AND** $RMSE_{XY}$ SHALL be computed and reported in centimeters alongside maximum observed drift.

#### Scenario: Formatting comparative table and exporting JSON
- **GIVEN** a completed quantization precision evaluation summary
- **WHEN** `format_quantization_markdown(summary)` and `export_quantization_json(summary, path)` execute
- **THEN** the Markdown output SHALL include columns for Model Precision, Size (MB), Latency (ms), FPS, Mean Pixel Error (px), Metric RMSE (cm), Max Metric Drift (cm), and Safety Budget Status
- **AND** the JSON file SHALL contain all numeric metrics and configuration metadata.
