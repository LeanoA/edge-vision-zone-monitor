# Tasks: Epistemological Observation States & Asymmetric Safety De-escalation

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 350 - 450 lines |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Delivery strategy | single-pr |
| Chain strategy | none |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: none
400-line budget risk: Medium

## Suggested Work Units

- **Unit 1: Foundation Types & Epistemic Kalman Tracking**
  - Files: `src/core/kalman_filter.py`, `src/core/__init__.py`, `src/pipeline/safety_pipeline.py`, `src/pipeline/__init__.py`, `tests/test_kalman.py`
  - Focused test command: `pytest tests/test_kalman.py`
  - Runtime harness: Python 3.10+ / NumPy vectorization
  - Rollback boundary: Revert changes to `src/core/kalman_filter.py`, `src/core/__init__.py`, `src/pipeline/safety_pipeline.py`, `tests/test_kalman.py`
- **Unit 2: Spatial FSM Asymmetric De-escalation & Dwell Freezing**
  - Files: `src/core/spatial_fsm.py`, `tests/test_fsm.py`
  - Focused test command: `pytest tests/test_fsm.py`
  - Runtime harness: Shapely 2.0+ prepared geometries & Python dataclasses
  - Rollback boundary: Revert changes to `src/core/spatial_fsm.py`, `tests/test_fsm.py`
- **Unit 3: Architecture Decisions & Documentation**
  - Files: `docs/decisions/adr-008-kalman-epistemology-noise-divergence.md`, `docs/architecture/preguntas-y-respuestas-arquitectura.md`, `README.md`
  - Focused test command: N/A (Documentation review & link verification)
  - Runtime harness: Markdown linting & cross-reference validation
  - Rollback boundary: Delete ADR-008, revert edits to Q&A and README

## Implementation Tasks

### Phase 1: Foundation Types & Contracts (`kalman-tracking` / `safety-pipeline`)

- [x] 1.1 (RED) Write unit tests in `tests/test_kalman.py` for `ObservationStatus` enum and enriched `PositionEstimate`:
  - Verify enum members and values: `ObservationStatus.OBSERVED == "OBSERVED"`, `ObservationStatus.PREDICTED == "PREDICTED"`, `ObservationStatus.STALE == "STALE"`.
  - Verify default field initialization: `PositionEstimate(xy_m=(1.0, 2.0), confidence=0.8, source=AnchorSource.ANKLES_DUAL)` sets `status == ObservationStatus.OBSERVED` and `missed_count == 0`.
  - Verify explicit keyword instantiation: custom `status=ObservationStatus.PREDICTED` and `missed_count=2` are stored correctly.
  - Verify validation constraints: raise `ValueError` on invalid `status` type (not an `ObservationStatus`) or negative `missed_count`.
- [x] 1.2 (GREEN) Implement `ObservationStatus(str, Enum)` and enrich `PositionEstimate` in `src/core/kalman_filter.py`:
  - Add `ObservationStatus` enum with members `OBSERVED`, `PREDICTED`, `STALE`.
  - Update `PositionEstimate` dataclass with `status: ObservationStatus = ObservationStatus.OBSERVED` and `missed_count: int = 0`.
  - Add validation checks for `status` and `missed_count` in `PositionEstimate.__post_init__`.
- [x] 1.3 (RED) Write unit tests in `tests/test_kalman.py` for `Track.observation_status` and `Track.estimate` horizon classification:
  - Scenario 1: Confirmed track with measurement update has `missed_count == 0`, `observation_status == ObservationStatus.OBSERVED`, and `estimate.status == ObservationStatus.OBSERVED`.
  - Scenario 2: Consecutive missed frames 1, 2, and 3 yield `observation_status == ObservationStatus.PREDICTED`, `estimate.status == ObservationStatus.PREDICTED`, and `estimate.missed_count == track.missed_count`.
  - Scenario 3: Consecutive missed frames 4 and 5 yield `observation_status == ObservationStatus.STALE`, `estimate.status == ObservationStatus.STALE`, and `estimate.missed_count == track.missed_count`.
  - Scenario 4: Re-detection via `track.update(...)` immediately resets `missed_count == 0` and transitions `observation_status` and `estimate.status` back to `ObservationStatus.OBSERVED`.
- [x] 1.4 (GREEN) Implement `observation_status` and enrich `estimate` property in `Track` (`src/core/kalman_filter.py`):
  - Expose `@property def observation_status(self) -> ObservationStatus` classifying `OBSERVED` ($k=0$), `PREDICTED` ($1 \le k \le 3$), and `STALE` ($k \ge 4$).
  - Update `@property def estimate(self) -> PositionEstimate` to pass `status=self.observation_status` and `missed_count=self._missed_count`.
- [x] 1.5 (GREEN) Re-export `ObservationStatus` in `src/core/__init__.py`, `src/pipeline/safety_pipeline.py`, and `src/pipeline/__init__.py` to ensure modular cross-layer accessibility.
- [x] 1.6 (REFACTOR) Run `pytest tests/test_kalman.py -k "observation or estimate"` to confirm foundation contract validity and backward compatibility.

### Phase 2: Spatial FSM Asymmetric De-escalation & Dwell Freezing (`spatial-fsm`)

- [x] 2.1 (RED) Write unit tests in `tests/test_fsm.py` for Asymmetric Safety De-escalation:
  - Verify danger escalation: A coasting track with status `PREDICTED` ($k=2$) or `STALE` ($k=4$) entering $P_{\text{danger}}$ increments `danger_count` and triggers `DANGER_INTRUSION` after $N_{\text{confirm}}$ frames (fail-safe proactive escalation).
  - Verify coasting de-escalation prevention: A track in `_violating_track_ids` coasting outside $P_{\text{release}}$ with status `PREDICTED` or `STALE` does NOT increment `record.clean_count` (remains 0), is NOT removed from `_violating_track_ids`, and the FSM remains tripped in `DANGER_INTRUSION`.
  - Verify verified optical de-escalation: A violating track outside $P_{\text{release}}$ with status `ObservationStatus.OBSERVED` increments `record.clean_count` by 1 per frame, clears the violation after $N_{\text{release}}$ frames, and safely de-escalates to `SAFE` (trip cleared).
- [x] 2.2 (GREEN) Implement Asymmetric De-escalation in `SpatialFSM.update()` (`src/core/spatial_fsm.py`):
  - Gate `record.clean_count += 1` strictly on `getattr(trk, "observation_status", ObservationStatus.OBSERVED) == ObservationStatus.OBSERVED`.
  - Prevent tracks in `PREDICTED` or `STALE` from incrementing `clean_count` or clearing `danger_count` when outside $P_{\text{release}}$.
- [x] 2.3 (RED) Write unit tests in `tests/test_fsm.py` for Warning Zone Dwell Time Freezing:
  - Scenario 1: Target residing in warning zone with `ObservationStatus.OBSERVED` accumulates `dwell_time_s` monotonically across consecutive frames.
  - Scenario 2: Target residing in warning zone that transitions to `PREDICTED` ($k=1..3$) or `STALE` ($k=4..5$) has `dwell_time_s` frozen at the last verified observed value; elapsed wall-clock time during unobserved frames is NOT accrued.
  - Scenario 3: Target re-observed in warning zone resumes monotonic accumulation from the frozen baseline plus active frame increment.
  - Scenario 4: Target moving completely outside $P_{\text{release}}$ with `ObservationStatus.OBSERVED` resets dwell time to $0.0\text{ s}$.
- [x] 2.4 (GREEN) Implement Dwell Time Freezing in `SpatialFSM.update()` (`src/core/spatial_fsm.py`):
  - Add `last_observed_dwell_s: float = 0.0` to `TrackSpatialRecord`.
  - In warning zone evaluation, advance `record.dwell_time_s` and update `record.last_observed_dwell_s` only when `observation_status == ObservationStatus.OBSERVED`.
  - When `observation_status` is `PREDICTED` or `STALE`, freeze `record.dwell_time_s = record.last_observed_dwell_s`.
- [x] 2.5 (RED) Write unit tests in `tests/test_fsm.py` for Disappearing Violator Latching:
  - Scenario 1: A non-violating track that disappears from active tracks is cleaned up normally from `_track_records`.
  - Scenario 2: A violating track in `_violating_track_ids` that disappears from active tracks (e.g. pruned after exceeding `max_missed`) triggers `trigger_lockout()`, transitioning the FSM to `LOCKOUT` with trip latched.
  - Scenario 3: FSM in `LOCKOUT` rejects automatic de-escalation and requires explicit `fsm.reset()` to return to `SAFE` once the hazard zone is confirmed clear.
- [x] 2.6 (GREEN) Implement Disappearing Violator Lockout Latching in `SpatialFSM.update()` (`src/core/spatial_fsm.py`):
  - In the inactive track cleanup loop, if a missing `tid` is present in `self._violating_track_ids`, call `self.trigger_lockout(...)` with explanatory diagnostics.
- [x] 2.7 (REFACTOR) Run `pytest tests/test_fsm.py` to confirm 100% pass rate across all spatial FSM tests.

### Phase 3: Architecture Documentation & ADR-008

- [x] 3.1 Create architectural decision record `docs/decisions/adr-008-kalman-epistemology-noise-divergence.md`:
  - Document Context: Epistemological conflation defect ("Prediction is Not Truth"), sensor dropout scenarios, and VBPD safety obligations under ISO 13855:2024 and ISO 13849-1.
  - Document Noise Spectral Decomposition: Keypoint jitter (10-30 Hz, $\pm 15\text{ mm}$), pixel quantization ($\pm 10\text{ to } 40\text{ mm}$), bounding box parallax ($\pm 100\text{ mm}$), and mathematical proof of numerical differentiation explosion ($\sigma_v \approx 0.64\text{ m/s}$, $3\sigma \approx 1.91\text{ m/s}$).
  - Document CV vs CA Justification: Biomechanical human acceleration bounds ($a_{\max} \le 3.5\text{ m/s}^2$), single-frame displacement ($\Delta x_{\text{acc}} \approx 1.94\text{ mm}$ vs $\sigma_{\text{jitter}} = 15\text{ mm}$), and proof of second derivative noise explosion in CA models ($\sigma_a \approx 33.1\text{ m/s}^2$).
  - Document Dead Reckoning Divergence Envelope: Quadratic divergence derivation ($\|\Delta \mathbf{p}\| \le \frac{1}{2} a_{\max} t^2 + v_0 t (1 - \cos \theta)$), tabular comparison against spatial hysteresis buffer ($\Delta d = 200\text{ mm}$), and justification of the 3-state horizon (`OBSERVED`, `PREDICTED`, `STALE`).
  - Document Decision: 3-state epistemic model, asymmetric safeguarding invariants (escalation permitted, de-escalation gated on optical evidence), dwell time freezing, and missing violator lockout latching.
  - Document Consequences and Compliance: Fail-safe behavior aligned with ISO 13849-1 Category 3/4 PL d/e and mitigation of nuisance trips.
- [x] 3.2 Update `docs/architecture/preguntas-y-respuestas-arquitectura.md` with Q16 & Q17:
  - Add **P16: ¿Por qué la predicción de Kalman NO es verdad física y cómo se calculan los horizontes de divergencia cinemática?** (Detallando la descomposición espectral de ruido, por qué la derivada $\Delta x/\Delta t$ falla, la justificación de CV sobre CA, y la cota cuadrática frente al colchón $\Delta d = 200\text{ mm}$).
  - Add **P17: ¿Por qué la desescalada de seguridad es asimétrica y qué ocurre cuando un intruso desaparece dentro de la zona de peligro?** (Detallando los cuatro invariantes de seguridad asimétrica, por qué la predicción puede disparar alarmas pero jamás silenciarlas, el congelamiento de dwell time y el enclavamiento en `LOCKOUT`).
- [x] 3.3 Update `README.md`:
  - Update the tracking description to document the 3-state epistemological observation framework (`OBSERVED`, `PREDICTED`, `STALE`).
  - Add the Asymmetric Safety Safeguarding principle to the spatial FSM section.
  - Add Q16 and Q17 to the study objectives and technical questions list with direct links to ADR-008.

### Phase 4: Full Regression Gate & Latency Profiling

- [x] 4.1 Run focused unit test suite for all modified modules:
  ```bash
  pytest tests/test_kalman.py tests/test_fsm.py tests/test_pipeline.py -v
  ```
- [x] 4.2 Run complete regression test suite across all capability suites:
  ```bash
  pytest tests/ -v
  ```
  Ensure 100% pass rate across `test_homography.py`, `test_export.py`, `test_onnx_engine.py`, `test_benchmark.py`, `test_fsm.py`, `test_visualizer.py`, `test_kalman.py`, and `test_pipeline.py`.
- [x] 4.3 Profile end-to-end pipeline latency on synthetic frames with occlusions and coasting:
  - Verify total reaction time $t_1 \le 50.0\text{ ms}$ (ISO 13855 safety budget).
  - Verify `observation_status` evaluation and dwell freezing add $< 10\mu\text{s}$ per frame overhead.
- [x] 4.4 Verify code style, type annotations, docstrings, and backward compatibility across all public interfaces.
