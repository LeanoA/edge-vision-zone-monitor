"""
tests/test_benchmark_traceability.py
Automated validation of benchmark invariants and provenance traceability metadata.
Guarantees that synthetic benchmark runs do not silently pass with 0 tracks,
no intrusion, missing dwell violations, or absent lockout states.
"""

import json
from pathlib import Path
import pytest

from src.utils.benchmark_verifier import (
    BenchmarkInvariantError,
    assert_benchmark_invariants,
    verify_benchmark_summary_invariants,
)
from scripts.run_dataset_test import DatasetTestConfig, DatasetTestRunner


def test_invariant_checker_fails_when_tracks_missing():
    """Verifier must report an invariant violation when total_tracks == 0."""
    violations = verify_benchmark_summary_invariants(
        dataset_name="sequence_a_clean_incursion",
        total_tracks=0,
        state_counts={"SAFE": 180},
        danger_events_count=0,
        dwell_violations_count=0,
    )
    assert len(violations) >= 1
    assert any("Expected >= 1 track" in v for v in violations)

    with pytest.raises(BenchmarkInvariantError, match="Expected >= 1 track"):
        assert_benchmark_invariants(
            dataset_name="sequence_a_clean_incursion",
            total_tracks=0,
            state_counts={"SAFE": 180},
            danger_events_count=0,
            dwell_violations_count=0,
        )


def test_invariant_checker_fails_when_incursion_missing():
    """Verifier must fail when an incursion benchmark experiences 0 danger events."""
    with pytest.raises(BenchmarkInvariantError, match="Expected incursion"):
        assert_benchmark_invariants(
            dataset_name="sequence_a_clean_incursion",
            total_tracks=1,
            state_counts={"SAFE": 180},
            danger_events_count=0,
            dwell_violations_count=0,
        )


def test_invariant_checker_fails_when_lockout_missing_in_sequence_b():
    """Verifier must fail when Sequence B does not trigger fail-safe LOCKOUT latch."""
    with pytest.raises(BenchmarkInvariantError, match="Expected fail-safe LOCKOUT"):
        assert_benchmark_invariants(
            dataset_name="sequence_b_occlusion_coasting",
            total_tracks=2,
            state_counts={"SAFE": 100, "DANGER_INTRUSION": 80},
            danger_events_count=80,
            dwell_violations_count=0,
        )


def test_invariant_checker_fails_when_dwell_missing_in_sequence_c():
    """Verifier must fail when Sequence C does not trigger dwell violations."""
    with pytest.raises(BenchmarkInvariantError, match="Expected dwell violation"):
        assert_benchmark_invariants(
            dataset_name="sequence_c_dwell_loitering",
            total_tracks=2,
            state_counts={"SAFE": 50, "DANGER_INTRUSION": 250},
            danger_events_count=250,
            dwell_violations_count=0,
        )


def test_invariant_checker_passes_on_valid_metrics():
    """Verifier passes cleanly without exceptions when all invariants hold."""
    # Sequence A
    assert_benchmark_invariants(
        dataset_name="sequence_a_clean_incursion",
        total_tracks=2,
        state_counts={"SAFE": 105, "DANGER_INTRUSION": 75},
        danger_events_count=75,
        dwell_violations_count=0,
    )
    # Sequence B
    assert_benchmark_invariants(
        dataset_name="sequence_b_occlusion_coasting",
        total_tracks=4,
        state_counts={"SAFE": 26, "WARNING_APPROACH": 19, "DANGER_INTRUSION": 28, "LOCKOUT": 107},
        danger_events_count=28,
        dwell_violations_count=0,
    )
    # Sequence C
    assert_benchmark_invariants(
        dataset_name="sequence_c_dwell_loitering",
        total_tracks=3,
        state_counts={"SAFE": 61, "DANGER_INTRUSION": 236},
        danger_events_count=236,
        dwell_violations_count=14,
    )


def test_runner_generates_cryptographic_traceability_metadata(tmp_path: Path):
    """DatasetTestRunner must record git, model sha256, config sha256, and parameter metadata."""
    sample_path = Path("data/samples/sequence_a_clean_incursion.mp4")
    if not sample_path.is_file():
        pytest.skip("Synthetic sample sequence_a not generated.")

    cfg = DatasetTestConfig(
        source=str(sample_path),
        config_path="configs/datasets/sequence_a_clean_incursion.yaml",
        dataset_name="test_traceability",
        output_dir=tmp_path,
        no_display=True,
        max_frames=15,
    )
    runner = DatasetTestRunner(cfg)
    summary = runner.run()

    summary_file = tmp_path / "test_traceability" / "summary.json"
    assert summary_file.is_file()

    with open(summary_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "metadata" in data
    meta = data["metadata"]
    assert "git" in meta and "commit" in meta["git"]
    assert len(meta["git"]["commit"]) == 40 or meta["git"]["commit"] == "unknown"
    assert "model" in meta and len(meta["model"]["sha256"]) == 64
    assert "config" in meta and len(meta["config"]["sha256"]) == 64
    assert "source" in meta and len(meta["source"]["sha256"]) == 64
    assert "parameters" in meta
    assert meta["parameters"]["conf_threshold"] == 0.4
    assert meta["parameters"]["max_frames"] == 15


def test_reproduced_benchmark_results_satisfy_invariants():
    """Verify that existing generated summaries in data/results/ satisfy all safety invariants."""
    results_dir = Path("data/results")
    benchmarks = [
        ("sequence_a_clean_incursion", True, False, False),
        ("sequence_b_occlusion_coasting", True, True, False),
        ("sequence_c_dwell_loitering", True, False, True),
    ]

    for name, req_incursion, req_lockout, req_dwell in benchmarks:
        summary_path = results_dir / name / "summary.json"
        if not summary_path.is_file():
            pytest.skip(f"Summary for {name} does not exist yet.")

        with open(summary_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["total_tracks"] >= 1, f"[{name}] Must have >= 1 track"
        if req_incursion:
            assert data["danger_events_count"] >= 1 or data["state_counts"].get("DANGER_INTRUSION", 0) >= 1
        if req_lockout:
            assert data["state_counts"].get("LOCKOUT", 0) >= 1, f"[{name}] Must trigger LOCKOUT"
        if req_dwell:
            assert data["dwell_violations_count"] >= 1, f"[{name}] Must trigger dwell violations"

        # Check metadata presence
        assert "metadata" in data
        assert "git" in data["metadata"]
        assert "sha256" in data["metadata"]["model"]
        assert "sha256" in data["metadata"]["config"]
        assert data["metadata"]["invariants_passed"] is True
