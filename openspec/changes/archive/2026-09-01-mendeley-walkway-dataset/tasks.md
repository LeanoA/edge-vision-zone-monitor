# Tasks: Mendeley Walkway Violation Dataset Integration

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~130 lines |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Full dataset profile, registry, tests & docs | Single PR | `pytest tests/test_dataset_walkway.py` | `python scripts/run_dataset_test.py --dataset mendeley_walkway_violation --no-display` | Delete new config & test file; revert registry/doc lines |

---

## Phase 1: Foundation & Configuration

- [x] 1.1 Create `configs/datasets/mendeley_walkway_violation.yaml` with camera resolution (1920x1080 @ 24.83 FPS), 4-point DLT ground homography calibration, and ISO 13855 danger/warning zone polygons. <!-- id: task-1.1-cfg -->
- [x] 1.2 Update canonical `DATASET_REGISTRY` in `scripts/download_datasets.py` to register `mendeley_walkway_violation` with priority 1 and default config path. <!-- id: task-1.2-registry -->

## Phase 2: Automated Test Suite

- [x] 2.1 Create `tests/test_dataset_walkway.py` with unit tests verifying YAML schema parsing, ZoneConfig construction, and DLT reprojection error $\le 0.05\text{ m}$. <!-- id: task-2.1-unit-test -->
- [x] 2.2 Add integration test in `tests/test_dataset_walkway.py` running `DatasetTestRunner` over `mendeley_walkway_violation.mp4`, validating output video, `events.jsonl`, and `summary.json`. <!-- id: task-2.2-integ-test -->

## Phase 3: Documentation & Full Benchmark Verification

- [x] 3.1 Execute `pytest tests/` to verify 100% regression pass across all unit and dataset tests. <!-- id: task-3.1-pytest -->
- [x] 3.2 Execute full 348-frame run with `scripts/run_dataset_test.py --dataset mendeley_walkway_violation` to record official benchmark summary. <!-- id: task-3.2-benchmark -->
- [x] 3.3 Update `docs/data/datasets.md` catalog with walkway violation dataset specifications, ground plane mapping details, and throughput metrics. <!-- id: task-3.3-docs -->
