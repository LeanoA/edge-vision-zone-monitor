# Tasks: Decoupled Spatial Occupancy FSM and Temporal Dwell Classification

## Review Workload Forecast

| Field | Value |
| :--- | :--- |
| Estimated changed lines | ~350 lines |
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
| 1 | Decouple FSM into OccupancyState and DwellState | PR 1 | `pytest tests/test_fsm.py` | `python scripts/run_demo.py --source data/samples/sequence_c_dwell_loitering.mp4 --no-display` | `src/core/spatial_fsm.py`, `tests/test_fsm.py` |

---

## Phase 1: Core Automaton & Output Contracts (`src/core/spatial_fsm.py`)

- [x] 1.1 Define `OccupancyState` enum (`OUTSIDE`, `ENTER_PENDING`, `INSIDE`, `EXIT_PENDING`) and `DwellState` enum (`NONE`, `NORMAL`, `WARNING`, `VIOLATION`).
- [x] 1.2 Refactor `SafetyOutput` dataclass to expose `occupancy_state`, `dwell_state`, `dwell_time_s`, `trip`, `warning`, `fault_reason`, and `lockout_active`.
- [x] 1.3 Refactor `SpatialFSM.update()` to evaluate `OccupancyState` first, and conditionally evaluate `DwellState` exclusively when `OccupancyState == INSIDE`.
- [x] 1.4 Maintain supervisory safety flags (`FAULT`, `LOCKOUT`, `MUTED`) with immediate fail-safe trip assertions.

## Phase 2: Downstream Consumer Alignment

- [x] 2.1 Update `SafetyPipeline.process_frame()` in `src/pipeline/safety_pipeline.py` to propagate decoupled states in `PipelineResult`.
- [x] 2.2 Update `DualVisualizer.render_perspective()` and `render_bev()` in `src/utils/visualizer.py` to render decoupled status banner strings.
- [x] 2.3 Update `scripts/run_demo.py` JSONL telemetry logger and `DemoSummary` terminal formatting to record both `occupancy_state` and `dwell_state`.

## Phase 3: Architecture Decision Record & Documentation

- [x] 3.1 Create formal `docs/decisions/adr-009-decoupled-spatial-dwell-statecharts.md` documenting orthogonal Statechart decomposition, mathematical formulations, and ASCII diagrams.
- [x] 3.2 Update `docs/decisions/README.md` indexing ADR-009.
- [x] 3.3 Update `README.md` with decoupled statechart diagrams, description of orthogonal regions, and updated FSM examples.

## Phase 4: Test Suite Updates & Verification

- [x] 4.1 Update `tests/test_fsm.py` with comprehensive unit tests for `OccupancyState` and `DwellState` transitions.
- [x] 4.2 Update `tests/test_pipeline.py` to assert decoupled safety output fields.
- [x] 4.3 Update `tests/test_visualizer.py` and `tests/test_demo_runner.py` for new state signatures.
- [x] 4.4 Run full test suite (`pytest tests/`) ensuring 100% pass rate.
