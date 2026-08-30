"""
Unit tests for scripts/benchmark.py.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import json
import numpy as np
import pytest

from src.inference.onnx_engine import OnnxEngine
from scripts.benchmark import (
    LATENCY_BUDGET_P95_MS,
    BenchmarkMetrics,
    format_benchmark_table,
    run_benchmark,
    main,
)


def test_benchmark_metrics_integrity():
    """BenchmarkMetrics dataclass enforces frozen fields and proper types."""
    metrics = BenchmarkMetrics(
        model_path="models/test.onnx",
        active_providers=["CoreMLExecutionProvider"],
        warmup_iterations=10,
        iterations=50,
        mean_ms=15.2,
        min_ms=12.1,
        max_ms=22.3,
        std_ms=1.4,
        p50_ms=15.0,
        p95_ms=18.5,
        p99_ms=21.0,
        fps=65.79,
        passed_budget=True,
    )
    assert metrics.passed_budget is True
    assert metrics.p95_ms <= LATENCY_BUDGET_P95_MS
    with pytest.raises(AttributeError):
        metrics.mean_ms = 20.0  # frozen dataclass check


def test_run_benchmark_distribution_percentiles(synthetic_onnx_path: Path):
    """run_benchmark measures latency distributions where min <= p50 <= p95 <= p99 <= max."""
    engine = OnnxEngine(synthetic_onnx_path)
    metrics = run_benchmark(engine, iterations=20, warmup=5)

    assert metrics.iterations == 20
    assert metrics.warmup_iterations == 5
    assert metrics.min_ms <= metrics.p50_ms
    assert metrics.p50_ms <= metrics.p95_ms
    assert metrics.p95_ms <= metrics.p99_ms
    assert metrics.p99_ms <= metrics.max_ms
    assert metrics.fps == pytest.approx(1000.0 / metrics.mean_ms, rel=1e-2)
    assert isinstance(metrics.passed_budget, bool)


def test_run_benchmark_warmup_isolation(synthetic_onnx_path: Path):
    """Warmup iterations are executed separately from recorded measurement iterations."""
    engine = OnnxEngine(synthetic_onnx_path)
    with patch.object(engine, "infer", wraps=engine.infer) as mock_infer:
        metrics = run_benchmark(engine, iterations=15, warmup=5)
        assert mock_infer.call_count == 20  # 5 warmup + 15 measured
        assert metrics.iterations == 15
        assert metrics.warmup_iterations == 5


def test_benchmark_budget_evaluation():
    """Budget compliance accurately reflects p95 vs 30.0ms budget."""
    pass_metrics = BenchmarkMetrics(
        model_path="models/pass.onnx",
        active_providers=["CPUExecutionProvider"],
        warmup_iterations=5,
        iterations=20,
        mean_ms=20.0,
        min_ms=15.0,
        max_ms=28.0,
        std_ms=2.0,
        p50_ms=19.5,
        p95_ms=27.5,
        p99_ms=28.0,
        fps=50.0,
        passed_budget=27.5 <= LATENCY_BUDGET_P95_MS,
    )
    assert pass_metrics.passed_budget is True

    fail_metrics = BenchmarkMetrics(
        model_path="models/fail.onnx",
        active_providers=["CPUExecutionProvider"],
        warmup_iterations=5,
        iterations=20,
        mean_ms=35.0,
        min_ms=30.0,
        max_ms=45.0,
        std_ms=3.0,
        p50_ms=34.0,
        p95_ms=42.0,
        p99_ms=44.5,
        fps=28.57,
        passed_budget=42.0 <= LATENCY_BUDGET_P95_MS,
    )
    assert fail_metrics.passed_budget is False


def test_format_benchmark_table():
    """format_benchmark_table produces aligned output containing key metrics."""
    metrics = BenchmarkMetrics(
        model_path="models/yolo11n-pose.onnx",
        active_providers=["CoreMLExecutionProvider", "CPUExecutionProvider"],
        warmup_iterations=50,
        iterations=200,
        mean_ms=18.42,
        min_ms=14.10,
        max_ms=25.80,
        std_ms=1.65,
        p50_ms=18.10,
        p95_ms=21.30,
        p99_ms=24.20,
        fps=54.29,
        passed_budget=True,
    )
    table = format_benchmark_table(metrics)
    assert "yolo11n-pose.onnx" in table
    assert "CoreMLExecutionProvider" in table
    assert "18.42" in table
    assert "21.30" in table
    assert "PASS" in table


def test_benchmark_cli_json_export(synthetic_onnx_path: Path, tmp_path: Path, monkeypatch):
    """CLI exports structured JSON adhering to edge safety benchmark schema."""
    json_dest = tmp_path / "benchmark_report.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "benchmark.py",
            "--model", str(synthetic_onnx_path),
            "--iterations", "10",
            "--warmup", "2",
            "--json-out", str(json_dest),
        ],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    assert json_dest.is_file()

    data = json.loads(json_dest.read_text(encoding="utf-8"))
    assert "model_path" in data
    assert "provider" in data
    assert data["warmup_iterations"] == 2
    assert data["iterations"] == 10
    assert "metrics" in data
    assert "p95_ms" in data["metrics"]
    assert "budget_ms" in data
    assert data["budget_ms"] == LATENCY_BUDGET_P95_MS
    assert "passed" in data


def test_benchmark_cli_strict_pass(synthetic_onnx_path: Path, monkeypatch):
    """CLI in --strict mode exits with 0 when budget passes."""
    monkeypatch.setattr(
        "sys.argv",
        [
            "benchmark.py",
            "--model", str(synthetic_onnx_path),
            "--iterations", "5",
            "--warmup", "2",
            "--strict",
        ],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


def test_benchmark_cli_strict_fail(synthetic_onnx_path: Path, monkeypatch):
    """CLI in --strict mode exits with 1 when budget fails."""
    # Patch run_benchmark to return a metric that breaches budget
    failing_metrics = BenchmarkMetrics(
        model_path=str(synthetic_onnx_path),
        active_providers=["CPUExecutionProvider"],
        warmup_iterations=5,
        iterations=10,
        mean_ms=35.0,
        min_ms=31.0,
        max_ms=45.0,
        std_ms=3.0,
        p50_ms=34.0,
        p95_ms=41.2,
        p99_ms=44.0,
        fps=28.57,
        passed_budget=False,
    )

    with patch("scripts.benchmark.run_benchmark", return_value=failing_metrics):
        monkeypatch.setattr(
            "sys.argv",
            [
                "benchmark.py",
                "--model", str(synthetic_onnx_path),
                "--strict",
            ],
        )
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1
