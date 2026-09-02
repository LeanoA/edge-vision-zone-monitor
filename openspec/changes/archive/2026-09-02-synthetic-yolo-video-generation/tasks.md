# Tasks: Synthetic YOLO Video Generation

## Phase 1: Asset Preparation & Extraction
- [x] 1.1 Create `data/assets/sprites/worker/` directory structure.
- [x] 1.2 Prepare high-contrast, photorealistic RGBA walking and idle worker sprite assets with clean alpha channels.
- [x] 1.3 Verify asset integrity, alpha transparency, and dimensions.

## Phase 2: Synthetic Generator Implementation
- [x] 2.1 Update `src/utils/synthetic_generator.py` to add sprite loading, caching, and fallback handling.
- [x] 2.2 Implement perspective-scaled RGBA alpha blending method `render_worker_sprite()`.
- [x] 2.3 Implement soft Gaussian contact shadow rendering.
- [x] 2.4 Update `generate_sequence_a()`, `generate_sequence_b()`, and `generate_sequence_c()` to use sprite-based rendering and depth-ordered occlusion.

## Phase 3: CLI & Tooling Updates
- [x] 3.1 Update `scripts/generate_samples.py` with support for sprite paths and enhanced logging.
- [x] 3.2 Regenerate benchmark videos in `data/samples/`.

## Phase 4: Testing & Verification
- [x] 4.1 Create `tests/test_synthetic_generator.py` testing sprite loading, alpha blending, shadow rendering, and trajectory bounds.
- [x] 4.2 Test YOLO11 detection confidence on generated sample frames (achieved 100% detection rate, avg conf 0.816).
- [x] 4.3 Run test suite via `pytest tests/test_synthetic_generator.py` (8 passed in 3.35s).

## Phase 5: Documentation & Archival
- [x] 5.1 Create `docs/data/synthetic_generation.md` documenting the architecture, sprite specification, and before-and-after benchmark comparison.
- [x] 5.2 Generate `verify-report.md` in change directory.
- [x] 5.3 Archive change to `openspec/changes/archive/2026-09-02-synthetic-yolo-video-generation` and sync `openspec/specs/`.
