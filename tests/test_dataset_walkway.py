"""
tests/test_dataset_walkway.py
Dedicated Unit and Integration Tests for Mendeley Walkway Violation Dataset and Calibration.
"""

from pathlib import Path
import numpy as np
import pytest
import yaml

from scripts.download_datasets import DATASET_REGISTRY, DatasetMetadata
from scripts.run_dataset_test import (
    DatasetTestConfig,
    DatasetTestRunner,
    DatasetTestSummary,
    load_zone_config_from_yaml,
)
from src.core.homography import HomographyManager
from src.core.spatial_fsm import ZoneConfig


class TestWalkwayDatasetProfile:
    """Test suite for mendeley_walkway_violation YAML configuration and homography."""

    @pytest.fixture
    def config_path(self) -> Path:
        return Path("configs/datasets/mendeley_walkway_violation.yaml")

    def test_registry_contains_walkway_dataset(self) -> None:
        """Verify mendeley_walkway_violation is registered in canonical DATASET_REGISTRY."""
        assert "mendeley_walkway_violation" in DATASET_REGISTRY
        meta = DATASET_REGISTRY["mendeley_walkway_violation"]
        assert isinstance(meta, DatasetMetadata)
        assert meta.filename == "mendeley_walkway_violation.mp4"
        assert meta.default_config == "configs/datasets/mendeley_walkway_violation.yaml"
        assert meta.priority == 1

    def test_yaml_schema_and_zone_parsing(self, config_path: Path) -> None:
        """Verify YAML profile parses correctly into ZoneConfig with valid ISO 13855 zones."""
        assert config_path.is_file(), f"Missing config file: {config_path}"

        zone_cfg = load_zone_config_from_yaml(config_path)
        assert isinstance(zone_cfg, ZoneConfig)
        assert zone_cfg.name == "FactoryWalkwaySafetyZone"
        assert len(zone_cfg.danger_polygon) >= 4
        assert zone_cfg.warning_polygon is not None
        assert len(zone_cfg.warning_polygon) >= 4
        assert zone_cfg.hysteresis_buffer_m == 0.20
        assert zone_cfg.n_confirm == 3
        assert zone_cfg.n_release == 5
        assert zone_cfg.dwell_warning_s == 3.0
        assert zone_cfg.dwell_violation_s == 6.0
        assert zone_cfg.iso_k_speed == 1.6

    def test_homography_reprojection_accuracy(self, config_path: Path) -> None:
        """Verify DLT homography reprojection error is <= 0.05m tolerance."""
        homography = HomographyManager(config_path=config_path)
        assert homography.H is not None
        assert homography.H.shape == (3, 3)

        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        img_pts = cfg["calibration"]["points"]["image"]
        world_pts = cfg["calibration"]["points"]["world"]

        for (u, v), (X_true, Y_true) in zip(img_pts, world_pts):
            proj_x, proj_y = homography.project_point(u, v)
            err = float(np.sqrt((proj_x - X_true) ** 2 + (proj_y - Y_true) ** 2))
            assert err <= cfg["calibration"]["reprojection_tolerance_m"], (
                f"DLT point ({u}, {v}) projected to ({proj_x:.4f}, {proj_y:.4f}), "
                f"expected ({X_true}, {Y_true}), error {err:.4f}m exceeds tolerance."
            )


class TestWalkwayDatasetIntegration:
    """End-to-end integration tests streaming walkway video frames through SafetyPipeline."""

    def test_walkway_video_execution(self, tmp_path: Path) -> None:
        """Verify DatasetTestRunner processes walkway video frames and exports telemetry."""
        video_path = Path("data/raw/mendeley_industrial/mendeley_walkway_violation.mp4")
        if not video_path.is_file():
            pytest.skip(f"Video file not present at {video_path}")

        config = DatasetTestConfig(
            source=str(video_path),
            config_path="configs/datasets/mendeley_walkway_violation.yaml",
            dataset_name="test_walkway_eval",
            output_dir=tmp_path,
            no_display=True,
            max_frames=30,
        )

        runner = DatasetTestRunner(config)
        runner.initialize()
        summary = runner.run()

        assert isinstance(summary, DatasetTestSummary)
        assert summary.total_frames == 30
        assert summary.average_fps > 0.0
        assert summary.latencies_mean_ms < 40.0

        results_dir = tmp_path / "test_walkway_eval"
        assert (results_dir / "annotated_test_walkway_eval.mp4").is_file()
        assert (results_dir / "events.jsonl").is_file()
        assert (results_dir / "summary.json").is_file()
