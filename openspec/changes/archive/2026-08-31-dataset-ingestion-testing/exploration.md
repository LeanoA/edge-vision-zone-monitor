# Exploration: Modular Dataset Ingestion & Video Test Pipeline

## Current State
The Edge Safety Guard repository currently features an end-to-end analytical pipeline (`SafetyPipeline`), an ONNX pose inference engine (`OnnxEngine`), planar homography transformation (`HomographyManager`), multi-target Kalman tracking (`MultiTargetKalmanTracker`), and spatial statechart FSM (`SpatialFSM`).

Presently:
1. **Synthetic Video Harness**: The repository includes `scripts/generate_samples.py` and `src/utils/synthetic_generator.py`, which generate 3 synthetic sequences (`sequence_a_clean_incursion.mp4`, `sequence_b_occlusion_coasting.mp4`, `sequence_c_dwell_loitering.mp4`).
2. **Demo Runner**: `scripts/run_demo.py` is capable of running a video file, webcam, or RTSP stream, but relies on a single hardcoded zone configuration in `configs/default_config.yaml`.
3. **Dataset Documentation**: `docs/data/datasets.md` specifies three canonical public benchmarks (PETS 2009 S2.L1, INRIA CAVIAR, Oxford TownCentre). However, many historical academic hosting URLs suffer from link rot, and there is no automated, modular downloader or dataset test runner.
4. **Git Ignore**: `.gitignore` currently only ignores `data/samples/*` and `*.onnx` / `*.pt`, but lacks explicit rules for raw downloaded datasets, video formats (`.avi`, `.mkv`, `.tar.gz`, `.zip`), and raw video ingestion caches.

## Objectives & Requirements
* **Modular Ingestion**: Decouple dataset downloading, extraction, calibration mapping, and test execution completely from core pipeline modules (`src/core/`, `src/inference/`).
* **Resilient Downloader Tooling**: A robust script (`scripts/download_datasets.py`) with URL registry, mirror fallbacks (including high-availability CDNs like OpenCV / OpenVINO / GitHub releases / HuggingFace), checksum/integrity checks, and local archive unpacking.
* **Git Hygiene**: Strict `.gitignore` rules preventing multi-megabyte video files and raw archives from entering git history.
* **Dataset Config Registry**: Dedicated configuration files per dataset in `configs/datasets/` defining image-to-world ground plane homography correspondences ($4+$ coplanar points) and spatial danger/warning polygons.
* **Evaluation & Triage Harness**: A dedicated dataset test runner (`scripts/run_dataset_test.py`) that processes downloaded sequences, verifies pose tracking and zone transitions, generates visual overlays (`data/results/`), and outputs structured telemetry JSONL to separate functioning scenarios from edge-case anomalies.

## Affected Areas
- `.gitignore` — Add broad exclusions for raw dataset directories (`data/raw/`, `data/datasets/`, `data/results/`) and video archives (`*.avi`, `.mkv`, `.tar.gz`, `.zip`).
- `scripts/download_datasets.py` (New) — Standalone CLI utility for downloading and unpacking benchmark datasets with progress bars (`urllib`/`requests`), mirror fallbacks, and format validation.
- `scripts/run_dataset_test.py` (New) — Modular test runner that links a specific dataset sequence, its YAML calibration/zone config, and logs test outcomes.
- `configs/datasets/` (New) — YAML configuration profiles (e.g. `opencv_vtest.yaml`, `pets2009_s2_l1.yaml`, `town_centre.yaml`) containing camera resolution, DLT points, and ISO 13855 zone coordinates.
- `docs/data/datasets.md` (Modified) — Documented CLI commands for dataset download, ingestion testing, and triage protocol.

## Approaches

### Approach 1: Monolithic Extension of `run_demo.py`
Extend `scripts/run_demo.py` with embedded download flags (`--download-dataset pets2009`) and internal hardcoded calibrations for all known datasets.
* **Pros**: Single script entry point for running demos.
* **Cons**: Violates Single Responsibility Principle; bloats demo orchestrator with network requests, archive unpacking, and dataset-specific branching; tightly couples demo logic with external asset management.
* **Effort**: Medium.

### Approach 2: Decoupled Downloader + Dedicated Ingestion Runner + Config Registry (Recommended)
Separate concerns into three distinct layers:
1. **Downloader Utility (`scripts/download_datasets.py`)**: Responsible solely for fetching, verifying, and extracting datasets into `data/raw/<dataset_name>/`.
2. **Dataset Configuration Registry (`configs/datasets/<dataset_name>.yaml`)**: Declarative YAML specifying camera parameters, DLT calibration correspondences, and danger/warning zone polygons.
3. **Dataset Test Runner (`scripts/run_dataset_test.py`)**: Reads the dataset video and YAML config, initializes `SafetyPipeline`, streams inference, records overlay diagnostics into `data/results/`, and outputs pass/fail and edge-case telemetry.
* **Pros**:
  - Zero modifications to core architecture (`src/core/`, `src/inference/`, `src/pipeline/`).
  - High extensibility: adding a new dataset only requires adding a YAML config and a download entry.
  - Test reproducibility: independent CLI commands for downloading, testing, and CI verification.
  - Clean error isolation and fallback support.
* **Cons**: Introduces two new lightweight scripts and a config directory.
* **Effort**: Medium.

### Approach 3: Ingestion Framework with Synthetic Fallback Only
Rely solely on synthetic generation and require users to manually place `.mp4` files without any automated downloader or dataset config repository.
* **Pros**: Minimal code to write.
* **Cons**: Poor developer experience; high friction for reproducing real-world benchmarks; lack of standardized calibration mappings.
* **Effort**: Low.

## Comparison Matrix

| Criteria | Approach 1 (Monolithic) | Approach 2 (Decoupled Downloader & Harness) | Approach 3 (Manual Only) |
| :--- | :--- | :--- | :--- |
| **Separation of Concerns** | Low (Tightly coupled) | High (Clean SRP boundaries) | High |
| **Core Intrusiveness** | Medium | Zero (Core untouched) | Zero |
| **Extensibility for New Datasets** | Low | High (Declarative YAML configs) | Low |
| **Automation & DX** | Medium | High (Automated download & test) | Low (Manual download) |
| **Triage & Reporting** | Low | High (Structured JSONL & video overlay) | Low |

## Recommendation
Adopt **Approach 2**: Implement a decoupled downloader (`scripts/download_datasets.py`), a dedicated dataset test harness (`scripts/run_dataset_test.py`), and declarative dataset configs under `configs/datasets/`.

Priority implementation will start with a verified, highly reliable surveillance sequence (e.g. `opencv_vtest` and `openvino_people` with working camera homographies), followed by modular support for PETS 2009 and Oxford TownCentre with mirror fallbacks.

## Risks & Mitigations
1. **Link Rot & Host Downtime**:
   * *Mitigation*: Multi-source registry with primary and fallback mirror URLs (GitHub raw / OpenVINO S3 / HuggingFace), plus support for local pre-downloaded archives.
2. **Homography Distortion in Uncalibrated Real Videos**:
   * *Mitigation*: Carefully select 4+ coplanar floor reference points (tiles, markers, lane lines) in each YAML config and enforce RMSE $\le 0.05\text{ m}$ verification.
3. **Large Binary Commit Risk**:
   * *Mitigation*: Update `.gitignore` with strict patterns (`data/raw/`, `data/results/`, `*.avi`, `*.mp4`, `*.tar.gz`, `*.zip`) and provide a sanity check in CI.

## Ready for Proposal
Yes. The architectural boundaries are clean, zero core changes are required, and the next step is formalizing the specification and design (`/sdd-propose`, `/sdd-design`, `/sdd-spec`).
