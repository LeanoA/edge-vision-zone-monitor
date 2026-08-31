## Exploration: Decoupling Spatial Occupancy FSM and Temporal Dwell State Classification

### Current State & Root Architectural Defect

In the current implementation ([`src/core/spatial_fsm.py`](file:///Users/xander/Projects/edge-safety-guard/src/core/spatial_fsm.py)), the state machine flattens two orthogonal physical questions into a single enum:
1. **Spatial Occupancy**: *Where is the person relative to the zone geometry, hysteresis bands, and approach trajectory?*
2. **Temporal Dwell Classification**: *How long has the person been inside the zone?*

```
CURRENT CONFLATED TOPOLOGY (Flat State Machine)
─────────────────────────────────────────────────────────────────────────────
[ OUTSIDE ] ──► [ ENTER_PENDING ] ──► [ INTRUSION_ACTIVE ] ──► [ DWELL_WARNING ] ──► [ DWELL_VIOLATION ] ──► [ EXIT_PENDING ]
```

#### Why This is an Anti-Pattern:
- **Conflation of Triggers**: Spatial state transitions are driven by discrete spatial coordinate observations $(X, Y) \in \mathbb{R}^2$ and boundary crossing events. Dwell transitions are driven by continuous time integration $\int dt$ conditioned on being inside.
- **Premature State Interlocking**: A worker in `DWELL_WARNING` is still physically `INTRUDED` / `INSIDE`. Treating `DWELL_WARNING` as a mutually exclusive state from `INTRUSION_ACTIVE` creates ambiguity in downstream safety relays.
- **Coupling of Policies**: Modifying dwell time parameters ($T_{\text{warn}}$, $T_{\text{violation}}$) or adding multi-stage loitering policies unnecessarily risks destabilizing spatial hysteresis debounce loops ($N_{\text{confirm}}, N_{\text{release}}$).

---

### Target Architecture: Orthogonal Statechart Hierarchy

By decomposing the automaton into two parallel orthogonal regions (Statecharts), we establish clean separation of concerns:

```
                            DECOUPLED ORTHOGONAL STATECHART
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ REGION 1: SPATIAL OCCUPANCY AUTOMATON                                                    │
│                                                                                          │
│                  ┌─────────────── [ OUTSIDE ] ◄─────────────────────────┐                │
│                  │                       │                              │                │
│   (Point in      │        (Point in      │                              │ (N_release     │
│    P_danger &    │         P_danger &    │                              │  OBSERVED      │
│    vn >= 1.6m/s) │         vn < 1.6m/s)  ▼                              │  outside       │
│                  │               [ ENTER_PENDING ]                      │  P_release)    │
│                  │                       │                              │                │
│                  │        (danger_count  │                              │                │
│                  │         >= N_confirm) ▼                              │                │
│                  └─────────────────► [ INSIDE ] ────────────────► [ EXIT_PENDING ]       │
│                                      (trip=True)   (Point outside       │                │
│                                                     P_danger)           │                │
└──────────────────────────────────────────┬──────────────────────────────┴────────────────┘
                                           │ (Condition: Occupancy == INSIDE)
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ REGION 2: TEMPORAL DWELL CLASSIFIER                                                      │
│                                                                                          │
│   (Occupancy != INSIDE) ──► [ NONE ] (Timer reset to 0.0s / frozen during coasting)      │
│                                                                                          │
│   [ NORMAL ] ───────(t >= T_warn)───────► [ WARNING ] ───────(t >= T_violation)───────►  │
│  (0 <= t < T_warn)                   (T_warn <= t < T_viol)              [ VIOLATION ]   │
│                                                                          (t >= T_viol)   │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Affected Areas

1. `src/core/spatial_fsm.py`:
   - Introduce `OccupancyState(Enum)`: `OUTSIDE`, `ENTER_PENDING`, `INSIDE`, `EXIT_PENDING`.
   - Introduce `DwellState(Enum)`: `NONE`, `NORMAL`, `WARNING`, `VIOLATION`.
   - Retain supervisory safety flags: `FAULT`, `LOCKOUT`, `MUTED`.
   - Update `SafetyOutput` contract:
     ```python
     @dataclass(frozen=True)
     class SafetyOutput:
         trip: bool
         occupancy_state: OccupancyState
         dwell_state: DwellState
         dwell_time_s: float
         warning: bool
         violating_tracks: List[int]
         timestamp: float
         message: str
         fault_reason: Optional[str] = None
         lockout_active: bool = False
     ```
2. `src/pipeline/safety_pipeline.py`:
   - Propagate decoupled states in `PipelineResult`.
3. `src/utils/visualizer.py`:
   - Render HUD banner with decoupled state readout: `OCCUPANCY: INSIDE | DWELL: WARNING (5.2s) | RELAY: OPEN (TRIPPED)`.
4. `scripts/run_demo.py`:
   - Update JSONL telemetry serialization and summary metrics breakdown.
5. `docs/decisions/adr-009-decoupled-spatial-dwell-statecharts.md`:
   - Create comprehensive Architecture Decision Record.
6. `README.md`:
   - Update FSM documentation and state diagrams.
7. `tests/`:
   - Update `test_fsm.py`, `test_pipeline.py`, `test_visualizer.py`, and `test_demo_runner.py`.

---

### Comparison of Approaches

| Approach | Description | Pros | Cons | Complexity |
| :--- | :--- | :--- | :--- | :--- |
| **Approach 1: Flat Compound Enum**<br>`INSIDE_NORMAL`, `INSIDE_WARNING`, `INSIDE_VIOLATION`, `EXITING_WARNING` | Retain a single flat state enum with compound naming. | Minimal API changes. | Combinatorial state explosion ($4 \times 4 = 16$ states); high coupling; violates Statechart orthogonality. | Low |
| **Approach 2: Pure Orthogonal Decomposition (Recommended)**<br>`OccupancyState` + `DwellState` in `SafetyOutput`. | Separate spatial geometry automaton from temporal dwell accumulator. | 100% clean SoC; independent tuning of spatial and temporal thresholds; ISO 13855 fail-safe trip invariant preserved. | Requires updating test assertions and HUD strings. | Medium |
| **Approach 3: Event-Driven Observer Pattern**<br>`SpatialFSM` emits `ZoneEntered`, `ZoneExited` events to an external `DwellObserver`. | Separate classes entirely connected via pub/sub callbacks. | Extreme decoupling. | Over-engineered for synchronous edge pipeline; complicates determinism and latency profiling. | High |

---

### Recommendation: Approach 2 (Pure Orthogonal Decomposition)
Implement `OccupancyState` and `DwellState` as first-class enums within `src/core/spatial_fsm.py` returned in an immutable `SafetyOutput` dataclass.

### Ready for Proposal / Design
Yes. Proceeding to `/sdd-propose` and `/sdd-design`.
