"""
tests/test_homography.py
Comprehensive test suite for Planar Homography Projection & Calibration Management.
Compliant with ISO 13855:2024 metric safety positioning.
"""

from pathlib import Path
import time
import numpy as np
import pytest
import yaml

from src.core.homography import CalibrationConfig, HomographyManager


# ============================================================================
# Phase 1: Calibration Configuration & Schema Validation Tests
# ============================================================================

def test_config_load_from_valid_yaml(tmp_path: Path):
    """Test loading and parsing a complete valid calibration YAML configuration."""
    yaml_content = """
camera:
  id: "industrial_cam_01"
  resolution:
    width: 1920
    height: 1080
  fps: 30

calibration:
  method: "DLT"
  reprojection_tolerance_m: 0.05
  points:
    image:
      - [480.0, 920.0]
      - [1440.0, 920.0]
      - [1200.0, 480.0]
      - [720.0, 480.0]
    world:
      - [0.0, 0.0]
      - [4.0, 0.0]
      - [4.0, 6.0]
      - [0.0, 6.0]
"""
    config_file = tmp_path / "valid_config.yaml"
    config_file.write_text(yaml_content)

    config = CalibrationConfig.from_yaml(config_file)
    assert isinstance(config, CalibrationConfig)
    assert config.image_points.shape == (4, 2)
    assert config.world_points.shape == (4, 2)
    assert config.image_points.dtype == np.float64
    assert config.world_points.dtype == np.float64
    assert config.reprojection_tolerance_m == 0.05
    assert config.reprojection_threshold_rmse == 0.05
    assert config.method == "DLT"
    assert config.camera_width == 1920
    assert config.camera_height == 1080
    assert config.camera_fps == 30
    assert config.camera_id == "industrial_cam_01"


def test_config_load_missing_file():
    """Test that loading from a nonexistent file path raises FileNotFoundError."""
    missing_path = Path("/nonexistent/path/calibration_config.yaml")
    with pytest.raises(FileNotFoundError, match="not found"):
        CalibrationConfig.from_yaml(missing_path)


def test_config_missing_camera_section(tmp_path: Path):
    """Test that missing required 'camera' section raises ValueError."""
    yaml_content = """
calibration:
  method: "DLT"
  reprojection_tolerance_m: 0.05
  points:
    image: [[100, 100], [200, 100], [200, 200], [100, 200]]
    world: [[0, 0], [1, 0], [1, 1], [0, 1]]
"""
    config_file = tmp_path / "missing_camera.yaml"
    config_file.write_text(yaml_content)
    with pytest.raises(ValueError, match="camera"):
        CalibrationConfig.from_yaml(config_file)


def test_config_missing_calibration_section(tmp_path: Path):
    """Test that missing required 'calibration' section raises ValueError."""
    yaml_content = """
camera:
  resolution:
    width: 1920
    height: 1080
"""
    config_file = tmp_path / "missing_calibration.yaml"
    config_file.write_text(yaml_content)
    with pytest.raises(ValueError, match="calibration"):
        CalibrationConfig.from_yaml(config_file)


def test_config_missing_points_keys(tmp_path: Path):
    """Test that missing 'image' or 'world' points raises ValueError."""
    yaml_content = """
camera:
  resolution:
    width: 1920
    height: 1080
calibration:
  points:
    image: [[100, 100], [200, 100], [200, 200], [100, 200]]
"""
    config_file = tmp_path / "missing_world_points.yaml"
    config_file.write_text(yaml_content)
    with pytest.raises(ValueError, match="world"):
        CalibrationConfig.from_yaml(config_file)


def test_config_non_numeric_coordinates(tmp_path: Path):
    """Test that non-numeric coordinate values raise TypeError or ValueError."""
    yaml_content = """
camera:
  resolution:
    width: 1920
    height: 1080
calibration:
  points:
    image:
      - ["x", 920.0]
      - [1440.0, 920.0]
      - [1200.0, 480.0]
      - [720.0, 480.0]
    world:
      - [0.0, 0.0]
      - [4.0, 0.0]
      - [4.0, 6.0]
      - [0.0, 6.0]
"""
    config_file = tmp_path / "non_numeric.yaml"
    config_file.write_text(yaml_content)
    with pytest.raises((TypeError, ValueError)):
        CalibrationConfig.from_yaml(config_file)


def test_config_frame_boundary_validation_exceeds(tmp_path: Path):
    """Test that image points exceeding camera resolution bounds raise ValueError."""
    yaml_content = """
camera:
  resolution:
    width: 1920
    height: 1080
calibration:
  points:
    image:
      - [2048.0, 500.0]
      - [1440.0, 920.0]
      - [1200.0, 480.0]
      - [720.0, 480.0]
    world:
      - [0.0, 0.0]
      - [4.0, 0.0]
      - [4.0, 6.0]
      - [0.0, 6.0]
"""
    config_file = tmp_path / "out_of_bounds.yaml"
    config_file.write_text(yaml_content)
    with pytest.raises(ValueError, match="resolution bounds|exceeds"):
        CalibrationConfig.from_yaml(config_file)


def test_config_frame_boundary_validation_negative(tmp_path: Path):
    """Test that negative image coordinates raise ValueError."""
    yaml_content = """
camera:
  resolution:
    width: 1920
    height: 1080
calibration:
  points:
    image:
      - [-10.0, 500.0]
      - [1440.0, 920.0]
      - [1200.0, 480.0]
      - [720.0, 480.0]
    world:
      - [0.0, 0.0]
      - [4.0, 0.0]
      - [4.0, 6.0]
      - [0.0, 6.0]
"""
    config_file = tmp_path / "negative_bounds.yaml"
    config_file.write_text(yaml_content)
    with pytest.raises(ValueError, match="bounds|negative"):
        CalibrationConfig.from_yaml(config_file)


def test_config_invalid_camera_dimensions(tmp_path: Path):
    """Test that non-positive camera dimensions raise ValueError."""
    yaml_content = """
camera:
  resolution:
    width: -1920
    height: 1080
calibration:
  points:
    image: [[100, 100], [200, 100], [200, 200], [100, 200]]
    world: [[0, 0], [1, 0], [1, 1], [0, 1]]
"""
    config_file = tmp_path / "invalid_cam_dim.yaml"
    config_file.write_text(yaml_content)
    with pytest.raises(ValueError, match="resolution|dimensions|positive"):
        CalibrationConfig.from_yaml(config_file)


def test_config_cardinality_under_four(tmp_path: Path):
    """Test that specifying fewer than 4 point correspondences raises ValueError."""
    yaml_content = """
camera:
  resolution:
    width: 1920
    height: 1080
calibration:
  points:
    image:
      - [480.0, 920.0]
      - [1440.0, 920.0]
      - [1200.0, 480.0]
    world:
      - [0.0, 0.0]
      - [4.0, 0.0]
      - [4.0, 6.0]
"""
    config_file = tmp_path / "under_four.yaml"
    config_file.write_text(yaml_content)
    with pytest.raises(ValueError, match="At least 4|insufficient"):
        CalibrationConfig.from_yaml(config_file)


def test_config_point_count_mismatch(tmp_path: Path):
    """Test that mismatched image and world point counts raise ValueError."""
    yaml_content = """
camera:
  resolution:
    width: 1920
    height: 1080
calibration:
  points:
    image:
      - [480.0, 920.0]
      - [1440.0, 920.0]
      - [1200.0, 480.0]
      - [720.0, 480.0]
    world:
      - [0.0, 0.0]
      - [4.0, 0.0]
      - [4.0, 6.0]
      - [0.0, 6.0]
      - [2.0, 3.0]
"""
    config_file = tmp_path / "count_mismatch.yaml"
    config_file.write_text(yaml_content)
    with pytest.raises(ValueError, match="mismatch"):
        CalibrationConfig.from_yaml(config_file)


def test_config_empty_points(tmp_path: Path):
    """Test that empty point arrays raise ValueError."""
    yaml_content = """
camera:
  resolution:
    width: 1920
    height: 1080
calibration:
  points:
    image: []
    world: []
"""
    config_file = tmp_path / "empty_points.yaml"
    config_file.write_text(yaml_content)
    with pytest.raises(ValueError, match="empty|At least 4"):
        CalibrationConfig.from_yaml(config_file)


def test_config_invalid_reprojection_threshold(tmp_path: Path):
    """Test that non-positive reprojection threshold raises ValueError."""
    yaml_content = """
camera:
  resolution:
    width: 1920
    height: 1080
calibration:
  reprojection_tolerance_m: -0.01
  points:
    image: [[100, 100], [200, 100], [200, 200], [100, 200]]
    world: [[0, 0], [1, 0], [1, 1], [0, 1]]
"""
    config_file = tmp_path / "negative_tol.yaml"
    config_file.write_text(yaml_content)
    with pytest.raises(ValueError, match="positive|tolerance|threshold"):
        CalibrationConfig.from_yaml(config_file)


def test_config_default_tolerance_when_omitted(tmp_path: Path):
    """Test that reprojection tolerance defaults to 0.05m when omitted."""
    yaml_content = """
camera:
  resolution:
    width: 1920
    height: 1080
calibration:
  points:
    image: [[100, 100], [200, 100], [200, 200], [100, 200]]
    world: [[0, 0], [1, 0], [1, 1], [0, 1]]
"""
    config_file = tmp_path / "omitted_tol.yaml"
    config_file.write_text(yaml_content)
    config = CalibrationConfig.from_yaml(config_file)
    assert config.reprojection_tolerance_m == 0.05


def test_config_immutability():
    """Test that CalibrationConfig is frozen and cannot be mutated."""
    img_pts = np.array([[100.0, 100.0], [200.0, 100.0], [200.0, 200.0], [100.0, 200.0]])
    world_pts = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    config = CalibrationConfig(
        image_points=img_pts,
        world_points=world_pts,
        reprojection_tolerance_m=0.05,
    )
    with pytest.raises((AttributeError, TypeError)):
        config.reprojection_tolerance_m = 0.1  # type: ignore


# ============================================================================
# Phase 2: Geometric Degeneracy & Homography Estimation Tests
# ============================================================================

def test_validate_points_cardinality_under_four():
    """validate_points must reject point sets with N < 4."""
    pts = np.array([[100.0, 100.0], [200.0, 100.0], [200.0, 200.0]])
    with pytest.raises(ValueError, match="At least 4 points"):
        HomographyManager.validate_points(pts)


def test_validate_points_count_mismatch():
    """validate_points must reject mismatched point counts."""
    img_pts = np.array([[100.0, 100.0], [200.0, 100.0], [200.0, 200.0], [100.0, 200.0]])
    world_pts = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]])
    with pytest.raises(ValueError, match="Point count mismatch"):
        HomographyManager.validate_points(img_pts, world_pts)


def test_validate_points_duplicate_image_coords():
    """validate_points must reject duplicate coordinates in image space."""
    img_pts = np.array([
        [100.0, 100.0],
        [100.0, 100.0],  # Duplicate
        [200.0, 200.0],
        [100.0, 200.0],
    ])
    with pytest.raises(ValueError, match="Duplicate points"):
        HomographyManager.validate_points(img_pts)


def test_validate_points_duplicate_world_coords():
    """validate_points must reject duplicate coordinates in world space."""
    img_pts = np.array([[100.0, 100.0], [200.0, 100.0], [200.0, 200.0], [100.0, 200.0]])
    world_pts = np.array([
        [0.0, 0.0],
        [1.0, 0.0],
        [1.0, 0.0],  # Duplicate
        [0.0, 1.0],
    ])
    with pytest.raises(ValueError, match="Duplicate points"):
        HomographyManager.validate_points(img_pts, world_pts)


def test_validate_points_collinear_three_points():
    """validate_points must reject collinear subset of 3 points."""
    # Points 0, 1, 2 are collinear on y=100
    img_pts = np.array([
        [100.0, 100.0],
        [200.0, 100.0],
        [300.0, 100.0],
        [100.0, 200.0],
    ])
    with pytest.raises(ValueError, match="collinear"):
        HomographyManager.validate_points(img_pts)


def test_validate_points_collinear_all_four_points():
    """validate_points must reject all points collinear along a single line."""
    img_pts = np.array([
        [100.0, 100.0],
        [200.0, 200.0],
        [300.0, 300.0],
        [400.0, 400.0],
    ])
    with pytest.raises(ValueError, match="collinear"):
        HomographyManager.validate_points(img_pts)


def test_validate_points_valid():
    """validate_points returns True for valid non-collinear correspondences."""
    img_pts = np.array([[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]])
    world_pts = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    assert HomographyManager.validate_points(img_pts, world_pts) is True


def test_homography_identity():
    """Exact identical correspondences produce normalized identity homography H = I_3."""
    pts = np.array([[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0]])
    manager = HomographyManager(image_points=pts, world_points=pts)
    assert manager.is_calibrated is True
    # Normalized so H[2, 2] == 1.0
    np.testing.assert_allclose(manager.H, np.eye(3), atol=1e-6)
    np.testing.assert_allclose(manager.H_inv, np.eye(3), atol=1e-6)
    assert manager.reprojection_error < 1e-6


def test_homography_pure_translation():
    """Translation by (tx, ty) yields analytical translation homography."""
    img_pts = np.array([[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0]])
    tx, ty = 5.0, 8.0
    world_pts = img_pts + np.array([tx, ty])

    manager = HomographyManager(image_points=img_pts, world_points=world_pts)
    expected_H = np.array([
        [1.0, 0.0, tx],
        [0.0, 1.0, ty],
        [0.0, 0.0, 1.0],
    ])
    np.testing.assert_allclose(manager.H, expected_H, atol=1e-6)
    res_x, res_y = manager.project_point(20.0, 30.0)
    assert pytest.approx(res_x, abs=1e-5) == 25.0
    assert pytest.approx(res_y, abs=1e-5) == 38.0


def test_homography_uniform_scale():
    """Uniform scale by s yields analytical scale homography."""
    img_pts = np.array([[10.0, 10.0], [100.0, 10.0], [100.0, 100.0], [10.0, 100.0]])
    scale = 0.25
    world_pts = img_pts * scale

    manager = HomographyManager(image_points=img_pts, world_points=world_pts)
    expected_H = np.array([
        [scale, 0.0, 0.0],
        [0.0, scale, 0.0],
        [0.0, 0.0, 1.0],
    ])
    np.testing.assert_allclose(manager.H, expected_H, atol=1e-6)
    res_x, res_y = manager.project_point(40.0, 80.0)
    assert pytest.approx(res_x, abs=1e-5) == 10.0
    assert pytest.approx(res_y, abs=1e-5) == 20.0


def test_homography_perspective_trapezoid():
    """Perspective trapezoid in image space correctly maps to ground plane metric rectangle."""
    img_pts = np.array([
        [480.0, 920.0],   # bottom-left
        [1440.0, 920.0],  # bottom-right
        [1200.0, 480.0],  # top-right
        [720.0, 480.0],   # top-left
    ])
    world_pts = np.array([
        [0.0, 0.0],
        [4.0, 0.0],
        [4.0, 6.0],
        [0.0, 6.0],
    ])
    manager = HomographyManager(image_points=img_pts, world_points=world_pts)
    assert manager.is_calibrated is True
    assert abs(np.linalg.det(manager.H)) > 1e-10
    assert np.linalg.cond(manager.H) < 1e10
    assert manager.reprojection_error < 1e-6

    # Test reprojecting corners
    for i in range(4):
        wx, wy = manager.project_point(img_pts[i, 0], img_pts[i, 1])
        assert pytest.approx(wx, abs=1e-4) == world_pts[i, 0]
        assert pytest.approx(wy, abs=1e-4) == world_pts[i, 1]


def test_homography_overdetermined_dlt():
    """Overdetermined system (N=8) solved via DLT least squares."""
    H_true = np.array([
        [1.2, 0.1, -50.0],
        [-0.05, 1.1, -30.0],
        [0.0002, -0.0001, 1.0],
    ])
    H_true_inv = np.linalg.inv(H_true)

    world_pts = np.array([
        [0.0, 0.0], [2.0, 0.0], [4.0, 0.0],
        [4.0, 3.0], [4.0, 6.0],
        [2.0, 6.0], [0.0, 6.0],
        [0.0, 3.0],
    ])
    w_h = np.column_stack([world_pts, np.ones(8)])
    img_h = (H_true_inv @ w_h.T).T
    img_pts = img_h[:, :2] / img_h[:, 2:3]

    manager = HomographyManager(image_points=img_pts, world_points=world_pts)
    assert manager.is_calibrated is True
    assert manager.reprojection_error < 1e-5


def test_homography_singular_matrix_rejection():
    """Singular or ill-conditioned homography correspondences raise ValueError."""
    img_pts = np.array([[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]])
    world_pts = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])
    with pytest.raises(ValueError, match="collinear|singular|ill-conditioned|rank"):
        HomographyManager(image_points=img_pts, world_points=world_pts)


def test_homography_init_from_config_file():
    """Test instantiating HomographyManager directly from configs/default_config.yaml."""
    cfg_path = Path("configs/default_config.yaml")
    assert cfg_path.is_file()

    manager = HomographyManager(config_path=cfg_path)
    assert manager.is_calibrated is True
    assert manager.reprojection_error <= 0.05
    assert manager.reprojection_rmse <= 0.05


def test_homography_init_from_config_object():
    """Test instantiating HomographyManager from a CalibrationConfig instance."""
    img_pts = np.array([[480.0, 920.0], [1440.0, 920.0], [1200.0, 480.0], [720.0, 480.0]])
    world_pts = np.array([[0.0, 0.0], [4.0, 0.0], [4.0, 6.0], [0.0, 6.0]])
    cfg = CalibrationConfig(image_points=img_pts, world_points=world_pts, reprojection_tolerance_m=0.05)

    manager = HomographyManager(config=cfg)
    assert manager.is_calibrated is True


def test_homography_init_missing_args():
    """Test instantiating HomographyManager without configuration raises ValueError."""
    with pytest.raises(ValueError, match="Neither config nor point correspondences"):
        HomographyManager()


def test_homography_reprojection_rmse_noisy_warning(caplog):
    """Test that noisy correspondences compute accurate RMSE and log warning when > tolerance."""
    img_pts = np.array([
        [480.0, 920.0],
        [1440.0, 920.0],
        [1200.0, 480.0],
        [720.0, 480.0],
        [960.0, 700.0],
    ])
    world_pts = np.array([
        [0.0, 0.0],
        [4.0, 0.0],
        [4.0, 6.0],
        [0.0, 6.0],
        [2.0, 3.4],  # Perturbed center point creating overdetermined fitting residual
    ])

    with caplog.at_level("WARNING"):
        manager = HomographyManager(
            image_points=img_pts,
            world_points=world_pts,
            reprojection_tolerance_m=0.05,
            strict_rmse=False,
        )
    assert manager.reprojection_error > 0.05
    assert any("exceeds tolerance" in record.message for record in caplog.records)


def test_homography_reprojection_rmse_noisy_strict_raise():
    """Test that noisy correspondences raise ValueError when strict_rmse=True."""
    img_pts = np.array([
        [480.0, 920.0],
        [1440.0, 920.0],
        [1200.0, 480.0],
        [720.0, 480.0],
        [960.0, 700.0],
    ])
    world_pts = np.array([
        [0.0, 0.0],
        [4.0, 0.0],
        [4.0, 6.0],
        [0.0, 6.0],
        [2.0, 3.4],  # Perturbed center point
    ])

    with pytest.raises(ValueError, match="exceeds tolerance"):
        HomographyManager(
            image_points=img_pts,
            world_points=world_pts,
            reprojection_tolerance_m=0.05,
            strict_rmse=True,
        )


# ============================================================================
# Phase 3: Bidirectional & Vectorized Batch Projection Tests
# ============================================================================

@pytest.fixture
def calibrated_manager() -> HomographyManager:
    """Fixture providing a standard calibrated HomographyManager."""
    img_pts = np.array([
        [480.0, 920.0],
        [1440.0, 920.0],
        [1200.0, 480.0],
        [720.0, 480.0],
    ])
    world_pts = np.array([
        [0.0, 0.0],
        [4.0, 0.0],
        [4.0, 6.0],
        [0.0, 6.0],
    ])
    return HomographyManager(image_points=img_pts, world_points=world_pts)


def test_project_uncalibrated():
    """Calling projection before calibration raises RuntimeError."""
    manager = HomographyManager.__new__(HomographyManager)
    manager._is_calibrated = False
    manager._H = None
    manager._H_inv = None
    with pytest.raises(RuntimeError, match="not calibrated"):
        manager.project_point(100.0, 100.0)
    with pytest.raises(RuntimeError, match="not calibrated"):
        manager.project_to_image(1.0, 1.0)
    with pytest.raises(RuntimeError, match="not calibrated"):
        manager.project_batch(np.array([[100.0, 100.0]]))


def test_project_point_forward(calibrated_manager: HomographyManager):
    """Test forward projection maps bottom-left image corner to (0.0, 0.0) m."""
    wx, wy = calibrated_manager.project_point(480.0, 920.0)
    assert pytest.approx(wx, abs=1e-4) == 0.0
    assert pytest.approx(wy, abs=1e-4) == 0.0


def test_project_to_image_inverse(calibrated_manager: HomographyManager):
    """Test inverse projection maps (4.0, 6.0) m back to (1200.0, 480.0) px."""
    u, v = calibrated_manager.project_to_image(4.0, 6.0)
    assert pytest.approx(u, abs=1e-3) == 1200.0
    assert pytest.approx(v, abs=1e-3) == 480.0


def test_single_point_roundtrip(calibrated_manager: HomographyManager):
    """Round-trip consistency check: image -> world -> image error < 1e-3 px."""
    test_points = [
        (600.0, 800.0),
        (1000.0, 700.0),
        (1300.0, 600.0),
        (800.0, 500.0),
        (960.0, 540.0),
    ]
    for u_orig, v_orig in test_points:
        X, Y = calibrated_manager.project_point(u_orig, v_orig)
        u_reproj, v_reproj = calibrated_manager.project_to_image(X, Y)
        err = np.hypot(u_orig - u_reproj, v_orig - v_reproj)
        assert err < 1e-3, f"Roundtrip error {err} exceeds 1e-3 px for ({u_orig}, {v_orig})"


def test_project_point_non_finite(calibrated_manager: HomographyManager):
    """Non-finite inputs (NaN, Inf) must raise ValueError."""
    with pytest.raises(ValueError, match="finite"):
        calibrated_manager.project_point(np.nan, 500.0)
    with pytest.raises(ValueError, match="finite"):
        calibrated_manager.project_point(500.0, float("inf"))
    with pytest.raises(ValueError, match="finite"):
        calibrated_manager.project_to_image(np.nan, 2.0)


def test_horizon_point_rejection_forward(calibrated_manager: HomographyManager):
    """Points near or on the horizon line (|W| < 1e-7) must raise ValueError."""
    h31, h32, h33 = calibrated_manager.H[2, :]
    if abs(h32) > 1e-8:
        v_horizon = -h33 / h32
        with pytest.raises(ValueError, match="horizon"):
            calibrated_manager.project_point(0.0, v_horizon)
    elif abs(h31) > 1e-8:
        u_horizon = -h33 / h31
        with pytest.raises(ValueError, match="horizon"):
            calibrated_manager.project_point(u_horizon, 0.0)


def test_horizon_point_rejection_inverse(calibrated_manager: HomographyManager):
    """World points near or on the divisor line (|w| < 1e-7) must raise ValueError."""
    h_inv_31, h_inv_32, h_inv_33 = calibrated_manager.H_inv[2, :]
    if abs(h_inv_32) > 1e-8:
        y_horizon = -h_inv_33 / h_inv_32
        with pytest.raises(ValueError, match="divisor|zero"):
            calibrated_manager.project_to_image(0.0, y_horizon)
    elif abs(h_inv_31) > 1e-8:
        x_horizon = -h_inv_33 / h_inv_31
        with pytest.raises(ValueError, match="divisor|zero"):
            calibrated_manager.project_to_image(x_horizon, 0.0)


def test_project_batch_forward(calibrated_manager: HomographyManager):
    """Vectorized batch projection matches element-wise project_point within 1e-6 m."""
    pts = np.array([
        [480.0, 920.0],
        [1440.0, 920.0],
        [1200.0, 480.0],
        [720.0, 480.0],
        [960.0, 700.0],
    ])
    world_batch = calibrated_manager.project_batch(pts, to_world=True)
    assert world_batch.shape == (5, 2)

    for i in range(len(pts)):
        wx_elem, wy_elem = calibrated_manager.project_point(pts[i, 0], pts[i, 1])
        assert pytest.approx(world_batch[i, 0], abs=1e-6) == wx_elem
        assert pytest.approx(world_batch[i, 1], abs=1e-6) == wy_elem


def test_project_batch_inverse(calibrated_manager: HomographyManager):
    """Vectorized batch inverse projection matches element-wise project_to_image within 1e-6 px."""
    world_pts = np.array([
        [0.0, 0.0],
        [4.0, 0.0],
        [4.0, 6.0],
        [0.0, 6.0],
        [2.0, 3.0],
    ])
    img_batch = calibrated_manager.project_batch(world_pts, to_world=False)
    assert img_batch.shape == (5, 2)

    for i in range(len(world_pts)):
        u_elem, v_elem = calibrated_manager.project_to_image(world_pts[i, 0], world_pts[i, 1])
        assert pytest.approx(img_batch[i, 0], abs=1e-6) == u_elem
        assert pytest.approx(img_batch[i, 1], abs=1e-6) == v_elem


def test_project_batch_roundtrip(calibrated_manager: HomographyManager):
    """Batch roundtrip for 100 points has max Euclidean error < 1e-3 pixels."""
    np.random.seed(42)
    # Generate 100 random points inside image polygon
    u = np.random.uniform(750.0, 1150.0, 100)
    v = np.random.uniform(500.0, 900.0, 100)
    img_pts = np.column_stack([u, v])

    world_pts = calibrated_manager.project_batch(img_pts, to_world=True)
    reproj_img_pts = calibrated_manager.project_batch(world_pts, to_world=False)

    errors = np.linalg.norm(img_pts - reproj_img_pts, axis=1)
    assert np.max(errors) < 1e-3, f"Max batch roundtrip error {np.max(errors)} >= 1e-3"


def test_project_batch_empty(calibrated_manager: HomographyManager):
    """Empty batch (shape 0, 2) returns empty array of shape (0, 2)."""
    empty = np.empty((0, 2), dtype=np.float64)
    res_world = calibrated_manager.project_batch(empty, to_world=True)
    assert res_world.shape == (0, 2)
    res_img = calibrated_manager.project_batch(empty, to_world=False)
    assert res_img.shape == (0, 2)


def test_project_batch_invalid_shape(calibrated_manager: HomographyManager):
    """Input with invalid shape (1D, 3D, or trailing dim != 2) raises ValueError."""
    with pytest.raises(ValueError, match="shape"):
        calibrated_manager.project_batch(np.array([100.0, 200.0]))
    with pytest.raises(ValueError, match="shape"):
        calibrated_manager.project_batch(np.ones((5, 3)))
    with pytest.raises(ValueError, match="shape"):
        calibrated_manager.project_batch(np.ones((2, 2, 2)))


def test_project_batch_non_finite(calibrated_manager: HomographyManager):
    """Batch containing NaN or Inf raises ValueError."""
    pts = np.array([[100.0, 200.0], [np.nan, 300.0]])
    with pytest.raises(ValueError, match="finite"):
        calibrated_manager.project_batch(pts)


def test_project_batch_horizon_rejection(calibrated_manager: HomographyManager):
    """Batch containing a point on the horizon raises ValueError."""
    h31, h32, h33 = calibrated_manager.H[2, :]
    if abs(h32) > 1e-8:
        v_horizon = -h33 / h32
        batch = np.array([
            [480.0, 920.0],
            [0.0, v_horizon],
        ])
        with pytest.raises(ValueError, match="horizon"):
            calibrated_manager.project_batch(batch, to_world=True)


def test_project_batch_aliases(calibrated_manager: HomographyManager):
    """project_points and project_to_image_batch aliases match project_batch."""
    img_pts = np.array([[480.0, 920.0], [1440.0, 920.0]])
    world_pts = np.array([[0.0, 0.0], [4.0, 0.0]])

    batch_w = calibrated_manager.project_points(img_pts)
    np.testing.assert_array_equal(batch_w, calibrated_manager.project_batch(img_pts, to_world=True))

    batch_i = calibrated_manager.project_to_image_batch(world_pts)
    np.testing.assert_array_equal(batch_i, calibrated_manager.project_batch(world_pts, to_world=False))


def test_projection_latency_budget(calibrated_manager: HomographyManager):
    """Batch projection of 100 points must execute in <0.5ms (budget for safety pipeline)."""
    np.random.seed(42)
    pts = np.random.uniform(500, 1000, size=(100, 2))

    # Warm-up
    for _ in range(10):
        _ = calibrated_manager.project_batch(pts)

    # Measure 100 iterations
    iters = 100
    start = time.perf_counter()
    for _ in range(iters):
        _ = calibrated_manager.project_batch(pts)
    elapsed = (time.perf_counter() - start) / iters  # seconds per call

    elapsed_ms = elapsed * 1000.0
    # Must be strictly within safety budget (<0.5ms)
    assert elapsed_ms < 0.5, f"Batch projection latency {elapsed_ms:.4f} ms exceeds 0.5 ms budget"
