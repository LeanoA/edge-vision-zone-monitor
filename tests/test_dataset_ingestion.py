"""
tests/test_dataset_ingestion.py
Unit and Integration Tests for Dataset Downloader, Registry, and Ingestion Test Runner.
"""

from pathlib import Path
import tempfile
import pytest
import yaml

from scripts.download_datasets import (
    DATASET_REGISTRY,
    DatasetMetadata,
    fetch_dataset,
    list_datasets,
)
from scripts.run_dataset_test import (
    DatasetTestConfig,
    DatasetTestRunner,
    DatasetTestSummary,
    load_zone_config_from_yaml,
)
from src.core.homography import HomographyManager
from src.core.spatial_fsm import ZoneConfig


class TestDatasetRegistryAndDownloader:
    """Test suite for dataset registry definitions and downloader mechanics."""

    def test_registry_contains_canonical_datasets(self) -> None:
        """Verify all canonical benchmark datasets exist in the registry with valid metadata."""
        expected_keys = ["opencv_vtest", "openvino_people", "pets2009_s2_l1", "oxford_town_centre"]
        for key in expected_keys:
            assert key in DATASET_REGISTRY
            meta = DATASET_REGISTRY[key]
            assert isinstance(meta, DatasetMetadata)
            assert meta.name == key
            assert len(meta.primary_url) > 0
            assert meta.filename.endswith((".avi", ".mp4", ".tar.gz", ".zip"))
            assert meta.priority in (1, 2, 3)

    def test_fetch_dataset_invalid_name_raises_error(self) -> None:
        """Verify requesting an unknown dataset name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown dataset 'non_existent_ds'"):
            fetch_dataset("non_existent_ds")

    def test_fetch_dataset_skips_when_file_exists(self, tmp_path: Path) -> None:
        """Verify fetch_dataset skips download if target file exists and not force."""
        ds_dir = tmp_path / "opencv_vtest"
        ds_dir.mkdir(parents=True)
        fake_file = ds_dir / "vtest.avi"
        fake_file.write_bytes(b"dummy video content 12345")

        result = fetch_dataset("opencv_vtest", output_base_dir=tmp_path, force=False)
        assert result == fake_file

    def test_list_datasets_runs_without_exceptions(self, tmp_path: Path) -> None:
        """Verify list_datasets formats table cleanly."""
        list_datasets(output_base_dir=tmp_path)


class TestDatasetConfigurations:
    """Test suite for YAML dataset calibration and zone profiles."""

    @pytest.mark.parametrize(
        "config_path",
        [
            "configs/datasets/opencv_vtest.yaml",
            "configs/datasets/openvino_people.yaml",
            "configs/datasets/pets2009_s2_l1.yaml",
            "configs/datasets/mendeley_industrial.yaml",
            "configs/datasets/mendeley_walkway_violation.yaml",
        ],
    )
    def test_yaml_config_validity(self, config_path: str) -> None:
        """Verify dataset YAML configs can be parsed by HomographyManager and load_zone_config_from_yaml."""
        path = Path(config_path)
        assert path.is_file(), f"Missing config file: {config_path}"

        # Test HomographyManager loads and initializes H matrix
        homography = HomographyManager(config_path=path)
        assert homography.H is not None
        assert homography.H.shape == (3, 3)

        # Test ZoneConfig parsing
        zone_cfg = load_zone_config_from_yaml(path)
        assert isinstance(zone_cfg, ZoneConfig)
        assert len(zone_cfg.danger_polygon) >= 3
        assert 0.15 <= zone_cfg.hysteresis_buffer_m <= 0.30

    def test_load_zone_config_file_not_found(self) -> None:
        """Verify FileNotFoundError on missing YAML config."""
        with pytest.raises(FileNotFoundError):
            load_zone_config_from_yaml("configs/datasets/non_existent.yaml")


class TestDatasetTestRunner:
    """Test suite for DatasetTestRunner execution and summary generation."""

    def test_runner_initialization_with_synthetic_sample(self, tmp_path: Path) -> None:
        """Verify runner initializes and processes frames on an available video sample."""
        sample_path = Path("data/samples/sequence_a_clean_incursion.mp4")
        if not sample_path.is_file():
            pytest.skip("Synthetic sample sequence_a not generated.")

        config = DatasetTestConfig(
            source=str(sample_path),
            config_path="configs/default_config.yaml",
            dataset_name="test_sample_run",
            output_dir=tmp_path,
            no_display=True,
            max_frames=10,
        )

        runner = DatasetTestRunner(config)
        runner.initialize()
        assert runner.cap is not None
        assert runner.pipeline is not None

        summary = runner.run()
        assert isinstance(summary, DatasetTestSummary)
        assert summary.total_frames == 10
        assert summary.average_fps > 0.0

        # Check output artifacts
        results_dir = tmp_path / "test_sample_run"
        assert (results_dir / "annotated_test_sample_run.mp4").is_file()
        assert (results_dir / "events.jsonl").is_file()
        assert (results_dir / "summary.json").is_file()

        # Check summary formatting text
        formatted = summary.format_text()
        assert "DATASET EVALUATION REPORT" in formatted
        assert "Processed Frames" in formatted
