# Tasks: Mahalanobis Innovation Gating, Hungarian Matching & Spatial NMS (`kalman-tracking`)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~120 lines |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | single-pr |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: single-pr
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Full Mahalanobis Gating & Hungarian MOT | PR 1 | `.venv/bin/pytest tests/test_kalman.py` | `python scripts/run_dataset_test.py --dataset openvino_people --no-display` | Revert `src/core/kalman_filter.py` and `tests/test_kalman.py` |

---

## Phase 1: Dependencies & Mathematical Foundation

- [x] 1.1 Add `scipy>=1.10.0` to `requirements.txt` and install into `.venv`.
- [x] 1.2 Implement `innovation_covariance(R=None)` and fast analytical $2\times2$ matrix inversion in `MetricKalmanFilter` (`src/core/kalman_filter.py`).

## Phase 2: TDD Association, Gating & Spatial Birth NMS

- [x] 2.1 [RED] Write failing tests in `tests/test_kalman.py` for Mahalanobis squared distance calculation and $\chi^2_2(0.99) \le 9.21$ gating rejection.
- [x] 2.2 [RED] Write failing tests in `tests/test_kalman.py` for Hungarian bipartite global assignment resolving crossing trajectories.
- [x] 2.3 [RED] Write failing tests in `tests/test_kalman.py` for World-Space Spatial Birth NMS suppressing duplicate detections within $0.6\text{ m}$.
- [x] 2.4 [GREEN] Implement `compute_mahalanobis_cost_matrix` and update `MultiTargetKalmanTracker.associate()` using `scipy.optimize.linear_sum_assignment` in `src/core/kalman_filter.py`.
- [x] 2.5 [GREEN] Implement World-Space Spatial Birth NMS check in `MultiTargetKalmanTracker.update()` prior to track instantiation.

## Phase 3: Benchmark & Integration Verification

- [x] 3.1 [VERIFY] Run `tests/test_kalman.py` association latency benchmark and assert execution time $< 0.15\text{ ms}$ for 10 targets.
- [x] 3.2 [VERIFY] Run full test suite (`.venv/bin/pytest tests/`) ensuring all existing tests pass with 100% green status.
- [x] 3.3 [VERIFY] Execute empirical ingestion test on `openvino_people` dataset and check telemetry tracking continuity.
