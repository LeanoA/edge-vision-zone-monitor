# Design: Decoupled Spatial Occupancy FSM and Temporal Dwell Classification

## Technical Approach
Decompose the flat `SafetyState` machine into two orthogonal Statechart components:
1. **`OccupancyState` Automaton**: Evaluates point-in-polygon containment, spatial boundary hysteresis ($\Delta d = 0.20\text{ m}$), approach velocity bypass ($v_n \ge 1.6\text{ m/s}$), and debounce confirmation counters ($N_{\text{confirm}}, N_{\text{release}}$).
2. **`DwellState` Classifier**: Evaluates continuous duration $t_{\text{dwell}}$ accrued exclusively while a track is in the `INSIDE` state, classifying it into `NONE`, `NORMAL`, `WARNING`, or `VIOLATION`.

---

## Architecture Decisions

| Decision | Options Considered | Selected Option & Rationale | Tradeoffs |
| :--- | :--- | :--- | :--- |
| **State Representation** | A: Flat compound enum (`INSIDE_NORMAL`, `INSIDE_WARNING`, etc.)<br>B: Decoupled orthogonal enums (`OccupancyState` $\times$ `DwellState`). | **Option B: Decoupled orthogonal enums.** Adheres to Harel Statechart orthogonal regions; prevents state explosion; isolates spatial debounce from temporal timers. | Downstream callers inspect two fields (`occupancy_state`, `dwell_state`) instead of one flat string. |
| **Dwell Trigger Condition** | A: Dwell accumulates in both `WARNING` perimeter and `INSIDE`.<br>B: Dwell accumulates strictly during confirmed `INSIDE` occupancy. | **Option B: Dwell strictly in `INSIDE`.** A worker in the warning perimeter is approaching; dwell time represents duration of unauthorized presence inside the hazardous zone. | Pre-warning approach is signaled by `ENTER_PENDING` or `warning=True` rather than dwell timer. |
| **Fail-Safe Trip Invariant** | A: Trip conditioned on dwell reaching violation.<br>B: Immediate trip on `INSIDE` ($t_{\text{dwell}} = 0.0\text{ s}$). | **Option B: Immediate fail-safe trip on `INSIDE`.** ISO 13855 / ISO 13849-1 mandatory requirement: contactor opens at instant of verified physical zone breach; dwell classifies operational severity. | Zero delay in machine shutdown. |
| **Supervisory State Handling** | A: Embed `FAULT`/`LOCKOUT` in `OccupancyState`.<br>B: Expose supervisory flags (`fault_active`, `lockout_active`) alongside occupancy. | **Option B: Explicit supervisory properties.** Allows distinguishing geometric occupancy (e.g. person left) while keeping safety latch (`LOCKOUT`) active until manual supervisor reset. | Clean separation between spatial physics and electrical interlocks. |

---

## Data & Decision Flow

```
                      END-TO-END DATA & DECISION FLOW

[ Track Positions (X, Y) & Velocities (vx, vy) ]
                         │
                         ▼
          ┌─────────────────────────────┐
          │ Shapely Prepared Geometries │
          │ (P_danger, P_release)       │
          └──────────────┬──────────────┘
                         │ (in_danger, in_release)
                         ▼
          ┌─────────────────────────────┐
          │ Spatial Debounce & Velocity │
          │ Bypass Evaluator            │
          └──────────────┬──────────────┘
                         │
                         ▼
        ┌───────────────────────────────────┐
        │  Region 1: OccupancyState         │
        │  • OUTSIDE                        │
        │  • ENTER_PENDING (0 < n < N_conf) │
        │  • INSIDE (n >= N_conf / vn bypass│
        │  • EXIT_PENDING (0 < c < N_rel)   │
        └────────────────┬──────────────────┘
                         │
                         ├── (If INSIDE) ──┐
                         │                 ▼
                         │  ┌───────────────────────────────────┐
                         │  │  Region 2: DwellState             │
                         │  │  • NONE (t = 0.0s)                │
                         │  │  • NORMAL (0 <= t < T_warn)       │
                         │  │  • WARNING (T_warn <= t < T_viol) │
                         │  │  • VIOLATION (t >= T_viol)        │
                         │  └──────────────┬────────────────────┘
                         │                 │
                         ▼                 ▼
          ┌─────────────────────────────────────────────────────┐
          │  SafetyOutput Aggregator                            │
          │  • trip: bool (True if INSIDE / FAULT / LOCKOUT)    │
          │  • occupancy_state: OccupancyState                  │
          │  • dwell_state: DwellState                          │
          │  • dwell_time_s: float                              │
          │  • warning: bool                                    │
          │  • violating_tracks: List[int]                      │
          └────────────────────────┬────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
        [ DualVisualizer HUD ]        [ Safety Relays / JSONL ]
```

---

## File Changes

| File | Action | Description |
| :--- | :--- | :--- |
| `src/core/spatial_fsm.py` | Modify | Define `OccupancyState`, `DwellState`, and refactor `SpatialFSM.update()` |
| `docs/decisions/adr-009-decoupled-spatial-dwell-statecharts.md` | Create | Formal Architecture Decision Record with statechart diagrams |
| `docs/decisions/README.md` | Modify | Index ADR-009 |
| `src/pipeline/safety_pipeline.py` | Modify | Update `PipelineResult` to consume decoupled states |
| `src/utils/visualizer.py` | Modify | Update HUD banner and overlay text formatting |
| `scripts/run_demo.py` | Modify | Update telemetry JSONL serialization and summary formatting |
| `README.md` | Modify | Update state machine documentation and diagrams |
| `tests/test_fsm.py` | Modify | Update unit test suite for orthogonal states |
| `tests/test_pipeline.py` | Modify | Update pipeline integration tests |
| `tests/test_visualizer.py` | Modify | Update visualizer unit tests |
| `tests/test_demo_runner.py` | Modify | Update demo runner integration tests |

---

## Interfaces / Contracts

```python
class OccupancyState(str, Enum):
    """Discrete spatial occupancy states relative to safeguarded zone geometry."""
    OUTSIDE = "OUTSIDE"
    ENTER_PENDING = "ENTER_PENDING"
    INSIDE = "INSIDE"
    EXIT_PENDING = "EXIT_PENDING"


class DwellState(str, Enum):
    """Discrete temporal duration classifications for confirmed occupants."""
    NONE = "NONE"
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    VIOLATION = "VIOLATION"


@dataclass(frozen=True)
class SafetyOutput:
    """Immutable safety decision output emitted on every pipeline frame."""
    trip: bool
    occupancy_state: OccupancyState
    dwell_state: DwellState
    dwell_time_s: float
    warning: bool
    violating_tracks: List[int] = field(default_factory=list)
    timestamp: float = 0.0
    message: str = ""
    fault_reason: Optional[str] = None
    lockout_active: bool = False
```

---

## Testing Strategy

| Layer | What to Test | Approach |
| :--- | :--- | :--- |
| **Unit** | `OccupancyState` transitions | Test pure spatial paths: enter pending debounce, fast approach bypass, exit hysteresis |
| **Unit** | `DwellState` transitions | Test time progressions ($t=0 \to \text{NORMAL} \to \text{WARNING} \to \text{VIOLATION}$) strictly while `INSIDE` |
| **Unit** | Coasting dwell freeze | Verify dwell timer freezes during `PREDICTED`/`STALE` unobserved frames |
| **Integration** | Pipeline & Visualizer propagation | Verify `SafetyPipeline.process_frame()` and `DualVisualizer.render()` propagate decoupled states |
| **Integration** | Demo CLI telemetry | Verify JSONL export records both `occupancy_state` and `dwell_state` |

---

## Threat Matrix
`N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.`

## Migration / Rollout
Non-breaking internal refactor; test fixtures and consumers updated synchronously.

## Open Questions
None.
