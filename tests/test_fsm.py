"""
tests/test_fsm.py
Unit tests for SpatialFSM, ZoneConfig, OccupancyState, DwellState, SafetyOutput, and dual hysteresis.
Compliant with ISO 13855:2024 and IEC 61508 / ISO 13849 fail-safe architecture.
"""

import time
import pytest
import numpy as np

from src.core.kalman_filter import MetricKalmanFilter, ObservationStatus, Track
from src.core.spatial_fsm import (
    DwellState,
    OccupancyState,
    SafetyOutput,
    SafetyState,
    SpatialFSM,
    ZoneConfig,
)


@pytest.fixture
def standard_zone_config() -> ZoneConfig:
    """Fixture providing a standard rectangular hazard zone."""
    # 2m x 2m hazard zone centered at (2, 2): X in [1, 3], Y in [1, 3]
    return ZoneConfig(
        name="robot_cell_primary",
        danger_polygon=[(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)],
        hysteresis_buffer_m=0.20,
        warning_polygon=[(0.5, 0.5), (3.5, 0.5), (3.5, 3.5), (0.5, 3.5)],
        n_confirm=3,
        n_release=5,
        dwell_warning_s=2.0,
        dwell_violation_s=5.0,
        iso_k_speed=1.6,
    )


def make_track(
    track_id: int,
    pos: tuple,
    vel: tuple = (0.0, 0.0),
    missed_count: int = 0,
) -> Track:
    """Helper to create a confirmed track at specified position, velocity, and missed_count."""
    trk = Track(track_id=track_id, initial_position=pos, n_confirm=1, max_missed=10)
    if vel != (0.0, 0.0):
        trk.filter._x[2] = vel[0]
        trk.filter._x[3] = vel[1]
    if missed_count > 0:
        for _ in range(missed_count):
            trk.predict()
            trk.mark_missed()
    trk.filter._x[0] = pos[0]
    trk.filter._x[1] = pos[1]
    return trk


class TestSpatialFSM:
    """Unit tests for Spatial Safety FSM, Orthogonal Regions, and Dual Hysteresis."""

    def test_fsm_initialization_failsafe(self, standard_zone_config):
        """Verify fail-safe startup: state is FAULT and trip is True before first update."""
        fsm = SpatialFSM(standard_zone_config)
        assert fsm.current_state == SafetyState.FAULT
        assert fsm.occupancy_state == OccupancyState.OUTSIDE
        assert fsm.dwell_state == DwellState.NONE
        assert fsm.is_tripped is True
        assert fsm.dwell_time == 0.0

    def test_zone_config_validation(self):
        """Verify ZoneConfig parameter validation and buffer constraints."""
        valid_poly = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]

        # Buffer parameter bounds: [0.15, 0.30]
        with pytest.raises(ValueError, match="buffer"):
            ZoneConfig(name="test", danger_polygon=valid_poly, hysteresis_buffer_m=0.10)
        with pytest.raises(ValueError, match="buffer"):
            ZoneConfig(name="test", danger_polygon=valid_poly, hysteresis_buffer_m=0.35)

        # Polygon with < 3 points
        with pytest.raises(ValueError, match="polygon"):
            ZoneConfig(name="test", danger_polygon=[(0.0, 0.0), (1.0, 1.0)])

        # Self-intersecting polygon (bowtie)
        bowtie = [(0.0, 0.0), (2.0, 2.0), (2.0, 0.0), (0.0, 2.0)]
        with pytest.raises(ValueError, match="valid"):
            ZoneConfig(name="test", danger_polygon=bowtie)

        # Non-positive parameters
        with pytest.raises(ValueError, match="positive"):
            ZoneConfig(name="test", danger_polygon=valid_poly, n_confirm=0)
        with pytest.raises(ValueError, match="positive"):
            ZoneConfig(name="test", danger_polygon=valid_poly, n_release=-1)
        with pytest.raises(ValueError, match="positive"):
            ZoneConfig(name="test", danger_polygon=valid_poly, iso_k_speed=0.0)

    def test_concentric_polygon_buffering(self, standard_zone_config):
        """Verify release polygon is properly dilated and contains danger polygon."""
        fsm = SpatialFSM(standard_zone_config)
        assert fsm.danger_polygon.is_valid
        assert fsm.release_polygon.is_valid
        assert fsm.release_polygon.contains(fsm.danger_polygon)
        dist = fsm.danger_polygon.exterior.distance(fsm.release_polygon.exterior)
        assert dist == pytest.approx(0.20, abs=1e-3)

    def test_first_tick_all_clear(self, standard_zone_config):
        """Verify first update with no tracks transitions from FAULT to SAFE and OUTSIDE."""
        fsm = SpatialFSM(standard_zone_config)
        out = fsm.update(tracks=[])
        assert out.state == SafetyState.SAFE
        assert out.occupancy_state == OccupancyState.OUTSIDE
        assert out.dwell_state == DwellState.NONE
        assert out.trip is False
        assert out.warning is False
        assert fsm.current_state == SafetyState.SAFE
        assert fsm.is_tripped is False

    def test_debounce_transient_rejection(self, standard_zone_config):
        """Verify transient detection inside danger zone (< N_confirm) transitions to ENTER_PENDING."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update(tracks=[])  # transition to SAFE

        # Worker appears inside danger polygon (X=2.0, Y=2.0) for 1 frame
        t1 = make_track(1, (2.0, 2.0))
        out1 = fsm.update([t1])
        assert out1.trip is False
        assert out1.occupancy_state == OccupancyState.ENTER_PENDING
        assert out1.dwell_state == DwellState.NONE
        assert out1.warning is True

        # Worker still inside for frame 2 (< n_confirm=3)
        out2 = fsm.update([t1])
        assert out2.trip is False
        assert out2.occupancy_state == OccupancyState.ENTER_PENDING

        # Worker disappears on frame 3 -> danger count resets
        out3 = fsm.update([])
        assert out3.trip is False
        assert out3.occupancy_state == OccupancyState.OUTSIDE
        assert out3.state == SafetyState.SAFE

    def test_confirmed_intrusion_trip(self, standard_zone_config):
        """Verify sustained presence in danger polygon for N_confirm frames asserts trip and INSIDE."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update([])

        t1 = make_track(1, (2.0, 2.0))
        fsm.update([t1])  # frame 1
        fsm.update([t1])  # frame 2
        out3 = fsm.update([t1])  # frame 3 = N_confirm

        assert out3.occupancy_state == OccupancyState.INSIDE
        assert out3.dwell_state == DwellState.NORMAL
        assert out3.state == SafetyState.DANGER_INTRUSION
        assert out3.trip is True
        assert out3.warning is True
        assert 1 in out3.violating_tracks
        assert fsm.is_tripped is True

    def test_dual_spatial_hysteresis_chattering_suppression(self, standard_zone_config):
        """Verify stepping out of P_danger into buffer [P_danger, P_release] keeps INSIDE/EXIT_PENDING and tripped."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update([])

        # Step into danger for 3 frames to trigger trip
        t1 = make_track(1, (2.0, 2.0))
        for _ in range(3):
            fsm.update([t1])
        assert fsm.occupancy_state == OccupancyState.INSIDE

        # Step 0.05m outside P_danger (danger X in [1, 3], buffer X in [0.8, 3.2])
        # Position X = 3.05 is outside P_danger (3.0) but inside P_release (3.20)
        t1_buffer = make_track(1, (3.05, 2.0))
        for _ in range(10):  # remain in buffer for 10 frames
            out = fsm.update([t1_buffer])
            assert out.trip is True
            assert fsm.is_tripped is True

    def test_temporal_release_counter_and_reset_on_reentry(self, standard_zone_config):
        """Verify release requires N_release clean frames, and re-entry resets clean counter."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update([])

        # Trigger intrusion
        t1 = make_track(1, (2.0, 2.0))
        for _ in range(3):
            fsm.update([t1])
        assert fsm.occupancy_state == OccupancyState.INSIDE

        # Move completely outside P_release (X=3.5 > 3.2) for 4 clean frames (< N_release=5)
        t1_clean = make_track(1, (3.5, 2.0))
        for _ in range(4):
            out = fsm.update([t1_clean])
            assert out.trip is True
            assert out.occupancy_state == OccupancyState.EXIT_PENDING

        # Re-enter buffer zone (X=3.10 < 3.20) on frame 5 -> clean count resets to 0
        t1_reentry = make_track(1, (3.10, 2.0))
        out_reentry = fsm.update([t1_reentry])
        assert out_reentry.trip is True

        # Must now stay outside for 5 full frames again
        for i in range(5):
            out = fsm.update([t1_clean])
            if i < 4:
                assert out.trip is True
            else:
                # Frame 5: successfully cleared
                assert out.occupancy_state == OccupancyState.OUTSIDE
                assert out.dwell_state == DwellState.NONE
                assert out.trip is False

    def test_iso_13855_approach_velocity_bypass(self, standard_zone_config):
        """Verify fast approach velocity (vn >= 1.6 m/s) bypasses debounce for instant trip."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update([])

        # Fast approach in warning zone
        fast_track = make_track(1, (0.8, 2.0), vel=(1.8, 0.2))
        out = fsm.update([fast_track])
        assert out.warning is True

        # Moving into danger boundary with fast approach -> instant trip without waiting 3 frames
        inside_danger = make_track(1, (1.05, 2.0), vel=(1.8, 0.2))
        out_trip = fsm.update([inside_danger])
        assert out_trip.occupancy_state == OccupancyState.INSIDE
        assert out_trip.trip is True

    def test_dwell_time_classification_progression(self, standard_zone_config):
        """Verify orthogonal DwellState progression (NORMAL -> WARNING -> VIOLATION) inside zone."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update([], timestamp=0.0)

        t1 = make_track(1, (2.0, 2.0))
        # Frame 1 to 3: Confirm intrusion at t=0.5s
        fsm.update([t1], timestamp=0.1)
        fsm.update([t1], timestamp=0.2)
        out_confirmed = fsm.update([t1], timestamp=0.5)
        assert out_confirmed.occupancy_state == OccupancyState.INSIDE
        assert out_confirmed.dwell_state == DwellState.NORMAL
        assert out_confirmed.trip is True

        # Dwell reaches 2.5s (>= dwell_warning_s = 2.0s)
        out_warn = fsm.update([t1], timestamp=3.0)
        assert out_warn.occupancy_state == OccupancyState.INSIDE
        assert out_warn.dwell_state == DwellState.WARNING
        assert out_warn.trip is True

        # Dwell reaches 5.5s (>= dwell_violation_s = 5.0s)
        out_violation = fsm.update([t1], timestamp=6.0)
        assert out_violation.occupancy_state == OccupancyState.INSIDE
        assert out_violation.dwell_state == DwellState.VIOLATION
        assert out_violation.trip is True

    def test_muting_override_and_release(self, standard_zone_config):
        """Verify muting suppresses trip, and unmuting while occupied trips immediately."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update([])

        fsm.set_muted(True)
        assert fsm.current_state == SafetyState.MUTED

        # Target in danger while muted -> warning active, trip suppressed
        t1 = make_track(1, (2.0, 2.0))
        for _ in range(5):
            out = fsm.update([t1])
            assert out.trip is False
            assert out.warning is True

        # Release muting while target is inside danger -> immediate trip
        fsm.set_muted(False)
        out_unmute = fsm.update([t1])
        assert out_unmute.occupancy_state == OccupancyState.INSIDE
        assert out_unmute.trip is True

    def test_fault_and_lockout_latched_reset(self, standard_zone_config):
        """Verify FAULT and LOCKOUT latching and authorized manual reset behavior."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update([])

        # Trigger internal fault
        out_fault = fsm.trigger_fault("Camera stream timeout")
        assert out_fault.state == SafetyState.FAULT
        assert out_fault.trip is True
        assert fsm.is_tripped is True

        # Trigger lockout
        out_lock = fsm.trigger_lockout("Latched E-Stop")
        assert out_lock.state == SafetyState.LOCKOUT
        assert out_lock.trip is True

        # Reset clears lockout when zone is clear
        fsm.update([])
        out_reset_ok = fsm.reset()
        assert out_reset_ok.state == SafetyState.SAFE
        assert out_reset_ok.occupancy_state == OccupancyState.OUTSIDE
        assert out_reset_ok.trip is False

    def test_asymmetric_safety_deescalation(self, standard_zone_config):
        """Verify asymmetric safety de-escalation behavior."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update([])

        # 1. Danger escalation on coasting tracks (PREDICTED or STALE)
        t_predicted = make_track(1, (2.0, 2.0), missed_count=2)
        assert t_predicted.observation_status == ObservationStatus.PREDICTED
        for _ in range(3):
            out = fsm.update([t_predicted])
        assert out.occupancy_state == OccupancyState.INSIDE
        assert out.trip is True
        assert 1 in out.violating_tracks

        # 2. Coasting de-escalation prevention:
        t_coast_outside = make_track(1, (3.5, 2.0), missed_count=2)
        for _ in range(10):
            out = fsm.update([t_coast_outside])
            assert out.trip is True
            assert 1 in out.violating_tracks
            assert fsm._track_records[1].clean_count == 0

        # 3. Verified optical de-escalation:
        t_observed_outside = make_track(1, (3.5, 2.0), missed_count=0)
        for i in range(1, 6):
            out = fsm.update([t_observed_outside])
            if i < 5:
                assert out.trip is True
                assert fsm._track_records[1].clean_count == i
            else:
                assert out.occupancy_state == OccupancyState.OUTSIDE
                assert out.trip is False
                assert len(out.violating_tracks) == 0

    def test_disappearing_violator_lockout_latching(self, standard_zone_config):
        """Verify disappearing violator latches FSM into LOCKOUT."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update([])

        t_violator = make_track(1, (2.0, 2.0))
        for _ in range(3):
            fsm.update([t_violator])
        assert fsm.occupancy_state == OccupancyState.INSIDE

        # Violator suddenly pruned/disappeared
        out_lost = fsm.update([])
        assert out_lost.state == SafetyState.LOCKOUT
        assert out_lost.trip is True
        assert fsm.is_tripped is True

        out_reset = fsm.reset()
        assert out_reset.state == SafetyState.SAFE
        assert out_reset.occupancy_state == OccupancyState.OUTSIDE
        assert out_reset.trip is False
