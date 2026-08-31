## Exploration: Edge AI Latency Profiler & Dual Reaction Time Architecture

### Current State Analysis

Currently, latency profiling in the codebase measures pipeline execution stages within [`src/pipeline/safety_pipeline.py`](file:///Users/xander/Projects/edge-safety-guard/src/pipeline/safety_pipeline.py) and [`src/inference/benchmark.py`](file:///Users/xander/Projects/edge-safety-guard/src/inference/benchmark.py):
* $T_{\text{pre}}$: Letterbox resizing and symmetrical padding.
* $T_{\text{infer}}$: ONNX Runtime forward inference pass.
* $T_{\text{pose}}$: Keypoint and bounding box tensor parsing.
* $T_{\text{proj}}$: Homography projection to ground plane $(X_w, Y_w)$.
* $T_{\text{track}}$: Kalman filter prediction, greedy assignment, and measurement update.
* $T_{\text{fsm}}$: Containment evaluation and debounce counting.
* $T_1$: Aggregate frame processing latency ($\sum T_i$).

```
CURRENT PROFILING SCOPE:
[ Frame received ] ──► [ Pre ] ──► [ Infer ] ──► [ Pose ] ──► [ Homography ] ──► [ Kalman ] ──► [ FSM ] ──► T1
```

#### The Gap in Industrial Edge AI:
1. **Missing Ingestion / Queue Lag ($T_{\text{capture}}$)**:
   In real-time Edge AI deployments (cameras running over V4L2 / MIPI CSI / RTSP GStreamer), frames sit in OS kernel buffers or driver ring buffers before `process_frame()` consumes them. Ignoring $T_{\text{capture}}$ hides buffer bloat and queue latency.
2. **Conflating Pipeline Throughput with Safety Event Reaction ($T_{\text{event}}$)**:
   A pipeline running at $15\text{ ms}$ per frame ($66\text{ FPS}$) does **not** stop the machine in $15\text{ ms}$. Under ISO 13855 debounce policies ($N_{\text{confirm}} = 3$ frames), the physical intrusion must be sustained across 3 consecutive frames.
   * At 30 FPS ($\Delta t = 33.3\text{ ms}$), physical debounce adds $2 \times 33.3\text{ ms} = 66.7\text{ ms}$.
   * Real event response: $T_{\text{event}} = 66.7\text{ ms} + 15\text{ ms} = \mathbf{81.7\text{ ms}}$.
   * Under ISO 13855 dynamic velocity bypass ($v_n \ge 1.6\text{ m/s}$), debounce is bypassed ($N_{\text{confirm}}=1$), so $T_{\text{event}} = \mathbf{15\text{ ms}}$.

---

### Target Architecture: Dual Latency Metric Model

```
════════════════════════════════════════════════════════════════════════════════
                        DUAL LATENCY TIME HORIZONS
════════════════════════════════════════════════════════════════════════════════

HORIZON 1: FRAME-LEVEL SYSTEM LATENCY (T_system)
┌───────────┐   ┌─────────────────────────────────────────────────────────┐
│ T_capture │ + │ T_pre + T_infer + T_pose + T_geom + T_track + T_fsm     │ = T_system
└───────────┘   └─────────────────────────────────────────────────────────┘
  (Buffer lag)                          (Pipeline T1)

HORIZON 2: SAFETY EVENT REACTION TIME (T_event)
Physical Breach
(t = t_entry)
      │
      ▼
┌──────────────┐     ┌──────────────┐     ┌───────────────────┐
│ Frame 1      │ ──► │ Frame 2      │ ──► │ Frame N_confirm   │ ──► RELAY OPEN (TRIP)
│ (t_entry)    │     │              │     │ (t_trip)          │     (t = t_trip)
└──────────────┘     └──────────────┘     └───────────────────┘
      │                                             ▲
      └────────────────── T_event ──────────────────┘
                 (t_trip - t_entry + T_system)
════════════════════════════════════════════════════════════════════════════════
```

---

### Affected Areas

1. `src/pipeline/safety_pipeline.py`:
   - Extend `StageLatencies` to include `capture_ms` and `total_system_ms`.
   - Support optional `capture_timestamp` in `process_frame()`.
2. `src/core/spatial_fsm.py`:
   - Add `first_danger_entry_ts: Optional[float]` in `TrackSpatialRecord`.
   - Calculate `event_latency_ms` on intrusion escalation (`trip = True`).
   - Expose `event_latency_ms` in `SafetyOutput`.
3. `src/inference/benchmark.py` & `scripts/benchmark_latency.py`:
   - Add dual statistical distribution tracking: $T_{\text{system}}$ percentiles (p50, p95, p99) and $T_{\text{event}}$ percentiles.
4. `scripts/run_demo.py`:
   - Stream `event_latency_ms` in JSONL telemetry.
   - Format dual summary tables in terminal output.
5. `docs/decisions/adr-010-dual-latency-profiling-iso13855.md`:
   - Create formal ADR-010.
6. `README.md`:
   - Document the mathematical formulation of $T_{\text{system}}$ and $T_{\text{event}}$.
7. `tests/`:
   - Update `test_pipeline.py`, `test_fsm.py`, `test_benchmark.py`, and `test_demo_runner.py`.

---

### Comparison of Approaches

| Approach | Description | Pros | Cons | Complexity |
| :--- | :--- | :--- | :--- | :--- |
| **Approach 1: Single Frame Stopwatch**<br>Only measure $T_1$ inside `process_frame`. | Current behavior. | Minimal code. | Completely blind to buffer lag ($T_{\text{capture}}$) and debounce duration ($T_{\text{event}}$). | Low |
| **Approach 2: Dual Time Horizon Profiler (Recommended)**<br>Track $T_{\text{system}}$ per frame + $T_{\text{event}}$ on state machine trip. | Measure both pipeline throughput and physical safety event response. | 100% compliant with ISO 13855 / IEC 61496; captures real-world safety stopping distance $S$; zero overhead. | Requires recording first entry timestamps in track records. | Medium |
| **Approach 3: Distributed Tracing Framework**<br>Integrate OpenTelemetry / Perfetto spans. | Full distributed tracing across microservices. | Industrial enterprise standard. | Excessive external dependencies; unsuitable for self-contained edge Python library. | High |

---

### Recommendation
Implement **Approach 2 (Dual Time Horizon Profiler)**, providing sub-millisecond precision with zero external dependencies.

### Ready for Proposal / Design
Yes. Ready to proceed to `/sdd-propose` and `/sdd-design`.
