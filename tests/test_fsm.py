"""
tests/test_fsm.py
Unit tests for SpatialFSM, ZoneConfig, SafetyState, SafetyOutput, and dual hysteresis.
Compliant with ISO 13855:2024 and IEC 61508 / ISO 13849 fail-safe architecture.
"""

import time
import pytest
import numpy as np

from src.core.kalman_filter import MetricKalmanFilter, Track
from src.core.spatial_fsm import (
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
        iso_k_speed=1.6,
    )


def make_track(track_id: int, pos: tuple, vel: tuple = (0.0, 0.0)) -> Track:
    """Helper to create a confirmed track at specified position and velocity."""
    trk = Track(track_id=track_id, initial_position=pos, n_confirm=1)
    # Set internal velocity if specified
    if vel != (0.0, 0.0):
        trk.filter._x[2] = vel[0]
        trk.filter._x[3] = vel[1]
    return trk


class TestSpatialFSM:
    """Unit tests for Phase 3: Spatial Safety FSM and Dual Hysteresis."""

    def test_fsm_initialization_failsafe(self, standard_zone_config):
        """Verify fail-safe startup: state is FAULT and trip is True before first update."""
        fsm = SpatialFSM(standard_zone_config)
        assert fsm.current_state == SafetyState.FAULT
        assert fsm.is_tripped is True
        assert fsm.is_muted is False
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
        # P_danger strictly inside P_release
        assert fsm.release_polygon.contains(fsm.danger_polygon)
        # Minimum boundary distance equals hysteresis buffer delta_d
        dist = fsm.danger_polygon.exterior.distance(fsm.release_polygon.exterior)
        assert dist == pytest.approx(0.20, abs=1e-3)

    def test_first_tick_all_clear(self, standard_zone_config):
        """Verify first update with no tracks transitions from FAULT to SAFE."""
        fsm = SpatialFSM(standard_zone_config)
        out = fsm.update(tracks=[])
        assert out.state == SafetyState.SAFE
        assert out.trip is False
        assert out.warning is False
        assert fsm.current_state == SafetyState.SAFE
        assert fsm.is_tripped is False

    def test_debounce_transient_rejection(self, standard_zone_config):
        """Verify transient detection inside danger zone (< N_confirm) does not trip."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update(tracks=[])  # transition to SAFE

        # Worker appears inside danger polygon (X=2.0, Y=2.0) for 1 frame
        t1 = make_track(1, (2.0, 2.0))
        out1 = fsm.update([t1])
        assert out1.trip is False
        assert out1.state in (SafetyState.SAFE, SafetyState.WARNING_APPROACH)

        # Worker still inside for frame 2 (< n_confirm=3)
        out2 = fsm.update([t1])
        assert out2.trip is False

        # Worker disappears on frame 3 -> danger count resets
        out3 = fsm.update([])
        assert out3.trip is False
        assert out3.state == SafetyState.SAFE

    def test_confirmed_intrusion_trip(self, standard_zone_config):
        """Verify sustained presence in danger polygon for N_confirm frames asserts trip."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update([])

        t1 = make_track(1, (2.0, 2.0))
        fsm.update([t1])  # frame 1
        fsm.update([t1])  # frame 2
        out3 = fsm.update([t1])  # frame 3 = N_confirm

        assert out3.state == SafetyState.DANGER_INTRUSION
        assert out3.trip is True
        assert out3.warning is True
        assert 1 in out3.violating_tracks
        assert fsm.is_tripped is True

    def test_dual_spatial_hysteresis_chattering_suppression(self, standard_zone_config):
        """Verify stepping out of P_danger into buffer [P_danger, P_release] does not release trip."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update([])

        # Step into danger for 3 frames to trigger trip
        t1 = make_track(1, (2.0, 2.0))
        for _ in range(3):
            fsm.update([t1])
        assert fsm.current_state == SafetyState.DANGER_INTRUSION

        # Step 0.05m outside P_danger (danger X in [1, 3], buffer X in [0.8, 3.2])
        # Position X = 3.05 is outside P_danger (3.0) but inside P_release (3.20)
        t1_buffer = make_track(1, (3.05, 2.0))
        for _ in range(10):  # remain in buffer for 10 frames
            out = fsm.update([t1_buffer])
            assert out.state == SafetyState.DANGER_INTRUSION
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
        assert fsm.current_state == SafetyState.DANGER_INTRUSION

        # Move completely outside P_release (X=3.5 > 3.2) for 4 clean frames (< N_release=5)
        t1_clean = make_track(1, (3.5, 2.0))
        for _ in range(4):
            out = fsm.update([t1_clean])
            assert out.state == SafetyState.DANGER_INTRUSION
            assert out.trip is True

        # Re-enter buffer zone (X=3.10 < 3.20) on frame 5 -> clean count resets to 0
        t1_reentry = make_track(1, (3.10, 2.0))
        out_reentry = fsm.update([t1_reentry])
        assert out_reentry.state == SafetyState.DANGER_INTRUSION
        assert out_reentry.trip is True

        # Must now stay outside for 5 full frames again
        for i in range(5):
            out = fsm.update([t1_clean])
            if i < 4:
                assert out.state == SafetyState.DANGER_INTRUSION
                assert out.trip is True
            else:
                # Frame 5: successfully cleared
                assert out.state == SafetyState.SAFE
                assert out.trip is False

    def test_iso_13855_approach_velocity_bypass(self, standard_zone_config):
        """Verify fast approach velocity (vn >= 1.6 m/s) bypasses debounce for instant trip."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update([])

        # Track at X=0.8 (outside danger [1, 3], nearest boundary at X=1.0)
        # Inward normal points in +X direction: n = [1, 0]^T
        # Velocity vx = 1.8 m/s (> 1.6 m/s), vy = 0.2 m/s
        fast_track = make_track(1, (0.8, 2.0), vel=(1.8, 0.2))

        # First frame: fast approach detected in warning zone
        out = fsm.update([fast_track])
        assert out.warning is True

        # Moving into danger boundary with fast approach -> instant trip without waiting 3 frames
        inside_danger = make_track(1, (1.05, 2.0), vel=(1.8, 0.2))
        out_trip = fsm.update([inside_danger])
        assert out_trip.state == SafetyState.DANGER_INTRUSION
        assert out_trip.trip is True

    def test_warning_zone_and_dwell_time(self, standard_zone_config):
        """Verify warning zone detection and cumulative dwell time monitoring."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update([], timestamp=0.0)

        # Worker enters warning zone (X=0.7, Y=2.0) outside P_release (X=0.8)
        t1 = make_track(1, (0.7, 2.0))
        out1 = fsm.update([t1], timestamp=1.0)
        assert out1.state == SafetyState.WARNING_APPROACH
        assert out1.trip is False
        assert out1.warning is True

        # Dwell for 2.5 seconds (> dwell_warning_s = 2.0s)
        out2 = fsm.update([t1], timestamp=3.5)
        assert out2.state == SafetyState.WARNING_APPROACH
        assert out2.dwell_time_s >= 2.0
        assert "dwell" in out2.message.lower()

        # Step outside warning zone (X=0.2 < 0.5)
        t1_outside = make_track(1, (0.2, 2.0))
        out3 = fsm.update([t1_outside], timestamp=4.0)
        assert out3.state == SafetyState.SAFE
        assert out3.dwell_time_s == 0.0

    def test_muting_override_and_release(self, standard_zone_config):
        """Verify muting suppresses trip, and unmuting while occupied trips immediately."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update([])

        fsm.set_muted(True)
        assert fsm.current_state == SafetyState.MUTED
        assert fsm.is_muted is True

        # Target in danger while muted -> warning active, trip suppressed
        t1 = make_track(1, (2.0, 2.0))
        for _ in range(5):
            out = fsm.update([t1])
            assert out.state == SafetyState.MUTED
            assert out.trip is False
            assert out.warning is True

        # Release muting while target is inside danger -> immediate DANGER_INTRUSION trip
        fsm.set_muted(False)
        out_unmute = fsm.update([t1])
        assert out_unmute.state == SafetyState.DANGER_INTRUSION
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

        # Reset rejected when target is in danger zone
        t1 = make_track(1, (2.0, 2.0))
        fsm.update([t1])
        out_reset_rej = fsm.reset()
        assert out_reset_rej.state == SafetyState.LOCKOUT
        assert out_reset_rej.trip is True

        # Remove targets from zone
        fsm.update([])
        out_reset_ok = fsm.reset()
        assert out_reset_ok.state == SafetyState.SAFE
        assert out_reset_ok.trip is False

    def test_prepared_geometry_benchmark(self, standard_zone_config):
        """Verify containment evaluation of 10 tracks takes < 0.1 ms using Shapely prepared geometries."""
        fsm = SpatialFSM(standard_zone_config)
        fsm.update([])

        tracks = [make_track(i, (float(i) * 0.3, float(i) * 0.3)) for i in range(10)]

        times = []
        for _ in range(100):
            t0 = time.perf_counter()
            fsm.update(tracks)
            t1 = time.perf_counter()
            times.append(t1 - t0)

        avg_latency_ms = (sum(times) / len(times)) * 1000.0
        # Target is < 0.1 ms (100 microseconds)
        assert avg_latency_ms < 0.10
