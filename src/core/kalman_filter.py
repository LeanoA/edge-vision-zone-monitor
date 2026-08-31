"""
src/core/kalman_filter.py
Discrete 2D Metric Kalman Filter and Multi-Target Tracker for Vision-Based Restricted Zone Monitoring.
Inspired by ISO 13855:2024 kinematic velocity estimation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Sequence, Tuple, Union
import numpy as np


class AnchorSource(str, Enum):
    """Origin provenance and fidelity classification of a ground position estimate."""
    ANKLES_DUAL = "ANKLES_DUAL"  # Tier 1: Midpoint of left and right ankles
    ANKLE_SINGLE = "ANKLE_SINGLE"  # Tier 2: Single detected ankle keypoint
    BBOX_BOTTOM = "BBOX_BOTTOM"  # Tier 3: Bounding box bottom-center proxy
    TRACKER_PREDICTED = "TRACKER_PREDICTED"  # Tier 4: Dead reckoning via Kalman prediction


class ObservationStatus(str, Enum):
    """
    Epistemological validity and temporal freshness of a spatial coordinate estimate.

    Members:
        OBSERVED: Fresh physical sensor detection matched and assimilated in current frame (k = 0).
        PREDICTED: Open-loop dead reckoning within safe hysteresis divergence horizon (1 <= k <= 3, <= 100ms).
        STALE: Open-loop dead reckoning exceeding safe divergence horizon (4 <= k <= max_missed, 133-167ms).
    """
    OBSERVED = "OBSERVED"
    PREDICTED = "PREDICTED"
    STALE = "STALE"


@dataclass(frozen=True)
class PositionEstimate:
    """
    Immutable metric ground position estimate with provenance, uncertainty, and observation status.

    Attributes:
        xy_m: Metric (X, Y) coordinates on the factory floor plane (meters).
        confidence: Normalized reliability metric in [0.0, 1.0].
        source: AnchorSource identifying the data tier.
        status: ObservationStatus defining epistemic freshness (default: OBSERVED).
        covariance: Optional 2x2 spatial position error covariance matrix (m^2).
        missed_count: Number of consecutive missed frames (default: 0).
    """
    xy_m: Tuple[float, float]
    confidence: float
    source: AnchorSource
    status: ObservationStatus = ObservationStatus.OBSERVED
    covariance: Optional[np.ndarray] = None
    missed_count: int = 0

    def __post_init__(self) -> None:
        if not (isinstance(self.xy_m, (tuple, list)) and len(self.xy_m) == 2):
            raise ValueError(f"xy_m must be a 2-tuple, got {self.xy_m}")
        if not (0.0 <= float(self.confidence) <= 1.0):
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence}")
        if not isinstance(self.source, AnchorSource):
            raise ValueError(f"source must be an instance of AnchorSource, got {type(self.source)}")
        if not isinstance(self.status, ObservationStatus):
            raise ValueError(f"status must be an instance of ObservationStatus, got {type(self.status)}")
        if self.missed_count < 0:
            raise ValueError(f"missed_count must be non-negative, got {self.missed_count}")
        if self.covariance is not None:
            if not isinstance(self.covariance, np.ndarray) or self.covariance.shape != (2, 2):
                raise ValueError("covariance must be a 2x2 numpy array if provided.")


class TrackState(str, Enum):
    """Lifecycle states of a tracked kinematic target."""
    TENTATIVE = "TENTATIVE"
    CONFIRMED = "CONFIRMED"
    COASTING = "COASTING"
    DELETED = "DELETED"


class MetricKalmanFilter:
    """
    2D Constant Velocity (CV) metric Kalman filter estimating position [X, Y]
    and velocity [vx, vy] on the factory floor plane (meters, m/s).
    """

    __slots__ = (
        "_dt",
        "_q_pos",
        "_q_vel",
        "_r_pos",
        "_x",
        "_P",
        "_Q",
        "_R",
        "_H",
        "_I",
        "_F_default",
    )

    def __init__(
        self,
        dt: float = 0.0333,
        q_pos: float = 0.01,
        q_vel: float = 0.1,
        r_pos: float = 0.05,
        initial_position: Optional[Union[np.ndarray, Tuple[float, float], Sequence[float]]] = None,
        initial_velocity: Optional[Union[np.ndarray, Tuple[float, float], Sequence[float]]] = None,
        P: Optional[np.ndarray] = None,
        Q: Optional[np.ndarray] = None,
        R: Optional[np.ndarray] = None,
    ) -> None:
        """
        Initialize the 2D Kalman filter with kinematic parameters.

        Args:
            dt: Sampling time interval in seconds (default: 0.0333s ~ 30 FPS).
            q_pos: Position process noise variance (m^2).
            q_vel: Velocity process noise variance ((m/s)^2).
            r_pos: Measurement noise variance (m^2).
            initial_position: Initial [X0, Y0] coordinates in meters.
            initial_velocity: Initial [vx0, vy0] velocity components in m/s.
            P: Optional custom 4x4 initial covariance matrix.
            Q: Optional custom 4x4 process noise matrix.
            R: Optional custom 2x2 measurement noise matrix.

        Raises:
            ValueError: If dt <= 0, or variances <= 0, or coordinates non-finite.
        """
        if dt <= 0.0:
            raise ValueError("dt must be positive.")
        if q_pos <= 0.0 or q_vel <= 0.0 or r_pos <= 0.0:
            raise ValueError("Variances must be positive.")

        if initial_position is None:
            pos = np.array([0.0, 0.0], dtype=np.float64)
        else:
            pos = np.asarray(initial_position, dtype=np.float64)
            if pos.shape != (2,):
                raise ValueError("initial_position must have length 2.")
            if not np.all(np.isfinite(pos)):
                raise ValueError("initial_position must contain finite real numbers.")

        if initial_velocity is None:
            vel = np.array([0.0, 0.0], dtype=np.float64)
        else:
            vel = np.asarray(initial_velocity, dtype=np.float64)
            if vel.shape != (2,):
                raise ValueError("initial_velocity must have length 2.")
            if not np.all(np.isfinite(vel)):
                raise ValueError("initial_velocity must contain finite real numbers.")

        self._dt: float = float(dt)
        self._q_pos: float = float(q_pos)
        self._q_vel: float = float(q_vel)
        self._r_pos: float = float(r_pos)

        # 4D state vector [X, Y, vx, vy]^T
        self._x: np.ndarray = np.array([pos[0], pos[1], vel[0], vel[1]], dtype=np.float64)

        # 4x4 Error Covariance Matrix P
        if P is None:
            self._P: np.ndarray = np.diag([r_pos, r_pos, 1.0, 1.0]).astype(np.float64)
        else:
            p_arr = np.asarray(P, dtype=np.float64)
            if p_arr.shape != (4, 4):
                raise ValueError("P must have shape (4, 4).")
            if not np.allclose(p_arr, p_arr.T, atol=1e-7):
                raise ValueError("P must be symmetric.")
            eigs = np.linalg.eigvalsh(p_arr)
            if np.any(eigs < -1e-9):
                raise ValueError("P must be positive semi-definite.")
            self._P = p_arr.copy()

        # 4x4 Process Noise Covariance Q
        if Q is None:
            self._Q: np.ndarray = np.diag([q_pos, q_pos, q_vel, q_vel]).astype(np.float64)
        else:
            q_arr = np.asarray(Q, dtype=np.float64)
            if q_arr.shape != (4, 4):
                raise ValueError("Q must have shape (4, 4).")
            if not np.allclose(q_arr, q_arr.T, atol=1e-7):
                raise ValueError("Q must be symmetric.")
            eigs = np.linalg.eigvalsh(q_arr)
            if np.any(eigs < -1e-9):
                raise ValueError("Q must be positive semi-definite.")
            self._Q = q_arr.copy()

        # 2x2 Measurement Noise Covariance R
        if R is None:
            self._R: np.ndarray = np.diag([r_pos, r_pos]).astype(np.float64)
        else:
            r_arr = np.asarray(R, dtype=np.float64)
            if r_arr.shape != (2, 2):
                raise ValueError("R must have shape (2, 2).")
            if not np.allclose(r_arr, r_arr.T, atol=1e-7):
                raise ValueError("R must be symmetric.")
            eigs = np.linalg.eigvalsh(r_arr)
            if np.any(eigs < -1e-9):
                raise ValueError("R must be positive semi-definite.")
            self._R = r_arr.copy()

        # Measurement matrix H (maps 4D state to 2D position)
        self._H: np.ndarray = np.array(
            [[1.0, 0.0, 0.0, 0.0],
             [0.0, 1.0, 0.0, 0.0]],
            dtype=np.float64,
        )
        self._I: np.ndarray = np.eye(4, dtype=np.float64)

        # Precomputed transition matrix for default dt
        self._F_default: np.ndarray = np.array(
            [[1.0, 0.0, self._dt, 0.0],
             [0.0, 1.0, 0.0, self._dt],
             [0.0, 0.0, 1.0, 0.0],
             [0.0, 0.0, 0.0, 1.0]],
            dtype=np.float64,
        )

    @property
    def state(self) -> np.ndarray:
        """Return the current 4D state vector [X, Y, vx, vy]^T."""
        return self._x.copy()

    @property
    def position(self) -> Tuple[float, float]:
        """Return estimated 2D position (X, Y) in meters."""
        return (float(self._x[0]), float(self._x[1]))

    @property
    def velocity(self) -> Tuple[float, float]:
        """Return estimated 2D velocity (vx, vy) in m/s."""
        return (float(self._x[2]), float(self._x[3]))

    @property
    def speed(self) -> float:
        """Return scalar speed magnitude ||v||_2 in m/s."""
        return float(np.hypot(self._x[2], self._x[3]))

    @property
    def heading(self) -> float:
        """Return heading angle theta = atan2(vy, vx) in radians."""
        return float(np.arctan2(self._x[3], self._x[2]))

    @property
    def heading_angle(self) -> float:
        """Alias for heading in radians."""
        return self.heading

    @property
    def covariance(self) -> np.ndarray:
        """Return the 4x4 error covariance matrix P."""
        return self._P.copy()

    @property
    def dt(self) -> float:
        """Return default time step in seconds."""
        return self._dt

    def predict(self, dt: Optional[float] = None) -> np.ndarray:
        """
        Project state and error covariance forward by dt using CV model.

        Args:
            dt: Optional override for time step in seconds.

        Returns:
            A priori predicted state vector [X, Y, vx, vy]^T.

        Raises:
            ValueError: If dt <= 0.
        """
        if dt is None or dt == self._dt:
            f_mat = self._F_default
        else:
            step_dt = float(dt)
            if step_dt <= 0.0:
                raise ValueError("dt must be positive.")
            f_mat = np.array(
                [[1.0, 0.0, step_dt, 0.0],
                 [0.0, 1.0, 0.0, step_dt],
                 [0.0, 0.0, 1.0, 0.0],
                 [0.0, 0.0, 0.0, 1.0]],
                dtype=np.float64,
            )

        self._x = f_mat @ self._x
        self._P = f_mat @ self._P @ f_mat.T + self._Q
        self._P = 0.5 * (self._P + self._P.T)
        return self._x.copy()

    def update(
        self,
        measurement: Union[np.ndarray, Tuple[float, float], Sequence[float]],
        R: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Incorporate 2D ground measurement [z_x, z_y] and update state.

        Args:
            measurement: Metric coordinates [z_x, z_y] in meters.
            R: Optional measurement noise covariance override (2x2). Defaults to nominal self._R.

        Returns:
            A posteriori corrected state vector [X, Y, vx, vy]^T.

        Raises:
            ValueError: If measurement contains NaN or Inf, invalid dimensions, or invalid R.
        """
        z = np.asarray(measurement, dtype=np.float64)
        if z.shape != (2,):
            raise ValueError("measurement must have length 2.")
        if not np.all(np.isfinite(z)):
            raise ValueError("measurement must contain finite real numbers.")

        if R is None:
            r_mat = self._R
        else:
            r_mat = np.asarray(R, dtype=np.float64)
            if r_mat.shape != (2, 2):
                raise ValueError("R must have shape (2, 2).")
            if not np.allclose(r_mat, r_mat.T, atol=1e-7):
                raise ValueError("R must be symmetric.")
            eigs = np.linalg.eigvalsh(r_mat)
            if np.any(eigs < -1e-9):
                raise ValueError("R must be positive semi-definite.")

        # Innovation: y = z - H * x
        y0 = z[0] - self._x[0]
        y1 = z[1] - self._x[1]
        y = np.array([y0, y1], dtype=np.float64)

        # Innovation covariance: S = H * P * H^T + R = P[:2, :2] + R
        s00 = self._P[0, 0] + r_mat[0, 0]
        s01 = self._P[0, 1] + r_mat[0, 1]
        s10 = self._P[1, 0] + r_mat[1, 0]
        s11 = self._P[1, 1] + r_mat[1, 1]
        det = s00 * s11 - s01 * s10

        if abs(det) < 1e-12:
            s_inv = np.linalg.pinv(np.array([[s00, s01], [s10, s11]], dtype=np.float64))
        else:
            inv_det = 1.0 / det
            s_inv = np.array(
                [[s11 * inv_det, -s01 * inv_det],
                 [-s10 * inv_det, s00 * inv_det]],
                dtype=np.float64,
            )

        # Kalman Gain: K = P * H^T * S^-1 = P[:, :2] @ S^-1
        p_ht = self._P[:, :2]
        k_gain = p_ht @ s_inv

        # State update
        self._x = self._x + k_gain @ y

        # Joseph form stabilized covariance update:
        a_mat = self._I.copy()
        a_mat[:, :2] -= k_gain
        self._P = a_mat @ self._P @ a_mat.T + k_gain @ r_mat @ k_gain.T
        self._P = 0.5 * (self._P + self._P.T)
        return self._x.copy()


class Track:
    """Represents a tracked target with lifecycle state and kinematic history."""

    __slots__ = (
        "_track_id",
        "_dt",
        "_n_confirm",
        "_max_missed",
        "_hits",
        "_age",
        "_missed_count",
        "_state",
        "_filter",
        "_source",
        "_confidence",
        "_last_confirmed_confidence",
    )

    def __init__(
        self,
        track_id: int,
        initial_position: Union[np.ndarray, Tuple[float, float], Sequence[float]],
        dt: float = 0.0333,
        q_pos: float = 0.01,
        q_vel: float = 0.1,
        r_pos: float = 0.05,
        n_confirm: int = 2,
        max_missed: int = 5,
        source: AnchorSource = AnchorSource.ANKLES_DUAL,
        confidence: float = 1.0,
    ) -> None:
        """
        Initialize track with unique ID and dedicated Kalman filter.

        Args:
            track_id: Unique integer tracking identifier.
            initial_position: Starting (X, Y) ground coordinates in meters.
            dt: Sampling time step in seconds.
            q_pos: Position process noise variance.
            q_vel: Velocity process noise variance.
            r_pos: Measurement noise variance.
            n_confirm: Detections required to promote TENTATIVE to CONFIRMED.
            max_missed: Consecutive missed frames allowed before DELETED.
            source: Initial AnchorSource provenance tier.
            confidence: Initial confidence scalar in [0.0, 1.0].
        """
        self._track_id: int = int(track_id)
        self._dt: float = float(dt)
        self._n_confirm: int = int(n_confirm)
        self._max_missed: int = int(max_missed)

        self._hits: int = 1
        self._age: int = 1
        self._missed_count: int = 0
        self._state: TrackState = (
            TrackState.CONFIRMED if self._hits >= self._n_confirm else TrackState.TENTATIVE
        )

        self._source: AnchorSource = source
        self._confidence: float = float(confidence)
        self._last_confirmed_confidence: float = float(confidence)

        self._filter: MetricKalmanFilter = MetricKalmanFilter(
            dt=dt,
            q_pos=q_pos,
            q_vel=q_vel,
            r_pos=r_pos,
            initial_position=initial_position,
        )

    @property
    def track_id(self) -> int:
        """Unique track integer identifier."""
        return self._track_id

    @property
    def state(self) -> TrackState:
        """Current lifecycle state."""
        return self._state

    @property
    def position(self) -> Tuple[float, float]:
        """Estimated 2D position (X, Y) in meters."""
        return self._filter.position

    @property
    def velocity(self) -> Tuple[float, float]:
        """Estimated 2D velocity (vx, vy) in m/s."""
        return self._filter.velocity

    @property
    def speed(self) -> float:
        """Scalar speed magnitude in m/s."""
        return self._filter.speed

    @property
    def heading(self) -> float:
        """Heading angle in radians."""
        return self._filter.heading

    @property
    def missed_count(self) -> int:
        """Number of consecutive missed frames."""
        return self._missed_count

    @property
    def hits(self) -> int:
        """Total number of successful measurement updates."""
        return self._hits

    @property
    def age(self) -> int:
        """Total elapsed frames since creation."""
        return self._age

    @property
    def filter(self) -> MetricKalmanFilter:
        """Underlying MetricKalmanFilter instance."""
        return self._filter

    @property
    def source(self) -> AnchorSource:
        """Current origin source of the track's position estimate."""
        return self._source

    @property
    def confidence(self) -> float:
        """Current normalized confidence score [0.0, 1.0]."""
        return self._confidence

    @property
    def observation_status(self) -> ObservationStatus:
        """
        Return current epistemological observation status based on missed frames.
        OBSERVED: missed_count == 0
        PREDICTED: 1 <= missed_count <= 3 (divergence contained within hysteresis buffer)
        STALE: missed_count >= 4 (divergence exceeds hysteresis buffer)
        """
        if self._missed_count == 0:
            return ObservationStatus.OBSERVED
        elif self._missed_count <= 3:
            return ObservationStatus.PREDICTED
        else:
            return ObservationStatus.STALE

    @property
    def estimate(self) -> PositionEstimate:
        """
        Unified immutable PositionEstimate encapsulating position, confidence,
        provenance source, observation status, error covariance, and missed count.
        """
        cov_2x2 = self._filter.covariance[:2, :2].copy()
        return PositionEstimate(
            xy_m=self.position,
            confidence=self._confidence,
            source=self._source,
            status=self.observation_status,
            covariance=cov_2x2,
            missed_count=self._missed_count,
        )

    def predict(self, dt: Optional[float] = None) -> np.ndarray:
        """Execute Kalman prediction cycle."""
        self._age += 1
        return self._filter.predict(dt)

    def update(
        self,
        measurement: Union[np.ndarray, Tuple[float, float], Sequence[float]],
        source: Optional[AnchorSource] = None,
        confidence: Optional[float] = None,
        R: Optional[np.ndarray] = None,
    ) -> None:
        """Execute Kalman update cycle and update lifecycle metrics."""
        self._filter.update(measurement, R=R)
        self._hits += 1
        self._missed_count = 0
        if source is not None:
            self._source = source
        if confidence is not None:
            self._confidence = float(confidence)
            self._last_confirmed_confidence = float(confidence)

        if self._state == TrackState.TENTATIVE:
            if self._hits >= self._n_confirm:
                self._state = TrackState.CONFIRMED
        elif self._state == TrackState.COASTING:
            self._state = TrackState.CONFIRMED

    def mark_missed(self) -> None:
        """Increment missed counter and transition lifecycle to COASTING or DELETED."""
        self._missed_count += 1
        self._source = AnchorSource.TRACKER_PREDICTED
        self._confidence = self._last_confirmed_confidence * (0.85 ** self._missed_count)

        if self._state == TrackState.TENTATIVE:
            self._state = TrackState.DELETED
        elif self._state in (TrackState.CONFIRMED, TrackState.COASTING):
            if self._missed_count > self._max_missed:
                self._state = TrackState.DELETED
            else:
                self._state = TrackState.COASTING

    def is_confirmed(self) -> bool:
        """Return True if track is in CONFIRMED state."""
        return self._state == TrackState.CONFIRMED

    def is_coasting(self) -> bool:
        """Return True if track is currently COASTING."""
        return self._state == TrackState.COASTING

    def is_deleted(self) -> bool:
        """Return True if track is DELETED."""
        return self._state == TrackState.DELETED


class MultiTargetKalmanTracker:
    """
    Manages multi-target tracking lifecycle, greedy spatial association,
    and target track pools across continuous video frames.
    """

    __slots__ = (
        "_dt",
        "_gating_threshold_m",
        "_max_missed",
        "_n_init",
        "_q_pos",
        "_q_vel",
        "_r_pos",
        "_next_id",
        "_tracks",
    )

    def __init__(
        self,
        dt: float = 0.0333,
        gating_threshold_m: float = 1.0,
        max_missed: int = 5,
        n_init: int = 2,
        q_pos: float = 0.01,
        q_vel: float = 0.1,
        r_pos: float = 0.05,
    ) -> None:
        """
        Initialize multi-target tracker.

        Args:
            dt: Sampling period in seconds.
            gating_threshold_m: Maximum Euclidean gating distance in meters.
            max_missed: Maximum consecutive missed frames before track deletion.
            n_init: Consecutive detections required to confirm a tentative track.
            q_pos: Kalman position process noise variance.
            q_vel: Kalman velocity process noise variance.
            r_pos: Kalman measurement noise variance.
        """
        self._dt: float = float(dt)
        self._gating_threshold_m: float = float(gating_threshold_m)
        self._max_missed: int = int(max_missed)
        self._n_init: int = int(n_init)
        self._q_pos: float = float(q_pos)
        self._q_vel: float = float(q_vel)
        self._r_pos: float = float(r_pos)

        self._next_id: int = 1
        self._tracks: List[Track] = []

    @property
    def dt(self) -> float:
        """Sampling period in seconds."""
        return self._dt

    @property
    def tracks(self) -> List[Track]:
        """Return all managed active tracks."""
        return list(self._tracks)

    @property
    def active_tracks(self) -> List[Track]:
        """Return all non-deleted tracks (TENTATIVE, CONFIRMED, COASTING)."""
        return [t for t in self._tracks if not t.is_deleted()]

    @property
    def confirmed_tracks(self) -> List[Track]:
        """Return all CONFIRMED and active COASTING tracks."""
        return [t for t in self._tracks if t.is_confirmed() or t.is_coasting()]

    def get_tracks(self) -> List[Track]:
        """Return confirmed and coasting tracks."""
        return self.confirmed_tracks

    def reset(self) -> None:
        """Purge all tracks and reset track counter to initial state."""
        self._next_id = 1
        self._tracks.clear()

    def associate(
        self,
        track_positions: Union[np.ndarray, Sequence[Sequence[float]]],
        detections: Union[np.ndarray, Sequence[Sequence[float]]],
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """
        Perform greedy Euclidean distance association with gating.

        Args:
            track_positions: Array of shape (N, 2) with predicted track positions.
            detections: Array of shape (M, 2) with measurement positions.

        Returns:
            Tuple of:
            - matches: List of (track_idx, det_idx) pairs.
            - unmatched_tracks: List of track indices without matching detections.
            - unmatched_detections: List of detection indices without matching tracks.
        """
        trks = np.asarray(track_positions, dtype=np.float64)
        dets = np.asarray(detections, dtype=np.float64)

        if trks.size == 0 or dets.size == 0:
            unmatched_t = list(range(len(trks)))
            unmatched_d = list(range(len(dets)))
            return [], unmatched_t, unmatched_d

        diff = trks[:, np.newaxis, :] - dets[np.newaxis, :, :]
        dist_matrix = np.hypot(diff[:, :, 0], diff[:, :, 1])

        num_tracks = len(trks)
        num_dets = len(dets)
        gate = self._gating_threshold_m

        pairs = []
        for i in range(num_tracks):
            for j in range(num_dets):
                d = dist_matrix[i, j]
                if d <= gate:
                    pairs.append((d, i, j))

        pairs.sort(key=lambda item: item[0])

        matched_tracks = set()
        matched_dets = set()
        matches = []

        for d, i, j in pairs:
            if i not in matched_tracks and j not in matched_dets:
                matched_tracks.add(i)
                matched_dets.add(j)
                matches.append((i, j))

        unmatched_tracks = [i for i in range(num_tracks) if i not in matched_tracks]
        unmatched_dets = [j for j in range(num_dets) if j not in matched_dets]

        return matches, unmatched_tracks, unmatched_dets

    def update(
        self,
        detections: Union[
            np.ndarray,
            Sequence[PositionEstimate],
            Sequence[Tuple[float, float]],
            Sequence[Sequence[float]],
        ],
    ) -> List[Track]:
        """
        Process a new frame of 2D metric ground detections.
        Executes prediction, association, updates, coasting, and birth/death lifecycle.

        Args:
            detections: Array or sequence of (M, 2) metric ground positions in meters,
                or Sequence of PositionEstimate instances.

        Returns:
            List of confirmed tracks active in the current frame.
        """
        # 1. Prediction step for all active tracks
        active = self.active_tracks
        for t in active:
            t.predict(self._dt)

        # Parse detections and provenance metadata
        parsed_coords: List[Tuple[float, float]] = []
        parsed_sources: List[AnchorSource] = []
        parsed_confs: List[float] = []

        if detections is not None and len(detections) > 0:
            if isinstance(detections[0], PositionEstimate):
                for d in detections:  # type: ignore
                    if not isinstance(d, PositionEstimate):
                        raise ValueError("Mixed detection types not supported; expected PositionEstimate.")
                    parsed_coords.append(d.xy_m)
                    parsed_sources.append(d.source)
                    parsed_confs.append(d.confidence)
            else:
                det_arr_in = np.asarray(detections, dtype=np.float64)
                if det_arr_in.ndim == 1 and det_arr_in.size == 2:
                    det_arr_in = det_arr_in.reshape(1, 2)
                elif det_arr_in.ndim != 2 or (det_arr_in.size > 0 and det_arr_in.shape[1] != 2):
                    raise ValueError("detections must have shape (N, 2).")
                for row in det_arr_in:
                    parsed_coords.append((float(row[0]), float(row[1])))
                    parsed_sources.append(AnchorSource.ANKLES_DUAL)
                    parsed_confs.append(1.0)

        num_dets = len(parsed_coords)
        det_arr = (
            np.array(parsed_coords, dtype=np.float64)
            if num_dets > 0
            else np.empty((0, 2), dtype=np.float64)
        )

        if len(active) == 0:
            # Spawn tracks for all incoming detections
            for j in range(num_dets):
                new_track = Track(
                    track_id=self._next_id,
                    initial_position=parsed_coords[j],
                    dt=self._dt,
                    q_pos=self._q_pos,
                    q_vel=self._q_vel,
                    r_pos=self._r_pos,
                    n_confirm=self._n_init,
                    max_missed=self._max_missed,
                    source=parsed_sources[j],
                    confidence=parsed_confs[j],
                )
                self._next_id += 1
                self._tracks.append(new_track)
            self._tracks = [t for t in self._tracks if not t.is_deleted()]
            return self.confirmed_tracks

        if num_dets == 0:
            for t in active:
                t.mark_missed()
            self._tracks = [t for t in self._tracks if not t.is_deleted()]
            return self.confirmed_tracks

        # Pairwise distance matrix between active tracks and detections
        track_positions = np.array([t.position for t in active], dtype=np.float64)
        matches, unmatched_track_indices, unmatched_det_indices = self.associate(
            track_positions, det_arr
        )

        source_scale_map = {
            AnchorSource.ANKLES_DUAL: 1.0,
            AnchorSource.ANKLE_SINGLE: 2.0,
            AnchorSource.BBOX_BOTTOM: 5.0,
            AnchorSource.TRACKER_PREDICTED: 1.0,
        }

        # Matched tracks
        for track_idx, det_idx in matches:
            src = parsed_sources[det_idx]
            conf = parsed_confs[det_idx]
            alpha = source_scale_map.get(src, 1.0)
            r_scaled = np.diag([alpha * self._r_pos, alpha * self._r_pos])
            active[track_idx].update(
                parsed_coords[det_idx],
                source=src,
                confidence=conf,
                R=r_scaled,
            )

        # Unmatched tracks coast
        for track_idx in unmatched_track_indices:
            active[track_idx].mark_missed()

        # Unmatched detections spawn new tentative tracks
        for det_idx in unmatched_det_indices:
            new_track = Track(
                track_id=self._next_id,
                initial_position=parsed_coords[det_idx],
                dt=self._dt,
                q_pos=self._q_pos,
                q_vel=self._q_vel,
                r_pos=self._r_pos,
                n_confirm=self._n_init,
                max_missed=self._max_missed,
                source=parsed_sources[det_idx],
                confidence=parsed_confs[det_idx],
            )
            self._next_id += 1
            self._tracks.append(new_track)

        # Prune deleted tracks
        self._tracks = [t for t in self._tracks if not t.is_deleted()]

        return self.confirmed_tracks
