# Design: Modular Dataset Ingestion & Video Test Pipeline

**Change ID:** `dataset-ingestion-testing`  
**Status:** In Review  
**Related Documents:**
- Proposal: [`openspec/changes/2026-08-31-dataset-ingestion-testing/proposal.md`](file:///Users/xander/Projects/edge-safety-guard/openspec/changes/2026-08-31-dataset-ingestion-testing/proposal.md)
- Exploration: [`openspec/changes/2026-08-31-dataset-ingestion-testing/exploration.md`](file:///Users/xander/Projects/edge-safety-guard/openspec/changes/2026-08-31-dataset-ingestion-testing/exploration.md)
- Dataset Documentation: [`docs/data/datasets.md`](file:///Users/xander/Projects/edge-safety-guard/docs/data/datasets.md)

---

## 1. Architecture Overview

### 1.1 Context & Objectives
To evaluate the Edge Safety Guard pipeline under empirical surveillance conditions without altering core architectural code (`src/core/`, `src/inference/`, `src/pipeline/`), this change provides a completely decoupled dataset management and ingestion framework:
1. **Dataset Downloader Utility (`scripts/download_datasets.py`)**: A resilient asset fetcher equipped with a multi-mirror registry (GitHub CDN, OpenVINO S3, HuggingFace, Zenodo), checksum verification, archive unpacking, and local file fallback.
2. **Declarative Dataset Configurations (`configs/datasets/*.yaml`)**: Per-dataset calibration mapping 4+ coplanar floor landmarks to metric coordinates ($Z_w=0$) alongside ISO 13855 danger/warning zone geometries.
3. **Decoupled Test Harness (`scripts/run_dataset_test.py`)**: An isolated runner that feeds video frames through `SafetyPipeline`, records dual composite video overlays and JSONL telemetry into `data/results/`, and computes tracking and safety compliance metrics.
4. **Git Hygiene**: Strict `.gitignore` rules ensuring all media binaries, raw dataset directories, and evaluation artifacts remain untracked.

### 1.2 Ingestion Architecture Dataflow

```
[Dataset Registry] ──► scripts/download_datasets.py ──► data/raw/<dataset_name>/video.<ext>
                              │
                              ▼
[Dataset Configs]  ──► configs/datasets/<dataset_name>.yaml
                              │
                              ▼
                      scripts/run_dataset_test.py
                              │
                              ▼
                    ┌─────────────────────────┐
                    │ SafetyPipeline (Core)   │
                    │  1. Preprocess          │
                    │  2. YOLO-Pose ONNX      │
                    │  3. Anchor Extraction   │
                    │  4. Homography DLT      │
                    │  5. Kalman Tracking     │
                    │  6. Spatial & Dwell FSM │
                    └────────────┬────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       data/results/<name>/             data/results/<name>/
       annotated_<name>.mp4             events.jsonl & summary.json
```

---

## 2. Component Design & Contracts

### 2.1 Dataset Registry (`scripts/download_datasets.py`)

The downloader maintains an immutable registry of supported benchmarks:

```python
@dataclass(frozen=True)
class DatasetMetadata:
    name: str
    description: str
    filename: str
    primary_url: str
    mirrors: Tuple[str, ...]
    priority: int  # 1: Clean baseline, 2: Occlusion/Edge case, 3: Large crowd
    expected_size_bytes: Optional[int] = None
    default_config: str = ""
    is_archive: bool = False
```

#### Pre-configured Registry Entries:
1. **`opencv_vtest` (Priority 1 - Clean Baseline)**:
   - Primary: `https://raw.githubusercontent.com/opencv/opencv/master/samples/data/vtest.avi`
   - Format: AVI (MPEG-4), $768 \times 576$ @ 25 FPS.
   - Characteristics: Clean outdoor pedestrian crossing over paved walkway, fixed high-angle camera.
2. **`openvino_people` (Priority 1 - Clean Baseline 1080p)**:
   - Primary: `https://storage.openvinotoolkit.org/repositories/openvino_notebooks/data/data/video/people.mp4`
   - Format: MP4 (H.264), $1920 \times 1080$ @ 30 FPS.
   - Characteristics: Pedestrian mall walkway with clear ground plane.
3. **`pets2009_s2_l1` (Priority 2 - Standard Multi-Target Tracking)**:
   - Primary/Mirrors: GitHub / academic mirrors with local file fallback.
   - Characteristics: Ground truth homography plane with Tsai calibration.
4. **`oxford_town_centre` (Priority 2 - Dwell / Loitering)**:
   - Primary/Mirrors: HuggingFace / Kaggle mirror references with local file fallback.

### 2.2 Dataset Configuration Profiles (`configs/datasets/*.yaml`)

Each dataset profile defines:
```yaml
camera:
  id: "opencv_vtest"
  resolution:
    width: 768
    height: 576
  fps: 25

calibration:
  method: "DLT"
  reprojection_tolerance_m: 0.05
  points:
    image:
      - [180.0, 520.0]    # bottom-left
      - [580.0, 520.0]    # bottom-right
      - [480.0, 240.0]    # top-right
      - [260.0, 240.0]    # top-left
    world:
      - [0.0, 0.0]        # (meters)
      - [6.0, 0.0]
      - [6.0, 10.0]
      - [0.0, 10.0]

zones:
  name: "PedestrianGuardedZone"
  danger_polygon:
    - [1.5, 2.0]
    - [4.5, 2.0]
    - [4.5, 6.0]
    - [1.5, 6.0]
  warning_polygon:
    - [1.0, 1.5]
    - [5.0, 1.5]
    - [5.0, 6.5]
    - [1.0, 6.5]
  hysteresis_buffer_m: 0.20
  n_confirm: 3
  n_release: 5
  dwell_warning_s: 3.0
  dwell_violation_s: 6.0
  iso_k_speed: 1.6
```

### 2.3 Dataset Ingestion Test Runner (`scripts/run_dataset_test.py`)

The runner accepts:
- `--dataset <name>`: Automatically looks up `data/raw/<dataset>/<video>` and `configs/datasets/<dataset>.yaml`.
- `--source <path>` and `--config <path>`: Custom override inputs.
- `--model <path>`: YOLO Pose ONNX model path.
- `--output-dir <path>`: Target results directory (default: `data/results/<dataset>/`).
- `--max-frames <int>`: Optional limit on frame evaluation count.
- `--no-display`: Headless execution.

#### Output Artifacts per Test Run:
1. `annotated_<dataset>.mp4`: Composite dual view (perspective camera + BEV ground plane with active safety zones, trajectories, and keypoint anchors).
2. `events.jsonl`: Frame-by-frame structured telemetry with timestamps, active tracks, observation statuses, dwell times, and latency profiles.
3. `summary.json`: Aggregate metrics (total frames, throughput FPS, latency percentiles p50/p95/p99, state occurrence distribution).

---

## 3. Implementation Plan & File Additions

| File | Purpose |
| :--- | :--- |
| `.gitignore` | Ensure `data/raw/`, `data/results/`, and video file extensions are excluded |
| `scripts/download_datasets.py` | Standalone CLI downloader with multi-source fallback and validation |
| `scripts/run_dataset_test.py` | Decoupled test runner executing `SafetyPipeline` over dataset video |
| `configs/datasets/opencv_vtest.yaml` | Calibration & zone profile for OpenCV vtest sequence |
| `configs/datasets/openvino_people.yaml` | Calibration & zone profile for OpenVINO people sequence |
| `configs/datasets/pets2009_s2_l1.yaml` | Calibration & zone profile for PETS 2009 sequence |
| `docs/data/datasets.md` | Updated operational documentation for downloading and evaluating datasets |

---

## 4. Verification & Validation Strategy
1. **Downloader Verification**: Execute `scripts/download_datasets.py --dataset opencv_vtest` and verify download completion, integrity, and non-destructive overwrite behavior.
2. **Ingestion Runner Verification**: Execute `scripts/run_dataset_test.py --dataset opencv_vtest --max-frames 100 --no-display` and verify generated `data/results/opencv_vtest/annotated_opencv_vtest.mp4`, `events.jsonl`, and `summary.json`.
3. **Core Immutability Check**: Verify with `git status` that zero files under `src/core/` or `src/inference/` are modified.
4. **Git Ignore Verification**: Run `git status --ignored` to confirm downloaded videos and results are correctly ignored.
