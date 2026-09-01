# Design: Mendeley Walkway Violation Dataset Integration

## Technical Approach
Integrate `mendeley_walkway_violation.mp4` into the benchmark harness by authoring a dedicated declarative YAML profile [`configs/datasets/mendeley_walkway_violation.yaml`](file:///Users/xander/Projects/edge-safety-guard/configs/datasets/mendeley_walkway_violation.yaml), registering the dataset in `scripts/download_datasets.py`, implementing automated test coverage in `tests/test_dataset_walkway.py`, and updating the documentation catalog in `docs/data/datasets.md`.

## Architecture Decisions

| Decision | Option Selected | Tradeoffs & Alternatives | Rationale |
| :--- | :--- | :--- | :--- |
| **Configuration Model** | Dedicated YAML profile (`mendeley_walkway_violation.yaml`) | Alt: Reuse generic `mendeley_industrial.yaml` | Dedicated YAML allows fine-grained customization of walkway dwell timers and zone offsets without impacting machine incursion tests. |
| **Ground Homography** | 4-point coplanar DLT mapping | Alt: Perspective PnP with 3D CAD mesh | Direct Linear Transform on ground plane quad offers $<0.05\text{ m}$ RMSE without requiring extrinsic laser scanning. |
| **Testing Isolation** | Dedicated pytest file (`tests/test_dataset_walkway.py`) | Alt: Modify `tests/test_safety_pipeline.py` | Keeps synthetic unit tests cleanly separated from empirical video benchmark tests. |

## Data Flow

```
[ mendeley_walkway_violation.mp4 ]
            │
            ▼
   cv2.VideoCapture (1920x1080 @ 24.83 FPS)
            │
            ▼
    SafetyPipeline ──[ OnnxEngine (YOLO11n-pose) ]
            │       ──[ HomographyManager (DLT matrix H) ]
            │       ──[ MultiTargetKalmanTracker (Coasting) ]
            │       ──[ SpatialFSM (Danger / Warning / Dwell) ]
            ▼
    DualVisualizer ──▶ Annotated Video (data/results/mendeley_walkway_violation/)
            │
            ├──▶ Telemetry Events (events.jsonl)
            └──▶ Benchmark Summary (summary.json)
```

## File Changes

| File | Action | Description |
| :--- | :--- | :--- |
| `configs/datasets/mendeley_walkway_violation.yaml` | Create | Declarative calibration points, camera FPS, and ISO 13855 zone coordinates |
| `scripts/download_datasets.py` | Modify | Add `mendeley_walkway_violation` to `DATASET_REGISTRY` |
| `tests/test_dataset_walkway.py` | Create | Automated unit & integration tests for configuration parsing and video evaluation |
| `docs/data/datasets.md` | Modify | Add walkway violation dataset specification and benchmark throughput data |
| `openspec/changes/2026-09-01-mendeley-walkway-dataset/tasks.md` | Modify | Update task checklist |

## Interfaces / Contracts

```yaml
# configs/datasets/mendeley_walkway_violation.yaml
camera:
  id: "mendeley_walkway_violation_cctv"
  resolution:
    width: 1920
    height: 1080
  fps: 24

calibration:
  method: "DLT"
  reprojection_tolerance_m: 0.05
  points:
    image:
      - [250.0, 1020.0]
      - [1680.0, 1020.0]
      - [1400.0, 480.0]
      - [520.0, 480.0]
    world:
      - [0.0, 0.0]
      - [10.0, 0.0]
      - [10.0, 15.0]
      - [0.0, 15.0]

zones:
  name: "FactoryWalkwaySafetyZone"
  danger_polygon:
    - [2.5, 3.0]
    - [7.5, 3.0]
    - [7.5, 10.0]
    - [2.5, 10.0]
  warning_polygon:
    - [1.8, 2.2]
    - [8.2, 2.2]
    - [8.2, 10.8]
    - [1.8, 10.8]
  hysteresis_buffer_m: 0.20
  n_confirm: 3
  n_release: 5
  dwell_warning_s: 3.0
  dwell_violation_s: 6.0
  iso_k_speed: 1.6
```

## Testing Strategy

| Layer | What to Test | Approach |
| :--- | :--- | :--- |
| **Unit** | Schema & Homography DLT | Verify YAML loads into `HomographyManager` and `ZoneConfig` with DLT error $< 0.05\text{ m}$ |
| **Integration** | `DatasetTestRunner` Stream | Run 50 frames and full 348 frames in headless mode, validating non-empty video, `events.jsonl`, and `summary.json` |
| **Regression** | Full Test Suite | Run `pytest tests/` ensuring all existing tests pass 100% |

## Threat Matrix
`N/A — no routing, shell execution, subprocess parsing, VCS/PR automation, executable-file classification, or process-integration boundary.`

## Migration / Rollout
No migration required. Pure additive dataset configuration and test harness extension.

## Open Questions
None.
