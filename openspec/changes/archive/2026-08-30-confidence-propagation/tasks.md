# Tasks: Lower-Limb Occlusion Degradation & Confidence Propagation

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 350 - 450 lines |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Delivery strategy | single-pr |
| Chain strategy | none |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: none
400-line budget risk: Medium

## Suggested Work Units

- **Unit 1: Core Contracts & Adaptive Kalman Tracking**
  - Files: `src/core/kalman_filter.py`, `src/core/__init__.py`, `tests/test_kalman.py`
  - Focused test command: `pytest tests/test_kalman.py`
  - Runtime harness: Python 3.10+ / NumPy vectorization
  - Rollback boundary: Revert changes to `src/core/kalman_filter.py`, `src/core/__init__.py`, `tests/test_kalman.py`
- **Unit 2: Pipeline Anchor Extraction & Metadata Propagation**
  - Files: `src/pipeline/safety_pipeline.py`, `src/pipeline/__init__.py`, `tests/test_pipeline.py`
  - Focused test command: `pytest tests/test_pipeline.py`
  - Runtime harness: OpenCV letterboxing & NumPy projection
  - Rollback boundary: Revert changes to `src/pipeline/safety_pipeline.py`, `src/pipeline/__init__.py`, `tests/test_pipeline.py`

## Implementation Tasks

### Phase 1: Foundation Contracts & Types (`kalman-tracking` / `safety-pipeline`)
- [x] 1.1 (RED) Write unit tests in `tests/test_kalman.py` verifying `AnchorSource` enum values (`ANKLES_DUAL`, `ANKLE_SINGLE`, `BBOX_BOTTOM`, `TRACKER_PREDICTED`) and `PositionEstimate` dataclass contract (2-tuple `xy_m`, `confidence` validation in $[0.0, 1.0]$, `source` type validation, optional 2x2 numpy array `covariance` validation, immutability via `frozen=True`).
- [x] 1.2 (GREEN) Implement `AnchorSource(str, Enum)` and `@dataclass(frozen=True) PositionEstimate` in `src/core/kalman_filter.py` with `__post_init__` coordinate, confidence range, and covariance shape validation.
- [x] 1.3 (GREEN) Re-export `AnchorSource` and `PositionEstimate` in `src/core/__init__.py`, `src/pipeline/safety_pipeline.py`, and `src/pipeline/__init__.py` to ensure modular cross-layer accessibility without circular imports.
- [x] 1.4 (REFACTOR) Enforce strict type hints and run `pytest tests/test_kalman.py -k "estimate or anchor_source"` to confirm foundation contract validity.

### Phase 2: Adaptive Kalman Filtering & Confidence Decay (`kalman-tracking`)
- [x] 2.1 (RED) Write unit tests in `tests/test_kalman.py` for `MetricKalmanFilter.update` with adaptive measurement noise $R$:
  - Verify backward compatibility: calling `update(measurement)` without $R$ uses nominal $R_0 = \text{diag}([r_{\text{pos}}, r_{\text{pos}}])$.
  - Verify custom noise matrix injection: passing custom $R$ overrides measurement covariance.
  - Verify Kalman gain attenuation: passing inflated $R$ ($2.0\times R_0$ and $5.0\times R_0$) attenuates Kalman gain and dampens state innovation update relative to $R_0$.
- [x] 2.2 (GREEN) Update `MetricKalmanFilter.update(measurement, R=None)` in `src/core/kalman_filter.py` to accept optional measurement covariance override `R: Optional[np.ndarray] = None`, defaulting to `self._R`.
- [x] 2.3 (RED) Write unit tests in `tests/test_kalman.py` for `Track` properties and kinematic confidence decay:
  - Verify initial track provenance attributes: `track.source == AnchorSource.ANKLES_DUAL`, `track.confidence == 1.0` (or passed initial values).
  - Verify typed property `track.estimate -> PositionEstimate` exposing metric position `xy_m`, `confidence`, `source`, and 2x2 submatrix `P[:2, :2]`.
  - Verify exponential confidence decay during coasting in `track.mark_missed()`: transition `track.source` to `AnchorSource.TRACKER_PREDICTED`, decay confidence $c_k = c_{\text{last-confirmed}} \times 0.85^k$ across consecutive missed frames, and verify covariance inflation.
  - Verify confidence restoration on re-detection: `missed_count` reset to 0, confidence updated to measurement confidence $c_{\text{meas}}$, source updated to incoming `AnchorSource`, and covariance trace strictly reduced.
- [x] 2.4 (GREEN) Extend `Track` in `src/core/kalman_filter.py`:
  - Add private state attributes `_source: AnchorSource`, `_confidence: float`, `_last_confirmed_confidence: float`.
  - Expose properties `source`, `confidence`, and `estimate`.
  - Update `Track.update(measurement, source=..., confidence=..., R=...)` to accept provenance metadata, update state, and reset missed counters.
  - Update `Track.mark_missed()` to transition `_source` to `AnchorSource.TRACKER_PREDICTED` and decay `_confidence = _last_confirmed_confidence * (0.85 ** self._missed_count)`.
- [x] 2.5 (RED) Write unit tests in `tests/test_kalman.py` for `MultiTargetKalmanTracker.update`:
  - Verify input polymorphism: accept both `Sequence[PositionEstimate]` and legacy 2D coordinate arrays/tuples.
  - Verify source-based $R$ scaling: map `ANKLES_DUAL` $\to 1.0 \times R_0$, `ANKLE_SINGLE` $\to 2.0 \times R_0$, `BBOX_BOTTOM` $\to 5.0 \times R_0$.
  - Verify Euclidean spatial gating: candidate detections with distance $d > d_{\text{gate}} = 1.0\text{ m}$ are rejected from association, forcing tracks into coast mode.
  - Verify backward compatibility: raw coordinate arrays default to `AnchorSource.ANKLES_DUAL` and confidence $1.0$.
- [x] 2.6 (GREEN) Update `MultiTargetKalmanTracker.update()` in `src/core/kalman_filter.py`:
  - Normalize incoming measurements to parse coordinates, sources, and confidences from `PositionEstimate` objects or raw arrays.
  - Calculate source-scaled measurement covariance $R_{\text{source}}$ for each candidate.
  - Enforce Euclidean gating constraint $d_{\text{gate}} = 1.0\text{ m}$ on association cost matrix.
  - Pass scaled $R$, `AnchorSource`, and confidence into matched track updates.
- [x] 2.7 (REFACTOR) Profile greedy association and Kalman update latency ($< 0.05\text{ ms}$ for 10 targets); run `pytest tests/test_kalman.py` to confirm 100% pass rate.

### Phase 3: Ground Anchor Extraction Hierarchy & Pipeline Propagation (`safety-pipeline`)
- [x] 3.1 (RED) Write unit tests in `tests/test_pipeline.py` for `extract_ground_anchor`:
  - Scenario 1 (Tier 1 `ANKLES_DUAL`): Left and right ankle confidences $\ge \tau_{\text{conf}}$ $\implies$ midpoint coordinate, `AnchorSource.ANKLES_DUAL`, confidence $= (c_{\text{left}} + c_{\text{right}}) / 2$.
  - Scenario 2 (Tier 2 `ANKLE_SINGLE`): Exactly one ankle $\ge \tau_{\text{conf}}$ $\implies$ single ankle coordinate, `AnchorSource.ANKLE_SINGLE`, confidence $= c_{\text{valid}} \times 0.75$.
  - Scenario 3 (Tier 3 `BBOX_BOTTOM`): Both ankles $< \tau_{\text{conf}}$, `allow_bbox_fallback=True`, and valid bbox $\implies$ bottom-center coordinate $((x_1+x_2)/2, y_2)$, `AnchorSource.BBOX_BOTTOM`, confidence $= c_{\text{det}} \times 0.40$.
  - Scenario 4 (Tier 4 Dropout): Both ankles $< \tau_{\text{conf}}$ and `allow_bbox_fallback=False` (or missing bbox) $\implies$ returns `None`.
  - Verify un-letterbox coordinate mapping applied across all tiers.
- [x] 3.2 (GREEN) Implement `extract_ground_anchor(keypoints, bbox=None, conf_threshold=0.5, scale=1.0, pad_x=0.0, pad_y=0.0, allow_bbox_fallback=True)` in `src/pipeline/safety_pipeline.py`.
- [x] 3.3 (RED) Write unit tests in `tests/test_pipeline.py` verifying backward compatibility of `extract_ankle_anchor`:
  - Unchanged signature `(keypoints, conf_threshold=0.5, scale=1.0, pad_x=0.0, pad_y=0.0) -> Optional[Tuple[float, float]]`.
  - Returns `None` when both ankles $< \tau_{\text{conf}}$ without attempting bbox fallback.
  - Returns un-letterboxed midpoint for dual ankles and single coordinate for single ankle.
- [x] 3.4 (GREEN) Verify `extract_ankle_anchor` in `src/pipeline/safety_pipeline.py` maintains its existing behavior and pass rate.
- [x] 3.5 (RED) Write unit tests in `tests/test_pipeline.py` for `PoseDetection` dataclass extension:
  - Positional backward compatibility: `PoseDetection(bbox, keypoints, anchor)` instantiates with `anchor_source=None` and `anchor_confidence=0.0`.
  - Keyword instantiation with `anchor_source` and `anchor_confidence`.
- [x] 3.6 (GREEN) Update `PoseDetection` dataclass in `src/pipeline/safety_pipeline.py` with default fields `anchor_source: Optional[AnchorSource] = None` and `anchor_confidence: float = 0.0`.
- [x] 3.7 (RED) Write unit tests in `tests/test_pipeline.py` for `SafetyPipeline.parse_detections` and `SafetyPipeline.process_frame`:
  - `parse_detections` extracts anchors via `extract_ground_anchor` and populates `anchor_source` and `anchor_confidence` on every detection.
  - `process_frame` projects valid anchors via `homography.project_batch` and packages ground positions into `PositionEstimate` instances passed to `tracker.update`.
  - Active tracks in `PipelineResult.tracks` expose `.estimate` carrying degraded provenance (`BBOX_BOTTOM`) and penalized confidence ($\le 0.40$).
- [x] 3.8 (GREEN) Update `SafetyPipeline.parse_detections()` and `SafetyPipeline.process_frame()` in `src/pipeline/safety_pipeline.py` to construct and propagate `PositionEstimate` objects through Stage 4 (projection) and Stage 5 (tracking).
- [x] 3.9 (REFACTOR) Profile Stage 3 (`keypoint_extract`) overhead to ensure un-letterbox and fallback logic adds $< 0.1\text{ ms}$; run `pytest tests/test_pipeline.py` to confirm 100% pass rate.

### Phase 4: End-to-End Integration, Validation & Latency Profiling
- [x] 4.1 Run complete unit test suite for modified modules: `pytest tests/test_kalman.py tests/test_pipeline.py` to confirm all TDD tests pass.
- [x] 4.2 Run full regression test suite: `pytest tests/` across all capability suites (`test_homography.py`, `test_export.py`, `test_onnx_engine.py`, `test_benchmark.py`, `test_fsm.py`, `test_visualizer.py`, `test_kalman.py`, `test_pipeline.py`) ensuring zero regressions.
- [x] 4.3 Profile pipeline end-to-end latency on synthetic frames with degraded lower-limb occlusions to verify total reaction time $t_1 \le 50.0\text{ ms}$ (ISO 13855 safety budget) and assert `PositionEstimate` creation overhead is negligible ($< 50\text{ ns}$ per detection).
- [x] 4.4 Verify typing, code style, and API documentation integrity across all modified files.
