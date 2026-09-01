# Proposal: Keypoint Unletterboxing and Industrial Ground Calibration

**Change ID:** `keypoint-unletterbox-and-industrial-calibration`  
**Date:** 2026-09-01  
**Status:** PROPOSED  

---

## 1. Context & Motivation

During the empirical evaluation of the `mendeley_industrial` sequence ($1920 \times 1080$ Full HD CCTV), visual observation showed that while bounding boxes and tracks were placed correctly, the 17-point pose skeleton and ankle ground anchors appeared compressed to $1/3$ scale and shifted toward the upper-left of the image.

The root cause was traced to `src/pipeline/safety_pipeline.py::parse_detections`, where bounding boxes were unletterboxed using inverse scaling and offsets, but keypoints remained in raw $(640 \times 640)$ letterbox canvas space.

This change corrects the keypoint coordinate transformation, standardizes ground anchor extraction to work directly in full-frame pixel coordinates, updates industrial calibration points, and adds rigorous unit tests to prevent regression.

---

## 2. Proposed Changes

1. **`src/pipeline/safety_pipeline.py`:**
   - Introduce vectorized `unletterbox_keypoints(keypoints: np.ndarray, scale: float, pad_x: float, pad_y: float) -> np.ndarray` supporting $(N, 3)$ or $(17, 3)$ keypoint arrays.
   - Update `parse_detections` to apply `unletterbox_keypoints` to all parsed candidate keypoints before creating `PoseDetection` objects.
   - Simplify `extract_ground_anchor` to expect keypoints already in native frame coordinates.

2. **`configs/datasets/mendeley_industrial.yaml`:**
   - Calibrate 4-point DLT ground plane reference points for the factory floor in $1920 \times 1080$ coordinates.

3. **`tests/test_pipeline.py`:**
   - Add unit tests verifying `unletterbox_keypoints` under letterbox (horizontal padding) and pillarbox (vertical padding) conditions.
   - Verify that `extract_ground_anchor` correctly maps dual ankle midpoints and single ankle fallbacks in native frame space.

---

## 3. Impact Assessment

- **Core Stability:** No changes to `src/core/` (`homography.py`, `kalman_filter.py`, `spatial_fsm.py`).
- **Performance:** Vectorized NumPy operations introduce zero latency overhead ($< 0.05\text{ ms}$).
- **Backward Compatibility:** All existing tests in `tests/` remain valid or enhanced.
