# Specification: End-to-End Safety Pipeline (`safety-pipeline`)

## Purpose
The `safety-pipeline` capability coordinates synchronous frame processing for Edge Safety Guard, linking vision letterboxing ($640\times640$), ONNX pose inference (`OnnxEngine`), ankle keypoint extraction (indices 15, 16), ground homography (`HomographyManager`), Kalman tracking (`MultiTargetKalmanTracker`), and spatial evaluation (`SpatialFSM`). It profiles stage latencies ensuring ISO 13855:2024 compliance ($t_1 \le 50\text{ ms}$, $\ge 20\text{ FPS}$) and enforces fail-safe tripping.

## Requirements

### Requirement: Synchronous Pipeline Execution Loop
The `SafetyPipeline` MUST execute a sequential loop per frame across 6 stages:
1. `preprocess`: Letterbox resize to $640\times640$ and normalize.
2. `inference`: Run forward pass via `OnnxEngine`.
3. `keypoint_extract`: Extract bounding boxes and ankle keypoints (indices 15, 16).
4. `projection`: Map ground anchors to world coordinates via `HomographyManager`.
5. `tracking`: Filter positions and estimate velocities via `MultiTargetKalmanTracker`.
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

### Requirement: Ankle Keypoint Ground Anchor Extraction
The `SafetyPipeline` MUST extract ground anchor points from detected poses using ankle keypoints (left: 15, right: 16). If both exceed confidence $\tau_{\text{conf}}$ (default: 0.5), anchor MUST be the midpoint $p = (p_{15} + p_{16}) / 2$. If one exceeds $\tau_{\text{conf}}$, that ankle MUST be used. If neither exceeds $\tau_{\text{conf}}$, the measurement MUST be dropped, allowing Kalman coasting. Anchors MUST be transformed from letterbox to camera coordinates prior to homography projection.

#### Scenario: Dual ankle midpoint calculation
- **GIVEN** detected ankles at $(200, 400)$ and $(220, 400)$ with confidence $\ge 0.5$
- **WHEN** anchor extraction executes
- **THEN** the ground anchor SHALL be $(210, 400)$ un-letterboxed to original frame coordinates.

#### Scenario: Single ankle detection fallback
- **GIVEN** a detected left ankle with confidence $0.7$ and right ankle occluded ($< 0.5$)
- **WHEN** anchor extraction executes
- **THEN** the ground anchor SHALL equal the left ankle coordinate.

#### Scenario: Dropped anchor on low confidence
- **GIVEN** a detection with both ankle confidences below $0.5$
- **WHEN** anchor extraction executes
- **THEN** zero ground anchors SHALL be produced for that detection.

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
