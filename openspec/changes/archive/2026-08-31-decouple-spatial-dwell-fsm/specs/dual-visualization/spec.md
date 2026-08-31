# Specification: dual-visualization (Delta)

## MODIFIED Requirements

### Requirement: Decoupled State Rendering in HUD Banner
The `DualVisualizer` SHALL render the status banner displaying both the current `occupancy_state` and `dwell_state`.

#### Scenario: Rendering Incursion and Dwell Warning
- **GIVEN** a `PipelineResult` with `occupancy_state=INSIDE` and `dwell_state=WARNING` ($t_{\text{dwell}} = 6.2\text{ s}$)
- **WHEN** `DualVisualizer.render_perspective()` composites the HUD banner
- **THEN** the overlay banner SHALL explicitly show both the occupancy state (`INSIDE / TRIPPED`) and the dwell duration classification (`DWELL: WARNING (6.2s)`).
