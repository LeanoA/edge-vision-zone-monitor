# Tasks: Edge AI Latency Profiler & Dual Reaction Time Architecture

## Review Workload Forecast

| Field | Value |
| :--- | :--- |
| Estimated changed lines | ~320 lines |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Implement dual latency profiling (T_system and T_event) | PR 1 | `pytest tests/test_benchmark.py tests/test_fsm.py` | `python scripts/run_demo.py --source data/samples/sequence_a_clean_incursion.mp4 --no-display` | `src/pipeline/safety_pipeline.py`, `src/core/spatial_fsm.py` |

---

## Phase 1: Core Structures & Event Tracking

- [x] 1.1 Extend `StageLatencies` in `src/pipeline/safety_pipeline.py` with `capture_ms` and `total_system_ms`, updating `process_frame()` to accept optional `capture_timestamp`.
- [x] 1.2 Add `first_danger_entry_ts` to `TrackSpatialRecord` in `src/core/spatial_fsm.py`.
- [x] 1.3 Add `event_latency_ms` to `SafetyOutput` and compute elapsed physical reaction time upon intrusion confirmation (`trip = True`).

## Phase 2: Benchmark Profiler & CLI Telemetry

- [x] 2.1 Update `src/inference/benchmark.py` and `scripts/benchmark_latency.py` to calculate percentiles (mean, p50, p95, p99) for both $T_{\text{system}}$ and $T_{\text{event}}$.
- [x] 2.2 Update `scripts/run_demo.py` to stream `event_latency_ms` in JSONL telemetry and include dual latency distributions in `DemoSummary`.

## Phase 3: Architecture Decision Record & Documentation

- [x] 3.1 Create formal `docs/decisions/adr-010-dual-latency-profiling-iso13855.md` documenting dual time horizons, formulas, and ASCII diagrams.
- [x] 3.2 Index ADR-010 in `docs/decisions/README.md`.
- [x] 3.3 Update `README.md` with dual latency formulas ($T_{\text{system}}$ vs $T_{\text{event}}$) and profiler documentation.

## Phase 4: Test Suite Updates & Verification

- [x] 4.1 Update `tests/test_pipeline.py` to test `StageLatencies` extended fields and capture timestamp profiling.
- [x] 4.2 Update `tests/test_fsm.py` to verify $T_{\text{event}}$ calculation under debounce ($N_{\text{confirm}}$) and fast-approach bypass ($v_n \ge 1.6\text{ m/s}$).
- [x] 4.3 Update `tests/test_benchmark.py` and `tests/test_demo_runner.py` to assert dual latency metrics.
- [x] 4.4 Run full test suite (`pytest tests/`) ensuring 100% pass rate.
