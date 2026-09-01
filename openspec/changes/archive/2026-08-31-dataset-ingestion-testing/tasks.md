# Tasks: Modular Dataset Ingestion & Video Test Pipeline

## Review Workload Forecast

| Field | Value |
| :--- | :--- |
| Estimated changed lines | 280 - 360 lines |
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
| 1 | Downloader CLI, Dataset Configs & Ingestion Runner | PR 1 | `pytest tests/test_dataset_ingestion.py` | `python scripts/download_datasets.py --list` | Delete `scripts/download_datasets.py`, `scripts/run_dataset_test.py`, `configs/datasets/` |

---

## Phase 1: Git Hygiene & Dataset Config Profiles

- [x] 1.1 Update `.gitignore` to strictly exclude `data/raw/*`, `data/results/*`, `*.avi`, `*.mp4`, `*.mkv`, `*.tar.gz`, `*.tar.bz2`, and `*.zip` while preserving `.gitkeep`.
- [x] 1.2 Create `configs/datasets/opencv_vtest.yaml` with camera resolution ($768 \times 576$), 4-point DLT ground homography correspondences, and ISO 13855 zone polygons.
- [x] 1.3 Create `configs/datasets/openvino_people.yaml` with 1080p camera geometry, planar DLT correspondences, and safety zones.
- [x] 1.4 Create `configs/datasets/pets2009_s2_l1.yaml` with reference geometry and guarding zones.

## Phase 2: Resilient Dataset Downloader

- [x] 2.1 Implement `scripts/download_datasets.py` with immutable `DatasetRegistry` (supporting `opencv_vtest`, `openvino_people`, `pets2009_s2_l1`, `oxford_town_centre`).
- [x] 2.2 Add multi-mirror HTTP download failover with streaming progress, size check, and existing-file skip logic.
- [x] 2.3 Implement CLI argument parsing (`--dataset`, `--list`, `--output-dir`, `--force`).

## Phase 3: Decoupled Dataset Ingestion Runner

- [x] 3.1 Implement `scripts/run_dataset_test.py` with dataset and YAML config resolution logic.
- [x] 3.2 Implement frame streaming loop using `SafetyPipeline` with dual perspective/BEV rendering (`DualVisualizer`).
- [x] 3.3 Add structured telemetry export (`data/results/<dataset>/events.jsonl` and `summary.json`) and annotated video generation (`annotated_<dataset>.mp4`).
- [x] 3.4 Support headless mode (`--no-display`) and bounded evaluation (`--max-frames`).

## Phase 4: Unit Testing & Verification

- [x] 4.1 Create `tests/test_dataset_ingestion.py` covering registry metadata lookup, existing file detection, CLI flag parsing, and YAML config validation.
- [x] 4.2 Execute unit test suite with `pytest tests/test_dataset_ingestion.py` to confirm 100% pass rate.
- [x] 4.3 Execute end-to-end baseline download: `python scripts/download_datasets.py --dataset opencv_vtest`.
- [x] 4.4 Execute end-to-end ingestion test: `python scripts/run_dataset_test.py --dataset opencv_vtest --max-frames 75 --no-display`.
- [x] 4.5 Verify output artifacts in `data/results/opencv_vtest/` (`annotated_opencv_vtest.mp4`, `events.jsonl`, `summary.json`).

## Phase 5: Documentation & Triage

- [x] 5.1 Update `docs/data/datasets.md` with instructions for `download_datasets.py` and `run_dataset_test.py`, documenting baseline validation results.
- [x] 5.2 Verify `git status` confirms zero modifications to `src/core/`, `src/inference/`, or `src/pipeline/`.
