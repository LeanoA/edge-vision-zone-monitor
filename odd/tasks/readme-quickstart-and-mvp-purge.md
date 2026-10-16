# Feature: Architectural Reference Implementation, Quickstart & MVP Purge

## Objective
Reposition the project terminology from "MVP/PoC" to "Architectural Reference Implementation / Industrial Engineering Prototype", eliminate all legacy "MVP" occurrences from documentation and compiled study guides, and restructure `README.md` with an immediate 3-minute Quickstart and an explicit dataset taxonomy (Primary Ground Truth vs Empirical Benchmarks vs Future Research Roadmap).

## Problem & Root Cause
1. In industrial machinery safety (ISO 13849 / IEC 61496), calling a safety vision pipeline an "MVP" is an anti-pattern: functional safety is binary (either certified or not), and uncertified software cannot be deployed as a trip device. The term "MVP" generates distrust among Plant Directors and Principal Architects.
2. The current `README.md` suffered from documentary sprawl: 400 lines of theory, statecharts, and ADR tables preceded the execution instructions, and the execution instructions missed the prerequisite ONNX export step (`models/export_onnx.py`), causing a `FileNotFoundError` on fresh clones.
3. The dataset catalog mixed synthetic ground truth, public CCTV benchmarks, and 4 TB robotic cell candidates without a clear hierarchy, confusing readers regarding which dataset validates the current pipeline versus what constitutes the future research roadmap.

## Scope & Constraints
- Documentation: `README.md`, `docs/architecture/industrial-edge-ai-specification.md`, `docs/architecture/preguntas-y-respuestas-arquitectura.md`, `openspec/changes/archive/2026-08-31-demo-orchestrator-cli/exploration.md`.
- PDF Deliverables: Recompiled `docs/guia-estudio-arquitectura-compendio.pdf`, `docs/guia-estudio-arquitectura.pdf`, and `docs/architecture-study-guide.pdf`.
- Constraints: Zero regressions in test suite (218 passing tests); zero remaining occurrences of `\bmvp\b` in user-facing documentation; ensure reproducible zero-to-working-demo flow.

## Tasks
- [x] TASK-1: Purge "MVP" terminology across documentation and architecture markdown files
- [x] TASK-2: Recompile master study guide PDF and Typst sources via `scripts/build_master_study_guide.py`
- [x] TASK-3: Restructure `README.md` with 3-minute Quickstart, Reference Implementation framing, and clear Dataset Taxonomy
- [x] TASK-4: Execute full test suite and verify reproducible demo pipeline

## Verification Evidence
- Zero `\bmvp\b` occurrences across all tracked Markdown files and Typst sources (`git grep -in "\bmvp\b"` returned 0 matches).
- Rebuilt master study guide compendium PDF (`docs/guia-estudio-arquitectura-compendio.pdf`, 1876 KB) and 8-page decks (`docs/guia-estudio-arquitectura.pdf`, `docs/architecture-study-guide.pdf`).
- Restructured `README.md` with:
  1. Positioning: "Architectural Reference Implementation & Industrial Engineering Prototype".
  2. ⚡ 3-Minute Quickstart placed directly below the header/pitch with full clone-to-demo instructions (including `python models/export_onnx.py`).
  3. 3-Tier Dataset Taxonomy: Tier 1 (Deterministic synthetic ground-truth workcells for millimetric ISO 13855 audit), Tier 2 (Empirical CCTV factory benchmarks via automated downloader), Tier 3 (Future research roadmap: InHARD HRC cobot SSM, HA4M 3D point cloud multi-modality, CPPE-5 heavy PPE boots).
- Test Suite: 218/218 passing in 16.15s (`./.venv/bin/pytest tests/`).
- Commit: `886917f` (`docs/reference-impl-quickstart-and-mvp-purge`)

## Next Step
Work unit complete; awaiting user instructions for merge or push.
