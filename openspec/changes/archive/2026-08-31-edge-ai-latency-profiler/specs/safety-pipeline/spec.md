# Specification: safety-pipeline (Delta)

## MODIFIED Requirements

### Requirement: Ingest Timestamp Profiling
The `SafetyPipeline` SHALL measure source-to-pipeline ingestion latency ($T_{\text{capture}}$) when an external capture timestamp is supplied, and report `total_system_ms` in `StageLatencies`.

#### Scenario: Processing Frame with Ingestion Timestamp
- **GIVEN** a camera frame captured at $t_{\text{capture}}$
- **WHEN** `SafetyPipeline.process_frame(frame, capture_timestamp=t_capture)` executes at $t_{\text{start}}$
- **THEN** `PipelineResult.latencies.capture_ms` SHALL measure $(t_{\text{start}} - t_{\text{capture}}) \times 1000.0$
- **AND** `PipelineResult.latencies.total_system_ms` SHALL equal $\text{capture\_ms} + \text{total\_t1\_ms}$.
