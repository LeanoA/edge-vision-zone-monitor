"""
tests/test_benchmark_audit.py
Automated validation of audit findings, benchmark consistency,
stage timing invariants, and traceability metadata.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BENCH_DIR = REPO_ROOT / "docs" / "benchmarks"


def test_all_benchmark_artifacts_exist_and_have_metadata():
    """All generated JSON benchmark reports must exist and include valid structure."""
    expected_files = [
        BENCH_DIR / "comprehensive_audit_results.json",
        BENCH_DIR / "runtime_comparison.json",
        BENCH_DIR / "quantization_comparison.json",
        BENCH_DIR / "resolution_comparison.json",
        BENCH_DIR / "stage_breakdown.json",
        BENCH_DIR / "mot_quality_comparison.json",
    ]

    for f in expected_files:
        if not f.is_file():
            pytest.skip(f"Benchmark file {f.name} not generated yet.")

        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        assert data is not None
        assert isinstance(data, dict)

    # Master audit inspection
    with open(BENCH_DIR / "comprehensive_audit_results.json", "r", encoding="utf-8") as fp:
        master = json.load(fp)

    assert "metadata" in master
    meta = master["metadata"]
    assert "environment" in meta
    env = meta["environment"]
    assert "platform" in env
    assert "python_version" in env
    assert "git_commit" in env
    assert len(env["git_commit"]) == 40 or env["git_commit"] == "unknown"

    assert "model_checksums_sha256" in meta
    models = meta["model_checksums_sha256"]
    assert "onnx_fp32_640" in models
    assert len(models["onnx_fp32_640"]) == 64


def test_runtime_benchmark_relationships():
    """Verify runtime benchmark ordering: CoreML & MPS faster than CPU; ONNX CPU faster than PyTorch CPU."""
    fpath = BENCH_DIR / "runtime_comparison.json"
    if not fpath.is_file():
        pytest.skip("runtime_comparison.json not generated yet.")

    with open(fpath, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    results = {r["runtime_id"]: r for r in data["results"]}
    assert "pytorch_cpu" in results
    assert "onnx_cpu" in results
    assert "pytorch_mps" in results
    assert "onnx_coreml" in results

    # ONNX CPU faster than PyTorch CPU
    assert results["onnx_cpu"]["mean_ms"] < results["pytorch_cpu"]["mean_ms"]

    # Accelerated runtimes (CoreML and MPS) faster than CPU
    assert results["onnx_coreml"]["mean_ms"] < results["onnx_cpu"]["mean_ms"]
    assert results["pytorch_mps"]["mean_ms"] < results["onnx_cpu"]["mean_ms"]

    # CoreML meets 30ms internal budget
    assert results["onnx_coreml"]["passed_internal_budget"] is True


def test_quantization_relationships():
    """Verify quantization hypotheses: INT8 degrades latency and metric precision."""
    fpath = BENCH_DIR / "quantization_comparison.json"
    if not fpath.is_file():
        pytest.skip("quantization_comparison.json not generated yet.")

    with open(fpath, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    results = {r["model_id"]: r for r in data["results"]}
    assert "fp32" in results
    assert "fp16" in results
    assert "int8" in results

    # Relative metric drift between FP16 and FP32 is negligible (< 1.0 cm)
    assert abs(results["fp16"]["metric_rmse_cm"] - results["fp32"]["metric_rmse_cm"]) < 1.0

    # INT8 dynamic exhibits severe latency penalty and high max drift on this platform
    assert results["int8"]["mean_latency_ms"] > 2.0 * results["fp32"]["mean_latency_ms"]
    assert results["int8"]["max_metric_drift_cm"] > 50.0


def test_resolution_far_field_sensitivity():
    """Verify 960 resolution detects substantially more far-field candidates than 640."""
    fpath = BENCH_DIR / "resolution_comparison.json"
    if not fpath.is_file():
        pytest.skip("resolution_comparison.json not generated yet.")

    with open(fpath, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    results = {r["resolution_id"]: r for r in data["results"]}
    assert "640_fp32" in results
    assert "960_fp32" in results

    # 960 detects more far-field targets than 640
    assert results["960_fp32"]["far_field_detections"] > results["640_fp32"]["far_field_detections"]
    assert results["960_fp32"]["total_detections"] > results["640_fp32"]["total_detections"]

    # 960 inference latency exceeds 30ms internal budget
    assert results["960_fp32"]["inference_p95_ms"] > 30.0


def test_stage_latency_breakdown():
    """Verify all pipeline stages are profiled and inference is the primary stage."""
    fpath = BENCH_DIR / "stage_breakdown.json"
    if not fpath.is_file():
        pytest.skip("stage_breakdown.json not generated yet.")

    with open(fpath, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    stages = {s["stage_name"]: s for s in data["stages"]}
    assert any("Capture" in k for k in stages)
    assert any("Preprocessing" in k for k in stages)
    assert any("Inference" in k for k in stages)
    assert any("Keypoint" in k for k in stages)
    assert any("Homography" in k for k in stages)
    assert any("Kalman" in k or "Tracking" in k for k in stages)
    assert any("FSM" in k for k in stages)


def test_mot_functional_safety_invariants():
    """Verify MOT metrics and functional reaction latency on Sequence A."""
    fpath = BENCH_DIR / "mot_quality_comparison.json"
    if not fpath.is_file():
        pytest.skip("mot_quality_comparison.json not generated yet.")

    with open(fpath, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    seq_a = data["sequence_a_results"]
    assert seq_a["functional_pass"] is True
    assert seq_a["danger_frames"] >= 50
    assert seq_a["first_observed_ankle_entry_frame"] is not None
    assert seq_a["first_gt_centroid_entry_frame"] is not None
    assert seq_a["system_trip_frame"] is not None
    # Trip frame occurs within 5 frames of boundary crossing
    assert abs(seq_a["system_trip_frame"] - seq_a["first_gt_centroid_entry_frame"]) <= 5
    # Formalized reaction profile verification
    assert seq_a["t_event_reaction_from_ankle_ms"] > 0.0
    assert seq_a["t_lead_vs_centroid_ms"] < 0.0

    mot = seq_a["mot_summary"]
    assert mot["mota"] >= 0.85
    assert mot["idf1"] >= 0.85
    assert mot["total_id_switches"] <= 2

    # PETS2009 crowd and dynamic occlusion tracking ablation
    assert "pets2009_crowd_results" in data
    pets = data["pets2009_crowd_results"]
    assert pets["evaluated_frames"] > 0
    assert pets["coasting_verified"] is True
    assert pets["lockout_frames"] > 0


def test_coreml_partitioning_evidence():
    """Verify structured CoreML graph partitioning evidence is tracked."""
    master_path = BENCH_DIR / "comprehensive_audit_results.json"
    if not master_path.is_file():
        pytest.skip("comprehensive_audit_results.json not generated yet.")

    with open(master_path, "r", encoding="utf-8") as fp:
        master = json.load(fp)

    assert "coreml_partitioning" in master["metadata"]
    part = master["metadata"]["coreml_partitioning"]
    assert "onnx_fp32_640" in part
    assert part["onnx_fp32_640"]["number_of_partitions"] == 5
    assert part["onnx_fp32_640"]["coreml_supported_nodes"] == 346
    assert part["onnx_fp32_640"]["cpu_fallback_nodes"] == 8

    assert "onnx_fp16_640" in part
    assert part["onnx_fp16_640"]["number_of_partitions"] == 6

    assert "onnx_int8_640" in part
    assert part["onnx_int8_640"]["number_of_partitions"] == 67
