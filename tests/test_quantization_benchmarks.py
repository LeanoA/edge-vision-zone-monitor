"""
tests/test_quantization_benchmarks.py
Unit tests for quantization and precision benchmark runner (scripts/benchmark_quantization.py).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import json
import numpy as np
import pytest

from scripts.benchmark_quantization import (
    QuantizationResult,
    QuantizationComparisonSummary,
    compute_geometric_drift,
    format_quantization_markdown,
    export_quantization_json,
)
from src.core.homography import HomographyManager


@pytest.fixture
def mock_homography(tmp_path: Path) -> HomographyManager:
    """Create a mock HomographyManager for test evaluation."""
    cfg = tmp_path / "homography.yaml"
    cfg.write_text(
        """
camera:
  resolution:
    width: 1920
    height: 1080
calibration:
  points:
    image:
      - [300.0, 950.0]
      - [1620.0, 950.0]
      - [1350.0, 420.0]
      - [570.0, 420.0]
    world:
      - [0.0, 0.0]
      - [8.0, 0.0]
      - [8.0, 12.0]
      - [0.0, 12.0]
""",
        encoding="utf-8",
    )
    return HomographyManager(config_path=str(cfg))


def test_compute_geometric_drift_exact_match(mock_homography: HomographyManager):
    """Zero drift when predictions are identical."""
    kps_ref = np.array([[[200.0, 300.0, 0.9], [210.0, 310.0, 0.9]]], dtype=np.float32)
    kps_cand = np.array([[[200.0, 300.0, 0.9], [210.0, 310.0, 0.9]]], dtype=np.float32)

    px_rmse, metric_rmse_cm, max_drift_cm = compute_geometric_drift(
        kps_ref=kps_ref,
        kps_cand=kps_cand,
        homography=mock_homography,
    )

    assert px_rmse == pytest.approx(0.0, abs=1e-3)
    assert metric_rmse_cm == pytest.approx(0.0, abs=1e-3)
    assert max_drift_cm == pytest.approx(0.0, abs=1e-3)


def test_compute_geometric_drift_with_offset(mock_homography: HomographyManager):
    """Calculates non-zero pixel and metric drift under known coordinate offsets."""
    kps_ref = np.array([[[200.0, 300.0, 0.9]]], dtype=np.float32)
    # 5 px offset in image space
    kps_cand = np.array([[[203.0, 304.0, 0.9]]], dtype=np.float32)  # dist = sqrt(3^2 + 4^2) = 5.0 px

    px_rmse, metric_rmse_cm, max_drift_cm = compute_geometric_drift(
        kps_ref=kps_ref,
        kps_cand=kps_cand,
        homography=mock_homography,
    )

    assert px_rmse == pytest.approx(5.0, rel=1e-2)
    assert metric_rmse_cm > 0.0
    assert max_drift_cm == metric_rmse_cm


def test_format_quantization_markdown():
    """format_quantization_markdown produces valid formatted Markdown table."""
    res_fp32 = QuantizationResult(
        model_id="fp32",
        display_name="FP32 (Baseline)",
        precision="FP32",
        size_mb=11.85,
        size_reduction_pct=0.0,
        mean_latency_ms=15.8,
        p95_latency_ms=18.5,
        fps=63.3,
        pixel_rmse_px=0.0,
        metric_rmse_cm=0.0,
        max_metric_drift_cm=0.0,
        passed_safety_tolerance=True,
    )

    res_int8 = QuantizationResult(
        model_id="int8",
        display_name="INT8 (Dynamic Quant)",
        precision="INT8",
        size_mb=3.42,
        size_reduction_pct=71.1,
        mean_latency_ms=12.2,
        p95_latency_ms=14.5,
        fps=82.0,
        pixel_rmse_px=1.2,
        metric_rmse_cm=2.4,
        max_metric_drift_cm=4.1,
        passed_safety_tolerance=True,
    )

    summary = QuantizationComparisonSummary(
        baseline_id="fp32",
        results=[res_fp32, res_int8],
    )

    md = format_quantization_markdown(summary)
    assert "FP32 (Baseline)" in md
    assert "INT8 (Dynamic Quant)" in md
    assert "71.1%" in md
    assert "2.40 cm" in md or "2.4 cm" in md
    assert "PASS" in md


def test_export_quantization_json(tmp_path: Path):
    """export_quantization_json writes structured comparison to valid JSON."""
    res = QuantizationResult(
        model_id="fp32",
        display_name="FP32",
        precision="FP32",
        size_mb=11.85,
        size_reduction_pct=0.0,
        mean_latency_ms=15.8,
        p95_latency_ms=18.5,
        fps=63.3,
        pixel_rmse_px=0.0,
        metric_rmse_cm=0.0,
        max_metric_drift_cm=0.0,
        passed_safety_tolerance=True,
    )
    summary = QuantizationComparisonSummary(baseline_id="fp32", results=[res])
    dest = tmp_path / "quant_report.json"

    export_quantization_json(summary, dest)
    assert dest.is_file()

    data = json.loads(dest.read_text(encoding="utf-8"))
    assert data["baseline_id"] == "fp32"
    assert len(data["results"]) == 1
    assert data["results"][0]["size_mb"] == 11.85
