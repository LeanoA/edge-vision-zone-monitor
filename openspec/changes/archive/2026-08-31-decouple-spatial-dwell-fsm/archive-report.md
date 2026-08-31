# Archive Report: Decoupled Spatial Occupancy FSM and Temporal Dwell Classification

- **Change**: `decouple-spatial-dwell-fsm`
- **Archive Path**: `openspec/changes/archive/2026-08-31-decouple-spatial-dwell-fsm/`
- **Archival Date**: 2026-08-31
- **Status**: COMPLETE

---

## 1. Executive Summary
The flat safety state machine was successfully refactored into two orthogonal Statechart regions:
1. **Spatial Occupancy Automaton (`OccupancyState`)**: Evaluates geometric containment in $P_{\text{danger}}$ and $P_{\text{release}}$ ($\Delta d = 0.20\text{ m}$), approach velocity bypass ($v_n \ge 1.6\text{ m/s}$), and debounce counters ($N_{\text{confirm}}, N_{\text{release}}$).
2. **Temporal Dwell Classifier (`DwellState`)**: Evaluates continuous duration accrued strictly during `INSIDE` occupancy, classifying it into `NONE`, `NORMAL`, `WARNING`, and `VIOLATION`.

The fail-safe invariant was maintained: `trip = True` asserts immediately on verified `INSIDE` ($t=0\text{ s}$).

---

## 2. Canonical Specs Synced
- `openspec/specs/spatial-fsm/spec.md`: Added `Requirement: Orthogonal Spatial and Temporal State Evaluation` and corresponding scenarios.

---

## 3. Architecture Records
- **ADR-009**: Documented in `docs/decisions/adr-009-decoupled-spatial-dwell-statecharts.md` and indexed in `docs/decisions/README.md`.
- **README**: Updated with decoupled Statechart ASCII diagrams and architecture rationale.

---

## 4. Verification & Validation Evidence
- **Task Completeness**: 14/14 tasks complete (100%).
- **PyTest Suite**: 153/153 tests passed in 3.62s.
- **Demo CLI Stream**: Runtime video ingestion verified on synthetic sequence C (`sequence_c_dwell_loitering.mp4`) at 47.5 FPS with JSONL telemetry logging.
- **Mechanical Move Verification**: Verified via `diff -r` with status `DIFF_STATUS=0`.
