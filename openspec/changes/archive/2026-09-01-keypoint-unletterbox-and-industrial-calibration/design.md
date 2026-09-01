# Technical Design: Keypoint Coordinate Inversion & Ground Anchor Alignment

**Change ID:** `keypoint-unletterbox-and-industrial-calibration`  
**Date:** 2026-09-01  
**Status:** DESIGNED  

---

## 1. Mathematical Formulation of Keypoint Inversion

Let a video frame have dimensions $(W_{\text{orig}}, H_{\text{orig}})$ and target letterbox dimensions $(W_{\text{target}}, H_{\text{target}}) = (640, 640)$.

The letterbox forward transformation applies uniform scaling and symmetrical padding:
$$s = \min\left(\frac{W_{\text{target}}}{W_{\text{orig}}}, \frac{H_{\text{target}}}{H_{\text{orig}}}\right)$$
$$\text{pad}_x = \frac{W_{\text{target}} - W_{\text{orig}} \cdot s}{2}, \quad \text{pad}_y = \frac{H_{\text{target}} - H_{\text{orig}} \cdot s}{2}$$

For any keypoint $(x_{\text{canvas}}, y_{\text{canvas}}, c)$ predicted by YOLO11-Pose in letterbox space, the exact original frame coordinate $(x_{\text{orig}}, y_{\text{orig}}, c)$ is given by:

$$x_{\text{orig}} = \frac{x_{\text{canvas}} - \text{pad}_x}{s}, \quad y_{\text{orig}} = \frac{y_{\text{canvas}} - \text{pad}_y}{s}$$

Confidence score $c$ is invariant under affine coordinate transformations ($c_{\text{orig}} = c$).

---

## 2. Vectorized Implementation Specification

```python
def unletterbox_keypoints(
    keypoints: np.ndarray,
    scale: float,
    pad_x: float,
    pad_y: float,
) -> np.ndarray:
    """
    Transform (17, 3) or (N, 3) keypoints from letterboxed canvas space to original frame space.

    Args:
        keypoints: Array of shape (..., 3) with [x, y, conf].
        scale: Scaling factor applied during letterboxing.
        pad_x: Horizontal padding offset.
        pad_y: Vertical padding offset.

    Returns:
        New float32 array of identical shape with transformed (x, y) and preserved confidence.
    """
    if scale <= 0.0:
        raise ValueError(f"Scale must be positive, got {scale}.")
    
    out = keypoints.copy().astype(np.float32)
    out[..., 0] = (out[..., 0] - pad_x) / scale
    out[..., 1] = (out[..., 1] - pad_y) / scale
    return out
```

---

## 3. Data Flow & Component Interaction

```
Raw Frame (1920x1080)
        │
        ▼
letterbox_image(frame, (640,640)) ──► [scale=0.333, pad_y=140, pad_x=0]
        │
        ▼
OnnxEngine.infer(tensor) ──► raw_output (1, 56, 8400)
        │
        ▼
parse_detections:
  ├── Bbox unletterbox: (lx1, ly1) -> (x1, y1), (lx2, ly2) -> (x2, y2)
  └── Keypoint unletterbox: kps_orig = unletterbox_keypoints(kps_canvas, scale, pad_x, pad_y)
        │
        ▼
extract_ground_anchor(kps_orig, bbox=(x1,y1,x2,y2))
  ├── Ankle Midpoint: (kps[15] + kps[16]) / 2 (already in 1920x1080 space)
  └── Single Ankle / Bbox Bottom fallback (already in 1920x1080 space)
        │
        ▼
Visualizer.render:
  ├── Perspective: Draw skeleton lines & joint dots using kps_orig directly on 1920x1080 canvas
  └── BEV: Project anchor (u, v) -> HomographyManager.project_to_ground -> (Xw, Yw) in meters
```

---

## 4. Ground Plane Calibration for Mendeley Industrial

In `configs/datasets/mendeley_industrial.yaml`, the 4 reference points on the industrial workshop floor are calibrated:
- Point 1 (Bottom-Left): `[250.0, 1020.0]` $\to [0.0, 0.0]\text{ m}$
- Point 2 (Bottom-Right): `[1680.0, 1020.0]` $\to [10.0, 0.0]\text{ m}$
- Point 3 (Top-Right): `[1400.0, 480.0]` $\to [10.0, 15.0]\text{ m}$
- Point 4 (Top-Left): `[520.0, 480.0]` $\to [0.0, 15.0]\text{ m}$
- Danger Zone $P_{\text{danger}}$: $[2.5, 3.0] \times [7.5, 10.0]\text{ m}$ (encompassing machinery footprint)
