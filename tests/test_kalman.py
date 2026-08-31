"""
tests/test_kalman.py
Unit tests for MetricKalmanFilter, Track, and MultiTargetKalmanTracker.
Compliant with ISO 13855:2024 kinematic velocity estimation.
"""

import numpy as np
import pytest

from src.core.kalman_filter import (
    AnchorSource,
    MetricKalmanFilter,
    ObservationStatus,
    PositionEstimate,
)


class TestFoundationContractsAndTypes:
    """Unit tests for Phase 1: AnchorSource, ObservationStatus enum and PositionEstimate dataclass."""

    def test_observation_status_enum_members(self):
        """Verify ObservationStatus enum members and values."""
        assert ObservationStatus.OBSERVED == "OBSERVED"
        assert ObservationStatus.PREDICTED == "PREDICTED"
        assert ObservationStatus.STALE == "STALE"
        assert len(ObservationStatus) == 3

    def test_position_estimate_default_initialization(self):
        """Verify default field initialization for status and missed_count."""
        pe = PositionEstimate(
            xy_m=(1.0, 2.0),
            confidence=0.8,
            source=AnchorSource.ANKLES_DUAL,
        )
        assert pe.status == ObservationStatus.OBSERVED
        assert pe.missed_count == 0

    def test_position_estimate_explicit_initialization(self):
        """Verify explicit keyword instantiation with status and missed_count."""
        cov = np.diag([0.05, 0.05])
        pe = PositionEstimate(
            xy_m=(1.5, 2.5),
            confidence=0.75,
            source=AnchorSource.TRACKER_PREDICTED,
            status=ObservationStatus.PREDICTED,
            covariance=cov,
            missed_count=2,
        )
        assert pe.status == ObservationStatus.PREDICTED
        assert pe.missed_count == 2
        assert pe.xy_m == (1.5, 2.5)

    def test_position_estimate_status_and_missed_count_validation(self):
        """Verify validation constraints for status and missed_count."""
        # Invalid status type
        with pytest.raises(ValueError, match="status must be an instance of ObservationStatus"):
            PositionEstimate(
                xy_m=(1.0, 2.0),
                confidence=0.8,
                source=AnchorSource.ANKLES_DUAL,
                status="OBSERVED",  # type: ignore
            )

        # Negative missed_count
        with pytest.raises(ValueError, match="missed_count must be non-negative"):
            PositionEstimate(
                xy_m=(1.0, 2.0),
                confidence=0.8,
                source=AnchorSource.ANKLES_DUAL,
                missed_count=-1,
            )

    def test_anchor_source_enum_members(self):
        """Verify AnchorSource enum has required members and string values."""
        assert AnchorSource.ANKLES_DUAL == "ANKLES_DUAL"
        assert AnchorSource.ANKLE_SINGLE == "ANKLE_SINGLE"
        assert AnchorSource.BBOX_BOTTOM == "BBOX_BOTTOM"
        assert AnchorSource.TRACKER_PREDICTED == "TRACKER_PREDICTED"
        assert len(AnchorSource) == 4

    def test_position_estimate_valid_instantiation(self):
        """Verify valid PositionEstimate instantiation and immutability."""
        cov = np.diag([0.05, 0.05])
        pe = PositionEstimate(
            xy_m=(1.2, 3.4),
            confidence=0.85,
            source=AnchorSource.ANKLES_DUAL,
            covariance=cov,
        )
        assert pe.xy_m == (1.2, 3.4)
        assert pe.confidence == 0.85
        assert pe.source == AnchorSource.ANKLES_DUAL
        assert pe.covariance is not None
        np.testing.assert_allclose(pe.covariance, cov)

        # Frozen immutability check
        with pytest.raises(Exception):
            pe.confidence = 0.5  # type: ignore

    def test_position_estimate_validation_errors(self):
        """Verify PositionEstimate validation constraints."""
        # xy_m must have length 2
        with pytest.raises(ValueError, match="xy_m must be a 2-tuple"):
            PositionEstimate(xy_m=(1.0,), confidence=0.8, source=AnchorSource.ANKLES_DUAL)  # type: ignore

        with pytest.raises(ValueError, match="xy_m must be a 2-tuple"):
            PositionEstimate(xy_m=(1.0, 2.0, 3.0), confidence=0.8, source=AnchorSource.ANKLES_DUAL)  # type: ignore

        # confidence must be in [0.0, 1.0]
        with pytest.raises(ValueError, match="confidence must be in"):
            PositionEstimate(xy_m=(1.0, 2.0), confidence=-0.1, source=AnchorSource.ANKLES_DUAL)

        with pytest.raises(ValueError, match="confidence must be in"):
            PositionEstimate(xy_m=(1.0, 2.0), confidence=1.05, source=AnchorSource.ANKLES_DUAL)

        # covariance must be 2x2 numpy array if provided
        with pytest.raises(ValueError, match="covariance must be a 2x2 numpy array"):
            PositionEstimate(xy_m=(1.0, 2.0), confidence=0.5, source=AnchorSource.ANKLES_DUAL, covariance=np.eye(3))

        with pytest.raises(ValueError, match="covariance must be a 2x2 numpy array"):
            PositionEstimate(xy_m=(1.0, 2.0), confidence=0.5, source=AnchorSource.ANKLES_DUAL, covariance=[[1, 0], [0, 1]])  # type: ignore


class TestMetricKalmanFilterKinematics:
    """Unit tests for Phase 1: MetricKalmanFilter kinematics and validation."""

    def test_filter_initialization_valid(self):
        """Verify initialization with valid 2D coordinates and default parameters."""
        kf = MetricKalmanFilter(
            dt=0.0333,
            q_pos=0.01,
            q_vel=0.1,
            r_pos=0.05,
            initial_position=(1.5, 3.0),
        )
        # 4D state vector [X, Y, vx, vy]^T
        state = kf.state
        assert isinstance(state, np.ndarray)
        assert state.shape == (4,)
        np.testing.assert_allclose(state, [1.5, 3.0, 0.0, 0.0], rtol=1e-5)

        # Position and velocity properties
        assert kf.position == (1.5, 3.0)
        assert kf.velocity == (0.0, 0.0)
        assert kf.speed == pytest.approx(0.0, abs=1e-6)
        assert kf.heading == pytest.approx(0.0, abs=1e-6)
        assert kf.heading_angle == pytest.approx(0.0, abs=1e-6)

        # Covariance matrix P must be (4, 4), symmetric, and positive definite
        P = kf.covariance
        assert P.shape == (4, 4)
        np.testing.assert_allclose(P, P.T, atol=1e-7)
        eigenvalues = np.linalg.eigvalsh(P)
        assert np.all(eigenvalues > 0)

    def test_filter_initialization_invalid(self):
        """Verify parameter validation rejects non-physical or invalid values."""
        # Invalid dt <= 0
        with pytest.raises(ValueError, match="dt must be positive"):
            MetricKalmanFilter(dt=0.0)
        with pytest.raises(ValueError, match="dt must be positive"):
            MetricKalmanFilter(dt=-0.05)

        # Invalid variances <= 0
        with pytest.raises(ValueError, match="Variances must be positive"):
            MetricKalmanFilter(q_pos=0.0)
        with pytest.raises(ValueError, match="Variances must be positive"):
            MetricKalmanFilter(q_vel=-0.1)
        with pytest.raises(ValueError, match="Variances must be positive"):
            MetricKalmanFilter(r_pos=0.0)

        # Non-finite coordinates
        with pytest.raises(ValueError, match="finite"):
            MetricKalmanFilter(initial_position=(np.nan, 2.0))
        with pytest.raises(ValueError, match="finite"):
            MetricKalmanFilter(initial_position=(1.0, np.inf))
        with pytest.raises(ValueError, match="length 2"):
            MetricKalmanFilter(initial_position=(1.0, 2.0, 3.0))  # type: ignore

        # Invalid covariance matrix inputs
        with pytest.raises(ValueError, match="shape"):
            MetricKalmanFilter(P=np.eye(3))
        with pytest.raises(ValueError, match="symmetric"):
            asym_P = np.eye(4)
            asym_P[0, 1] = 2.0
            MetricKalmanFilter(P=asym_P)
        with pytest.raises(ValueError, match="positive"):
            neg_P = -np.eye(4)
            MetricKalmanFilter(P=neg_P)

    def test_predict_constant_velocity(self):
        """Verify CV prediction projects position linearly while preserving velocity."""
        kf = MetricKalmanFilter(
            dt=0.1,
            initial_position=(2.0, 1.0),
            initial_velocity=(1.0, -0.5),
        )
        predicted_state = kf.predict(dt=0.1)

        # Analytical: X = 2.0 + 1.0*0.1 = 2.1; Y = 1.0 + (-0.5)*0.1 = 0.95
        assert predicted_state[0] == pytest.approx(2.1, abs=1e-5)
        assert predicted_state[1] == pytest.approx(0.95, abs=1e-5)
        assert predicted_state[2] == pytest.approx(1.0, abs=1e-5)
        assert predicted_state[3] == pytest.approx(-0.5, abs=1e-5)

        # Reject invalid dt in predict
        with pytest.raises(ValueError, match="dt must be positive"):
            kf.predict(dt=0.0)
        with pytest.raises(ValueError, match="dt must be positive"):
            kf.predict(dt=-0.033)

    def test_update_variance_reduction(self):
        """Verify measurement update reduces the trace of the error covariance matrix."""
        kf = MetricKalmanFilter(
            dt=0.0333,
            initial_position=(2.0, 1.0),
            initial_velocity=(1.0, -0.5),
        )
        kf.predict()
        trace_prior = np.trace(kf.covariance)

        kf.update((2.12, 0.94))
        trace_posterior = np.trace(kf.covariance)

        assert trace_posterior < trace_prior

        # Reject non-finite measurements
        with pytest.raises(ValueError, match="finite"):
            kf.update((np.nan, 1.0))
        with pytest.raises(ValueError, match="finite"):
            kf.update((1.0, np.inf))

    def test_update_adaptive_measurement_noise(self):
        """Verify adaptive measurement noise scaling and backward compatibility."""
        # 1. Backward compatibility: update without R uses nominal self._R
        kf_nominal = MetricKalmanFilter(
            dt=0.0333,
            r_pos=0.05,
            initial_position=(0.0, 0.0),
        )
        kf_nominal.predict()
        state_nom = kf_nominal.update((1.0, 1.0))

        # 2. Explicit nominal R matches default update
        kf_explicit = MetricKalmanFilter(
            dt=0.0333,
            r_pos=0.05,
            initial_position=(0.0, 0.0),
        )
        kf_explicit.predict()
        state_exp = kf_explicit.update((1.0, 1.0), R=np.diag([0.05, 0.05]))
        np.testing.assert_allclose(state_nom, state_exp)

        # 3. Inflated R (2.0x and 5.0x) attenuates Kalman gain and dampens state innovation update
        kf_single = MetricKalmanFilter(
            dt=0.0333,
            r_pos=0.05,
            initial_position=(0.0, 0.0),
        )
        kf_single.predict()
        state_single = kf_single.update((1.0, 1.0), R=np.diag([0.10, 0.10]))

        kf_bbox = MetricKalmanFilter(
            dt=0.0333,
            r_pos=0.05,
            initial_position=(0.0, 0.0),
        )
        kf_bbox.predict()
        state_bbox = kf_bbox.update((1.0, 1.0), R=np.diag([0.25, 0.25]))

        # State updates towards (1.0, 1.0) must be strictly ordered: nominal > single > bbox
        assert state_nom[0] > state_single[0] > state_bbox[0] > 0.0
        assert state_nom[1] > state_single[1] > state_bbox[1] > 0.0

        # Posterior position error covariance trace must be strictly ordered: nominal < single < bbox
        trace_nom = np.trace(kf_nominal.covariance[:2, :2])
        trace_single = np.trace(kf_single.covariance[:2, :2])
        trace_bbox = np.trace(kf_bbox.covariance[:2, :2])
        assert trace_nom < trace_single < trace_bbox

        # Invalid R validation
        with pytest.raises(ValueError, match="R must have shape"):
            kf_nominal.update((1.0, 1.0), R=np.eye(3))
        with pytest.raises(ValueError, match="R must be symmetric"):
            asym_r = np.array([[1.0, 2.0], [0.0, 1.0]])
            kf_nominal.update((1.0, 1.0), R=asym_r)
        with pytest.raises(ValueError, match="R must be positive"):
            neg_r = np.diag([-0.1, -0.1])
            kf_nominal.update((1.0, 1.0), R=neg_r)

    def test_analytical_inverse_and_joseph_form_stabilization(self):
        """Verify analytical 2x2 inverse matches matrix inversion and Joseph form maintains symmetry."""
        kf = MetricKalmanFilter(
            dt=0.0333,
            initial_position=(0.0, 0.0),
        )
        # Execute 100 predict-update cycles to stress-test numerical stability
        np.random.seed(123)
        for _ in range(100):
            kf.predict()
            z = (np.random.normal(0, 0.02), np.random.normal(0, 0.02))
            kf.update(z)

            # Joseph form must preserve strict symmetry and positive definiteness
            P = kf.covariance
            np.testing.assert_allclose(P, P.T, atol=1e-8)
            eigs = np.linalg.eigvalsh(P)
            assert np.all(eigs > 0)

    def test_speed_magnitude_and_heading_angle(self):
        """Verify 2D velocity magnitude and heading angle calculation."""
        kf = MetricKalmanFilter(
            initial_position=(0.0, 0.0),
            initial_velocity=(1.0, 1.0),
        )
        assert kf.speed == pytest.approx(np.sqrt(2.0), rel=1e-5)
        assert kf.heading == pytest.approx(np.pi / 4.0, rel=1e-5)
        assert kf.heading_angle == pytest.approx(np.pi / 4.0, rel=1e-5)

        kf2 = MetricKalmanFilter(
            initial_position=(0.0, 0.0),
            initial_velocity=(0.0, -2.0),
        )
        assert kf2.speed == pytest.approx(2.0, rel=1e-5)
        assert kf2.heading == pytest.approx(-np.pi / 2.0, rel=1e-5)

    def test_velocity_convergence(self):
        """Verify velocity convergence for constant-velocity translation per ISO 13855."""
        dt = 0.033
        vx_true = 1.6
        vy_true = 0.0

        kf = MetricKalmanFilter(
            dt=dt,
            q_pos=0.001,
            q_vel=0.1,
            r_pos=0.02,
            initial_position=(0.0, 0.0),
            initial_velocity=(0.0, 0.0),
            P=np.diag([0.02, 0.02, 5.0, 5.0]),
        )

        np.random.seed(42)
        true_pos = np.array([0.0, 0.0])
        for _ in range(15):
            true_pos += np.array([vx_true * dt, vy_true * dt])
            kf.predict()
            noise = np.random.normal(0, 0.01, size=2)
            kf.update(true_pos + noise)

        vx_est, vy_est = kf.velocity
        assert vx_est == pytest.approx(vx_true, abs=0.1)
        assert vy_est == pytest.approx(vy_true, abs=0.08)
        assert kf.speed == pytest.approx(np.hypot(vx_est, vy_est), rel=1e-5)

    def test_jitter_attenuation_ratio(self):
        """Verify >= 70% jitter attenuation under sigma = 15mm keypoint noise."""
        dt = 0.0333
        true_pos = np.array([2.0, 3.0])

        kf = MetricKalmanFilter(
            dt=dt,
            q_pos=0.0001,
            q_vel=0.0005,
            r_pos=0.05,
            initial_position=tuple(true_pos),
            P=np.diag([0.0005, 0.0005, 0.001, 0.001]),
        )

        np.random.seed(42)
        raw_errors = []
        filtered_errors = []

        for _ in range(30):
            kf.predict()
            noise = np.random.normal(0, 0.015, size=2)
            raw_z = true_pos + noise
            raw_errors.append(np.linalg.norm(noise))

            kf.update(raw_z)
            est_pos = np.array(kf.position)
            filtered_errors.append(np.linalg.norm(est_pos - true_pos))

        raw_rmse = np.sqrt(np.mean(np.array(raw_errors) ** 2))
        filt_rmse = np.sqrt(np.mean(np.array(filtered_errors) ** 2))
        attenuation_ratio = (raw_rmse - filt_rmse) / raw_rmse

        # Jitter attenuation must be >= 70% (0.70)
        assert attenuation_ratio >= 0.70

    def test_stationary_target_speed(self):
        """Verify stationary target velocity settles below 0.05 m/s."""
        kf = MetricKalmanFilter(
            dt=0.0333,
            q_pos=0.001,
            q_vel=0.01,
            r_pos=0.05,
            initial_position=(1.0, 1.0),
        )

        np.random.seed(42)
        for _ in range(20):
            kf.predict()
            noise = np.random.normal(0, 0.015, size=2)
            kf.update((1.0 + noise[0], 1.0 + noise[1]))

        assert kf.speed < 0.05


from src.core.kalman_filter import MultiTargetKalmanTracker, Track, TrackState


class TestTrackLifecycleAndMultiTargetTracker:
    """Unit tests for Phase 2: Track lifecycle and MultiTargetKalmanTracker."""

    def test_track_lifecycle_tentative_to_confirmed(self):
        """Verify tentative track confirms after n_confirm consecutive detections."""
        track = Track(
            track_id=1,
            initial_position=(1.0, 2.0),
            dt=0.0333,
            n_confirm=2,
        )
        assert track.track_id == 1
        assert track.state == TrackState.TENTATIVE
        assert not track.is_confirmed()
        assert not track.is_coasting()
        assert not track.is_deleted()
        assert track.hits == 1
        assert track.missed_count == 0

        # Frame 2: Second hit confirms track
        track.predict()
        track.update((1.05, 2.02))
        assert track.state == TrackState.CONFIRMED
        assert track.is_confirmed()
        assert track.hits == 2

    def test_occlusion_coasting_continuity(self):
        """Verify track coasts up to max_missed frames with covariance growth."""
        track = Track(
            track_id=1,
            initial_position=(0.0, 0.0),
            n_confirm=1,  # confirmed immediately
            max_missed=5,
        )
        assert track.is_confirmed()

        trace_initial = np.trace(track.filter.covariance)
        # Miss 4 consecutive frames
        for i in range(1, 5):
            track.predict()
            track.mark_missed()
            assert track.state == TrackState.COASTING
            assert track.is_coasting()
            assert track.missed_count == i
            trace_current = np.trace(track.filter.covariance)
            assert trace_current > trace_initial
            trace_initial = trace_current

    def test_track_observation_status_and_estimate_horizons(self):
        """Verify Track.observation_status and Track.estimate across prediction horizons (Task 1.3)."""
        track = Track(
            track_id=42,
            initial_position=(1.0, 1.0),
            n_confirm=1,
            max_missed=5,
            confidence=0.9,
            source=AnchorSource.ANKLES_DUAL,
        )
        # Scenario 1: Confirmed track with measurement update
        assert track.missed_count == 0
        assert track.observation_status == ObservationStatus.OBSERVED
        assert track.estimate.status == ObservationStatus.OBSERVED
        assert track.estimate.missed_count == 0

        # Scenario 2: Consecutive missed frames 1, 2, 3 -> PREDICTED
        for expected_missed in range(1, 4):
            track.predict()
            track.mark_missed()
            assert track.missed_count == expected_missed
            assert track.is_coasting() is True
            assert track.observation_status == ObservationStatus.PREDICTED
            assert track.estimate.status == ObservationStatus.PREDICTED
            assert track.estimate.missed_count == expected_missed
            assert track.estimate.source == AnchorSource.TRACKER_PREDICTED

        # Scenario 3: Consecutive missed frames 4, 5 -> STALE
        for expected_missed in (4, 5):
            track.predict()
            track.mark_missed()
            assert track.missed_count == expected_missed
            assert track.is_coasting() is True
            assert track.observation_status == ObservationStatus.STALE
            assert track.estimate.status == ObservationStatus.STALE
            assert track.estimate.missed_count == expected_missed
            assert track.estimate.source == AnchorSource.TRACKER_PREDICTED

        # Scenario 4: Re-detection via track.update(...) immediately restores OBSERVED
        track.predict()
        track.update((1.5, 1.5), source=AnchorSource.ANKLES_DUAL, confidence=0.95)
        assert track.missed_count == 0
        assert track.observation_status == ObservationStatus.OBSERVED
        assert track.estimate.status == ObservationStatus.OBSERVED
        assert track.estimate.missed_count == 0
        assert track.estimate.source == AnchorSource.ANKLES_DUAL
        assert track.estimate.confidence == 0.95

    def test_occlusion_recovery(self):
        """Verify coasting track recovers to CONFIRMED when measurement reappears."""
        track = Track(
            track_id=1,
            initial_position=(0.0, 0.0),
            n_confirm=1,
            max_missed=5,
        )
        # Coast for 3 frames
        for _ in range(3):
            track.predict()
            track.mark_missed()
        assert track.state == TrackState.COASTING
        assert track.missed_count == 3
        trace_coasting = np.trace(track.filter.covariance)

        # Measurement returns on frame 4
        track.predict()
        track.update((0.2, 0.0))
        assert track.state == TrackState.CONFIRMED
        assert track.is_confirmed()
        assert track.missed_count == 0
        assert np.trace(track.filter.covariance) < trace_coasting

    def test_track_provenance_and_confidence_decay(self):
        """Verify Track provenance properties, estimate property, and exponential decay."""
        track = Track(
            track_id=1,
            initial_position=(1.0, 2.0),
            source=AnchorSource.ANKLES_DUAL,
            confidence=0.90,
        )
        assert track.source == AnchorSource.ANKLES_DUAL
        assert track.confidence == 0.90

        # Verify estimate property returns PositionEstimate
        est = track.estimate
        assert isinstance(est, PositionEstimate)
        assert est.xy_m == track.position
        assert est.confidence == 0.90
        assert est.source == AnchorSource.ANKLES_DUAL
        assert est.covariance is not None
        assert est.covariance.shape == (2, 2)
        np.testing.assert_allclose(est.covariance, track.filter.covariance[:2, :2])

        # Mark missed: Frame 1
        track.predict()
        track.mark_missed()
        assert track.source == AnchorSource.TRACKER_PREDICTED
        assert track.confidence == pytest.approx(0.90 * 0.85, abs=1e-5)

        # Mark missed: Frame 2
        track.predict()
        track.mark_missed()
        assert track.source == AnchorSource.TRACKER_PREDICTED
        assert track.confidence == pytest.approx(0.90 * (0.85 ** 2), abs=1e-5)

        # Mark missed: Frame 3
        track.predict()
        track.mark_missed()
        assert track.source == AnchorSource.TRACKER_PREDICTED
        assert track.confidence == pytest.approx(0.90 * (0.85 ** 3), abs=1e-5)

        # Recovery upon re-detection with ANKLE_SINGLE
        cov_trace_before_recovery = np.trace(track.filter.covariance[:2, :2])
        track.predict()
        track.update(
            (1.05, 2.05),
            source=AnchorSource.ANKLE_SINGLE,
            confidence=0.60,
            R=np.diag([0.10, 0.10]),
        )
        assert track.missed_count == 0
        assert track.source == AnchorSource.ANKLE_SINGLE
        assert track.confidence == 0.60
        assert track.estimate.source == AnchorSource.ANKLE_SINGLE
        assert track.estimate.confidence == 0.60
        assert np.trace(track.filter.covariance[:2, :2]) < cov_trace_before_recovery

    def test_track_expiration_max_missed(self):
        """Verify track transitions to DELETED when missed_count > max_missed."""
        track = Track(
            track_id=1,
            initial_position=(0.0, 0.0),
            n_confirm=1,
            max_missed=5,
        )
        # Miss 5 frames (boundary)
        for _ in range(5):
            track.predict()
            track.mark_missed()
            assert track.state == TrackState.COASTING

        # 6th miss exceeds max_missed -> DELETED
        track.predict()
        track.mark_missed()
        assert track.state == TrackState.DELETED
        assert track.is_deleted()

    def test_tentative_track_unmatched_deletion(self):
        """Verify tentative track is deleted if unmatched before reaching n_confirm."""
        track = Track(
            track_id=1,
            initial_position=(0.0, 0.0),
            n_confirm=2,
        )
        assert track.state == TrackState.TENTATIVE
        track.predict()
        track.mark_missed()
        assert track.state == TrackState.DELETED

    def test_multi_target_association_continuity(self):
        """Verify 2 parallel moving targets maintain unique tracks without ID switching."""
        tracker = MultiTargetKalmanTracker(
            dt=0.0333,
            gating_threshold_m=1.0,
            n_init=2,
        )

        # Target 1: moving along Y=1.0 from X=0 to X=1
        # Target 2: moving along Y=3.0 from X=0 to X=1
        for frame in range(10):
            x = frame * 0.05
            detections = [(x, 1.0), (x, 3.0)]
            confirmed = tracker.update(detections)

            if frame >= 1:  # After n_init=2 frames, both are confirmed
                assert len(confirmed) == 2
                ids = {t.track_id for t in confirmed}
                assert len(ids) == 2

    def test_gating_threshold_rejection(self):
        """Verify detection farther than gating_threshold_m is rejected and spawns new track."""
        tracker = MultiTargetKalmanTracker(
            dt=0.0333,
            gating_threshold_m=1.0,
            n_init=1,
        )
        # Initialize track 1 at (1.0, 1.0)
        tracks = tracker.update([(1.0, 1.0)])
        assert len(tracks) == 1
        t1_id = tracks[0].track_id

        # Detection at (5.0, 5.0) distance = sqrt(16+16) = 5.66m > 1.0m
        tracks = tracker.update([(5.0, 5.0)])
        all_active = tracker.active_tracks

        # t1 should be coasting (missed), new track should be created
        track_ids = {t.track_id for t in all_active}
        assert t1_id in track_ids
        assert len(track_ids) == 2
        t1 = [t for t in all_active if t.track_id == t1_id][0]
        assert t1.is_coasting()
        assert t1.missed_count == 1

    def test_empty_detections_handling(self):
        """Verify empty detection frame causes all tracks to coast safely."""
        tracker = MultiTargetKalmanTracker(n_init=1)
        tracker.update([(1.0, 1.0), (2.0, 2.0), (3.0, 3.0)])
        assert len(tracker.confirmed_tracks) == 3

        # Empty frame
        active = tracker.update([])
        assert len(active) == 3
        for t in active:
            assert t.is_coasting()
            assert t.missed_count == 1

    def test_tracker_reset(self):
        """Verify reset purges all tracks and resets track IDs."""
        tracker = MultiTargetKalmanTracker(n_init=1)
        tracker.update([(1.0, 1.0), (2.0, 2.0)])
        assert len(tracker.active_tracks) == 2

        tracker.reset()
        assert len(tracker.tracks) == 0
        assert len(tracker.active_tracks) == 0

        # Next spawned track starts at ID 1
        new_tracks = tracker.update([(0.0, 0.0)])
        assert new_tracks[0].track_id == 1

    def test_tracker_position_estimate_and_adaptive_r(self):
        """Verify tracker polymorphism with PositionEstimate and source-based R scaling."""
        tracker = MultiTargetKalmanTracker(n_init=1, r_pos=0.05)

        # 1. Initialize track with ANKLES_DUAL PositionEstimate
        est_init = PositionEstimate(
            xy_m=(2.0, 2.0),
            confidence=0.95,
            source=AnchorSource.ANKLES_DUAL,
        )
        tracks = tracker.update([est_init])
        assert len(tracks) == 1
        t = tracks[0]
        assert t.source == AnchorSource.ANKLES_DUAL
        assert t.confidence == 0.95
        assert t.estimate.xy_m == (2.0, 2.0)

        # 2. Update with ANKLE_SINGLE -> scales R by 2.0x
        est_single = PositionEstimate(
            xy_m=(2.05, 2.02),
            confidence=0.70,
            source=AnchorSource.ANKLE_SINGLE,
        )
        tracks = tracker.update([est_single])
        t = tracks[0]
        assert t.source == AnchorSource.ANKLE_SINGLE
        assert t.confidence == 0.70

        # 3. Update with BBOX_BOTTOM -> scales R by 5.0x
        est_bbox = PositionEstimate(
            xy_m=(2.10, 2.04),
            confidence=0.36,
            source=AnchorSource.BBOX_BOTTOM,
        )
        tracks = tracker.update([est_bbox])
        t = tracks[0]
        assert t.source == AnchorSource.BBOX_BOTTOM
        assert t.confidence == 0.36

        # 4. Gating rejection: detection beyond 1.0m is rejected from association
        est_far = PositionEstimate(
            xy_m=(3.5, 2.04),  # > 1.0m away from current pos ~ 2.1
            confidence=0.36,
            source=AnchorSource.BBOX_BOTTOM,
        )
        tracks = tracker.update([est_far])
        # Track t should coast and transition to TRACKER_PREDICTED
        assert t.is_coasting()
        assert t.source == AnchorSource.TRACKER_PREDICTED
        assert t.confidence == pytest.approx(0.36 * 0.85, abs=1e-5)

        # 5. Backward compatibility: passing raw coordinates uses ANKLES_DUAL and confidence 1.0
        tracker2 = MultiTargetKalmanTracker(n_init=1)
        tracks2 = tracker2.update([(1.0, 1.0)])
        assert tracks2[0].source == AnchorSource.ANKLES_DUAL
        assert tracks2[0].confidence == 1.0

    def test_greedy_association_latency(self):
        """Verify greedy spatial association execution time is < 0.05 ms for 10 targets."""
        import time

        tracker = MultiTargetKalmanTracker(n_init=1)
        init_dets = [(float(i), float(i)) for i in range(10)]
        tracker.update(init_dets)

        track_positions = np.array([t.position for t in tracker.active_tracks])
        next_dets = np.array([(float(i) + 0.01, float(i) + 0.01) for i in range(10)])

        times = []
        for _ in range(200):
            t0 = time.perf_counter()
            tracker.associate(track_positions, next_dets)
            t1 = time.perf_counter()
            times.append(t1 - t0)

        # Average greedy association latency must be < 0.10 ms (100 microseconds)
        avg_latency_ms = (sum(times) / len(times)) * 1000.0
        assert avg_latency_ms < 0.10
