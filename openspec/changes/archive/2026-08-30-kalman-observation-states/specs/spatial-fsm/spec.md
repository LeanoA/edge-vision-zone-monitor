# Specification Delta: Spatial Finite State Machine with Dual Hysteresis (`spatial-fsm`)

## MODIFIED Requirements

### Requirement: Temporal Debounce Confirmation and Release Counters
The `SpatialFSM` MUST implement temporal debounce counters with strict epistemological asymmetric safeguarding:
1. **Escalation Invariant**: Escalation to `DANGER_INTRUSION` MUST occur if a track resides inside $P_{\text{danger}}$ for at least $N_{\text{confirm}}$ consecutive frames (default: 3 frames), regardless of its observation status (`OBSERVED`, `PREDICTED`, or `STALE`). Proactive fail-safe tripping during dead-reckoned coasting into danger MUST be preserved. Fast approach velocities ($v_n \ge K_{\text{fast}}$) MUST continue to bypass confirmation debounce.
2. **Asymmetric De-escalation Invariant**: De-escalation back towards `SAFE` (incrementing `clean_count` and decrementing or removing violating track IDs) MUST require positive sensory verification:
   - A track residing completely outside $P_{\text{release}}$ SHALL increment `clean_count` and clear `danger_count` ONLY IF `track.observation_status == ObservationStatus.OBSERVED`.
   - If a track residing outside $P_{\text{release}}$ has `track.observation_status` of `PREDICTED` or `STALE`, `clean_count` MUST NOT increment, and the track MUST NOT contribute to hazard de-escalation.
   - De-escalation from `DANGER_INTRUSION` MUST require persistence completely outside $P_{\text{release}}$ for at least $N_{\text{release}}$ consecutive frames (default: 5 frames) with strictly `OBSERVED` status.
3. **Disappearing / Expired Violator Latch**: If a violating track that triggered or sustained `DANGER_INTRUSION` ceases to be tracked (exceeds `max_missed` and is deleted without positive optical observation outside $P_{\text{release}}$), the system MUST NOT silently release the safety trip. The FSM MUST either transition to `LOCKOUT` or retain the trip condition until explicit authorized manual reset (`fsm.reset()`) is performed.

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

### Requirement: Warning Zone Dwell Time Tracking and Freezing
The `SpatialFSM` MUST track the cumulative dwell time $t_{\text{dwell}}$ (in seconds) of any target residing continuously within the warning zone (outside $P_{\text{danger}}$ but inside $P_{\text{release}}$ or within configured warning perimeter), and MUST freeze dwell accrual during dead-reckoning coasting:
1. **Dwell Accrual under Sensory Observation**: While a target is inside the warning zone with `track.observation_status == ObservationStatus.OBSERVED`, `dwell_time_s` MUST accumulate monotonically based on wall-clock elapsed time.
2. **Dwell Freezing during Dead Reckoning**: While a target resides inside the warning zone with `track.observation_status` of `PREDICTED` or `STALE`, its `dwell_time_s` MUST be frozen at the last verified observed dwell duration. Dead reckoning SHALL NOT accrue false dwell time against unverified physical presence.
3. **Threshold Escalation**: If the frozen or active `dwell_time_s` satisfies $t_{\text{dwell}} \ge T_{\text{dwell-warn}}$ (default: $3.0\text{ s}$ or configured `dwell_warning_s`), the FSM MUST assert warning telemetry and emit a dwell warning alert.
4. **Dwell Reset**: When a target moves completely outside $P_{\text{release}}$ with `ObservationStatus.OBSERVED`, its dwell timer MUST reset to $0.0\text{ s}$.

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
