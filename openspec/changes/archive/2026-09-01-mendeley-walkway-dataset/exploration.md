# Exploration: Mendeley Walkway Violation Dataset Integration

## Current State
The repository contains empirical dataset testing harnesses (`scripts/run_dataset_test.py`, `scripts/download_datasets.py`) and dataset YAML profiles (`configs/datasets/opencv_vtest.yaml`, `configs/datasets/openvino_people.yaml`, `configs/datasets/pets2009_s2_l1.yaml`, `configs/datasets/mendeley_industrial.yaml`).
The video file `data/raw/mendeley_industrial/mendeley_walkway_violation.mp4` (1920x1080 @ 24.83 FPS, 348 frames, 14.02s) captures workers moving along a factory floor corridor and approaching restricted machinery.
Currently, this video is present locally in `data/raw/mendeley_industrial/` but lacks a dedicated configuration profile in `configs/datasets/`, an explicit entry in `DATASET_REGISTRY`, and automated test coverage in `tests/`.

## Affected Areas
- `configs/datasets/mendeley_walkway_violation.yaml` — Dedicated camera calibration, DLT ground correspondences, and ISO 13855 zone polygons for walkway and machine buffer.
- `scripts/download_datasets.py` — Canonical `DATASET_REGISTRY` entry with metadata, priority, and default config path.
- `tests/test_dataset_walkway.py` — Automated unit/integration test verifying YAML parsing, reprojection error bounds ($\le 0.05\text{ m}$), and end-to-end pipeline execution on the video sequence.
- `docs/data/datasets.md` — Documentation catalog update detailing resolution, FPS, zone coordinates, and latency benchmarks.

## Approaches

### 1. Dedicated Walkway Profile & Dedicated Test Suite (Recommended)
- **Description**: Add `configs/datasets/mendeley_walkway_violation.yaml` referencing the industrial camera perspective with tailored restricted zones, register `mendeley_walkway_violation` in `DATASET_REGISTRY`, and add a dedicated pytest integration test in `tests/test_dataset_walkway.py`.
- **Pros**:
  - Full modularity: each dataset has a self-contained configuration profile and automated regression test.
  - Zero coupling with core engine/pipeline code (`src/core/`, `src/pipeline/`).
  - Enables standalone benchmark commands: `python scripts/run_dataset_test.py --dataset mendeley_walkway_violation`.
- **Cons**: Adds one new YAML configuration and one test file to maintain.
- **Effort**: Low.

### 2. Alias Mapping to Existing Mendeley Industrial Profile
- **Description**: Map `mendeley_walkway_violation` directly to the existing `configs/datasets/mendeley_industrial.yaml` without creating a distinct YAML profile.
- **Pros**: Fewer configuration files.
- **Cons**:
  - Less flexibility if walkway-specific dwell thresholds (e.g. `dwell_warning_s`, `dwell_violation_s`) or distinct safety buffer geometries need to diverge from machine intervention scenarios.
  - Violates the 1-to-1 dataset-to-config naming convention used across all other benchmarks.
- **Effort**: Very Low.

## Recommendation
Proceed with **Approach 1**: Create `configs/datasets/mendeley_walkway_violation.yaml`, register the dataset in `scripts/download_datasets.py`, create `tests/test_dataset_walkway.py`, and update the benchmark documentation in `docs/data/datasets.md`.

## Risks
- **Keypoint occlusion on distant workers**: Handled by Kalman Filter coasting (`COASTING_AGE` / `n_release` tolerance).
- **Homography reprojection stability**: DLT points form a planar trapezoid with reprojection tolerance $\le 0.05\text{ m}$.

## Ready for Proposal
Yes. The exploration is complete, empirical video characteristics and ground geometry have been verified, and the next phase is `/sdd-propose` (accompanied by `/sdd-design` and `/sdd-spec`).
