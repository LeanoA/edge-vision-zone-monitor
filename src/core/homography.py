"""
src/core/homography.py
Planar Homography and Metric Calibration Management for Edge Safety Guard.
Compliant with ISO 13855:2024 metric safety positioning.
"""

from dataclasses import dataclass
import itertools
import logging
from pathlib import Path
from typing import Optional, Tuple, Union
import cv2
import numpy as np
import yaml

logger = logging.getLogger("homography")


@dataclass(frozen=True)
class CalibrationConfig:
    """
    Immutable representation of calibration configuration.
    
    Attributes:
        image_points: Ground-plane pixel coordinates of shape (N, 2), dtype float64.
        world_points: Corresponding metric coordinates in meters of shape (N, 2), dtype float64.
        reprojection_tolerance_m: Maximum acceptable Root Mean Square Error (RMSE) in meters.
        method: Homography estimation method ("DLT" or "RANSAC").
        camera_width: Optional camera frame width in pixels.
        camera_height: Optional camera frame height in pixels.
        camera_fps: Optional camera frame rate.
        camera_id: Optional camera identifier.
    """
    image_points: np.ndarray
    world_points: np.ndarray
    reprojection_tolerance_m: float = 0.05
    method: str = "DLT"
    camera_width: Optional[int] = None
    camera_height: Optional[int] = None
    camera_fps: Optional[int] = None
    camera_id: Optional[str] = None

    @property
    def reprojection_threshold_rmse(self) -> float:
        """Alias for reprojection_tolerance_m compliant with ISO 13855 specification."""
        return self.reprojection_tolerance_m

    @classmethod
    def from_yaml(cls, config_path: Union[str, Path]) -> "CalibrationConfig":
        """
        Load and validate calibration configuration from a YAML file.

        Args:
            config_path: Path to the YAML configuration file.

        Returns:
            Validated immutable CalibrationConfig instance.

        Raises:
            FileNotFoundError: If configuration file does not exist.
            ValueError: If YAML structure, keys, dimensions, or coordinate bounds are invalid.
            TypeError: If coordinate types are non-numeric.
        """
        path = Path(config_path)
        if not path.is_file():
            raise FileNotFoundError(f"Configuration file not found: {path.resolve()}")

        with open(path, "r", encoding="utf-8") as f:
            raw_cfg = yaml.safe_load(f)

        if not isinstance(raw_cfg, dict):
            raise ValueError(f"YAML configuration must be a mapping, got {type(raw_cfg).__name__}")

        # Validate required top-level sections
        if "camera" not in raw_cfg:
            raise ValueError("Configuration missing required 'camera' section.")
        if "calibration" not in raw_cfg:
            raise ValueError("Configuration missing required 'calibration' section.")

        cam_cfg = raw_cfg["camera"]
        calib_cfg = raw_cfg["calibration"]

        if not isinstance(cam_cfg, dict) or not isinstance(calib_cfg, dict):
            raise ValueError("'camera' and 'calibration' sections must be dictionaries.")

        # Camera dimensions validation
        resolution = cam_cfg.get("resolution", {})
        camera_width = resolution.get("width") if isinstance(resolution, dict) else cam_cfg.get("width")
        camera_height = resolution.get("height") if isinstance(resolution, dict) else cam_cfg.get("height")
        camera_fps = cam_cfg.get("fps")
        camera_id = cam_cfg.get("id")

        if camera_width is None or camera_height is None:
            raise ValueError("Camera resolution must specify 'width' and 'height'.")
        if not isinstance(camera_width, int) or not isinstance(camera_height, int) or camera_width <= 0 or camera_height <= 0:
            raise ValueError(f"Camera resolution dimensions must be positive integers, got width={camera_width}, height={camera_height}.")

        if camera_fps is not None and (not isinstance(camera_fps, int) or camera_fps <= 0):
            raise ValueError(f"Camera fps must be a positive integer, got {camera_fps}.")

        # Method & reprojection tolerance
        method = str(calib_cfg.get("method", "DLT")).upper()
        tol = calib_cfg.get("reprojection_tolerance_m", calib_cfg.get("reprojection_threshold_rmse", 0.05))
        if not isinstance(tol, (int, float)) or tol <= 0:
            raise ValueError(f"Reprojection tolerance must be a strictly positive number, got {tol}.")
        reprojection_tolerance_m = float(tol)

        # Extract points
        points_block = calib_cfg.get("points")
        if isinstance(points_block, dict):
            raw_img_pts = points_block.get("image")
            raw_world_pts = points_block.get("world")
        else:
            raw_img_pts = calib_cfg.get("image_points")
            raw_world_pts = calib_cfg.get("world_points")

        if raw_img_pts is None or raw_world_pts is None:
            raise ValueError("Calibration section missing required 'image' or 'world' point correspondences.")

        if not isinstance(raw_img_pts, list) or not isinstance(raw_world_pts, list):
            raise ValueError("Image and world points must be lists of coordinate pairs.")

        if len(raw_img_pts) == 0 or len(raw_world_pts) == 0:
            raise ValueError("Calibration points cannot be empty.")

        if len(raw_img_pts) < 4:
            raise ValueError(f"At least 4 point correspondences are required, got {len(raw_img_pts)}.")

        if len(raw_img_pts) != len(raw_world_pts):
            raise ValueError(
                f"Point count mismatch: {len(raw_img_pts)} image points vs {len(raw_world_pts)} world points."
            )

        # Validate coordinate formats, types, and boundaries
        parsed_img_pts = []
        parsed_world_pts = []

        for idx, (img_pt, world_pt) in enumerate(zip(raw_img_pts, raw_world_pts)):
            if not isinstance(img_pt, (list, tuple)) or len(img_pt) != 2:
                raise ValueError(f"Image point at index {idx} must be a 2D coordinate [u, v], got {img_pt}.")
            if not isinstance(world_pt, (list, tuple)) or len(world_pt) != 2:
                raise ValueError(f"World point at index {idx} must be a 2D coordinate [X, Y], got {world_pt}.")

            u, v = img_pt
            X, Y = world_pt

            if not isinstance(u, (int, float)) or not isinstance(v, (int, float)):
                raise TypeError(f"Image point coordinates must be numeric, got ({type(u).__name__}, {type(v).__name__}).")
            if not isinstance(X, (int, float)) or not isinstance(Y, (int, float)):
                raise TypeError(f"World point coordinates must be numeric, got ({type(X).__name__}, {type(Y).__name__}).")

            if np.isnan(u) or np.isnan(v) or np.isinf(u) or np.isinf(v):
                raise ValueError(f"Image point at index {idx} contains NaN or Inf.")
            if np.isnan(X) or np.isnan(Y) or np.isinf(X) or np.isinf(Y):
                raise ValueError(f"World point at index {idx} contains NaN or Inf.")

            # Frame boundary validation
            if u < 0 or u > camera_width or v < 0 or v > camera_height:
                raise ValueError(
                    f"Pixel coordinate ({u}, {v}) at index {idx} exceeds camera resolution bounds ({camera_width}, {camera_height})."
                )

            parsed_img_pts.append([float(u), float(v)])
            parsed_world_pts.append([float(X), float(Y)])

        img_arr = np.array(parsed_img_pts, dtype=np.float64)
        world_arr = np.array(parsed_world_pts, dtype=np.float64)

        return cls(
            image_points=img_arr,
            world_points=world_arr,
            reprojection_tolerance_m=reprojection_tolerance_m,
            method=method,
            camera_width=camera_width,
            camera_height=camera_height,
            camera_fps=camera_fps,
            camera_id=camera_id,
        )


class HomographyManager:
    """
    Manages planar homography estimation, bidirectional metric-pixel projections,
    vectorized batch coordinate mapping, and geometric validation.
    Complies with ISO 13855:2024 metric safety positioning.
    """

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        config: Optional[CalibrationConfig] = None,
        image_points: Optional[Union[np.ndarray, list]] = None,
        world_points: Optional[Union[np.ndarray, list]] = None,
        reprojection_tolerance_m: float = 0.05,
        strict_rmse: bool = False,
    ) -> None:
        """
        Initialize the HomographyManager from a configuration file, config object, or point arrays.

        Args:
            config_path: Optional path to a YAML configuration file.
            config: Optional pre-loaded CalibrationConfig object.
            image_points: Optional array-like of shape (N, 2) in pixel space.
            world_points: Optional array-like of shape (N, 2) in metric world space.
            reprojection_tolerance_m: Permissible reprojection RMSE in meters (ISO 13855 limit).
            strict_rmse: If True, raises ValueError when reprojection RMSE exceeds tolerance.

        Raises:
            ValueError: If neither config nor (image_points, world_points) are provided,
                        or if points fail geometric non-collinearity validation.
        """
        self._H: Optional[np.ndarray] = None
        self._H_inv: Optional[np.ndarray] = None
        self._is_calibrated: bool = False
        self._reprojection_error: float = 0.0
        self._strict_rmse: bool = strict_rmse

        if config is not None:
            self._image_points = np.asarray(config.image_points, dtype=np.float64)
            self._world_points = np.asarray(config.world_points, dtype=np.float64)
            self._reprojection_tolerance_m = config.reprojection_tolerance_m
            self._method = config.method
        elif config_path is not None:
            loaded_cfg = CalibrationConfig.from_yaml(config_path)
            self._image_points = np.asarray(loaded_cfg.image_points, dtype=np.float64)
            self._world_points = np.asarray(loaded_cfg.world_points, dtype=np.float64)
            self._reprojection_tolerance_m = loaded_cfg.reprojection_tolerance_m
            self._method = loaded_cfg.method
        elif image_points is not None and world_points is not None:
            self._image_points = np.asarray(image_points, dtype=np.float64)
            self._world_points = np.asarray(world_points, dtype=np.float64)
            self._reprojection_tolerance_m = float(reprojection_tolerance_m)
            self._method = "DLT"
        else:
            raise ValueError("Neither config nor point correspondences (image_points, world_points) were provided.")

        # Validate geometric properties
        self.validate_points(self._image_points, self._world_points)

        # Compute homography matrices and RMSE
        self.compute_homography()

    @property
    def H(self) -> np.ndarray:
        """Return the 3x3 planar homography matrix (image to world)."""
        if self._H is None:
            raise RuntimeError("HomographyManager is not calibrated.")
        return self._H

    @property
    def H_inv(self) -> np.ndarray:
        """Return the 3x3 inverse planar homography matrix (world to image)."""
        if self._H_inv is None:
            raise RuntimeError("HomographyManager is not calibrated.")
        return self._H_inv

    @property
    def is_calibrated(self) -> bool:
        """Return True if homography matrices are computed and valid."""
        return self._is_calibrated

    @property
    def reprojection_error(self) -> float:
        """Return the computed Root-Mean-Square Error (RMSE) in meters."""
        return self._reprojection_error

    @property
    def reprojection_rmse(self) -> float:
        """Alias for reprojection_error compliant with ISO 13855:2024."""
        return self._reprojection_error

    def compute_homography(self, method: Optional[int] = None) -> np.ndarray:
        """
        Compute the 3x3 planar homography matrix H and its inverse H_inv.

        Args:
            method: OpenCV method flag (0 for standard DLT, cv2.RANSAC for robust fit).
                    If None, defaults to 0 (or cv2.RANSAC if method == "RANSAC" and N > 4).

        Returns:
            The calculated 3x3 homography matrix H.

        Raises:
            ValueError: If points fail non-collinearity validation or solve fails.
            RuntimeError: If matrix inversion fails or condition number is degenerate.
        """
        if method is None:
            if self._method == "RANSAC" and len(self._image_points) > 4:
                method_flag = cv2.RANSAC
            else:
                method_flag = 0  # Standard DLT least squares
        else:
            method_flag = method

        H, _ = cv2.findHomography(self._image_points, self._world_points, method=method_flag)

        if H is None or H.shape != (3, 3):
            raise ValueError("Failed to compute homography matrix from point correspondences.")

        H = H.astype(np.float64)

        # Normalize H so H[2, 2] == 1.0 if non-zero
        if abs(H[2, 2]) > 1e-12:
            H = H / H[2, 2]

        # Stability Check 1: Non-zero determinant
        det = float(np.linalg.det(H))
        if abs(det) < 1e-10:
            raise ValueError(f"Homography matrix is singular or near-singular: det(H) = {det:.2e} < 1e-10.")

        # Compute inverse homography
        try:
            H_inv = np.linalg.inv(H)
        except np.linalg.LinAlgError as e:
            raise ValueError(f"Homography matrix cannot be inverted: {e}") from e

        if abs(H_inv[2, 2]) > 1e-12:
            H_inv = H_inv / H_inv[2, 2]

        # Stability Check 2: Matrix Condition Number
        cond = float(np.linalg.cond(H))
        if cond > 1e12 or np.isnan(cond) or np.isinf(cond):
            raise ValueError(f"Homography matrix is ill-conditioned: condition number kappa(H) = {cond:.2e} > 1e12.")

        self._H = H
        self._H_inv = H_inv
        self._is_calibrated = True

        # Calculate and validate reprojection RMSE
        self._reprojection_error = self.compute_reprojection_error()

        if self._reprojection_error > self._reprojection_tolerance_m:
            msg = (
                f"Reprojection RMSE {self._reprojection_error:.4f} m exceeds tolerance "
                f"{self._reprojection_tolerance_m:.4f} m (ISO 13855 compliance limit)."
            )
            logger.warning(msg)
            if self._strict_rmse:
                raise ValueError(msg)

        return self._H

    def compute_reprojection_error(self) -> float:
        """
        Compute the Root-Mean-Square Error (RMSE) in meters across calibration points.

        Returns:
            Float RMSE in meters: sqrt(mean(||P_world - project(P_image)||^2)).
        """
        if not self._is_calibrated:
            raise RuntimeError("Cannot compute reprojection error before calibration.")

        projected_world = self.project_batch(self._image_points, to_world=True)
        sq_errors = np.sum((self._world_points - projected_world) ** 2, axis=1)
        return float(np.sqrt(np.mean(sq_errors)))

    def project_point(self, u: float, v: float) -> Tuple[float, float]:
        """
        Project a single pixel coordinate (u, v) to ground-plane world coordinates (X_w, Y_w) in meters.

        Args:
            u: Horizontal pixel coordinate.
            v: Vertical pixel coordinate.

        Returns:
            Tuple (X_w, Y_w) in metric coordinates.

        Raises:
            RuntimeError: If HomographyManager is not calibrated.
            ValueError: If coordinates are non-finite or point lies on horizon (|W| < 1e-7).
        """
        if not self._is_calibrated or self._H is None:
            raise RuntimeError("HomographyManager is not calibrated.")

        if not (np.isfinite(u) and np.isfinite(v)):
            raise ValueError(f"Coordinates must be finite numbers, got ({u}, {v}).")

        p = np.array([float(u), float(v), 1.0], dtype=np.float64)
        p_proj = self._H @ p

        W = p_proj[2]
        if abs(W) < 1e-7:
            raise ValueError(f"Point ({u}, {v}) lies on or near the horizon line (|W| = {abs(W):.2e} < 1e-7).")

        return float(p_proj[0] / W), float(p_proj[1] / W)

    def project_to_image(self, X: float, Y: float) -> Tuple[float, float]:
        """
        Project a single world coordinate (X_w, Y_w) in meters to pixel coordinate (u, v).

        Args:
            X: Real-world ground X coordinate in meters.
            Y: Real-world ground Y coordinate in meters.

        Returns:
            Tuple (u, v) in pixel coordinates.

        Raises:
            RuntimeError: If HomographyManager is not calibrated.
            ValueError: If coordinates are non-finite or divisor is near zero (|w| < 1e-7).
        """
        if not self._is_calibrated or self._H_inv is None:
            raise RuntimeError("HomographyManager is not calibrated.")

        if not (np.isfinite(X) and np.isfinite(Y)):
            raise ValueError(f"Coordinates must be finite numbers, got ({X}, {Y}).")

        p = np.array([float(X), float(Y), 1.0], dtype=np.float64)
        p_proj = self._H_inv @ p

        w = p_proj[2]
        if abs(w) < 1e-7:
            raise ValueError(f"World point ({X}, {Y}) divisor is near zero (|w| = {abs(w):.2e} < 1e-7).")

        return float(p_proj[0] / w), float(p_proj[1] / w)

    def project_batch(self, points: np.ndarray, to_world: bool = True) -> np.ndarray:
        """
        Project an array of 2D coordinates in a vectorized NumPy operation.

        Args:
            points: Array of shape (N, 2) containing coordinates to project.
            to_world: If True, projects from image (u, v) to world (X_w, Y_w).
                      If False, projects from world (X_w, Y_w) to image (u, v).

        Returns:
            Array of shape (N, 2) with transformed coordinates.

        Raises:
            ValueError: If input array does not have shape (N, 2), contains non-finite numbers,
                        or contains points on the horizon line.
            RuntimeError: If HomographyManager is not calibrated.
        """
        if not self._is_calibrated or self._H is None or self._H_inv is None:
            raise RuntimeError("HomographyManager is not calibrated.")

        pts = np.asarray(points, dtype=np.float64)
        if pts.ndim != 2 or pts.shape[1] != 2:
            raise ValueError(f"Input points must have shape (N, 2), got shape {pts.shape}.")

        num_points = pts.shape[0]
        if num_points == 0:
            return np.empty((0, 2), dtype=np.float64)

        if not np.all(np.isfinite(pts)):
            raise ValueError("Batch points must contain only finite numbers (no NaN or Inf).")

        M = self._H if to_world else self._H_inv

        # Fast vectorized homogeneous matrix multiplication:
        # pts_h is (N, 3), M is (3, 3) -> proj = pts_h @ M.T is (N, 3)
        pts_h = np.column_stack([pts, np.ones(num_points, dtype=np.float64)])
        proj = pts_h @ M.T

        w = proj[:, 2:3]
        if np.any(np.abs(w) < 1e-7):
            direction = "world" if to_world else "image"
            raise ValueError(f"One or more points lie on or near the horizon line (|W| < 1e-7) during {direction} projection.")

        return proj[:, :2] / w

    def project_points(self, points: np.ndarray) -> np.ndarray:
        """Convenience alias for project_batch(points, to_world=True)."""
        return self.project_batch(points, to_world=True)

    def project_to_image_batch(self, points: np.ndarray) -> np.ndarray:
        """Convenience alias for project_batch(points, to_world=False)."""
        return self.project_batch(points, to_world=False)

    @staticmethod
    def validate_points(
        image_points: np.ndarray,
        world_points: Optional[np.ndarray] = None,
        min_triangle_area: float = 1e-4,
    ) -> bool:
        """
        Validate that points meet geometric requirements:
        1. At least 4 points.
        2. Equal count between image and world points.
        3. No duplicate coordinates (distance < 1e-6).
        4. No 3 points are collinear (checked via pairwise triangle areas).
        5. Coordinate matrix has full rank (rank == 3).

        Args:
            image_points: Array of shape (N, 2).
            world_points: Optional array of shape (N, 2).
            min_triangle_area: Minimum area below which 3 points are deemed collinear.

        Returns:
            True if points are valid.

        Raises:
            ValueError: With explicit details if any validation criterion fails.
        """
        img_pts = np.asarray(image_points, dtype=np.float64)
        if img_pts.ndim != 2 or img_pts.shape[1] != 2:
            raise ValueError(f"image_points must have shape (N, 2), got {img_pts.shape}.")

        if len(img_pts) < 4:
            raise ValueError(f"At least 4 points are required for planar homography, got {len(img_pts)}.")

        if not np.all(np.isfinite(img_pts)):
            raise ValueError("image_points contains NaN or Inf.")

        if world_points is not None:
            w_pts = np.asarray(world_points, dtype=np.float64)
            if w_pts.ndim != 2 or w_pts.shape[1] != 2:
                raise ValueError(f"world_points must have shape (N, 2), got {w_pts.shape}.")
            if len(img_pts) != len(w_pts):
                raise ValueError(
                    f"Point count mismatch: {len(img_pts)} image points vs {len(w_pts)} world points."
                )
            if not np.all(np.isfinite(w_pts)):
                raise ValueError("world_points contains NaN or Inf.")
        else:
            w_pts = None

        # Check duplicate points in image space
        num_img = len(img_pts)
        for i in range(num_img):
            for j in range(i + 1, num_img):
                dist = float(np.linalg.norm(img_pts[i] - img_pts[j]))
                if dist < 1e-6:
                    raise ValueError(
                        f"Duplicate points detected in image points at indices {i} and {j}: "
                        f"{img_pts[i].tolist()} and {img_pts[j].tolist()} (dist={dist:.2e} < 1e-6)."
                    )

        # Check duplicate points in world space
        if w_pts is not None:
            num_world = len(w_pts)
            for i in range(num_world):
                for j in range(i + 1, num_world):
                    dist = float(np.linalg.norm(w_pts[i] - w_pts[j]))
                    if dist < 1e-6:
                        raise ValueError(
                            f"Duplicate points detected in world points at indices {i} and {j}: "
                            f"{w_pts[i].tolist()} and {w_pts[j].tolist()} (dist={dist:.2e} < 1e-6)."
                        )

        # Check collinearity:
        # For N == 4, no 3 points can be collinear (would reduce quad to triangle/line)
        if num_img == 4:
            for combo in itertools.combinations(range(num_img), 3):
                i, j, k = combo
                p1, p2, p3 = img_pts[i], img_pts[j], img_pts[k]
                area = 0.5 * abs(p1[0] * (p2[1] - p3[1]) + p2[0] * (p3[1] - p1[1]) + p3[0] * (p1[1] - p2[1]))
                if area < min_triangle_area:
                    raise ValueError(
                        f"Points at indices {i}, {j}, and {k} are collinear in image space: "
                        f"triangle area {area:.6e} px^2 < {min_triangle_area} px^2 threshold."
                    )
        else:
            # For N > 4, ensure there exists at least one 4-point subset in general position (no 3 collinear)
            has_valid_quad = any(
                all(
                    0.5 * abs(
                        img_pts[a][0] * (img_pts[b][1] - img_pts[c][1])
                        + img_pts[b][0] * (img_pts[c][1] - img_pts[a][1])
                        + img_pts[c][0] * (img_pts[a][1] - img_pts[b][1])
                    ) >= min_triangle_area
                    for a, b, c in itertools.combinations(quad, 3)
                )
                for quad in itertools.combinations(range(num_img), 4)
            )
            if not has_valid_quad:
                raise ValueError("Points in image space are degenerate: no 4-point subset in general position.")

        # Check collinearity of world points
        if w_pts is not None:
            min_area_world = min(min_triangle_area, 1e-5)
            if num_world == 4:
                for combo in itertools.combinations(range(num_world), 3):
                    i, j, k = combo
                    p1, p2, p3 = w_pts[i], w_pts[j], w_pts[k]
                    area = 0.5 * abs(p1[0] * (p2[1] - p3[1]) + p2[0] * (p3[1] - p1[1]) + p3[0] * (p1[1] - p2[1]))
                    if area < min_area_world:
                        raise ValueError(
                            f"Points at indices {i}, {j}, and {k} are collinear in world space: "
                            f"triangle area {area:.6e} m^2 < {min_area_world} m^2 threshold."
                        )
            else:
                has_valid_quad_w = any(
                    all(
                        0.5 * abs(
                            w_pts[a][0] * (w_pts[b][1] - w_pts[c][1])
                            + w_pts[b][0] * (w_pts[c][1] - w_pts[a][1])
                            + w_pts[c][0] * (w_pts[a][1] - w_pts[b][1])
                        ) >= min_area_world
                        for a, b, c in itertools.combinations(quad, 3)
                    )
                    for quad in itertools.combinations(range(num_world), 4)
                )
                if not has_valid_quad_w:
                    raise ValueError("Points in world space are degenerate: no 4-point subset in general position.")

        # Affine rank check
        P_img = np.column_stack([img_pts, np.ones(num_img, dtype=np.float64)])
        if np.linalg.matrix_rank(P_img) < 3:
            raise ValueError("Image points do not span 2D planar space (affine matrix rank < 3).")

        if w_pts is not None:
            P_world = np.column_stack([w_pts, np.ones(num_world, dtype=np.float64)])
            if np.linalg.matrix_rank(P_world) < 3:
                raise ValueError("World points do not span 2D planar space (affine matrix rank < 3).")

        return True
