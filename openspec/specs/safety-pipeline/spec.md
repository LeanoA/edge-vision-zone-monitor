# Specification: End-to-End Safety Pipeline (`safety-pipeline`)

## Purpose
The `safety-pipeline` capability coordinates synchronous frame processing for Edge Safety Guard, linking vision letterboxing ($640\times640$), ONNX pose inference (`OnnxEngine`), ground anchor keypoint extraction (`extract_ground_anchor`), ground homography (`HomographyManager`), adaptive Kalman tracking (`MultiTargetKalmanTracker`), and spatial evaluation (`SpatialFSM`). It profiles stage latencies ensuring ISO 13855:2024 compliance ($t_1 \le 50\text{ ms}$, $\ge 20\text{ FPS}$) and enforces fail-safe tripping.

## Requirements

### Requirement: Synchronous Pipeline Execution Loop
The `SafetyPipeline` MUST execute a sequential loop per frame across 6 stages:
1. `preprocess`: Letterbox resize to $640\times640$ and normalize.
2. `inference`: Run forward pass via `OnnxEngine`.
3. `keypoint_extract`: Extract bounding boxes and ground anchor keypoints via hierarchical degradation (`extract_ground_anchor`).
4. `projection`: Map ground anchors to world coordinates via `HomographyManager`.
5. `tracking`: Filter positions, scale measurement noise by anchor source, and estimate velocities via `MultiTargetKalmanTracker`.
6. `fsm_evaluation`: Evaluate spatial zones and trip condition via `SpatialFSM`.

The pipeline MUST return a typed `PipelineResult` with `safety_output`, active `tracks`, keypoints, and per-stage `latencies`.

#### Scenario: Nominal frame processing
- **GIVEN** an initialized `SafetyPipeline` and a valid BGR frame
- **WHEN** `pipeline.process_frame(frame)` executes
- **THEN** all 6 stages SHALL run in sequential order
- **AND** the returned `PipelineResult` SHALL contain valid `safety_output` and `tracks`.

#### Scenario: Zero detection frame
- **GIVEN** a camera frame without detected persons
- **WHEN** `pipeline.process_frame(frame)` executes
- **THEN** tracker SHALL coast active tracks without spawning new tracks
- **AND** FSM SHALL evaluate safety without error.

---

### Requirement: Ingest Timestamp Profiling
The `SafetyPipeline` SHALL measure source-to-pipeline ingestion latency ($T_{\text{capture}}$) when an external capture timestamp is supplied, and report `total_system_ms` in `StageLatencies`.

#### Scenario: Processing Frame with Ingestion Timestamp
- **GIVEN** a camera frame captured at $t_{\text{capture}}$
- **WHEN** `SafetyPipeline.process_frame(frame, capture_timestamp=t_capture)` executes at $t_{\text{start}}$
- **THEN** `PipelineResult.latencies.capture_ms` SHALL measure $(t_{\text{start}} - t_{\text{capture}}) \times 1000.0$
- **AND** `PipelineResult.latencies.total_system_ms` SHALL equal $\text{capture\_ms} + \text{total\_t1\_ms}$.

---

### Requirement: Ground Anchor Graceful Degradation Hierarchy
The `SafetyPipeline` MUST implement a 4-tier graceful degradation hierarchy for extracting ground anchor points from detected human poses:
1. **Tier 1 (`ANKLES_DUAL`)**: If both left ankle (index 15) and right ankle (index 16) keypoint confidences satisfy $c_{\text{left}} \ge \tau_{\text{conf}}$ and $c_{\text{right}} \ge \tau_{\text{conf}}$ (default $\tau_{\text{conf}} = 0.5$), the ground anchor point MUST be calculated as the midpoint:
   $$p_{\text{anchor}} = \frac{p_{15} + p_{16}}{2}$$
   The resulting anchor confidence MUST be the arithmetic mean $c = (c_{\text{left}} + c_{\text{right}}) / 2$, and the anchor source MUST be tagged as `AnchorSource.ANKLES_DUAL`.
2. **Tier 2 (`ANKLE_SINGLE`)**: If exactly one ankle satisfies $c \ge \tau_{\text{conf}}$, the ground anchor point MUST be assigned to that valid ankle's coordinate:
   $$p_{\text{anchor}} = p_{\text{valid}}$$
   The resulting anchor confidence MUST be penalized to $c = c_{\text{valid}} \times 0.75$, and the anchor source MUST be tagged as `AnchorSource.ANKLE_SINGLE`.
3. **Tier 3 (`BBOX_BOTTOM`)**: If both ankle confidences fall below $\tau_{\text{conf}}$ ($c_{\text{left}} < \tau_{\text{conf}}$ and $c_{\text{right}} < \tau_{\text{conf}}$) and bounding box fallback is enabled (`allow_bbox_fallback=True`), the ground anchor point MUST be assigned to the bottom-center coordinate of the detection bounding box $(x_1, y_1, x_2, y_2)$:
   $$p_{\text{anchor}} = \left(\frac{x_1 + x_2}{2}, y_2\right)$$
   The resulting anchor confidence MUST be penalized to $c = c_{\text{det}} \times 0.40$ (where $c_{\text{det}}$ is the person detection confidence), and the anchor source MUST be tagged as `AnchorSource.BBOX_BOTTOM`.
4. **Tier 4 (Dropout / Coasting)**: If both ankle confidences fall below $\tau_{\text{conf}}$ and bounding box fallback is disabled (`allow_bbox_fallback=False`), or if no valid bounding box is present, anchor extraction MUST yield `None`, enabling downstream tracking filter coasting.

All extracted anchor coordinates MUST be un-letterboxed to original frame coordinates prior to homography projection.

The hierarchy extraction logic MUST be implemented via `extract_ground_anchor(keypoints, bbox=None, conf_threshold=0.5, scale=1.0, pad_x=0.0, pad_y=0.0, allow_bbox_fallback=True)`.

#### Scenario: Dual ankles available (Tier 1)
- **GIVEN** a detection with left ankle at $(200, 400)$ with confidence $0.9$ and right ankle at $(220, 400)$ with confidence $0.8$
- **WHEN** `extract_ground_anchor` is executed with `conf_threshold = 0.5`
- **THEN** the extracted anchor coordinate SHALL be $(210, 400)$ un-letterboxed
- **AND** the source SHALL equal `AnchorSource.ANKLES_DUAL`
- **AND** the anchor confidence SHALL equal $0.85$.

#### Scenario: Single ankle occluded (Tier 2)
- **GIVEN** a detection with left ankle at $(195, 390)$ with confidence $0.8$ and right ankle occluded with confidence $0.2$ ($< 0.5$)
- **WHEN** `extract_ground_anchor` is executed with `conf_threshold = 0.5`
- **THEN** the extracted anchor coordinate SHALL equal $(195, 390)$ un-letterboxed
- **AND** the source SHALL equal `AnchorSource.ANKLE_SINGLE`
- **AND** the anchor confidence SHALL equal $0.8 \times 0.75 = 0.60$.

#### Scenario: Both ankles occluded with bbox fallback enabled (Tier 3)
- **GIVEN** a detection with both ankle confidences below $0.5$ (e.g. $0.15$ and $0.10$)
- **AND** a valid detection bounding box $(x_1=100, y_1=50, x_2=200, y_2=450)$ with detection score $0.90$
- **WHEN** `extract_ground_anchor` is executed with `allow_bbox_fallback = True`
- **THEN** the extracted anchor coordinate SHALL equal the bottom-center coordinate $(150, 450)$ un-letterboxed
- **AND** the source SHALL equal `AnchorSource.BBOX_BOTTOM`
- **AND** the anchor confidence SHALL equal $0.90 \times 0.40 = 0.36$.

#### Scenario: Both ankles occluded without bbox fallback (Tier 4)
- **GIVEN** a detection with both ankle confidences below $0.5$
- **AND** a valid bounding box $(100, 50, 200, 450)$
- **WHEN** `extract_ground_anchor` is executed with `allow_bbox_fallback = False`
- **THEN** the function SHALL return `None`
- **AND** zero ground anchors SHALL be produced for that detection.

---

### Requirement: Backward-Compatibility Guarantee for Ankle Anchor Extraction
The existing function `extract_ankle_anchor(keypoints, conf_threshold=0.5, scale=1.0, pad_x=0.0, pad_y=0.0)` MUST maintain its exact functional signature and return type `Optional[Tuple[float, float]]`. It MUST continue to implement binary ankle midpoint and single-ankle extraction, returning `None` whenever both ankles fall below `conf_threshold`. It SHALL NOT perform bounding box fallback.

#### Scenario: Preserving legacy extract_ankle_anchor behavior
- **GIVEN** keypoints with both ankles below `conf_threshold`
- **WHEN** `extract_ankle_anchor` is called
- **THEN** the function SHALL return `None`.

#### Scenario: Preserving legacy dual ankle midpoint extraction
- **GIVEN** keypoints with both ankles exceeding `conf_threshold`
- **WHEN** `extract_ankle_anchor` is called
- **THEN** the function SHALL return the un-letterboxed tuple $(u, v)$ matching previous behavior.

---

### Requirement: PositionEstimate Metadata Propagation in PoseDetection and PipelineResult
`PoseDetection` MUST propagate ground anchor provenance and confidence:
1. `PoseDetection` MUST include optional fields `anchor_source: Optional[AnchorSource] = None` and `anchor_confidence: float = 0.0` while maintaining positional parameter compatibility `(bbox, keypoints, anchor)`.
2. In Stage 3 (`keypoint_extract`), `SafetyPipeline` MUST populate `anchor_source` and `anchor_confidence` on every valid detection.
3. In Stage 4 (`projection`) and Stage 5 (`tracking`), ground-projected anchors MUST retain their `AnchorSource` and confidence, passed to `MultiTargetKalmanTracker.update` as structured `PositionEstimate` objects or equivalent metadata.
4. `PipelineResult` MUST expose active tracks whose `.estimate` property provides a typed `PositionEstimate(xy_m, confidence, source, covariance)`.

#### Scenario: PoseDetection dataclass backward compatibility
- **GIVEN** legacy invocation `PoseDetection(bbox=b, keypoints=kp, anchor=a)`
- **WHEN** the dataclass is instantiated without new keyword arguments
- **THEN** instantiation SHALL succeed without error
- **AND** `det.anchor_source` SHALL default to `None`
- **AND** `det.anchor_confidence` SHALL default to `0.0`.

#### Scenario: Full pipeline propagation of degraded anchor metadata
- **GIVEN** an input frame containing a person with lower legs occluded by a barrier
- **WHEN** `pipeline.process_frame(frame)` executes
- **THEN** the corresponding `PoseDetection` SHALL report `anchor_source == AnchorSource.BBOX_BOTTOM`
- **AND** the resulting active track SHALL expose `track.estimate.source == AnchorSource.BBOX_BOTTOM`
- **AND** `track.estimate.confidence` SHALL be $\le 0.40$.

---

### Requirement: Sub-Millisecond Latency Profiling
The `SafetyPipeline` MUST record high-resolution timestamps (`time.perf_counter`) for each stage and total loop $t_1$. Latency $t_1$ MUST satisfy $t_1 \le 50.0\text{ ms}$ on target hardware ($\ge 20\text{ FPS}$) per ISO 13855. Latencies in milliseconds MUST be included in `PipelineResult.latencies`.

#### Scenario: Stage latency telemetry
- **GIVEN** a processed video frame
- **WHEN** `pipeline.process_frame(frame)` completes
- **THEN** `result.latencies` SHALL report non-negative durations for all 6 stages and `total_t1_ms`.

#### Scenario: Timing constraint compliance
- **GIVEN** continuous execution of nominal frames
- **WHEN** latency profiling executes
- **THEN** `total_t1_ms` SHALL NOT exceed $50.0\text{ ms}$ ($\ge 20\text{ FPS}$).

---

### Requirement: Fail-Safe Fault Containment
The `SafetyPipeline` MUST catch any runtime exception in any stage, set `SpatialFSM` state to `SafetyState.FAULT`, and assert `trip = True`.

#### Scenario: Corrupted input frame
- **GIVEN** an invalid or corrupted frame input
- **WHEN** `pipeline.process_frame(frame)` is invoked
- **THEN** the pipeline SHALL return `safety_output.trip == True` and `safety_output.state == SafetyState.FAULT`.
