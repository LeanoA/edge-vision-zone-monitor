# Feature: Declarative Foveated Far-Field ROI Inference & Mendeley Walkway Delimitation

## Objective
Implement declarative Foveated Far-Field ROI (`far_field_roi`) inference in `SafetyPipeline` alongside the Option B physical floor delimitation for the Mendeley Industrial datasets (`mendeley_walkway_violation` and `mendeley_industrial`), and thoroughly document the architectural decision, optical physics, and execution guide in `ADR-013`, `README.md`, and the study documentation.

## Problem & Why
1. **Zone Delimitation Alignment:** The original `mendeley_walkway_violation.yaml` and `mendeley_industrial.yaml` used a small central polygon ($[2.5, 3.0] \times [7.5, 10.0]\text{ m}$) that missed both the stamping press operators on the left and the grey vehicle lane to the left of the green painted pedestrian walkway. Aligning $X_w = 10.0\text{ m}$ with the inner yellow border of the green walkway restricts the entire hazardous shopfloor to its left ($[0.0, 0.0] \times [9.8, 17.5]\text{ m}$).
2. **Vanishing-Point Spatial Subsampling (ID 5 & Upper-Right Far Corridor Workers):** At $Y_w \in [15, 22]\text{ m}$ (under the *MAMUL DEPO* sign), workers measure $\approx 60\text{ px}$ tall in $1080\text{p}$. Standard letterboxing to $640 \times 360$ ($0.333\times$) compresses them to $\approx 20\text{ px}$ ($< 1.5$ feature cells at stride 16/32), causing YOLO's person score to drop to $\approx 0.149 < 0.40$ *before* `extract_ground_anchor` can apply the `BBOX_BOTTOM` fallback.
3. **Educational Clarity & Cold-Start Usability:** Repository readers need a complete, self-contained guide in `README.md`, `ADR-013`, and `docs/data/datasets.md` explaining both the commands (`run_dataset_test.py` vs `run_demo.py`) and the underlying computer vision / projective geometry trade-offs.

## Authorized Scope & Constraints
- **In Scope:**
  - `configs/datasets/mendeley_walkway_violation.yaml` and `configs/datasets/mendeley_industrial.yaml` (Option B floor calibration + `far_field_roi` declaration).
  - `src/pipeline/safety_pipeline.py`, `scripts/run_dataset_test.py`, and `scripts/run_demo.py` (declarative `far_field_roi` crop inference, coordinate offset mapping back to native $1080\text{p}$ space, and metric world-space deduplication within $0.6\text{ m}$ so full-frame + ROI detections never create duplicate tracks).
  - `tests/test_pipeline.py` and `tests/test_dataset_walkway.py` (unit and integration tests for `far_field_roi` and Mendeley profiles).
  - `docs/decisions/adr-013-foveated-far-field-roi-inference.md`, `docs/decisions/README.md`, `docs/data/datasets.md`, `docs/architecture/preguntas-y-respuestas-arquitectura.md`, `openspec/specs/walkway-dataset-profile/spec.md`, and `README.md`.
- **Constraints:**
  - Preserve $T_1 \le 50\text{ ms}$ ISO 13855 real-time reaction budget.
  - Zero regressions across the existing 218 automated tests.
  - RDD mode: `disabled/unmanaged` (decided by default).
  - TDD / Test Runner: `.venv/bin/pytest` (functional & unit verification per task).
  - Delivery Strategy: `ask-on-risk` (forecast $\approx 320$ authored lines across 2 tasks).

## Actionable Checklist
- [x] **TASK-1:** Implement declarative `far_field_roi` crop inference & metric deduplication in `SafetyPipeline`, wire YAML loading in `run_dataset_test.py` / `run_demo.py`, configure Option B + `far_field_roi` in `mendeley_walkway_violation.yaml` and `mendeley_industrial.yaml`, and add unit tests in `tests/test_pipeline.py` and `tests/test_dataset_walkway.py`. (Commit: `0d3f44b`, 219/219 tests passing)
- [x] **TASK-2:** Re-evaluate `mendeley_walkway_violation` and `mendeley_industrial` datasets, author `ADR-013` (`docs/decisions/adr-013-foveated-far-field-roi-inference.md`), and update `docs/decisions/README.md`, `docs/data/datasets.md`, `docs/architecture/preguntas-y-respuestas-arquitectura.md`, and `README.md`. (Commit: `beb1886`, 219/219 tests passing; `mendeley_walkway_violation`: $T_1 = 30.58\text{ ms}$, $p_{95} = 33.53\text{ ms}$, 7 tracks, 35 `DANGER_INTRUSION`, 182 `LOCKOUT`; `mendeley_industrial`: $T_1 = 30.38\text{ ms}$, $p_{95} = 33.81\text{ ms}$, 10 tracks, 65 `WARNING_APPROACH`, 73 `DANGER_INTRUSION`)

## Acceptance Criteria & Applicable Checks
1. `SafetyPipeline` with `far_field_roi` detects the far-corridor workers in `mendeley_walkway_violation` and ID 5 from frame 1 in `mendeley_industrial` without spawning duplicate tracks when workers cross the ROI boundary. (**VERIFIED**)
2. Mean pipeline latency $T_1$ remains $\le 50\text{ ms}$ ($\le 40\text{ ms}$ target). (**VERIFIED**: $30.38\text{ ms}$ and $30.58\text{ ms}$)
3. All unit and integration tests in `.venv/bin/pytest` pass (100% green). (**VERIFIED**: 219/219 passed)
4. `ADR-013` and `README.md` clearly document the mathematical cause, the 3 architectural alternatives, the foveated ROI solution, and copy-pasteable CLI commands. (**VERIFIED**)

## Progress & Verification Evidence
- Initialized feature branch `feat/foveated-far-field-roi` and ODD task document `odd/tasks/foveated-far-field-roi.md`.
- **TASK-1 Complete (`0d3f44b`):** Added `far_field_roi` crop inference, `deduplicate_detections` (IoU + pixel anchor distance), and metric world-space deduplication ($0.55\text{ m}$) in `SafetyPipeline`; wired YAML loading in `run_dataset_test.py` and `run_demo.py`; updated `mendeley_walkway_violation.yaml` and `mendeley_industrial.yaml` with Option B floor boundaries + `far_field_roi: [1320, 200, 1700, 580]`; verified 219/219 tests passing in `.venv/bin/pytest` (RDD: `disabled/unmanaged`).
- **TASK-2 Complete (`beb1886`):** Re-evaluated `mendeley_walkway_violation` and `mendeley_industrial`, authored `docs/decisions/adr-013-foveated-far-field-roi-inference.md`, and updated `docs/decisions/README.md`, `docs/data/datasets.md`, `docs/architecture/preguntas-y-respuestas-arquitectura.md`, and `README.md` (RDD: `disabled/unmanaged`).
- Next Step: Feature complete; ready for user review / merge decision.
