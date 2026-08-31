# Proposal: Edge AI Latency Profiler & Dual Reaction Time Architecture

## Intent
Implement a high-resolution Edge AI performance profiler decoupling **$T_{\text{system}}$** (per-frame pipeline execution time: $T_{\text{capture}} + T_{\text{pre}} + T_{\text{infer}} + T_{\text{pose}} + T_{\text{geom}} + T_{\text{track}} + T_{\text{fsm}}$) from **$T_{\text{event}}$** (physical intrusion-to-trip reaction time: $t_{\text{trip}} - t_{\text{physical\_entry}}$) per ISO 13855 / IEC 61496.

```
════════════════════════════════════════════════════════════════════════════════
                        DUAL LATENCY ARCHITECTURE
════════════════════════════════════════════════════════════════════════════════
1. PIPELINE LATENCY: T_system = T_capture + T_pre + T_infer + T_pose + T_geom + T_track + T_fsm
2. EVENT REACTION  : T_event  = (t_trip - t_physical_entry) + T_system
   • Normal Approach (vn < 1.6 m/s) : T_event = (N_confirm - 1) * Δt_frame + T_system
   • Fast Approach   (vn >= 1.6 m/s): T_event = T_system (ISO 13855 instant bypass)
════════════════════════════════════════════════════════════════════════════════
```

## Scope

### In Scope
- **Extended Latency Data Structures (`src/pipeline/safety_pipeline.py`)**: `StageLatencies` with `capture_ms` and `total_system_ms`.
- **Physical Incursion Tracking (`src/core/spatial_fsm.py`)**: Record $t_{\text{entry}}$ upon initial $P_{\text{danger}}$ containment and compute $T_{\text{event}}$ upon `trip = True`.
- **Output & Telemetry Instrumentation (`src/core/spatial_fsm.py`, `scripts/run_demo.py`)**: Expose `event_latency_ms` in `SafetyOutput` and JSONL telemetry.
- **Benchmark Profiler (`src/inference/benchmark.py`, `scripts/benchmark_latency.py`)**: Compute percentile distributions (p50, p95, p99) for both $T_{\text{system}}$ and $T_{\text{event}}$.
- **Formal ADR-010 & Documentation**: Document dual latency metrics in `docs/decisions/adr-010-*.md` and `README.md`.
- **Automated Tests**: Unit and integration test coverage across `tests/`.

### Out of Scope
- Hardware-specific kernel ring buffer driver modifications.

## Capabilities

### Modified Capabilities
- `latency-benchmark`: Add dual distribution profiling ($T_{\text{system}}$ vs $T_{\text{event}}$).
- `spatial-fsm`: Track physical entry timestamp and compute `event_latency_ms`.
- `safety-pipeline`: Propagate capture timestamps and comprehensive stage breakdowns.

### New Capabilities
- None.

## Approach
1. Enhance `TrackSpatialRecord` to track `first_danger_entry_ts`.
2. Compute `event_latency_ms` upon confirming `INSIDE` occupancy or fast-approach bypass.
3. Add `capture_timestamp` support in `SafetyPipeline.process_frame()`.
4. Update CLI demo runner and benchmark scripts to export dual latency profiles.

## Affected Areas

| Area | Impact | Description |
| :--- | :--- | :--- |
| `src/pipeline/safety_pipeline.py` | Modified | Add `capture_ms` and `total_system_ms` to `StageLatencies` |
| `src/core/spatial_fsm.py` | Modified | Add $t_{\text{entry}}$ tracking and `event_latency_ms` to `SafetyOutput` |
| `src/inference/benchmark.py` | Modified | Add dual percentile statistical calculations |
| `scripts/benchmark_latency.py` | Modified | Format dual latency summary table |
| `scripts/run_demo.py` | Modified | Stream `event_latency_ms` in JSONL telemetry |
| `docs/decisions/adr-010-*.md` | New | Document formal ADR-010 |
| `docs/decisions/README.md` | Modified | Index ADR-010 |
| `README.md` | Modified | Update latency formulas |
| `tests/` | Modified | Add unit tests for $T_{\text{system}}$ and $T_{\text{event}}$ |

## Risks

| Risk | Likelihood | Mitigation |
| :--- | :--- | :--- |
| Clock drift across asynchronous capture threads | Low | Use high-resolution monotonic timestamps (`time.perf_counter()`) |

## Rollback Plan
Revert changes with `git checkout` and delete `openspec/changes/edge-ai-latency-profiler/`.

## Success Criteria
- [ ] `StageLatencies` captures $T_{\text{capture}}$, $T_{\text{pre}}$, $T_{\text{infer}}$, $T_{\text{pose}}$, $T_{\text{geom}}$, $T_{\text{track}}$, $T_{\text{fsm}}$, and $T_{\text{system}}$.
- [ ] $T_{\text{event}}$ matches theoretical debounce $(N_{\text{confirm}}-1)\Delta t + T_{\text{system}}$ and instant bypass ($T_{\text{system}}$).
- [ ] JSONL telemetry records `event_latency_ms` on intrusion events.
- [ ] 100% test pass rate across `pytest tests/`.
