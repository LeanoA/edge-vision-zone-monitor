# Proposal: Synthetic YOLO Video Generation

## Intent
Upgrade the synthetic video generator (`src/utils/synthetic_generator.py`) from geometric primitive drawings (vector lines/rectangles) to a perspective-accurate, photorealistic RGBA sprite-based rendering engine. This enables YOLOv8/YOLO11 object detection and pose estimation models to reliably detect human workers ($conf \ge 0.70$) across benchmark test sequences while preserving 100% deterministic metric ground-truth coordinates $(X, Y)$ and ISO 13855 safety zone evaluation.

## Scope

### In Scope
- **Photorealistic Sprite Asset Pipeline (`data/assets/sprites/`)**: High-contrast, photorealistic industrial worker walking and standing sprites with 8-bit RGBA alpha channels.
- **Enhanced Synthetic Video Engine (`src/utils/synthetic_generator.py`)**:
  - Perspective-scaled RGBA alpha blending with bilinear filtering.
  - Directional projected soft ground contact shadows with Gaussian falloff.
  - Occlusion layering with depth sorting ($Y$-buffer).
  - Deterministic metric kinematics for Benchmark Sequences A, B, and C.
- **CLI Regeneration Tooling (`scripts/generate_samples.py`)**: Seamless command-line interface to produce updated synthetic benchmark video artifacts.
- **Automated Test Suite (`tests/test_synthetic_generator.py`)**:
  - Unit tests for sprite loading, scaling, alpha blending, and occlusion masks.
  - End-to-end integration tests verifying YOLO detection confidence $\ge 0.50$ on generated frames.
- **Documentation (`docs/data/synthetic_generation.md`)**: Full architectural reference and storytelling before-and-after comparison.

### Out of Scope
- Heavy 3D rendering engines (Blender CLI, Unreal, Unity) or headless OpenGL dependencies.
- Changes to core spatial FSM or Kalman Filter tracking logic.

## Capabilities

### New Capabilities
- `synthetic-yolo-video-generator`: High-fidelity RGBA sprite-based synthetic video generation with homography ground-truth, depth-ordered occlusion, and YOLO-compatible photorealism.

### Modified Capabilities
- `synthetic-generator-cli`: Updates `scripts/generate_samples.py` to support new sprite configurations and high-resolution rendering.

## Approach
1. Prepare curated high-resolution photorealistic worker sprites (walking cycle + idle/standing pose) formatted as PNGs with 4-channel RGBA transparency in `data/assets/sprites/worker/`.
2. Refactor `SyntheticVideoGenerator` to replace geometric primitive body parts with perspective-scaled alpha blending of realistic worker sprites onto the calibrated factory floor.
3. Add soft contact shadow projection with Gaussian blur and depth-ordered occlusion compositing.
4. Implement comprehensive unit tests in `tests/test_synthetic_generator.py` testing both geometry and YOLO inference confidence.
5. Regenerate benchmark videos in `data/samples/` (`sequence_a_clean_incursion.mp4`, `sequence_b_occlusion_coasting.mp4`, `sequence_c_dwell_loitering.mp4`).

## Affected Areas

| Area | Impact | Description |
| :--- | :--- | :--- |
| `data/assets/sprites/worker/` | New | RGBA PNG sprite sequence for walking and standing worker |
| `src/utils/synthetic_generator.py` | Modified | Implementation of RGBA sprite blending, perspective scaling, and shadows |
| `scripts/generate_samples.py` | Modified | Updated CLI flags and sequence generator integration |
| `tests/test_synthetic_generator.py` | New / Modified | Test suite verifying generator output and YOLO detection rates |
| `docs/data/synthetic_generation.md` | New | Technical documentation and before/after benchmark results |

## Risks

| Risk | Likelihood | Mitigation |
| :--- | :--- | :--- |
| Alpha Blending Performance | Low | Optimized vectorized NumPy/OpenCV slicing and bounding box clipping |
| Aspect Ratio Distortion | Low | Perspective height scaling preserves source sprite aspect ratio |
| YOLO Detection Drift on Low Res | Low | Render at 1080p with Lanczos4 interpolation for crisp worker edges |

## Rollback Plan
Revert changes to `src/utils/synthetic_generator.py` and `scripts/generate_samples.py` from git history.

## Success Criteria
- [ ] Worker sprites are loaded and rendered with clean alpha blending without edge halos.
- [ ] Generated synthetic video sequences (`A`, `B`, `C`) achieve YOLO11 pose / detection confidence $\ge 0.50$ across visible frames.
- [ ] Sequence B correctly preserves occlusion coasting when lower limbs pass behind the industrial barrier.
- [ ] All unit and integration tests in `tests/test_synthetic_generator.py` pass 100%.
