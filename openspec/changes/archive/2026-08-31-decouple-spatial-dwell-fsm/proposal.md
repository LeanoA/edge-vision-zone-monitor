# Proposal: Decoupled Spatial Occupancy FSM and Temporal Dwell Classification

## Intent
Decompose the flat safety state machine into two orthogonal Statechart regions: **Spatial Occupancy** (`OUTSIDE`, `ENTER_PENDING`, `INSIDE`, `EXIT_PENDING`) and **Temporal Dwell Classification** (`NONE`, `NORMAL`, `WARNING`, `VIOLATION`), eliminating state conflation and isolating spatial debounce from dwell accumulation.

```
                    ORTHOGONAL DECOUPLED STATECHARTS

┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. SPATIAL OCCUPANCY FSM (Driven by Position (X,Y) & Approach Velocity)     │
│                                                                             │
│               [ OUTSIDE ] ◄─────────────────┐                               │
│                    │                        │                               │
│     (Point inside) │                        │ (N_release observed outside)  │
│                    ▼                        │                               │
│            [ ENTER_PENDING ]                │                               │
│                    │                        │                               │
│ (N_confirm frames  │                        │                               │
│  or vn >= 1.6 m/s) ▼                        │                               │
│               [ INSIDE ] ──────────► [ EXIT_PENDING ]                       │
└────────────────────┬────────────────────────────────────────────────────────┘
                     │ (Condition: Occupancy == INSIDE)
                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. TEMPORAL DWELL CLASSIFIER (Driven by Continuous Time Accumulation)       │
│                                                                             │
│    (Occupancy != INSIDE) ──► [ NONE ] (Timer reset to 0.0s / coast freeze)  │
│                                                                             │
│    [ NORMAL ] ──(t >= T_warn)──► [ WARNING ] ──(t >= T_violation)──► [ VIOLATION ] │
│   (0 <= t < T_warn)            (T_warn <= t < T_viol)           (t >= T_viol)│
└─────────────────────────────────────────────────────────────────────────────┘
```

## Scope

### In Scope
- **Spatial Occupancy Enum (`src/core/spatial_fsm.py`)**: `OccupancyState` (`OUTSIDE`, `ENTER_PENDING`, `INSIDE`, `EXIT_PENDING`).
- **Temporal Dwell Enum (`src/core/spatial_fsm.py`)**: `DwellState` (`NONE`, `NORMAL`, `WARNING`, `VIOLATION`).
- **Safety Output Contract (`src/core/spatial_fsm.py`)**: `SafetyOutput` exposing `occupancy_state`, `dwell_state`, `dwell_time_s`, and `trip`.
- **Downstream Consumer Updates**: `SafetyPipeline`, `DualVisualizer`, and `scripts/run_demo.py`.
- **Documentation & Architecture Record**: `ADR-009` and `README.md` updates.
- **Automated Tests**: Update `tests/test_fsm.py`, `tests/test_pipeline.py`, `tests/test_visualizer.py`, and `tests/test_demo_runner.py`.

### Out of Scope
- Multi-camera distributed spatial fusion.
- Nested multi-zone hierarchies.

## Capabilities

### Modified Capabilities
- `spatial-fsm`: Decompose flat state enum into orthogonal `OccupancyState` and `DwellState`.
- `safety-pipeline`: Propagate decoupled states in `PipelineResult`.
- `dual-visualization`: Render perspective overlays and BEV status banners using decoupled states.

### New Capabilities
- None.

## Approach
1. Define `OccupancyState` and `DwellState` in `src/core/spatial_fsm.py`.
2. Evaluate geometric containment and debounce to determine `OccupancyState`.
3. If `OccupancyState == INSIDE`, evaluate continuous dwell accumulation to determine `DwellState`; otherwise set `DwellState.NONE` and reset timer.
4. Enforce immediate fail-safe trip on confirmed `INSIDE` ($t_{\text{dwell}} = 0\text{ s}$) or `FAULT` / `LOCKOUT`.

## Affected Areas

| Area | Impact | Description |
| :--- | :--- | :--- |
| `src/core/spatial_fsm.py` | Modified | Decouple `OccupancyState` and `DwellState` in FSM logic |
| `docs/decisions/adr-009-*.md` | New | Document formal ADR-009 |
| `docs/decisions/README.md` | Modified | Add ADR-009 to index |
| `src/pipeline/safety_pipeline.py` | Modified | Propagate decoupled states |
| `src/utils/visualizer.py` | Modified | Update HUD banner rendering |
| `scripts/run_demo.py` | Modified | Update JSONL telemetry serialization |
| `README.md` | Modified | Update FSM state diagrams |
| `tests/` | Modified | Update unit and integration test assertions |

## Risks

| Risk | Likelihood | Mitigation |
| :--- | :--- | :--- |
| Test assertion regressions from changed enum names | High | Update test suite systematically across `tests/` |
| Broken telemetry consumers | Low | Provide both `occupancy_state` and `dwell_state` in JSONL records |

## Rollback Plan
Revert changes via `git checkout` and remove `docs/decisions/adr-009-*.md`.

## Success Criteria
- [ ] `OccupancyState` transitions independently: `OUTSIDE` $\leftrightarrow$ `ENTER_PENDING` $\leftrightarrow$ `INSIDE` $\leftrightarrow$ `EXIT_PENDING`.
- [ ] `DwellState` evaluates conditionally: `NONE` $\to$ `NORMAL` $\to$ `WARNING` $\to$ `VIOLATION`.
- [ ] Immediate fail-safe trip asserted on confirmed `INSIDE`.
- [ ] 100% test pass rate across `pytest tests/`.
