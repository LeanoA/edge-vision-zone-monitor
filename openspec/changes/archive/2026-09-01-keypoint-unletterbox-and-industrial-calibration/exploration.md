# Exploration: Keypoint Unletterboxing and Industrial Ground Calibration

**Change ID:** `keypoint-unletterbox-and-industrial-calibration`  
**Date:** 2026-09-01  
**Author:** AI Pair Programmer & Senior Architect

---

## 1. Problem Identification

When evaluating Full HD ($1920 \times 1080$) industrial camera feeds (`mendeley_industrial` and `openvino_people`), the detected human pose skeletons and ground anchor markers appear shrunken and displaced toward the top-left quadrant of the frame, disconnected from the actual position of the human operator.

### 1.1 Root Cause Analysis

1. **Letterbox Transformation:**
   The original frame ($W_{\text{orig}} \times H_{\text{orig}}$) is scaled and padded to $640 \times 640$ via `letterbox_image`:
   $$\text{scale} = \min\left(\frac{640}{W_{\text{orig}}}, \frac{640}{H_{\text{orig}}}\right), \quad \text{pad}_x = \frac{640 - W_{\text{orig}}\cdot\text{scale}}{2}, \quad \text{pad}_y = \frac{640 - H_{\text{orig}}\cdot\text{scale}}{2}$$
   For $1920 \times 1080$, $\text{scale} = 0.3333$, $\text{pad}_x = 0$, $\text{pad}_y = 140\text{ px}$.

2. **Bounding Box vs Keypoints Coordinate Mapping:**
   In `src/pipeline/safety_pipeline.py::parse_detections`:
   - Bounding boxes $(cx, cy, w, h)$ are mapped back to original image space via `unletterbox_point`.
   - **Keypoints ($17 \times 3$) remained in $(640, 640)$ letterbox space:**
     ```python
     kps = np.zeros((17, 3), dtype=np.float32)
     if raw.shape[0] >= 56:
         kp_data = raw[5:56, idx].reshape(17, 3)
         kps[:] = kp_data  # <-- BUG: Still in letterbox space (640x640)
     ```
   - Furthermore, `extract_ground_anchor(kps, ...)` received `scale=1.0, pad_x=0.0, pad_y=0.0`, computing ankle midpoints in letterbox space rather than in full resolution frame space.

3. **Visualizer Rendering Impact:**
   `src/utils/visualizer.py::render_perspective` plots skeleton connections and keypoints directly using `det.keypoints` on the original resolution canvas. Because keypoints were unscaled, $(x, y)$ coordinates in $[0..640]$ were drawn on the $[0..1920] \times [0..1080]$ canvas, shrinking the skeleton by a factor of 3.

---

## 2. Proposed Architectural Solution

1. **Vectorized Keypoint Unletterboxing Function:**
   Implement `unletterbox_keypoints(keypoints: np.ndarray, scale: float, pad_x: float, pad_y: float) -> np.ndarray`:
   $$kps_{\text{orig}}[:, 0] = \frac{kps[:, 0] - \text{pad}_x}{\text{scale}}$$
   $$kps_{\text{orig}}[:, 1] = \frac{kps[:, 1] - \text{pad}_y}{\text{scale}}$$
   $$kps_{\text{orig}}[:, 2] = kps[:, 2] \quad (\text{preserves confidence scores})$$

2. **Integration in `parse_detections`:**
   Immediately transform keypoints upon parsing the YOLO tensor so that `PoseDetection.keypoints` is in original frame coordinates.

3. **Refactoring `extract_ground_anchor`:**
   Standardize `extract_ground_anchor` to operate on unletterboxed keypoints and unletterboxed bounding boxes directly, removing redundant scaling arguments.

4. **Industrial Ground Plane Calibration Profile:**
   Calibrate `configs/datasets/mendeley_industrial.yaml` with precise 4-point DLT ground homography matching the $1920 \times 1080$ production floor perspective.

5. **Automated Unit Tests:**
   Add comprehensive test coverage in `tests/test_pipeline.py` verifying keypoint unletterbox inversion and aspect ratio preservation.
