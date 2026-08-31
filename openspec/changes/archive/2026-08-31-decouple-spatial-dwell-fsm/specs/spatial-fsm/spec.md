# Specification: spatial-fsm (Delta)

## MODIFIED Requirements

### Requirement: Orthogonal Spatial and Temporal State Evaluation
The spatial FSM SHALL evaluate spatial occupancy and temporal dwell duration as decoupled orthogonal statechart regions.

#### Scenario: Normal Entry and Dwell Progression
- **GIVEN** a worker track entering the danger polygon at normal approach speed ($v_n < 1.6\text{ m/s}$)
- **WHEN** the track completes $N_{\text{confirm}}$ consecutive frames inside $P_{\text{danger}}$
- **THEN** the FSM SHALL transition `occupancy_state` from `ENTER_PENDING` to `INSIDE`, assert `trip=True`, and transition `dwell_state` from `NONE` to `NORMAL` with $t_{\text{dwell}} \ge 0.0\text{ s}$.

#### Scenario: Dwell Warning and Violation Thresholds
- **GIVEN** a confirmed worker track in `occupancy_state=INSIDE`
- **WHEN** continuous presence inside the zone reaches $t_{\text{dwell}} \ge T_{\text{warn}}$ (e.g. $5.0\text{ s}$)
- **THEN** `dwell_state` SHALL transition to `WARNING`.
- **WHEN** presence reaches $t_{\text{dwell}} \ge T_{\text{violation}}$ (e.g. $10.0\text{ s}$)
- **THEN** `dwell_state` SHALL transition to `VIOLATION`.

#### Scenario: Exit Hysteresis and Dwell Reset
- **GIVEN** a worker track in `occupancy_state=INSIDE` and `dwell_state=WARNING`
- **WHEN** the track moves outside $P_{\text{danger}}$ into the buffer band
- **THEN** `occupancy_state` SHALL transition to `EXIT_PENDING`, and the dwell accumulation SHALL stop.
- **WHEN** the track completes $N_{\text{release}}$ consecutive `OBSERVED` frames outside $P_{\text{release}}$
- **THEN** `occupancy_state` SHALL transition to `OUTSIDE`, `trip` SHALL de-assert to `False`, and `dwell_state` SHALL reset to `NONE`.
