# Specification: demo-orchestrator

## Overview
End-to-end command-line interface execution, video source decoding, interactive display window, video writer, and structured telemetry export for industrial vision safety monitoring.

---

### Requirement: Unified Source Ingestion
The demo runner SHALL accept video files, numerical webcam indices, or RTSP/HTTP streams.

#### Scenario: File Source Ingestion
- **GIVEN** a valid video file path (e.g. `data/samples/sequence_a_clean_incursion.mp4`)
- **WHEN** `DemoRunner.initialize()` is called with the source path
- **THEN** it SHALL successfully open the video capture and query native resolution and frame rate.

#### Scenario: Webcam Index Ingestion
- **GIVEN** an integer string source (e.g. `"0"` or `"1"`)
- **WHEN** `DemoRunner.initialize()` is called
- **THEN** it SHALL parse the source as an integer and open the corresponding capture device index.

---

### Requirement: Headless Execution Safeguard
The demo runner SHALL allow headless execution via `--no-display` without attempting to open GUI windows or calling `cv2.imshow`.

#### Scenario: Headless Processing in CI
- **GIVEN** a configuration with `no_display=True`
- **WHEN** `DemoRunner.run()` processes frames
- **THEN** it SHALL execute all pipeline stages and dual visualization render logic without calling OpenCV GUI functions (`cv2.namedWindow`, `cv2.imshow`).

---

### Requirement: Video Recording & Telemetry Export
The demo runner SHALL support optional recording of composited dual-stream video and line-delimited JSON telemetry export.

#### Scenario: Recording Annotated Video
- **GIVEN** an output video path specified via `--output-video`
- **WHEN** `DemoRunner.run()` processes frames
- **THEN** it SHALL write composited frames to the output file using the `mp4v` codec matching input FPS and composited dimensions.

#### Scenario: Telemetry Streaming
- **GIVEN** an output events path specified via `--output-events`
- **WHEN** `DemoRunner.run()` evaluates each frame
- **THEN** it SHALL append a valid JSON object containing `frame_id`, `timestamp`, `safety_state`, `trip_active`, `tracks`, and `latencies_ms`.

---

### Requirement: Stream Summary Metrics
The demo runner SHALL compute aggregate metrics upon stream completion.

#### Scenario: Summary Compilation
- **GIVEN** a completed execution of $N > 0$ frames
- **WHEN** `DemoRunner.get_summary()` is called
- **THEN** it SHALL compute `total_frames`, `average_fps`, latency percentiles (mean, p50, p95, p99), and safety state occurrence counts.
