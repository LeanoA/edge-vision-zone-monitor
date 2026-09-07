"""
src/utils/benchmark_verifier.py
Benchmark and Ground-Truth Invariant Verifier for Vision Safety Pipeline.
Validates that synthetic benchmark sequences adhere strictly to safety specifications:
- Sequence A (Clean Incursion): Must observe >= 1 track, >= 1 danger intrusion event.
- Sequence B (Occlusion Coasting): Must observe >= 1 track, >= 1 danger intrusion, >= 1 lockout event.
- Sequence C (Dwell Loitering): Must observe >= 1 track, >= 1 danger intrusion, >= 1 dwell violation.
"""

from typing import Dict, List


class BenchmarkInvariantError(AssertionError):
    """Raised when a benchmark video sequence violates expected ground-truth safety invariants."""
    pass


def verify_benchmark_summary_invariants(
    dataset_name: str,
    total_tracks: int,
    state_counts: Dict[str, int],
    danger_events_count: int,
    dwell_violations_count: int,
) -> List[str]:
    """
    Verify that the execution summary of a benchmark sequence satisfies safety invariants.
    Returns a list of violation messages. If empty, all invariants passed.
    """
    violations: List[str] = []
    name = dataset_name.lower()

    if "sequence_a" in name or "clean_incursion" in name:
        if total_tracks < 1:
            violations.append(
                f"[{dataset_name}] Invariant Failure: Expected >= 1 track, but observed {total_tracks} tracks."
            )
        if danger_events_count < 1 and state_counts.get("DANGER_INTRUSION", 0) < 1:
            violations.append(
                f"[{dataset_name}] Invariant Failure: Expected incursion (DANGER_INTRUSION), "
                f"but observed 0 danger events (state_counts: {state_counts})."
            )

    elif "sequence_b" in name or "occlusion" in name:
        if total_tracks < 1:
            violations.append(
                f"[{dataset_name}] Invariant Failure: Expected >= 1 track, but observed {total_tracks} tracks."
            )
        if danger_events_count < 1 and state_counts.get("DANGER_INTRUSION", 0) < 1:
            violations.append(
                f"[{dataset_name}] Invariant Failure: Expected incursion (DANGER_INTRUSION), "
                f"but observed 0 danger events (state_counts: {state_counts})."
            )
        if state_counts.get("LOCKOUT", 0) < 1:
            violations.append(
                f"[{dataset_name}] Invariant Failure: Expected fail-safe LOCKOUT latch after occlusion "
                f"disappearance inside hazard zone, but observed 0 LOCKOUT frames (state_counts: {state_counts})."
            )

    elif "sequence_c" in name or "dwell" in name:
        if total_tracks < 1:
            violations.append(
                f"[{dataset_name}] Invariant Failure: Expected >= 1 track, but observed {total_tracks} tracks."
            )
        if danger_events_count < 1 and state_counts.get("DANGER_INTRUSION", 0) < 1:
            violations.append(
                f"[{dataset_name}] Invariant Failure: Expected incursion (DANGER_INTRUSION), "
                f"but observed 0 danger events (state_counts: {state_counts})."
            )
        if dwell_violations_count < 1:
            violations.append(
                f"[{dataset_name}] Invariant Failure: Expected dwell violation (dwell_violations_count >= 1), "
                f"but observed {dwell_violations_count} dwell violations (state_counts: {state_counts})."
            )

    return violations


def assert_benchmark_invariants(
    dataset_name: str,
    total_tracks: int,
    state_counts: Dict[str, int],
    danger_events_count: int,
    dwell_violations_count: int,
) -> None:
    """
    Assert that the execution summary of a benchmark sequence satisfies safety invariants.
    Raises BenchmarkInvariantError if any invariant fails.
    """
    violations = verify_benchmark_summary_invariants(
        dataset_name,
        total_tracks,
        state_counts,
        danger_events_count,
        dwell_violations_count,
    )
    if violations:
        raise BenchmarkInvariantError("\n".join(violations))
