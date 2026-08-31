# Design: Edge AI Latency Profiler & Dual Reaction Time Architecture

## Technical Approach
Instrument the end-to-end pipeline and safety automaton to profile two orthogonal time horizons:
1. **$T_{\text{system}}$ (Per-Frame Pipeline Latency)**: High-resolution timestamping of each processing stage ($T_{\text{capture}}$, $T_{\text{pre}}$, $T_{\text{infer}}$, $T_{\text{pose}}$, $T_{\text{geom}}$, $T_{\text{track}}$, $T_{\text{fsm}}$, $T_{\text{total}}$).
2. **$T_{\text{event}}$ (Physical Safety Event Reaction Latency)**: Time elapsed from the first physical entry into $P_{\text{danger}}$ ($t_{\text{entry}}$) to safety trip assertion ($t_{\text{trip}}$), exposing the real-world temporal cost of debounce ($N_{\text{confirm}}$) versus ISO 13855 dynamic velocity bypass.

---

## Architecture Decisions

| Decision | Options Considered | Selected Option & Rationale | Tradeoffs |
| :--- | :--- | :--- | :--- |
| **Clock Source** | A: Wall-clock (`time.time()`)<br>B: High-resolution monotonic (`time.perf_counter()`). | **Option B: `time.perf_counter()`.** Immune to NTP time jumps and system clock adjustments; provides sub-microsecond precision. | Timestamps are monotonic offsets, not calendar UTC dates. |
| **Capture Latency Origin** | A: Measure only inside Python pipeline.<br>B: Accept optional external hardware/source timestamp `capture_timestamp`. | **Option B: Optional `capture_timestamp`.** Allows measuring camera driver buffer queue lag when available while degrading gracefully to 0.0 ms if omitted. | Caller must supply capture timestamp if buffer lag profiling is desired. |
| **Event Reaction Tracking** | A: Global stopwatch across frames.<br>B: Per-track `first_danger_entry_ts` recorded in `TrackSpatialRecord`. | **Option B: Per-track `first_danger_entry_ts`.** Supports simultaneous multi-target incursions, isolating individual reaction latency per worker. | Requires 8 bytes extra state per track. |

---

## Data & Latency Flow

```
════════════════════════════════════════════════════════════════════════════════
                        DATA & LATENCY FLOW PIPELINE
════════════════════════════════════════════════════════════════════════════════

[ Camera Capture ] (t_capture)
       │
       ▼ (T_capture = t_start - t_capture)
[ Preprocess (Letterbox) ] (t_pre)
       │
       ▼ (T_infer)
[ YOLO11-Pose ONNX ]
       │
       ▼ (T_pose)
[ Keypoint & Ankle Extraction ]
       │
       ▼ (T_geom)
[ Homography Projection (X,Y) ]
       │
       ▼ (T_track)
[ Kalman Multi-Target Filter ]
       │
       ▼ (T_fsm)
[ Spatial FSM Evaluation ]
       │
       ├──► (If target first breaches P_danger) ──► Record t_entry
       ├──► (If N_confirm reached OR vn >= 1.6m/s) ──► Compute T_event = (now - t_entry)*1000 + T_system
       │
       ▼
[ SafetyOutput & PipelineResult ]
  • StageLatencies (T_capture .. T_fsm, total_t1, total_system)
  • event_latency_ms (if intrusion trip occurred)
       │
       ├──► [ DualVisualizer HUD ]
       └──► [ Telemetry JSONL Stream / Benchmark Summary ]
════════════════════════════════════════════════════════════════════════════════
```

---

## File Changes

| File | Action | Description |
| :--- | :--- | :--- |
| `src/pipeline/safety_pipeline.py` | Modify | Update `StageLatencies` with `capture_ms` and `total_system_ms`; update `process_frame` |
| `src/core/spatial_fsm.py` | Modify | Add `first_danger_entry_ts` to `TrackSpatialRecord` and `event_latency_ms` to `SafetyOutput` |
| `src/inference/benchmark.py` | Modify | Add dual latency distribution calculation (system percentiles vs event reaction) |
| `scripts/benchmark_latency.py` | Modify | Format dual latency benchmark reporting |
| `scripts/run_demo.py` | Modify | Export `event_latency_ms` in JSONL and summary stats |
| `docs/decisions/adr-010-*.md` | Create | Architecture Decision Record for dual latency metrics |
| `docs/decisions/README.md` | Modify | Index ADR-010 |
| `README.md` | Modify | Update latency formulas and ISO 13855 documentation |
| `tests/` | Modify | Update test suites (`test_pipeline.py`, `test_fsm.py`, `test_benchmark.py`, `test_demo_runner.py`) |

---

## Interfaces / Contracts

```python
@dataclass(frozen=True)
class StageLatencies:
    """High-resolution per-stage and total reaction latencies in milliseconds."""
    capture_ms: float
    preprocess_ms: float
    inference_ms: float
    keypoint_extract_ms: float
    projection_ms: float
    tracking_ms: float
    fsm_evaluation_ms: float
    total_t1_ms: float       # Execution time of pipeline stages (preprocess -> fsm)
    total_system_ms: float   # End-to-end time from capture to decision (capture_ms + total_t1_ms)


@dataclass(frozen=True)
class SafetyOutput:
    """Immutable safety decision output emitted on every pipeline frame."""
    trip: bool
    occupancy_state: OccupancyState
    dwell_state: DwellState
    dwell_time_s: float
    warning: bool
    state: SafetyState = SafetyState.SAFE
    violating_tracks: List[int] = field(default_factory=list)
    timestamp: float = 0.0
    message: str = ""
    fault_reason: Optional[str] = None
    lockout_active: bool = False
    event_latency_ms: Optional[float] = None
```

---

## Testing Strategy

| Layer | What to Test | Approach |
| :--- | :--- | :--- |
| **Unit** | `StageLatencies` immutability and fields | Verify dataclass structure and field calculations |
| **Unit** | $T_{\text{event}}$ under debounce ($N_{\text{confirm}} = 3$) | Test that $T_{\text{event}} \approx (N_{\text{confirm}}-1)\Delta t + T_{\text{system}}$ |
| **Unit** | $T_{\text{event}}$ under fast approach ($v_n \ge 1.6\text{ m/s}$) | Test instant bypass where $T_{\text{event}} \approx T_{\text{system}}$ |
| **Integration** | Pipeline & Demo Runner telemetry export | Verify `event_latency_ms` in JSONL stream on intrusion sequences |

---

## Threat Matrix
`N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.`

## Migration / Rollout
Non-breaking addition; defaults `capture_ms = 0.0` and `event_latency_ms = None` for non-trip frames.
