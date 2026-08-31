# Specification: spatial-fsm (Delta)

## MODIFIED Requirements

### Requirement: Physical Entry Tracking and Event Reaction Latency
The `SpatialFSM` SHALL track the initial physical entry timestamp of any track entering $P_{\text{danger}}$ and compute the exact event reaction latency upon asserting `trip = True`.

#### Scenario: Computing event latency on intrusion trip
- **GIVEN** a track entering $P_{\text{danger}}$ at timestamp $t_{\text{entry}}$
- **WHEN** the FSM completes confirmation debounce and asserts `trip = True` at timestamp $t_{\text{trip}}$
- **THEN** `SafetyOutput.event_latency_ms` SHALL be populated with $(t_{\text{trip}} - t_{\text{entry}}) \times 1000.0$.
