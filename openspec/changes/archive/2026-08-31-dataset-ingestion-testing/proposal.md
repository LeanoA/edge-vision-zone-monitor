# Proposal: Modular Dataset Ingestion & Video Test Pipeline

## Intent
Validate the end-to-end industrial safety pipeline against real-world surveillance video streams with empirical ground geometry, while keeping core analytics strictly decoupled and version control clean of multi-megabyte media assets.

## Scope

### In Scope
- **Git Security**: Comprehensive `.gitignore` rules for downloaded video formats (`.avi`, `.mp4`, `.tar.gz`, `.zip`) and raw working directories (`data/raw/`, `data/results/`).
- **Resilient Dataset Downloader (`scripts/download_datasets.py`)**: CLI utility with multi-mirror fallback (GitHub CDN / OpenVINO / HuggingFace / Zenodo) and local file ingestion support.
- **Dataset Configuration Profiles (`configs/datasets/*.yaml`)**: Declarative calibrations pairing real-world videos with 4+ ground DLT correspondences and ISO 13855 safety zones.
- **Decoupled Ingestion Runner (`scripts/run_dataset_test.py`)**: Standalone test harness streaming external frames through `SafetyPipeline`, generating verification overlay video and telemetry JSONL.
- **Dataset Triage & Baseline Validation**: Prioritize testing a verified primary sequence (`opencv_vtest` / `openvino_people`), establishing a baseline to separate working sequences from edge cases.

### Out of Scope
- Modifications to core modules (`src/core/`, `src/inference/`, `src/pipeline/`).
- Neural network model retraining or weight updates.
- Multi-camera spatial fusion.

## Capabilities

### New Capabilities
- `dataset-downloader`: Automated retrieval, verification, and extraction of public surveillance benchmarks with mirror failover.
- `dataset-ingestion-runner`: Modular evaluation harness for benchmark video streams and declarative YAML dataset configs.

### Modified Capabilities
- None.

## Approach
1. Enforce repository hygiene by updating `.gitignore`.
2. Implement `scripts/download_datasets.py` with multi-source registry and local file fallbacks.
3. Build declarative YAML calibration specs under `configs/datasets/`.
4. Create `scripts/run_dataset_test.py` to stream video frames into `SafetyPipeline`, recording composite diagnostic overlays and JSONL event telemetry into `data/results/`.
5. Execute baseline validation and document findings in `docs/data/datasets.md`.

## Affected Areas

| Area | Impact | Description |
| :--- | :--- | :--- |
| `.gitignore` | Modified | Add exclusions for raw datasets and video extensions |
| `scripts/download_datasets.py` | New | CLI tool to download and unpack benchmark datasets |
| `scripts/run_dataset_test.py` | New | Modular harness to execute safety pipeline over dataset videos |
| `configs/datasets/` | New | YAML calibration and zone profiles for external datasets |
| `docs/data/datasets.md` | Modified | Usage documentation and triage guide for empirical datasets |

## Risks

| Risk | Likelihood | Mitigation |
| :--- | :--- | :--- |
| Academic Link Rot | High | Registry with multi-mirror fallbacks and local archive support |
| Large Binary Commits | High | Strict `.gitignore` globs preventing media staging |
| Reprojection Inaccuracy | Medium | Validate 4-point coplanar DLT with RMSE $\le 0.05\text{ m}$ in configs |

## Rollback Plan
Delete `scripts/download_datasets.py`, `scripts/run_dataset_test.py`, and `configs/datasets/`. Revert `.gitignore`. Core pipeline remains 100% untouched.

## Dependencies
- `requests>=2.28.0` or `urllib`
- `opencv-python>=4.8.0`, `numpy>=1.24.0`, `pyyaml>=6.0`

## Success Criteria
- [ ] `.gitignore` prevents tracking any downloaded media files or raw directories.
- [ ] `download_datasets.py` successfully fetches verified reference surveillance sequence.
- [ ] `run_dataset_test.py` processes downloaded sequence without modifying core code.
- [ ] Composite diagnostic video generated in `data/results/` validating pose, ground projections, and FSM zone transitions.
- [ ] Baseline test results documented with clear pass/edge-case triage.
