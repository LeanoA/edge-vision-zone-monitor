# Specification: safety-pipeline (Delta)

## MODIFIED Requirements

### Requirement: Propagate Decoupled Safety Outputs
The `SafetyPipeline` SHALL propagate decoupled `occupancy_state` and `dwell_state` in the emitted `PipelineResult`.

#### Scenario: Frame Result Delivery
- **GIVEN** a processed video frame
- **WHEN** `SafetyPipeline.process_frame()` evaluates the active tracks
- **THEN** `PipelineResult.safety_output` SHALL contain valid `occupancy_state`, `dwell_state`, `dwell_time_s`, and `trip` fields.
