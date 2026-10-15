# Specification: Planar Homography Projection (`homography-projection`)

## Overview
The `homography-projection` capability provides planar homography calibration and bidirectional coordinate transformation between 2D image pixel space $(u, v)$ and the 2D metric ground plane $(X_w, Y_w)$ in meters ($Z_w = 0$). Implemented in `HomographyManager` (`src/core/homography.py`), it computes the $3 \times 3$ Direct Linear Transform (DLT) homography matrix $H$, verifies geometric non-degeneracy, executes single-point and vectorized batch projections, and validates calibration accuracy using reprojection Root Mean Square Error (RMSE).

## ADDED Requirements

### Requirement: Direct Linear Transform (DLT) Matrix Computation
The `HomographyManager` MUST compute a $3 \times 3$ homography matrix $H$ using the Direct Linear Transform (DLT) algorithm (`cv2.findHomography`) from at least 4 coplanar point correspondences, such that for any correspondence pair $(u_i, v_i) \leftrightarrow (X_i, Y_i)$:
$$s \begin{bmatrix} X_w \\ Y_w \\ 1 \end{bmatrix} = H \begin{bmatrix} u \\ v \\ 1 \end{bmatrix}$$
The manager MUST also compute and cache the inverse transformation matrix $H^{-1}$.

#### Scenario: Computing valid 3x3 homography matrix from 4 coplanar points
- **GIVEN** 4 non-collinear image points and 4 corresponding metric world ground-plane points
- **WHEN** `HomographyManager` is instantiated with these correspondences
- **THEN** a $3 \times 3$ homography matrix $H$ of dtype `float64` SHALL be calculated
- **AND** the determinant $\det(H)$ SHALL be non-zero
- **AND** the inverse matrix $H^{-1}$ SHALL be computed and stored.

#### Scenario: Overdetermined calibration using least-squares DLT
- **GIVEN** $N > 4$ (e.g., 6 or 8) coplanar calibration correspondences
- **WHEN** `HomographyManager` computes the homography matrix
- **THEN** the solver SHALL compute the optimal least-squares homography matrix minimizing total algebraic or reprojection error across all $N$ pairs.

---

### Requirement: Geometric Degeneracy and Non-Collinearity Validation
The `HomographyManager` MUST validate calibration point geometry prior to homography computation and MUST reject degenerate point configurations (such as collinear or coincident points) with descriptive exceptions.

#### Scenario: Rejecting collinear calibration points
- **GIVEN** 4 calibration points where 3 or more points lie on the same straight line in image or world space
- **WHEN** `HomographyManager` performs degeneracy validation during initialization
- **THEN** the manager SHALL raise a `ValueError` indicating that points are collinear and cannot span a 2D planar projection.

#### Scenario: Rejecting duplicate or coincident calibration points
- **GIVEN** a calibration set containing identical or near-identical coordinates (distance $< 1\text{e-6}$)
- **WHEN** `HomographyManager` validates the point set
- **THEN** the manager SHALL raise a `ValueError` indicating duplicate calibration points are present.

#### Scenario: Rejecting singular or ill-conditioned homography matrix
- **GIVEN** an ill-conditioned set of correspondences resulting in a near-zero matrix determinant or extreme condition number ($\kappa(H) > 1\text{e12}$)
- **WHEN** homography estimation executes
- **THEN** the manager SHALL raise a `ValueError` stating the transformation matrix is singular or numerically unstable.

---

### Requirement: Forward Metric Ground-Plane Projection
The `HomographyManager` MUST provide forward projection mapping 2D image coordinates $(u, v)$ to real-world ground-plane metric coordinates $(X_w, Y_w)$ in meters, assuming $Z_w = 0$.

#### Scenario: Forward projecting a single pixel coordinate to ground plane
- **GIVEN** an initialized `HomographyManager` with a calibrated ground-plane homography $H$
- **WHEN** `manager.project_point(u, v)` is invoked with pixel coordinates within frame bounds
- **THEN** the method SHALL return a tuple or array $(X_w, Y_w)$ in meters
- **AND** the projected point SHALL satisfy the homogeneous mapping $[X_w, Y_w, 1]^T \propto H [u, v, 1]^T$.

#### Scenario: Rejecting non-numeric coordinate inputs in forward projection
- **GIVEN** an initialized `HomographyManager`
- **WHEN** `manager.project_point(u, v)` is called with NaN or infinite values
- **THEN** the method SHALL raise a `ValueError`.

---

### Requirement: Inverse Ground-to-Image Projection
The `HomographyManager` MUST provide inverse projection mapping real-world metric coordinates $(X_w, Y_w)$ on the ground plane back to 2D image pixel coordinates $(u, v)$.

#### Scenario: Inverse projecting a single metric coordinate to pixel space
- **GIVEN** an initialized `HomographyManager`
- **WHEN** `manager.project_to_image(X_w, Y_w)` is invoked with metric ground-plane coordinates
- **THEN** the method SHALL return pixel coordinates $(u, v)$
- **AND** the projected point SHALL satisfy $[u, v, 1]^T \propto H^{-1} [X_w, Y_w, 1]^T$.

#### Scenario: Round-trip projection consistency
- **GIVEN** an arbitrary valid pixel coordinate $(u, v)$ within the calibrated camera field of view
- **WHEN** $(X_w, Y_w) = \text{project-point}(u, v)$ is computed
- **AND** $(u', v') = \text{project-to-image}(X_w, Y_w)$ is computed
- **THEN** the round-trip Euclidean error $\sqrt{(u - u')^2 + (v - v')^2}$ SHALL be less than $1\text{e-3}$ pixels.

---

### Requirement: Vectorized Batch Coordinate Projection
The `HomographyManager` MUST provide vectorized batch projection for multi-keypoint coordinate arrays (e.g. ankle keypoints from multiple detected persons) with shape $(N, 2)$ without iterative Python loops.

#### Scenario: Batch forward projection of multiple keypoints
- **GIVEN** an array of $N$ image keypoints with shape $(N, 2)$ and dtype `float32` or `float64`
- **WHEN** `world_pts = manager.project_points(image_pts)` is called
- **THEN** `world_pts` SHALL be a NumPy array of shape $(N, 2)$ containing metric coordinates in meters
- **AND** each row $i$ in `world_pts` SHALL match `manager.project_point(image_pts[i, 0], image_pts[i, 1])` within numerical precision ($< 1\text{e-6}\text{ m}$).

#### Scenario: Batch inverse projection of multiple world coordinates
- **GIVEN** an array of $N$ world ground-plane coordinates with shape $(N, 2)$
- **WHEN** `image_pts = manager.project_to_image_batch(world_pts)` is called
- **THEN** `image_pts` SHALL be a NumPy array of shape $(N, 2)$ containing pixel coordinates $(u, v)$.

#### Scenario: Handling empty keypoint array in batch projection
- **GIVEN** an empty keypoint array with shape $(0, 2)$
- **WHEN** `manager.project_points(empty_pts)` is called
- **THEN** the method SHALL return an empty NumPy array of shape $(0, 2)$ without raising an error.

#### Scenario: Rejecting invalid batch array dimensions
- **GIVEN** an input array with incompatible shape (e.g. shape $(N, 3)$ or $(N,)$)
- **WHEN** batch projection is invoked
- **THEN** the method SHALL raise a `ValueError` stating the expected trailing dimension must be 2.

---

### Requirement: Reprojection Root Mean Square Error (RMSE) Validation
The `HomographyManager` MUST compute the reprojection Root Mean Square Error (RMSE) against calibration ground truth correspondences upon initialization and MUST enforce that calibration achieves $\text{RMSE} \le 0.05\text{ m}$ (or configured threshold).

#### Scenario: Calibrated homography meeting reprojection RMSE tolerance
- **GIVEN** calibration point correspondences with accurate ground truth measurements
- **WHEN** `HomographyManager` initializes and computes reprojection RMSE:
$$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N \| \text{project-point}(u_i, v_i) - (X_i, Y_i) \|^2}$$
- **THEN** the computed RMSE SHALL be $\le 0.05\text{ m}$ (or the configured threshold)
- **AND** the RMSE value SHALL be accessible via `manager.reprojection_rmse`.

#### Scenario: Flagging or rejecting calibration exceeding RMSE tolerance
- **GIVEN** corrupted or imprecise calibration points resulting in $\text{RMSE} > 0.05\text{ m}$
- **WHEN** `HomographyManager` completes initialization with strict error enforcement
- **THEN** the manager SHALL raise a `ValueError` (or issue a designated high-priority warning if non-strict mode is requested) detailing the measured RMSE and the threshold violation.
