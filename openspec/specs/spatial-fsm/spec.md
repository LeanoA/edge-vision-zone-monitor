# Specification: Spatial Finite State Machine with Dual Hysteresis (`spatial-fsm`)

## Overview
The `spatial-fsm` capability implements a 6-state deterministic safety automaton with dual concentric spatial hysteresis and temporal debounce for industrial hazard zones. Operating on filtered 2D metric tracks from `kalman-tracking`, it computes spatial containment within danger polygon $P_{\text{danger}}$ and release buffer polygon $P_{\text{release}}$ ($\Delta d \in [150, 300]\text{ mm}$ via Shapely), evaluates ISO 13855 boundary normal approach velocities ($K$), monitors warning zone dwell times, and enforces a strict fail-safe trip boolean contract (`trip == True` on danger, fault, or lockout) with $< 1\text{ ms}$ evaluation latency.

## ADDED Requirements

### Requirement: Orthogonal Spatial and Temporal State Evaluation
The spatial FSM SHALL evaluate spatial occupancy and temporal dwell duration as decoupled orthogonal statechart regions:
1. **Occupancy Automaton (`OccupancyState`)**: Evaluates geometric containment, boundary hysteresis, and approach speed across `OUTSIDE`, `ENTER_PENDING`, `INSIDE`, and `EXIT_PENDING`.
2. **Dwell Classifier (`DwellState`)**: Evaluates continuous duration accrued strictly in `INSIDE`, across `NONE`, `NORMAL`, `WARNING`, and `VIOLATION`.

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

### Requirement: 6-State Safety Automaton Definition and State Transitions
The `SpatialFSM` MUST implement supervisory states (`SAFE`, `WARNING_APPROACH`, `DANGER_INTRUSION`, `MUTED`, `FAULT`, `LOCKOUT`) alongside the orthogonal occupancy and dwell statecharts.

#### Scenario: Latching into LOCKOUT upon emergency stop trigger
- **GIVEN** the FSM in `DANGER_INTRUSION` state
- **WHEN** machine stop is initiated or zone clearance protocol begins
- **THEN** the FSM SHALL transition into `LOCKOUT` state
- **AND** the FSM SHALL remain in `LOCKOUT` even if all targets clear the zone until an explicit authorized `reset()` command is executed.

#### Scenario: Authorized manual reset from LOCKOUT to SAFE
- **GIVEN** the FSM in `LOCKOUT` state and the spatial zone is completely clear of all targets ($N_{\text{release}}$ frames verified)
- **WHEN** `fsm.reset()` is invoked by an authorized operator
- **THEN** the FSM SHALL transition to `SAFE` state
- **AND** trip signal SHALL de-assert to `False`.

#### Scenario: Rejecting manual reset when zone is not clear
- **GIVEN** the FSM in `LOCKOUT` state with an active target still inside $P_{\text{release}}$
- **WHEN** `fsm.reset()` is called
- **THEN** the FSM SHALL reject the reset request
- **AND** the state SHALL remain `LOCKOUT`
- **AND** trip signal SHALL remain `True`
- **AND** a warning log or exception SHALL indicate that the zone is obstructed.

#### Scenario: Immediate transition to FAULT on runtime exception
- **GIVEN** the FSM in any operational state (`SAFE`, `WARNING_APPROACH`, `MUTED`)
- **WHEN** an unhandled exception, NaN coordinate input, or camera failure occurs
- **THEN** the FSM MUST transition immediately to `FAULT`
- **AND** the trip signal MUST assert `True`.

#### Scenario: Muting activation with interlock
- **GIVEN** the FSM in `SAFE` state
- **WHEN** `fsm.set_muted(True)` is invoked with valid authorization
- **THEN** the FSM SHALL transition to `MUTED`
- **AND** subsequent target incursions into $P_{\text{danger}}$ SHALL NOT assert trip.

---

### Requirement: Dual Concentric Spatial Hysteresis ($P_{\text{danger}}$ and $P_{\text{release}}$)
The `SpatialFSM` MUST maintain two concentric polygons: the primary danger polygon $P_{\text{danger}}$ and an expanded release polygon $P_{\text{release}}$. The release polygon $P_{\text{release}}$ MUST be computed by dilating $P_{\text{danger}}$ outward by buffer distance $\Delta d \in [0.15, 0.30]\text{ m}$ ($150\text{ mm} \le \Delta d \le 300\text{ mm}$, default $\Delta d = 0.20\text{ m}$) using Shapely:
$$P_{\text{release}} = P_{\text{danger}} \oplus \Delta d$$
Geometric containment $P_{\text{danger}} \subset P_{\text{release}}$ MUST be strictly satisfied.

The FSM MUST apply spatial hysteresis such that:
- Entry into danger is evaluated against $P_{\text{danger}}$.
- De-escalation back towards `SAFE` is permitted ONLY after the target has fully crossed outside $P_{\text{release}}$.

#### Scenario: Precomputing concentric release boundary via Shapely buffer
- **GIVEN** a defined danger zone polygon $P_{\text{danger}}$ and buffer parameter $\Delta d = 0.20\text{ m}$ ($200\text{ mm}$)
- **WHEN** `SpatialFSM` initializes its spatial geometries
- **THEN** $P_{\text{release}}$ SHALL be generated as $P_{\text{danger}}.\text{buffer}(\Delta d)$
- **AND** the minimum Euclidean distance between the boundary $\partial P_{\text{danger}}$ and boundary $\partial P_{\text{release}}$ SHALL equal $\Delta d \pm 1\text{e-4}\text{ m}$
- **AND** $P_{\text{danger}} \subset P_{\text{release}}$ SHALL evaluate to `True`.

#### Scenario: Validating buffer parameter bounds
- **GIVEN** a buffer parameter $\Delta d < 0.15\text{ m}$ or $\Delta d > 0.30\text{ m}$
- **WHEN** `SpatialFSM` is initialized
- **THEN** the constructor SHALL raise a `ValueError` requiring $\Delta d \in [0.15, 0.30]\text{ m}$.

#### Scenario: Boundary chattering elimination within hysteresis buffer
- **GIVEN** the FSM in `DANGER_INTRUSION` state triggered by an intrusion into $P_{\text{danger}}$
- **WHEN** the target steps outside $P_{\text{danger}}$ by $0.05\text{ m}$ ($50\text{ mm}$), remaining inside $P_{\text{release}}$
- **THEN** the FSM MUST NOT de-escalate to `SAFE` or `WARNING_APPROACH`
- **AND** the FSM state SHALL remain in `DANGER_INTRUSION` (or lock into `LOCKOUT`).

#### Scenario: De-escalation condition upon completely clearing release polygon
- **GIVEN** the FSM in `DANGER_INTRUSION` (or de-escalation sequence)
- **WHEN** the target moves completely outside $P_{\text{release}}$
- **THEN** de-escalation timers/counters SHALL begin incrementing
- **AND** de-escalation SHALL only finalize when the clearance condition persists for $N_{\text{release}}$ frames.

---

### Requirement: Temporal Debounce Confirmation and Release Counters
The `SpatialFSM` MUST implement temporal debounce counters with strict epistemological asymmetric safeguarding:
1. **Escalation Invariant**: Escalation to `DANGER_INTRUSION` MUST occur if a track resides inside $P_{\text{danger}}$ for at least $N_{\text{confirm}}$ consecutive frames (default: 3 frames), regardless of its observation status (`OBSERVED`, `PREDICTED`, or `STALE`). Proactive fail-safe tripping during dead-reckoned coasting into danger MUST be preserved. Fast approach velocities ($v_n \ge K_{\text{fast}}$) MUST continue to bypass confirmation debounce.
2. **Asymmetric De-escalation Invariant**: De-escalation back towards `SAFE` (incrementing `clean_count` and decrementing or removing violating track IDs) MUST require positive sensory verification:
   - A track residing completely outside $P_{\text{release}}$ SHALL increment `clean_count` and clear `danger_count` ONLY IF `track.observation_status == ObservationStatus.OBSERVED`.
   - If a track residing outside $P_{\text{release}}$ has `track.observation_status` of `PREDICTED` or `STALE`, `clean_count` MUST NOT increment, and the track MUST NOT contribute to hazard de-escalation.
   - De-escalation from `DANGER_INTRUSION` MUST require persistence completely outside $P_{\text{release}}$ for at least $N_{\text{release}}$ consecutive frames (default: 5 frames) with strictly `OBSERVED` status.
3. **Disappearing / Expired Violator Latch**: If a violating track that triggered or sustained `DANGER_INTRUSION` ceases to be tracked (exceeds `max_missed` and is deleted without positive optical observation outside $P_{\text{release}}$), the system MUST NOT silently release the safety trip. The FSM MUST either transition to `LOCKOUT` or retain the trip condition until explicit authorized manual reset (`fsm.reset()`) is performed.

#### Scenario: Rejecting single-frame transient false positive
- **GIVEN** the FSM in `SAFE` or `WARNING_APPROACH` state and $N_{\text{confirm}} = 3$
- **WHEN** a single spurious detection inside $P_{\text{danger}}$ occurs for 1 frame, followed immediately by frames outside $P_{\text{danger}}$
- **THEN** the confirmation counter SHALL increment to 1 and then reset to 0
- **AND** the FSM state MUST NOT transition to `DANGER_INTRUSION`
- **AND** trip signal SHALL remain `False`.

#### Scenario: Confirming sustained intrusion after N_confirm frames
- **GIVEN** the FSM in `WARNING_APPROACH` state and $N_{\text{confirm}} = 3$
- **WHEN** a target resides inside $P_{\text{danger}}$ for 3 consecutive frames
- **THEN** the confirmation counter SHALL reach 3
- **AND** the FSM MUST immediately transition to `DANGER_INTRUSION`
- **AND** trip signal MUST assert `True`.

#### Scenario: Interrupted release resetting N_release counter
- **GIVEN** the FSM de-escalating with release counter at 4 frames ($N_{\text{release}} = 5$)
- **WHEN** the target re-enters $P_{\text{release}}$ on frame 5
- **THEN** the release counter SHALL be reset to 0
- **AND** the FSM MUST NOT transition to `SAFE`.

#### Scenario: De-escalation after N_release consecutive clear frames
- **GIVEN** the FSM in a de-escalating state with $N_{\text{release}} = 5$
- **WHEN** all targets remain outside $P_{\text{release}}$ for 5 consecutive frames
- **THEN** the release counter SHALL reach 5
- **AND** the FSM SHALL complete de-escalation to `SAFE` (or allow lockout clearance)
- **AND** trip signal SHALL de-assert to `False` (if not latched in `LOCKOUT`).

#### Scenario: Danger escalation triggered on PREDICTED or STALE coasting track
- **GIVEN** an active track coasting with status `PREDICTED` ($k = 2$) whose trajectory crosses inside $P_{\text{danger}}$
- **WHEN** the FSM evaluates the track over consecutive frames inside $P_{\text{danger}}$
- **THEN** `record.danger_count` SHALL increment on each frame
- **AND** upon reaching $N_{\text{confirm}}$ frames, the track SHALL be added to `_violating_track_ids`
- **AND** the FSM SHALL assert `trip = True` and transition to `DANGER_INTRUSION`.

#### Scenario: Violating track coasting outside danger zone cannot de-escalate without OBSERVED proof
- **GIVEN** a track currently in `_violating_track_ids` that caused `DANGER_INTRUSION`
- **WHEN** the track coasts outside $P_{\text{release}}$ with status `PREDICTED` or `STALE` for 5 consecutive frames
- **THEN** `record.clean_count` SHALL NOT increment and SHALL remain 0
- **AND** the track SHALL remain in `_violating_track_ids`
- **AND** the FSM SHALL NOT de-escalate towards `SAFE`
- **AND** `trip` SHALL remain `True`.

#### Scenario: Observed track outside danger cleanly increments clean_count
- **GIVEN** a track currently in `_violating_track_ids`
- **WHEN** the track is detected outside $P_{\text{release}}$ with status `ObservationStatus.OBSERVED`
- **THEN** `record.clean_count` SHALL increment by 1 on each consecutive observed frame
- **AND** after $N_{\text{release}}$ consecutive frames with `ObservationStatus.OBSERVED`, the track SHALL be removed from `_violating_track_ids`
- **AND** if no other violating tracks exist, de-escalation SHALL complete.

---

### Requirement: Boundary Normal Approach Velocity Evaluation (ISO 13855 Speed $K$)
The `SpatialFSM` MUST evaluate target velocity vectors $\vec{v} = [v_x, v_y]^T$ against the boundary normals of the hazard polygon according to ISO 13855:2024. For a target at position $\vec{p}$ approaching boundary edge segment $E$, the unit inward normal vector $\hat{n}_{\text{inward}}$ pointing into the hazard zone MUST be determined. The approach velocity component MUST be calculated as:
$$v_{\text{approach}} = \vec{v} \cdot \hat{n}_{\text{inward}}$$
If $v_{\text{approach}} \ge K_{\text{fast}}$ (where $K_{\text{fast}} = 1.6\text{ m/s}$ walking speed or $2.0\text{ m/s}$ running/hand speed per ISO 13855), the FSM MUST trigger fast-approach escalation, reducing or bypassing $N_{\text{confirm}}$ to guarantee safety stop before the boundary is breached.

#### Scenario: Inward approach velocity calculation
- **GIVEN** a danger polygon with vertical boundary at $X = 2.0\text{ m}$ (inward normal $\hat{n} = [1, 0]^T$)
- **WHEN** a target at $X = 1.5\text{ m}$ moves with velocity $\vec{v} = [1.2, 0.4]^T\text{ m/s}$
- **THEN** the computed approach velocity $v_{\text{approach}}$ SHALL equal $1.2\text{ m/s}$.

#### Scenario: Fast approach triggering ISO 13855 immediate escalation
- **GIVEN** a target in the warning buffer zone moving towards $P_{\text{danger}}$ with $v_{\text{approach}} = 1.8\text{ m/s}$ ($> K = 1.6\text{ m/s}$)
- **WHEN** the FSM processes the frame
- **THEN** the FSM SHALL trigger an accelerated approach alert
- **AND** the required confirmation frames $N_{\text{confirm}}$ SHALL be overridden to 1 frame (instant trip upon entry)
- **AND** telemetry SHALL flag `fast_approach_detected = True`.

#### Scenario: Non-threatening receding or parallel motion
- **GIVEN** a target near the hazard boundary moving parallel to the boundary ($\vec{v} \cdot \hat{n} \le 0.0$) or receding away from the hazard ($\vec{v} \cdot \hat{n} < 0.0$)
- **WHEN** approach speed is evaluated
- **THEN** $v_{\text{approach}}$ SHALL evaluate to $\le 0.0\text{ m/s}$
- **AND** no accelerated escalation SHALL occur.

---

### Requirement: Warning Zone Dwell Time Tracking and Freezing
The `SpatialFSM` MUST track the cumulative dwell time $t_{\text{dwell}}$ (in seconds) of any target residing continuously within the warning zone (outside $P_{\text{danger}}$ but inside $P_{\text{release}}$ or within configured warning perimeter), and MUST freeze dwell accrual during dead-reckoning coasting:
1. **Dwell Accrual under Sensory Observation**: While a target is inside the warning zone with `track.observation_status == ObservationStatus.OBSERVED`, `dwell_time_s` MUST accumulate monotonically based on wall-clock elapsed time.
2. **Dwell Freezing during Dead Reckoning**: While a target resides inside the warning zone with `track.observation_status` of `PREDICTED` or `STALE`, its `dwell_time_s` MUST be frozen at the last verified observed dwell duration. Dead reckoning SHALL NOT accrue false dwell time against unverified physical presence.
3. **Threshold Escalation**: If the frozen or active `dwell_time_s` satisfies $t_{\text{dwell}} \ge T_{\text{dwell\_warn}}$ (default: $3.0\text{ s}$ or configured `dwell_warning_s`), the FSM MUST assert warning telemetry and emit a dwell warning alert.
4. **Dwell Reset**: When a target moves completely outside $P_{\text{release}}$ with `ObservationStatus.OBSERVED`, its dwell timer MUST reset to $0.0\text{ s}$.

#### Scenario: Dwell time accumulation within warning zone
- **GIVEN** a target located in the warning zone between $P_{\text{danger}}$ and $P_{\text{release}}$
- **WHEN** the target remains inside the warning zone for 60 consecutive frames at $30\text{ fps}$ ($\Delta t = 0.0333\text{ s}$)
- **THEN** the tracked dwell time $t_{\text{dwell}}$ SHALL reach $2.0 \pm 0.05\text{ s}$
- **AND** telemetry payload SHALL report `dwell_time: 2.0`.

#### Scenario: Continuous dwell time accumulation during sustained observation
- **GIVEN** a target detected continuously in the warning zone with `ObservationStatus.OBSERVED`
- **WHEN** 60 consecutive observed frames elapse at $\Delta t = 0.0333\text{ s}$
- **THEN** `record.dwell_time_s` SHALL accumulate to $2.0 \pm 0.05\text{ s}$
- **AND** telemetry payload SHALL report active accumulated dwell time.

#### Scenario: Warning track freezes dwell time during occlusion
- **GIVEN** a target in the warning zone that accumulated $t_{\text{dwell}} = 1.8\text{ s}$ while `OBSERVED`
- **WHEN** the target becomes occluded and coasts in the warning zone for 3 consecutive frames as `PREDICTED`
- **THEN** `record.dwell_time_s` SHALL remain frozen at $1.8\text{ s}$
- **AND** wall-clock time elapsed during the coasting frames SHALL NOT be added to `dwell_time_s`.

#### Scenario: Resuming dwell time accumulation upon re-observation
- **GIVEN** a target with frozen dwell time $t_{\text{dwell}} = 1.8\text{ s}$ during occlusion
- **WHEN** the target is re-detected in the warning zone on frame 4 with `ObservationStatus.OBSERVED`
- **THEN** dwell time tracking SHALL resume from the frozen baseline $1.8\text{ s}$ plus the active frame increment
- **AND** dwell time accumulation SHALL continue monotonically.

#### Scenario: Dwell warning threshold escalation
- **GIVEN** configured dwell warning threshold $T_{\text{dwell\_warn}} = 3.0\text{ s}$
- **WHEN** a target dwells in the warning zone for $t_{\text{dwell}} \ge 3.0\text{ s}$
- **THEN** the FSM SHALL set `dwell_alarm = True` in the telemetry payload
- **AND** state SHALL indicate prolonged dwell warning.

#### Scenario: Dwell time reset upon exiting warning zone
- **GIVEN** a target with accumulated dwell time $t_{\text{dwell}} = 2.5\text{ s}$
- **WHEN** the target moves completely outside $P_{\text{release}}$ into the safe area
- **THEN** the dwell timer for that target SHALL be reset to $0.0\text{ s}$.

---

### Requirement: Industrial Fail-Safe Output Contract and Real-Time Latency
The `SpatialFSM` MUST return a strictly typed output tuple or object `(trip: bool, status: str, telemetry: dict)` on every evaluation cycle:
1. `trip` (boolean): MUST be `True` if state $\in \{\text{DANGER\_INTRUSION}, \text{FAULT}, \text{LOCKOUT}\}$. MUST be `False` if state $\in \{\text{SAFE}, \text{WARNING\_APPROACH}, \text{MUTED}\}$.
2. `status` (string): MUST correspond to the current state name string.
3. `telemetry` (dictionary): MUST include `timestamp`, `state`, `trip`, `active_tracks`, `min_distance_to_danger`, `max_approach_speed`, `debounce_confirm_count`, `debounce_release_count`, and `dwell_times`.
4. Latency: The total execution time of `fsm.step()` MUST be strictly less than $1.0\text{ ms}$ on standard edge CPU hardware for up to 10 simultaneous targets.

#### Scenario: Fail-safe trip assertion on danger intrusion
- **GIVEN** the FSM transitioned to `DANGER_INTRUSION`
- **WHEN** `fsm.step()` produces its output
- **THEN** `trip` SHALL be `True`
- **AND** `status` SHALL equal `"DANGER_INTRUSION"`.

#### Scenario: Fail-safe trip assertion on system fault
- **GIVEN** the FSM transitioned to `FAULT`
- **WHEN** `fsm.step()` produces its output
- **THEN** `trip` SHALL be `True`
- **AND** `status` SHALL equal `"FAULT"`.

#### Scenario: Normal safe output
- **GIVEN** the FSM in `SAFE` state with no targets near hazard
- **WHEN** `fsm.step()` executes
- **THEN** `trip` SHALL be `False`
- **AND** `status` SHALL equal `"SAFE"`.

#### Scenario: Real-time execution latency constraint (< 1 ms)
- **GIVEN** an active FSM configured with complex polygonal boundaries and 5 active tracked targets
- **WHEN** `fsm.step(tracks)` is executed
- **THEN** the elapsed processing duration SHALL be strictly less than $1.0\text{ ms}$.
