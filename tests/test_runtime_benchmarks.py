"""
tests/test_runtime_benchmarks.py
Unit tests for multi-runtime comparative benchmark runner (scripts/benchmark_runtimes.py).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import json
import numpy as np
import pytest

from scripts.benchmark_runtimes import (
    RuntimeBenchmarkResult,
    ComparativeBenchmarkSummary,
    run_runtime_benchmark,
    run_multi_runtime_comparison,
    format_comparison_markdown,
    export_comparison_json,
    main,
)


class MockEngine:
    """Mock engine simulating inference times."""
    def __init__(self, name: str, latency_ms: float = 10.0):
        self.name = name
        self.latency_ms = latency_ms
        self.model_path = Path(f"models/{name}.model")

    def infer(self, image: np.ndarray) -> np.ndarray:
        import time
        # Busy sleep small fraction
        time.sleep(self.latency_ms / 1000.0)
        return np.zeros((1, 56, 8400), dtype=np.float32)

    def get_providers(self):
        return [self.name]

    def get_device_info(self):
        return self.name


def test_run_runtime_benchmark_statistics():
    """run_runtime_benchmark computes valid percentile, std, and jitter metrics."""
    engine = MockEngine("mock_fast", latency_ms=1.0)
    result = run_runtime_benchmark(
        engine=engine,
        runtime_id="mock_fast",
        display_name="Mock Fast Engine",
        iterations=10,
        warmup=2,
    )

    assert result.runtime_id == "mock_fast"
    assert result.display_name == "Mock Fast Engine"
    assert result.iterations == 10
    assert result.warmup == 2
    assert result.min_ms <= result.p50_ms <= result.p95_ms <= result.p99_ms <= result.max_ms
    assert result.std_ms >= 0.0
    assert result.variance_ms2 >= 0.0
    assert result.fps > 0.0


def test_comparative_benchmark_summary_speedup():
    """ComparativeBenchmarkSummary accurately calculates relative speedup vs baseline."""
    res_cpu = RuntimeBenchmarkResult(
        runtime_id="pytorch_cpu",
        display_name="PyTorch (CPU)",
        provider_or_device="cpu",
        warmup=5,
        iterations=20,
        mean_ms=50.0,
        min_ms=45.0,
        max_ms=55.0,
        std_ms=2.0,
        variance_ms2=4.0,
        p50_ms=50.0,
        p95_ms=54.0,
        p99_ms=54.8,
        fps=20.0,
        passed_iso_budget=False,
    )

    res_coreml = RuntimeBenchmarkResult(
        runtime_id="onnx_coreml",
        display_name="ONNX Runtime (CoreML)",
        provider_or_device="CoreMLExecutionProvider",
        warmup=5,
        iterations=20,
        mean_ms=10.0,
        min_ms=9.0,
        max_ms=12.0,
        std_ms=0.5,
        variance_ms2=0.25,
        p50_ms=10.0,
        p95_ms=11.0,
        p99_ms=11.8,
        fps=100.0,
        passed_iso_budget=True,
    )

    summary = ComparativeBenchmarkSummary(
        baseline_id="pytorch_cpu",
        results=[res_cpu, res_coreml],
    )

    speedups = summary.get_speedups()
    assert speedups["pytorch_cpu"] == pytest.approx(1.0, rel=1e-2)
    assert speedups["onnx_coreml"] == pytest.approx(5.0, rel=1e-2)


def test_format_comparison_markdown():
    """format_comparison_markdown outputs properly structured GitHub Markdown table."""
    res1 = RuntimeBenchmarkResult(
        runtime_id="pytorch_cpu",
        display_name="PyTorch (CPU)",
        provider_or_device="cpu",
        warmup=5,
        iterations=20,
        mean_ms=45.0,
        min_ms=40.0,
        max_ms=50.0,
        std_ms=2.0,
        variance_ms2=4.0,
        p50_ms=45.0,
        p95_ms=48.0,
        p99_ms=49.5,
        fps=22.2,
        passed_iso_budget=False,
    )
    res2 = RuntimeBenchmarkResult(
        runtime_id="onnx_coreml",
        display_name="ONNX Runtime (CoreML)",
        provider_or_device="CoreMLExecutionProvider",
        warmup=5,
        iterations=20,
        mean_ms=10.0,
        min_ms=9.0,
        max_ms=11.5,
        std_ms=0.5,
        variance_ms2=0.25,
        p50_ms=10.0,
        p95_ms=11.0,
        p99_ms=11.4,
        fps=100.0,
        passed_iso_budget=True,
    )

    summary = ComparativeBenchmarkSummary(baseline_id="pytorch_cpu", results=[res1, res2])
    md = format_comparison_markdown(summary)

    assert "PyTorch (CPU)" in md
    assert "ONNX Runtime (CoreML)" in md
    assert "4.50x" in md or "4.5x" in md
    assert "PASS" in md
    assert "FAIL" in md


def test_export_comparison_json(tmp_path: Path):
    """export_comparison_json serializes full comparative metrics to valid JSON."""
    res1 = RuntimeBenchmarkResult(
        runtime_id="pytorch_cpu",
        display_name="PyTorch (CPU)",
        provider_or_device="cpu",
        warmup=5,
        iterations=20,
        mean_ms=45.0,
        min_ms=40.0,
        max_ms=50.0,
        std_ms=2.0,
        variance_ms2=4.0,
        p50_ms=45.0,
        p95_ms=48.0,
        p99_ms=49.5,
        fps=22.2,
        passed_iso_budget=False,
    )
    summary = ComparativeBenchmarkSummary(baseline_id="pytorch_cpu", results=[res1])
    json_path = tmp_path / "comparison.json"

    export_comparison_json(summary, json_path)
    assert json_path.is_file()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["baseline_id"] == "pytorch_cpu"
    assert len(data["results"]) == 1
    assert data["results"][0]["runtime_id"] == "pytorch_cpu"
    assert "speedup_vs_baseline" in data["results"][0]
