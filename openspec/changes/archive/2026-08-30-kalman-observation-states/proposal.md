# Proposal: Epistemological Observation States & Asymmetric Safety De-escalation

## Intent
Prevent open-loop Kalman prediction from silently masquerading as physical truth by formalizing observation states (`OBSERVED`, `PREDICTED`, `STALE`), enforcing asymmetric safety de-escalation, and freezing dwell time accumulation during dead reckoning.

## Scope

### In Scope
- **Epistemological Status (`src/core/kalman_filter.py`)**: `ObservationStatus` enum (`OBSERVED`, `PREDICTED`, `STALE`), enriched `PositionEstimate` (`status`, `missed_count`), and `Track.observation_status`.
- **Asymmetric De-escalation (`src/core/spatial_fsm.py`)**: Require `OBSERVED` status to increment `clean_count`; coasting tracks cannot de-escalate danger.
- **Dwell Time Freezing (`src/core/spatial_fsm.py`)**: Freeze warning zone dwell-time accrual during coasting.
- **Documentation**: ADR-008, architecture Q&A, and README updates.

### Out of Scope
- Non-linear motion models (EKF/UKF).
- Multi-camera spatial fusion.
- Acoustic or LiDAR sensors.

## Capabilities

### Modified Capabilities
- `kalman-tracking`: Add `ObservationStatus`, `Track.observation_status`, and `PositionEstimate` enrichment with prediction horizon thresholds.
- `spatial-fsm`: Enforce asymmetric de-escalation requiring `OBSERVED` status and freeze dwell time during coasting.

### New Capabilities
- None.

## Approach
Implement Approach 3 from exploration:
1. **Epistemic Modeling**: Classify estimates as `OBSERVED` ($k=0$), `PREDICTED` ($1 \le k \le 3$, within $\Delta d = 200\text{ mm}$ buffer), and `STALE` ($4 \le k \le 5$).
2. **Contract Enrichment**: Add `ObservationStatus` to `kalman_filter.py`, expose via `PositionEstimate` and `Track.observation_status`.
3. **Asymmetric Safeguarding**: In `SpatialFSM.update`, allow danger escalation from any state; gate `clean_count` strictly on `OBSERVED` tracks.
4. **Dwell Accrual Control**: Freeze dwell time $t_{\text{dwell}}$ during unobserved intervals.

## Affected Areas
| File | Change Type | Purpose |
| :--- | :--- | :--- |
| `src/core/kalman_filter.py` | Modified | Add `ObservationStatus`, enrich `PositionEstimate`, add `Track.observation_status` |
| `src/core/spatial_fsm.py` | Modified | Enforce asymmetric de-escalation and freeze coasting dwell time |
| `docs/decisions/adr-008-kalman-observation-states.md` | New | Document ADR-008 architectural rationale |
| `docs/architecture/preguntas-y-respuestas-arquitectura.md` | Modified | Add Q16 & Q17 on observation horizons and fail-safe de-escalation |
| `README.md` | Modified | Update tracker state documentation |
| `tests/test_kalman.py` | Modified | Test `ObservationStatus` and `PositionEstimate` |
| `tests/test_fsm.py` | Modified | Test asymmetric de-escalation and dwell time freezing |

## Risks & Mitigation
- **Nuisance Trips on Brief Occlusion Exit**: Occluded workers exiting danger remain tripped until observed outside. *Mitigation*: Fail-safe per ISO 13849-1; clears upon $N_{\text{release}}$ observed frames.
- **Test Regressions**: Tests assuming auto-clearance on track loss fail. *Mitigation*: Update test fixtures with synthetic `OBSERVED` clear frames.

## Rollback Plan
Revert changes via `git checkout` on modified files and delete ADR-008.

## Success Criteria
- [ ] `Track.observation_status` returns `OBSERVED` ($k=0$), `PREDICTED` ($1 \le k \le 3$), and `STALE` ($4 \le k \le 5$).
- [ ] Danger de-escalation strictly requires $N_{\text{release}}$ consecutive `OBSERVED` frames outside $P_{\text{release}}$.
- [ ] Warning zone dwell time freezes during coasting frames.
- [ ] 100% test pass rate across `tests/test_kalman.py` and `tests/test_fsm.py`.
