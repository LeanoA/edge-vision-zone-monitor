#!/usr/bin/env python3
"""
scripts/verify_synthetic_results.py
CLI Automated Checker for Synthetic Benchmark Invariants and Provenance Traceability.
Fails with exit code 1 if any benchmark sequence has no tracks, no intrusion,
no dwell violation, or no lockout, or if traceability metadata is absent.
"""

import argparse
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.benchmark_verifier import verify_benchmark_summary_invariants
from scripts.run_dataset_test import DatasetTestConfig, DatasetTestRunner


def check_summary_file(summary_path: Path) -> list:
    """Inspect existing summary JSON file and return any invariant violations."""
    errors = []
    if not summary_path.is_file():
        return [f"Summary file not found: {summary_path}"]

    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    dataset_name = data.get("dataset_name", summary_path.parent.name)
    total_tracks = data.get("total_tracks", 0)
    state_counts = data.get("state_counts", {})
    danger_events = data.get("danger_events_count", 0)
    dwell_violations = data.get("dwell_violations_count", 0)
    metadata = data.get("metadata", {})

    # 1. Check invariants
    inv_errors = verify_benchmark_summary_invariants(
        dataset_name=dataset_name,
        total_tracks=total_tracks,
        state_counts=state_counts,
        danger_events_count=danger_events,
        dwell_violations_count=dwell_violations,
    )
    errors.extend(inv_errors)

    # 2. Check traceability metadata
    if not metadata:
        errors.append(f"[{dataset_name}] Missing traceability metadata dictionary.")
    else:
        git_info = metadata.get("git", {})
        if not git_info.get("commit"):
            errors.append(f"[{dataset_name}] Missing Git commit hash in metadata.")
        model_info = metadata.get("model", {})
        if not model_info.get("sha256"):
            errors.append(f"[{dataset_name}] Missing Model SHA256 checksum in metadata.")
        config_info = metadata.get("config", {})
        if not config_info.get("sha256"):
            errors.append(f"[{dataset_name}] Missing Config SHA256 checksum in metadata.")
        source_info = metadata.get("source", {})
        if not source_info.get("sha256"):
            errors.append(f"[{dataset_name}] Missing Source SHA256 checksum in metadata.")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify synthetic benchmark invariant compliance.")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=REPO_ROOT / "data" / "results",
        help="Path to results directory containing benchmark output subdirectories.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Re-run evaluation through SafetyPipeline prior to verification.",
    )
    args = parser.parse_args()

    benchmarks = [
        "sequence_a_clean_incursion",
        "sequence_b_occlusion_coasting",
        "sequence_c_dwell_loitering",
    ]

    print("=" * 76)
    print("🔍 VERIFYING SYNTHETIC BENCHMARK INVARIANTS & TRACEABILITY")
    print("=" * 76)

    if args.run:
        print("[*] Re-running dataset evaluation benchmarks...")
        for seq in benchmarks:
            cfg = DatasetTestConfig(
                source=str(REPO_ROOT / "data" / "samples" / f"{seq}.mp4"),
                config_path=str(REPO_ROOT / "configs" / "datasets" / f"{seq}.yaml"),
                dataset_name=seq,
                output_dir=args.results_dir,
                no_display=True,
                verify_invariants=True,
            )
            runner = DatasetTestRunner(cfg)
            runner.initialize()
            runner.run()

    total_failures = 0
    for seq in benchmarks:
        summary_path = args.results_dir / seq / "summary.json"
        print(f"[*] Checking: {seq} ({summary_path.relative_to(REPO_ROOT)})...")
        errors = check_summary_file(summary_path)
        if errors:
            total_failures += len(errors)
            for err in errors:
                print(f"    ❌ FAIL: {err}")
        else:
            print("    ✅ PASS: Tracks, intrusions, dwell/lockout states, and metadata verified.")

    print("-" * 76)
    if total_failures > 0:
        print(f"[❌] INVARIANT VERIFICATION FAILED with {total_failures} error(s).")
        sys.exit(1)
    else:
        print("[✅] ALL SYNTHETIC BENCHMARK INVARIANTS & TRACEABILITY METADATA VERIFIED.")
        sys.exit(0)


if __name__ == "__main__":
    main()
