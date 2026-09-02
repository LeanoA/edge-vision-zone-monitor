# Exploration: Quantization & Precision Benchmark (FP32 vs FP16 vs INT8)

## 1. Motivation & Industrial Objective
In industrial edge safety (ISO 13855), high throughput and low model size are desirable, but safety-critical geometry requires sub-decimeter metric accuracy.
Quantization reduces floating point bitwidth:
- **FP32** (32-bit single precision, baseline: $11.85\text{ MB}$)
- **FP16** (16-bit half precision, $5.95\text{ MB}$, $50\%$ storage reduction)
- **INT8** (8-bit dynamic quantization, $3.42\text{ MB}$, $71\%$ storage reduction)

The critical architectural question for edge deployments is:
**Does INT8 or FP16 quantization introduce spatial drift in detected ankle keypoints that translates into dangerous metric errors when projected onto the factory floor via the homography matrix $H$?**

## 2. Technical Findings
1. In the near field ($Y_w < 5\text{m}$), $1\text{ px} \approx 1 - 2\text{ cm}$.
2. In the far field ($Y_w > 12\text{m}$), perspective foreshortening magnifies pixel errors: $1\text{ px} \approx 10 - 25\text{ cm}$.
3. Therefore, spatial degradation must be evaluated in two domains:
   - **Image Space**: Keypoint Euclidean displacement $E_{\text{px}} = \sqrt{(\Delta u)^2 + (\Delta v)^2}$.
   - **World Ground Metric Space**: Projected ground error $E_{\text{world}} = \sqrt{(\Delta X_w)^2 + (\Delta Y_w)^2}$ in centimeters.
