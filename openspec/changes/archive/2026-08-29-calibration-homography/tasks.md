# Tasks: Planar Homography Projection & Calibration Management

## Review Workload Forecast
Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: Medium

## Suggested Work Units
- **Unit 1: Calibration Configuration**
  - Files: `configs/default_config.yaml`, `src/core/homography.py`, `tests/test_homography.py`
  - Focused test command: `pytest tests/test_homography.py -k "config"`
  - Runtime harness: Python 3.10+ / PyYAML & NumPy
  - Rollback boundary: Delete `configs/default_config.yaml`, revert `CalibrationConfig` in `src/core/homography.py` and config tests
- **Unit 2: Homography Manager & Projection Pipeline**
  - Files: `src/core/homography.py`, `tests/test_homography.py`
  - Focused test command: `pytest tests/test_homography.py`
  - Runtime harness: OpenCV (`cv2.findHomography`) & NumPy vectorization
  - Rollback boundary: Delete `src/core/homography.py`, `tests/test_homography.py`

## Implementation Tasks

### Phase 1: Calibration Configuration & Schema Validation (Unit 1)
- [x] 1.1 (RED) Write unit tests in `tests/test_homography.py` for configuration loading, missing file error (`FileNotFoundError`), missing keys, non-numeric values, and frame boundary validation.
- [x] 1.2 (GREEN) Create default configuration file `configs/default_config.yaml` defining camera parameters (1920x1080, 30 FPS), 4 coplanar correspondence pairs, and reprojection tolerance ($0.05\text{ m}$).
- [x] 1.3 (GREEN) Implement immutable `CalibrationConfig` dataclass and `from_yaml()` loader with schema and boundary validation in `src/core/homography.py`.
- [x] 1.4 (REFACTOR) Standardize error messaging, type annotations, and verify configuration test pass rate via `pytest tests/test_homography.py -k "config"`.

### Phase 2: Geometric Degeneracy & Homography Estimation (Unit 2)
- [x] 2.1 (RED) Write unit tests in `tests/test_homography.py` for point count requirements ($N \ge 4$), count matching ($N_{\text{image}} = N_{\text{world}}$), collinearity rejection via triangle area, duplicate coordinates, and synthetic DLT transforms (identity, translation, scale, perspective trapezoid).
- [x] 2.2 (GREEN) Implement `HomographyManager.validate_points()` for cardinality, duplicate detection, and collinearity triangle area checks in `src/core/homography.py`.
- [x] 2.3 (GREEN) Implement `HomographyManager.__init__()` and `compute_homography()` using `cv2.findHomography(..., method=0)`, precompute and cache $H$ and $H^{-1}$, and calculate reprojection RMSE ($\le 0.05\text{ m}$).
- [x] 2.4 (REFACTOR) Add condition number / determinant stability checks ($|\det(H)| > 10^{-10}$) and verify with `pytest tests/test_homography.py -k "homography or validation"`.

### Phase 3: Bidirectional & Vectorized Batch Projection (Unit 2)
- [x] 3.1 (RED) Write unit tests in `tests/test_homography.py` for forward `project_point`, inverse `project_to_image`, round-trip consistency ($< 1\text{e-3}$ error), horizon divisor rejection ($|W| < 10^{-7}$), and vectorized `project_batch` with shape $(N, 2)$ and empty $(0, 2)$.
- [x] 3.2 (GREEN) Implement single-point forward projection `project_point(u, v)` and inverse projection `project_to_image(X, Y)` with horizon threshold check in `src/core/homography.py`.
- [x] 3.3 (GREEN) Implement vectorized `project_batch(points, to_world=True)` in `src/core/homography.py` via homogeneous coordinate matrix multiplication.
- [x] 3.4 (REFACTOR) Optimize projection latency budget ($t_{\text{homo}} < 0.5\text{ ms}$) and harden against non-finite inputs.

### Phase 4: Integration & Quality Gate
- [x] 4.1 Run complete test suite with `pytest tests/test_homography.py` to confirm 100% pass rate.
- [x] 4.2 Verify round-trip accuracy ($< 1\text{e-3}$ m/px) and ISO 13855:2024 compliance threshold ($\text{RMSE} \le 0.05\text{ m}$).
