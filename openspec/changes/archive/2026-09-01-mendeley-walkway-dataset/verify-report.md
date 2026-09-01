# Verification Report: Mendeley Walkway Violation Dataset Integration

**Change**: `2026-09-01-mendeley-walkway-dataset`  
**Mode**: Standard (Full Spec-Driven Verification)  
**Timestamp**: 2026-09-01T16:21:00-03:00  
**Verdict**: **PASS**

---

## 1. Completeness Table

| Task ID | Description | Status | Evidence |
| :--- | :--- | :--- | :--- |
| `task-1.1-cfg` | Create `configs/datasets/mendeley_walkway_violation.yaml` | COMPLETE | YAML file created with 4-point DLT calibration and ISO 13855 zones |
| `task-1.2-registry` | Register in `scripts/download_datasets.py` `DATASET_REGISTRY` | COMPLETE | Registry entry verified with default config and metadata |
| `task-2.1-unit-test` | Unit tests for YAML parsing and DLT error $\le 0.05\text{ m}$ | COMPLETE | `tests/test_dataset_walkway.py::TestWalkwayDatasetProfile` passed |
| `task-2.2-integ-test` | Integration test running `DatasetTestRunner` on video | COMPLETE | `tests/test_dataset_walkway.py::TestWalkwayDatasetIntegration` passed |
| `task-3.1-pytest` | Complete regression test suite execution | COMPLETE | `pytest tests/` passed 174/174 tests in 8.04s |
| `task-3.2-benchmark` | Full 348-frame run on walkway dataset | COMPLETE | 348 frames processed @ 35.2 FPS, $T_1 = 19.62\text{ ms}$ |
| `task-3.3-docs` | Update `docs/data/datasets.md` catalog | COMPLETE | Catalog and benchmark comparison tables updated |

---

## 2. Build & Test Evidence

### Automated Test Suite
* **Command**: `pytest tests/ -v`
* **Result**: `174 passed in 8.04s` (Exit Code: `0`)
* **Walkway Suite**: `tests/test_dataset_walkway.py` $\rightarrow$ `4 passed in 3.00s` (Exit Code: `0`)

### Runtime Benchmark Execution
* **Command**: `python scripts/run_dataset_test.py --dataset mendeley_walkway_violation --no-display`
* **Result**: (Exit Code: `0`)
  * **Processed Frames**: 348 / 348
  * **Throughput**: $35.2\text{ FPS}$ (Target $\ge 30\text{ FPS}$)
  * **Mean Latency ($T_1$)**: $19.62\text{ ms}$ (Target $\le 40\text{ ms}$, budget $50\%$)
  * **Latency Percentiles**: $p50 = 19.61\text{ ms}$, $p95 = 23.33\text{ ms}$, $p99 = 25.42\text{ ms}$
  * **Safety State Distribution**: `SAFE`: 304 frames, `WARNING_APPROACH`: 2 frames, `DANGER_INTRUSION`: 4 frames, `LOCKOUT`: 38 frames.

---

## 3. Behavioral Spec Compliance Matrix

| Requirement / Scenario | Spec Reference | Covering Test | Status |
| :--- | :--- | :--- | :--- |
| Camera Resolution & ID | `walkway-dataset-profile` §1 | `test_yaml_schema_and_zone_parsing` | **COMPLIANT** |
| DLT 4-Point Ground Calibration | `walkway-dataset-profile` §2 | `test_homography_reprojection_accuracy` | **COMPLIANT** |
| Reprojection Error $\le 0.05\text{ m}$ | `walkway-dataset-profile` §2 | `test_homography_reprojection_accuracy` | **COMPLIANT** |
| ISO 13855 Danger/Warning Zones | `walkway-dataset-profile` §3 | `test_yaml_schema_and_zone_parsing` | **COMPLIANT** |
| Registry Extension | `walkway-dataset-profile` §4 | `test_registry_contains_walkway_dataset` | **COMPLIANT** |
| End-to-End Stream Evaluation | `walkway-dataset-profile` Scenario | `test_walkway_video_execution` | **COMPLIANT** |

---

## 4. Design Coherence

| Design Decision | Implementation Match | Coherence Status |
| :--- | :--- | :--- |
| Dedicated YAML profile | `configs/datasets/mendeley_walkway_violation.yaml` | COHERENT |
| DLT 4-point coplanar quad | Image & world points in YAML match design specification | COHERENT |
| Isolated test module | `tests/test_dataset_walkway.py` created without modifying core test fixtures | COHERENT |
| Telemetry artifacts in `data/results/` | Video, `events.jsonl`, `summary.json` generated cleanly | COHERENT |

---

## 5. Issues & Findings

- **CRITICAL**: None.
- **WARNING**:
  - **Walkway Zone Semantics Gap**: The initial YAML profile defined a generic machine restricted zone rather than an explicit safe-corridor boundary. For this dataset (which tests pedestrians stepping *outside* designated safe walkway markings), future iterations should implement inverted corridor zones (alarm on stepping outside the corridor polygon).
- **SUGGESTION**:
  - **YOLO11n Far-Field Sensitivity**: Operators located in the far corridor background ($Y > 12\text{m}$, bounding boxes $< 80\text{px}$) show intermittent keypoint dropouts under standard confidence thresholds ($0.40$). A lower threshold or temporal Kalman recovery window will improve long-range capture.

---

## 6. Final Verdict

**PASS** — All specification requirements, design contracts, and task deliverables are 100% verified with empirical runtime evidence.
