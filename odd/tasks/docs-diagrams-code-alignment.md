# Feature: Comprehensive Documentation, Diagrams & Code Alignment

## Objective
Align all repository documentation (`README.md`, `MEDIUM_POST.md`, `docs/**/*.md`), Mermaid/matplotlib architectural diagrams (`scripts/generate_figures.py`), study-guide generators (`scripts/build_master_study_guide.py`, `scripts/generate_study_pdf.py`), and telemetry/visualizer attribute contracts (`src/utils/visualizer.py`, `scripts/run_demo.py`, `scripts/run_dataset_test.py`) with the actual source code in `src/`, `configs/`, and `scripts/`.

## Problem & Why
1. **Latent Telemetry & Visualizer Attribute Bugs:**
   - `SafetyVisualizer.draw_bev` (`src/utils/visualizer.py:415`) checks `hasattr(track, "anchor_source")`, whereas `Track` (`src/core/kalman_filter.py:535`) exposes `track.source`, leaving the BEV anchor tag (`[ANK]`, `[BBX]`, `[PRD]`) always blank.
   - `scripts/run_demo.py:341` and `scripts/run_dataset_test.py:301` read `t.dwell_time_s` on `Track`, whereas per-track dwell timers live inside `SpatialFSM._track_records[tid].dwell_time_s`, causing `dwell_s` in `events.jsonl` to always be `0.0`.
2. **Diagram & Mathematical Constant Drift:**
   - Multiple docs and diagrams (`README.md`, `MEDIUM_POST.md`, `docs/architecture/engineering-case-study.md`, `docs/guia-estudio-arquitectura.md`, `scripts/generate_figures.py`) state $\kappa(H) < 10^6$ (or $10^5$), whereas `HomographyProjector.compute_homography` (`src/core/homography.py:321`) and `ADR-005` enforce $\kappa(H) < 10^{12}$.
   - Mermaid flowcharts in `README.md`, `MEDIUM_POST.md`, and `docs/architecture/engineering-case-study.md` reverse the order of Kalman prediction, Mahalanobis gating ($\chi^2_2 \le 9.210$), and Hungarian assignment (`linear_sum_assignment`), and omit the Foveated Far-Field ROI (`far_field_roi`) + 2D/metric deduplication pipeline stages.
   - `docs/architecture/industrial-edge-ai-specification.md` still renders the legacy pre-ADR-009 linear 6-state FSM diagram (`INTRUSION_ACTIVE`, `DWELL_WARNING`, `DWELL_VIOLATION`) instead of the orthogonal `OccupancyState` $\times$ `DwellState` statecharts.
3. **Contract, Dataset, CLI & Benchmark Drift:**
   - `AnchorSource` enum values (`"ANKLES_DUAL"`, `"ANKLE_SINGLE"`, `"BBOX_BOTTOM"`, `"TRACKER_PREDICTED"`) and per-frame fallback hierarchy (Tiers 1–3 in `extract_ground_anchor`, Tier 4 coasting in `MultiTargetKalmanTracker`) are written in lowercase and with Tiers 3 & 4 swapped across `README.md`, `ADR-007`, `docs/data/datasets.md`, and `docs/architecture/preguntas-y-respuestas-arquitectura.md`; `docs/architecture/safety-directives-iso13855.md` still claims `BBOX_BOTTOM` is prohibited and that ankle `conf_threshold` is `0.3` (actual default is `0.5`).
   - Synthetic dataset geometry in `README.md` and `docs/data/datasets.md` claims a $6\text{m} \times 6\text{m}$ cell, $[2.0, 2.0] \times [4.0, 4.0]\text{ m}$ danger zone, and $7.0\text{ s}$ stop, whereas `configs/default_config.yaml`, `sequence_{a,b,c}.yaml`, and `src/utils/synthetic_generator.py` implement a $4\text{m} \times 6\text{m}$ cell, $[1.0, 2.0] \times [3.0, 4.0]\text{ m}$ danger zone, `dwell_warning_s=2.0`, `dwell_violation_s=5.0`, and $6.0\text{ s}$ stop at $1920 \times 1080$ (not $1280 \times 720$).
   - `README.md` references non-existent `src/inference/benchmark.py` (actual: `scripts/benchmark.py`), `Y > 8 m` (actual: `Y_w > 6 m`), `python scripts/audit_and_reproduce_benchmarks.py --all` (no `--all` flag unless supported by `argparse`), and an incomplete repository tree.
   - `ADR-013`, updated benchmark numbers from `docs/benchmarks/*.json`, and accurate `src/` production code snippets are missing or stale in `docs/benchmarks/experiments-plan.md`, `MEDIUM_POST.md`, `docs/architecture/engineering-case-study.md`, `docs/guia-estudio-arquitectura.md`, `scripts/build_master_study_guide.py`, and `scripts/generate_study_pdf.py`.

## Authorized Scope & Constraints
- **In Scope:**
  - `src/utils/visualizer.py`, `src/core/spatial_fsm.py`, `scripts/run_demo.py`, `scripts/run_dataset_test.py`, `scripts/audit_and_reproduce_benchmarks.py`, and `tests/` (fixing `track.source` BEV tag, per-track `dwell_s` telemetry exposure, and optional `--all` CLI flag compatibility).
  - `README.md`, `MEDIUM_POST.md`, `docs/architecture/*.md`, `docs/decisions/adr-007-occlusion-handling-confidence-propagation.md`, `docs/data/datasets.md`, `docs/benchmarks/experiments-plan.md`.
  - `scripts/generate_figures.py`, `scripts/build_master_study_guide.py`, `scripts/generate_study_pdf.py`, `docs/figures/pipeline_flow.png`, and `docs/guia-estudio-arquitectura.{md,typ,pdf}`.
- **Constraints:**
  - Maintain 100% test pass rate in `.venv/bin/pytest`.
  - RDD mode: `disabled/unmanaged` (decided by default).
  - TDD / Test Runner: `.venv/bin/pytest` (unit and integration checks per task).
  - Delivery Strategy: `ask-on-risk` (forecast $\approx 380$ authored lines across 3 tasks).

## Actionable Checklist
- [x] **TASK-1:** Fix code-to-telemetry/visualizer attribute mismatches (`track.source` in `src/utils/visualizer.py`, per-track `dwell_time_s` lookup via `SpatialFSM.get_track_dwell_time(track_id)` in `scripts/run_demo.py` and `scripts/run_dataset_test.py`, and `--all` flag support in `scripts/audit_and_reproduce_benchmarks.py`) with unit test coverage in `tests/test_visualizer.py` and `tests/test_fsm.py`. (Commit: `6ca8ed2`, 221/221 tests passing)
- [x] **TASK-2:** Align `README.md`, `MEDIUM_POST.md`, `docs/architecture/{engineering-case-study,industrial-edge-ai-specification,preguntas-y-respuestas-arquitectura,safety-directives-iso13855}.md`, `docs/decisions/adr-007-occlusion-handling-confidence-propagation.md`, `docs/data/datasets.md`, and `docs/benchmarks/experiments-plan.md` (Mermaid diagrams, $\kappa(H) < 10^{12}$, Kalman/Mahalanobis/Hungarian ordering, Foveated ROI branch, orthogonal statecharts, `AnchorSource` tiers, synthetic $4\text{m}\times 6\text{m}$ geometry & $1920\times 1080$ resolution, repository tree, ADR-013 index, and benchmark JSON sync). (Commit: `ee19286`, 221/221 tests passing)
- [x] **TASK-3:** Synchronize `scripts/generate_figures.py`, `scripts/build_master_study_guide.py`, and `scripts/generate_study_pdf.py` with actual `src/` production signatures, $\kappa(H) < 10^{12}$, Foveated ROI stage, and ADR-013, and regenerate `docs/figures/pipeline_flow.png` and `docs/guia-estudio-arquitectura.{md,typ,pdf}`. (Commit: `cb93de7`, 221/221 tests passing)

## Acceptance Criteria & Applicable Checks
1. `SafetyVisualizer.draw_bev` renders `[ANK]`, `[BBX]`, and `[PRD]` tags from `track.source`, and `run_demo.py` / `run_dataset_test.py` emit accurate per-track `dwell_s` values in telemetry JSONL. (**VERIFIED**)
2. Every Mermaid diagram, mathematical threshold ($\kappa(H) < 10^{12}$, $Y_w > 6\text{ m}$, `conf_threshold=0.5`), `AnchorSource` tier table, synthetic dataset dimension ($4\text{m}\times 6\text{m}$, $1920\times 1080$), ADR index (13 ADRs), and benchmark table across `README.md`, `MEDIUM_POST.md`, and `docs/` matches the codebase and `docs/benchmarks/*.json`. (**VERIFIED**)
3. `scripts/generate_figures.py`, `scripts/build_master_study_guide.py`, and `scripts/generate_study_pdf.py` execute cleanly and regenerate `docs/figures/pipeline_flow.png` and `docs/guia-estudio-arquitectura.{md,typ,pdf}` with faithful production snippets. (**VERIFIED**)
4. All automated tests in `.venv/bin/pytest` pass (100% green). (**VERIFIED**: 221/221 passed)

## Progress & Verification Evidence
- Initialized ODD task document `odd/tasks/docs-diagrams-code-alignment.md` on branch `docs/architecture-diagrams-code-alignment`.
- **TASK-1 Complete (`6ca8ed2`):** Fixed `track.source` lookup in `DualVisualizer.render_bev`, added `SpatialFSM.get_track_dwell_time(track_id)` and wired it in `run_demo.py` and `run_dataset_test.py`, added `--all` CLI flag compatibility in `scripts/audit_and_reproduce_benchmarks.py`, and verified 221/221 tests passing in `.venv/bin/pytest` (RDD: `disabled/unmanaged`).
- **TASK-2 Complete (`ee19286`):** Aligned `README.md`, `MEDIUM_POST.md`, `docs/architecture/{engineering-case-study,industrial-edge-ai-specification,preguntas-y-respuestas-arquitectura,safety-directives-iso13855}.md`, `docs/decisions/adr-007-occlusion-handling-confidence-propagation.md`, `docs/data/datasets.md`, and `docs/benchmarks/experiments-plan.md` with codebase constants, Mermaid diagrams, `AnchorSource` tiers, synthetic $4\text{m}\times 6\text{m}$ ($1920\times 1080$) geometry, ADR-013 index, and JSON benchmark artifacts (RDD: `disabled/unmanaged`).
- **TASK-3 Complete (`cb93de7`):** Synchronized `scripts/generate_figures.py`, `scripts/build_master_study_guide.py`, and `scripts/generate_study_pdf.py` with actual `src/` production signatures, $\kappa(H) < 10^{12}$, Foveated ROI stage, and ADR-013; regenerated `docs/figures/pipeline_flow.png`, `docs/guia-estudio-arquitectura.{md,typ,pdf}`, `docs/guia-estudio-arquitectura-compendio.pdf`, and `docs/architecture-study-guide.pdf`; verified 221/221 tests passing in `.venv/bin/pytest` (RDD: `disabled/unmanaged`).
- Next Step: Ready for user review / merge into `main`.
