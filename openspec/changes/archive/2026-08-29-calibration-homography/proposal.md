# Proposal: Planar Homography Projection & Calibration Management

## Intent
Eliminate perspective distortion by establishing a planar homography calibration pipeline that maps 2D ankle keypoints $(u, v)$ from image space to metric ground-plane coordinates $(X_w, Y_w)$ in meters ($Z_w = 0$), enabling precise spatial safety zone evaluation.

## Scope

### In Scope
- YAML configuration schema (`configs/default_config.yaml`) for 4+ coplanar calibration point pairs (pixel and metric), camera resolution, and reprojection tolerances.
- `HomographyManager` core class (`src/core/homography.py`):
  - Direct Linear Transform (DLT) $3 \times 3$ homography matrix $H$ via `cv2.findHomography`.
  - Bidirectional projection: forward `project_point(u, v) -> (X_w, Y_w)` and inverse `project_to_image(X_w, Y_w) -> (u, v)`.
  - Batch projection for multi-keypoint arrays.
  - Reprojection error computation ($\text{RMSE} \le 0.05\text{ m}$).
  - Degeneracy detection for collinear or insufficient (<4) calibration points.
- Comprehensive unit test suite (`tests/test_homography.py`) covering DLT computation, round-trip fidelity, synthetic transformations, and error handling.

### Out of Scope
- Temporal Kalman filter tracking and trajectory smoothing.
- Spatial FSM zone intrusion, hysteresis, and dwell tracking.
- RTSP video ingestion and real-time visualization overlays.

## Capabilities

### New Capabilities
- `calibration-config`: Declarative YAML specification for camera resolution, coplanar calibration correspondences, and reprojection bounds.
- `homography-projection`: Planar homography estimation, bidirectional metric coordinate transformation, and reprojection error validation.

### Modified Capabilities
- None (initial foundation for Roadmap Steps 1 & 2).

## Approach
1. **Calibration Schema**: Define structured YAML containing image pixel coordinates $[(u_i, v_i)]$ and corresponding real-world ground-plane metric coordinates $[(X_i, Y_i)]$.
2. **Homography Estimation**: Compute $H$ using OpenCV DLT. Enforce input validation (non-collinearity check via triangle area / rank check) and calculate reprojection RMSE against ground truth points.
3. **Metric Transformation**: Apply normalized homogeneous coordinates for single-point and vectorized batch projections between pixel space and world coordinates.

## Affected Areas
| File | Change Type | Purpose |
| :--- | :--- | :--- |
| `configs/default_config.yaml` | New | Calibration correspondences, resolution, and validation tolerances |
| `src/core/homography.py` | New | `HomographyManager` implementation for DLT, forward/inverse projection, and validation |
| `tests/test_homography.py` | New | Unit tests for calibration accuracy, roundtrip consistency, and edge cases |

## Risks & Mitigation
- **Collinear / Degenerate Point Selection**: Singular or ill-conditioned matrix $H$.
  *Mitigation*: Validate geometric degeneracy before solving; raise explicit `ValueError` if points are collinear or $<4$.
- **High Reprojection Error**: Lens distortion or inaccurate physical markings degrade accuracy.
  *Mitigation*: Compute RMSE during initialization; raise warning or error if $\text{RMSE} > 0.05\text{ m}$.

## Rollback Plan
Remove `configs/default_config.yaml`, `src/core/homography.py`, and `tests/test_homography.py`. No legacy modules or database schemas are modified.

## Dependencies
- `opencv-python>=4.8.0`
- `numpy>=1.24.0`
- `pyyaml>=6.0`
- `pytest>=7.0.0`

## Success Criteria
- [ ] `HomographyManager` parses YAML config and computes valid $3 \times 3$ homography matrix $H$.
- [ ] Bidirectional projection roundtrip error $(u, v) \leftrightarrow (X_w, Y_w) < 1\text{e-3}$ m/px.
- [ ] Reprojection error on standard calibration targets achieves $\text{RMSE} \le 0.05\text{ m}$.
- [ ] Degenerate/collinear calibration point inputs raise explicit descriptive exceptions.
- [ ] 100% test pass rate in `pytest tests/test_homography.py`.
