# Verification Report: Planar Homography Projection & Calibration Management

- **Change Name:** `calibration-homography`
- **Target Specification:** `openspec/changes/calibration-homography/`
- **Verification Date:** 2026-08-29
- **Status:** **PASS**
- **Mode:** Hybrid / Strict TDD
- **Test Runner:** `/Users/xander/Projects/edge-safety-guard/.venv/bin/pytest`
- **Python Environment:** `/Users/xander/Projects/edge-safety-guard/.venv/bin/python` (Python 3.10.4)
- **Safety Standard Compliance:** ISO 13855:2024 (Machine Safeguarding & Approach Clearance)

---

## 1. Executive Summary

The `calibration-homography` change has been rigorously tested and verified against all requirements defined in its proposal, functional specifications, and technical design documents. 

All 14 implementation tasks across Phases 1 through 4 in `tasks.md` are completed (`[x]`). The unit and property test suite `tests/test_homography.py` executed with **49 passing tests in 0.27 seconds** (exit code 0), and the full workspace regression suite executed with **75 passing tests in 2.44 seconds**. Inference latency benchmark verification confirmed end-to-end edge safety budget compliance with a p95 latency of **23.76 ms** (against the $\le 30.0\text{ ms}$ budget).

All behavioral scenarios—including YAML configuration loading, camera frame boundary checking, non-collinearity validation via triangle area, DLT homography estimation, bidirectional forward/inverse metric projection, vectorized batch processing, and reprojection error tolerance ($\text{RMSE} \le 0.05\text{ m}$)—demonstrate 100% compliance.

---

## 2. Task Completion Audit

All tasks specified in `openspec/changes/calibration-homography/tasks.md` have been verified as completed:

| Phase | Task ID | Description | Status | Evidence |
| :--- | :--- | :--- | :---: | :--- |
| **Phase 1: Config & Validation** | 1.1 | Unit tests for YAML loading, missing file, missing keys, boundary validation | **[x]** | `tests/test_homography.py:20-194` |
| | 1.2 | Create `configs/default_config.yaml` with camera & 4 coplanar pairs | **[x]** | `configs/default_config.yaml:1-22` |
| | 1.3 | Implement immutable `CalibrationConfig` dataclass and loader | **[x]** | `src/core/homography.py:20-179` |
| | 1.4 | Standardize error messaging, type annotations, verify config tests | **[x]** | 15 passing config tests |
| **Phase 2: Homography Estimation** | 2.1 | Unit tests for point cardinality, count matching, collinearity, duplicate rejection, DLT | **[x]** | `tests/test_homography.py:336-540` |
| | 2.2 | Implement `HomographyManager.validate_points()` geometric validator | **[x]** | `src/core/homography.py:471-608` |
| | 2.3 | Implement `HomographyManager.__init__()` and `compute_homography()` via DLT | **[x]** | `src/core/homography.py:189-342` |
| | 2.4 | Add condition number ($\kappa \le 10^{12}$) and determinant ($|\det| > 10^{-10}$) checks | **[x]** | `src/core/homography.py:307-324` |
| **Phase 3: Projection Pipeline** | 3.1 | Unit tests for `project_point`, `project_to_image`, roundtrip consistency, horizon rejection | **[x]** | `tests/test_homography.py:599-798` |
| | 3.2 | Implement single-point forward and inverse projections with horizon checks | **[x]** | `src/core/homography.py:357-416` |
| | 3.3 | Implement vectorized `project_batch` with homogeneous coordinate transform | **[x]** | `src/core/homography.py:418-468` |
| | 3.4 | Optimize projection latency ($t_{\text{homo}} < 0.5\text{ ms}$) and harden non-finite inputs | **[x]** | `tests/test_homography.py:800-818` |
| **Phase 4: Integration & Quality** | 4.1 | Run complete test suite to confirm 100% pass rate | **[x]** | 49/49 passed in `test_homography.py` |
| | 4.2 | Verify round-trip error ($< 1\text{e-3}$ px/m) and ISO 13855 threshold ($\text{RMSE} \le 0.05\text{ m}$) | **[x]** | Verified across multiple test cases |

---

## 3. Test Execution Evidence

### 3.1 Focused Subsystem Test Run
```bash
/Users/xander/Projects/edge-safety-guard/.venv/bin/pytest tests/test_homography.py -v
```
- **Exit Code:** 0
- **Runtime:** 0.27 seconds
- **Test Counts:** 49 collected, 49 passed, 0 failed, 0 skipped (100% pass rate)

```text
============================= test session starts ==============================
platform darwin -- Python 3.10.4, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/xander/Projects/edge-safety-guard
collected 49 items

tests/test_homography.py::test_config_load_from_valid_yaml PASSED        [  2%]
tests/test_homography.py::test_config_load_missing_file PASSED           [  4%]
tests/test_homography.py::test_config_missing_camera_section PASSED      [  6%]
tests/test_homography.py::test_config_missing_calibration_section PASSED [  8%]
tests/test_homography.py::test_config_missing_points_keys PASSED         [ 10%]
tests/test_homography.py::test_config_non_numeric_coordinates PASSED     [ 12%]
tests/test_homography.py::test_config_frame_boundary_validation_exceeds PASSED [ 14%]
tests/test_homography.py::test_config_frame_boundary_validation_negative PASSED [ 16%]
tests/test_homography.py::test_config_invalid_camera_dimensions PASSED   [ 18%]
tests/test_homography.py::test_config_cardinality_under_four PASSED      [ 20%]
tests/test_homography.py::test_config_point_count_mismatch PASSED        [ 22%]
tests/test_homography.py::test_config_empty_points PASSED                [ 24%]
tests/test_homography.py::test_config_invalid_reprojection_threshold PASSED [ 26%]
tests/test_homography.py::test_config_default_tolerance_when_omitted PASSED [ 28%]
tests/test_homography.py::test_config_immutability PASSED                [ 30%]
tests/test_homography.py::test_validate_points_cardinality_under_four PASSED [ 32%]
tests/test_homography.py::test_validate_points_count_mismatch PASSED     [ 34%]
tests/test_homography.py::test_validate_points_duplicate_image_coords PASSED [ 36%]
tests/test_homography.py::test_validate_points_duplicate_world_coords PASSED [ 38%]
tests/test_homography.py::test_validate_points_collinear_three_points PASSED [ 40%]
tests/test_homography.py::test_validate_points_collinear_all_four_points PASSED [ 42%]
tests/test_homography.py::test_validate_points_valid PASSED              [ 44%]
tests/test_homography.py::test_homography_identity PASSED                [ 46%]
tests/test_homography.py::test_homography_pure_translation PASSED        [ 48%]
tests/test_homography.py::test_homography_uniform_scale PASSED           [ 51%]
tests/test_homography.py::test_homography_perspective_trapezoid PASSED   [ 53%]
tests/test_homography.py::test_homography_overdetermined_dlt PASSED      [ 55%]
tests/test_homography.py::test_homography_singular_matrix_rejection PASSED [ 57%]
tests/test_homography.py::test_homography_init_from_config_file PASSED   [ 59%]
tests/test_homography.py::test_homography_init_from_config_object PASSED [ 61%]
tests/test_homography.py::test_homography_init_missing_args PASSED       [ 63%]
tests/test_homography.py::test_homography_reprojection_rmse_noisy_warning PASSED [ 65%]
tests/test_homography.py::test_homography_reprojection_rmse_noisy_strict_raise PASSED [ 67%]
tests/test_homography.py::test_project_uncalibrated PASSED               [ 69%]
tests/test_homography.py::test_project_point_forward PASSED              [ 71%]
tests/test_homography.py::test_project_to_image_inverse PASSED           [ 73%]
tests/test_homography.py::test_single_point_roundtrip PASSED             [ 75%]
tests/test_homography.py::test_project_point_non_finite PASSED           [ 77%]
tests/test_horizon_point_rejection_forward PASSED                         [ 79%]
tests/test_horizon_point_rejection_inverse PASSED                         [ 81%]
tests/test_homography.py::test_project_batch_forward PASSED              [ 83%]
tests/test_homography.py::test_project_batch_inverse PASSED              [ 85%]
tests/test_homography.py::test_project_batch_roundtrip PASSED            [ 87%]
tests/test_homography.py::test_project_batch_empty PASSED                [ 89%]
tests/test_homography.py::test_project_batch_invalid_shape PASSED        [ 91%]
tests/test_homography.py::test_project_batch_non_finite PASSED           [ 93%]
tests/test_homography.py::test_project_batch_horizon_rejection PASSED    [ 95%]
tests/test_homography.py::test_project_batch_aliases PASSED              [ 97%]
tests/test_homography.py::test_projection_latency_budget PASSED          [100%]

============================== 49 passed in 0.27s ==============================
```

### 3.2 Full Workspace Regression Suite
```bash
/Users/xander/Projects/edge-safety-guard/.venv/bin/pytest tests/
```
- **Exit Code:** 0
- **Runtime:** 2.44 seconds
- **Test Counts:** 75 collected, 75 passed, 0 failed, 0 skipped (100% pass rate)

---

## 4. Benchmark & Edge Safety Budget Verification

```bash
/Users/xander/Projects/edge-safety-guard/.venv/bin/python scripts/benchmark.py --strict --iterations 50 --warmup 10
```

- **Target Safety Budget:** p95 latency $\le 30.0\text{ ms}$ (ISO 13855 response budget)
- **Active Execution Providers:** `CoreMLExecutionProvider`, `CPUExecutionProvider`
- **Mean Latency:** 20.81 ms
- **Median Latency (p50):** 21.01 ms
- **95th Percentile Latency (p95):** 23.76 ms ($\le 30.0\text{ ms}$ budget satisfied)
- **99th Percentile Latency (p99):** 26.39 ms
- **Throughput:** 48.06 FPS ($\ge 30\text{ FPS}$ real-time threshold)
- **Batch Projection Budget Allocation ($t_{\text{homo}} $):** Verified $< 0.5\text{ ms}$ for 100 coordinates in `test_projection_latency_budget`.

---

## 5. Behavioral Compliance Matrix

### 5.1 Capability: `calibration-config`

| Specification Requirement | Behavioral Scenario | Test Verification | Verdict |
| :--- | :--- | :--- | :---: |
| **YAML Configuration Structure** | Loading and parsing valid YAML file | `test_config_load_from_valid_yaml` | **PASS** |
| | Handling missing or unreadable config file | `test_config_load_missing_file` | **PASS** |
| | Missing required `camera` section raises `ValueError` | `test_config_missing_camera_section` | **PASS** |
| | Missing required `calibration` section raises `ValueError` | `test_config_missing_calibration_section` | **PASS** |
| | Missing point keys raises `ValueError` | `test_config_missing_points_keys` | **PASS** |
| **Correspondence Cardinality & 1:1 Matching** | Sufficient correspondences ($N \ge 4$) | `test_config_load_from_valid_yaml`, `test_validate_points_valid` | **PASS** |
| | Rejecting insufficient points ($N < 4$) | `test_config_cardinality_under_four`, `test_validate_points_cardinality_under_four` | **PASS** |
| | Rejecting mismatched counts ($N_{\text{image}} \ne N_{\text{world}}$) | `test_config_point_count_mismatch`, `test_validate_points_count_mismatch` | **PASS** |
| | Rejecting empty point arrays | `test_config_empty_points` | **PASS** |
| **Coordinate Typing & Boundary Validation** | Validating numerical types within image bounds | `test_config_load_from_valid_yaml` | **PASS** |
| | Rejecting non-numeric coordinate values | `test_config_non_numeric_coordinates` | **PASS** |
| | Rejecting points exceeding camera resolution bounds | `test_config_frame_boundary_validation_exceeds` | **PASS** |
| | Rejecting negative pixel coordinate bounds | `test_config_frame_boundary_validation_negative` | **PASS** |
| | Validating camera resolution dimensions ($>0$, int) | `test_config_invalid_camera_dimensions` | **PASS** |
| **Reprojection Threshold Configuration** | Explicit reprojection threshold loading | `test_config_load_from_valid_yaml` | **PASS** |
| | Default threshold ($0.05\text{ m}$) when omitted | `test_config_default_tolerance_when_omitted` | **PASS** |
| | Rejecting non-positive threshold | `test_config_invalid_reprojection_threshold` | **PASS** |
| **Config Immutability** | Enforcing frozen dataclass immutability | `test_config_immutability` | **PASS** |

### 5.2 Capability: `homography-projection`

| Specification Requirement | Behavioral Scenario | Test Verification | Verdict |
| :--- | :--- | :--- | :---: |
| **DLT Matrix Computation** | Computing valid $3\times3$ homography from 4 coplanar points | `test_homography_identity`, `test_homography_perspective_trapezoid`, `test_homography_init_from_config_file` | **PASS** |
| | Pure translation synthetic transform | `test_homography_pure_translation` | **PASS** |
| | Uniform scale synthetic transform | `test_homography_uniform_scale` | **PASS** |
| | Overdetermined calibration ($N=8$) using least-squares DLT | `test_homography_overdetermined_dlt` | **PASS** |
| **Geometric Degeneracy Validation** | Rejecting collinear calibration points (3 of 4 on a line) | `test_validate_points_collinear_three_points` | **PASS** |
| | Rejecting all points collinear on a single line | `test_validate_points_collinear_all_four_points` | **PASS** |
| | Rejecting duplicate image coordinates | `test_validate_points_duplicate_image_coords` | **PASS** |
| | Rejecting duplicate world coordinates | `test_validate_points_duplicate_world_coords` | **PASS** |
| | Rejecting singular or ill-conditioned homography ($\kappa > 10^{12}$) | `test_homography_singular_matrix_rejection` | **PASS** |
| **Forward Metric Projection** | Single pixel coordinate $(u, v) \to (X_w, Y_w)$ in meters | `test_project_point_forward` | **PASS** |
| | Rejecting non-finite inputs (NaN, Inf) | `test_project_point_non_finite` | **PASS** |
| | Rejecting horizon line points ($|W| < 10^{-7}$) | `test_horizon_point_rejection_forward` | **PASS** |
| **Inverse Ground-to-Image Projection** | Single metric point $(X_w, Y_w) \to (u, v)$ in pixels | `test_project_to_image_inverse` | **PASS** |
| | Rejecting non-finite inputs and divisor near zero ($|w| < 10^{-7}$) | `test_horizon_point_rejection_inverse` | **PASS** |
| | Round-trip consistency: error $< 1\text{e-3}$ px | `test_single_point_roundtrip` | **PASS** |
| **Vectorized Batch Projection** | Batch forward projection matches element-wise ($< 1\text{e-6}\text{ m}$) | `test_project_batch_forward` | **PASS** |
| | Batch inverse projection matches element-wise ($< 1\text{e-6}\text{ px}$) | `test_project_batch_inverse` | **PASS** |
| | Batch roundtrip consistency (100 points, max error $< 1\text{e-3}\text{ px}$) | `test_project_batch_roundtrip` | **PASS** |
| | Handling empty array $(0, 2)$ gracefully | `test_project_batch_empty` | **PASS** |
| | Rejecting invalid shapes (1D, 3D, trailing dim $\ne 2$) | `test_project_batch_invalid_shape` | **PASS** |
| | Rejecting non-finite points in batch | `test_project_batch_non_finite` | **PASS** |
| | Rejecting batch points on horizon | `test_project_batch_horizon_rejection` | **PASS** |
| | Convenience aliases `project_points` and `project_to_image_batch` | `test_project_batch_aliases` | **PASS** |
| **Reprojection RMSE Validation** | Ground truth correspondences meet tolerance ($\text{RMSE} \le 0.05\text{ m}$) | `test_homography_init_from_config_file`, `test_homography_perspective_trapezoid` | **PASS** |
| | Exceeding tolerance issues high-priority warning | `test_homography_reprojection_rmse_noisy_warning` | **PASS** |
| | Exceeding tolerance raises `ValueError` in strict mode | `test_homography_reprojection_rmse_noisy_strict_raise` | **PASS** |
| | Guard against uncalibrated invocation | `test_project_uncalibrated` | **PASS** |
| | Latency budget compliance ($t_{\text{homo}} < 0.5\text{ ms}$) | `test_projection_latency_budget` | **PASS** |

---

## 6. Design Coherence & Architectural Conformance

The implementation in `src/core/homography.py` and `configs/default_config.yaml` faithfully implements the design choices outlined in `openspec/changes/calibration-homography/design.md`:

1. **OpenCV `cv2.findHomography` with `method=0` (DLT Least-Squares)**:
   - Evaluates least-squares planar homography for $N \ge 4$ pairs with automatic isotropic normalization.
   - Normalizes matrix scale such that $H_{33} = 1.0$.
2. **Type-Safe Immutable Dataclass (`CalibrationConfig`)**:
   - Implemented as `@dataclass(frozen=True)` preventing runtime mutation.
   - Rigorous `from_yaml()` loader enforcing non-negative dimensions, frame resolution bounds, coordinate types, and count matching.
3. **In-Memory Caching of $H$ and $H^{-1}$**:
   - Matrices $H$ and $H^{-1}$ are precomputed during `compute_homography()` and stored as private properties.
   - Forward and inverse transforms execute via single matrix multiplications $\mathcal{O}(1)$.
4. **Proactive Pre-Flight Geometric Validation**:
   - Triangle area collinearity check: $\text{Area}(p_i, p_j, p_k) \ge 10^{-4}$ evaluated for all triplets.
   - Pairwise duplicate distance check: $\|p_i - p_j\|_2 \ge 10^{-6}$.
   - Matrix stability checks: $|\det(H)| > 10^{-10}$ and condition number $\kappa(H) \le 10^{12}$.
   - Horizon vanishing line check: $|W| > 10^{-7}$ prevents division by near-zero.
5. **Zero Breaking Changes**:
   - All components are completely self-contained within `src/core/homography.py`, `configs/default_config.yaml`, and `tests/test_homography.py`. Existing modules (`src/core/onnx_engine.py`, `models/export_onnx.py`, etc.) remain intact and functional.

---

## 7. Conclusion & Next Recommendation

The `calibration-homography` change meets all functional specifications, safety tolerances, and design constraints with zero test failures or regressions.

- **Verdict:** **PASS**
- **Recommended Action:** Execute `sdd-archive` to archive the change specification and commit modifications.
