# Proposal: Mendeley Walkway Violation Dataset Integration

## Intent
Integrate and calibrate `mendeley_walkway_violation.mp4` into the edge safety guard benchmark catalog, establishing dedicated ground homography fiducials, ISO 13855 safety/warning zones tailored for factory walkways, and automated integration tests.

## Scope

### In Scope
- **Dataset Configuration Profile (`configs/datasets/mendeley_walkway_violation.yaml`)**: Declarative calibration with 4-point DLT ground correspondences and restricted zone geometry.
- **Dataset Registry Extension (`scripts/download_datasets.py`)**: Register canonical metadata and default config path.
- **Automated Integration Tests (`tests/test_dataset_walkway.py`)**: Verify YAML schema parsing, reprojection error $\le 0.05\text{ m}$, and end-to-end telemetry generation.
- **Documentation (`docs/data/datasets.md`)**: Update benchmark catalog with empirical FPS and latency metrics.

### Out of Scope
- Core pipeline modifications (`src/core/`, `src/pipeline/`).
- Neural network retraining or weight alterations.

## Capabilities

### New Capabilities
- `walkway-dataset-profile`: Dedicated declarative camera calibration, ground plane homography, and walkway restricted zones for `mendeley_walkway_violation.mp4`.

### Modified Capabilities
- `dataset-downloader`: Extend registry with `mendeley_walkway_violation` entry.
- `dataset-ingestion-runner`: Validate execution with walkway dataset configuration profile.

## Approach
1. Author `configs/datasets/mendeley_walkway_violation.yaml` defining camera parameters, 4-point DLT ground plane homography mapping, and ISO 13855 danger/warning zone polygons.
2. Register `mendeley_walkway_violation` in `DATASET_REGISTRY` in `scripts/download_datasets.py`.
3. Add `tests/test_dataset_walkway.py` to validate configuration parsing, DLT RMSE, and complete stream processing.
4. Update `docs/data/datasets.md` with benchmark characteristics and execution commands.

## Affected Areas

| Area | Impact | Description |
| :--- | :--- | :--- |
| `configs/datasets/mendeley_walkway_violation.yaml` | New | Camera calibration and zone geometry profile |
| `scripts/download_datasets.py` | Modified | Add `mendeley_walkway_violation` to `DATASET_REGISTRY` |
| `tests/test_dataset_walkway.py` | New | Integration test suite for walkway dataset |
| `docs/data/datasets.md` | Modified | Dataset catalog and benchmark documentation |

## Risks

| Risk | Likelihood | Mitigation |
| :--- | :--- | :--- |
| Homography Reprojection Error | Low | Validate 4-point non-collinear DLT with RMSE $\le 0.05\text{ m}$ |
| Walkway Edge Occlusion | Low | Handled by Kalman Filter coasting and hysteresis buffers |

## Rollback Plan
Delete `configs/datasets/mendeley_walkway_violation.yaml` and `tests/test_dataset_walkway.py`, and revert changes in `scripts/download_datasets.py` and `docs/data/datasets.md`.

## Success Criteria
- [ ] `configs/datasets/mendeley_walkway_violation.yaml` parses without error and achieves DLT RMSE $\le 0.05\text{ m}$.
- [ ] `python scripts/run_dataset_test.py --dataset mendeley_walkway_violation` processes 348 frames @ $\ge 30\text{ FPS}$ with $T_1 \le 40\text{ ms}$.
- [ ] `pytest tests/test_dataset_walkway.py` passes 100%.
