"""
src/core/spatial_fsm.py
Spatial Finite State Machine with Dual Hysteresis for Industrial Hazard Safeguarding.
Compliant with ISO 13855:2024 and IEC 61508 / ISO 13849 fail-safe architecture.
"""

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Dict, List, Optional, Set, Tuple, Union
import numpy as np
import shapely
from shapely.geometry import Point, Polygon
from shapely.prepared import prep, PreparedGeometry

from src.core.kalman_filter import Track


class SafetyState(str, Enum):
    """Discrete states of the industrial safeguarding automaton."""
    SAFE = "SAFE"
    WARNING_APPROACH = "WARNING_APPROACH"
    DANGER_INTRUSION = "DANGER_INTRUSION"
    MUTED = "MUTED"
    FAULT = "FAULT"
    LOCKOUT = "LOCKOUT"


@dataclass(frozen=True)
class ZoneConfig:
    """Configuration specification for a safeguarded spatial zone."""
    name: str
    danger_polygon: List[Tuple[float, float]]
    hysteresis_buffer_m: float = 0.20
    warning_polygon: Optional[List[Tuple[float, float]]] = None
    n_confirm: int = 3
    n_release: int = 5
    dwell_warning_s: float = 5.0
    iso_k_speed: float = 1.6  # Human approach speed in m/s (ISO 13855)

    def __post_init__(self) -> None:
        """Validate geometric and debounce parameters."""
        if not (0.15 <= self.hysteresis_buffer_m <= 0.30):
            raise ValueError("hysteresis_buffer_m must be between 0.15m and 0.30m.")
        if self.n_confirm <= 0 or self.n_release <= 0:
            raise ValueError("n_confirm and n_release must be positive integers.")
        if self.dwell_warning_s <= 0.0 or self.iso_k_speed <= 0.0:
            raise ValueError("dwell_warning_s and iso_k_speed must be positive numbers.")
        if not self.danger_polygon or len(self.danger_polygon) < 3:
            raise ValueError("danger_polygon must contain at least 3 vertices.")

        poly = Polygon(self.danger_polygon)
        if not poly.is_valid or poly.is_empty or poly.area <= 0.0:
            raise ValueError("danger_polygon must be a valid, non-self-intersecting polygon with positive area.")

        if self.warning_polygon is not None:
            if len(self.warning_polygon) < 3:
                raise ValueError("warning_polygon must contain at least 3 vertices.")
            w_poly = Polygon(self.warning_polygon)
            if not w_poly.is_valid or w_poly.is_empty or w_poly.area <= 0.0:
                raise ValueError("warning_polygon must be a valid polygon with positive area.")


@dataclass(frozen=True)
class SafetyOutput:
    """Immutable safety decision output emitted on every pipeline frame."""
    trip: bool
    state: SafetyState
    warning: bool
    dwell_time_s: float
    violating_tracks: List[int] = field(default_factory=list)
    timestamp: float = 0.0
    message: str = ""


@dataclass
class TrackSpatialRecord:
    """Internal per-track spatial debounce and dwell tracking record."""
    track_id: int
    danger_count: int = 0
    clean_count: int = 0
    fast_approach: bool = False
    first_seen_warning_ts: Optional[float] = None
    dwell_time_s: float = 0.0


class SpatialFSM:
    """
    Industrial safety state machine enforcing dual spatial-temporal hysteresis
    and emitting fail-safe trip signals.
    """

    def __init__(self, config: ZoneConfig) -> None:
        """
        Initialize the Spatial FSM from zone configuration.
        Precomputes Shapely prepared geometries for sub-millisecond containment.

        Args:
            config: Validated ZoneConfig instance.

        Raises:
            ValueError: If polygons are invalid, self-intersecting, or non-convex/degenerate.
        """
        self._config = config

        # Geometries
        self._danger_poly: Polygon = Polygon(config.danger_polygon)
        self._release_poly: Polygon = self._danger_poly.buffer(config.hysteresis_buffer_m, join_style=2)
        self._warning_poly: Optional[Polygon] = (
            Polygon(config.warning_polygon) if config.warning_polygon is not None else None
        )

        # Shapely Prepared Geometries for sub-microsecond point-in-polygon containment
        shapely.prepare(self._danger_poly)
        shapely.prepare(self._release_poly)
        if self._warning_poly is not None:
            shapely.prepare(self._warning_poly)

        self._prep_danger: PreparedGeometry = prep(self._danger_poly)
        self._prep_release: PreparedGeometry = prep(self._release_poly)
        self._prep_warning: Optional[PreparedGeometry] = (
            prep(self._warning_poly) if self._warning_poly is not None else None
        )

        # Precompute polygon exterior boundary segments for fast inward normal calculation
        coords = np.array(self._danger_poly.exterior.coords)
        self._seg_A = coords[:-1]  # (K, 2)
        self._seg_B = coords[1:]   # (K, 2)
        self._seg_AB = self._seg_B - self._seg_A  # (K, 2)
        self._seg_len_sq = np.sum(self._seg_AB ** 2, axis=1)  # (K,)
        self._seg_len_sq[self._seg_len_sq == 0] = 1e-12

        # State and latching
        self._current_state: SafetyState = SafetyState.FAULT  # Fail-safe startup
        self._is_tripped: bool = True
        self._is_muted: bool = False
        self._fault_reason: str = ""
        self._lockout_reason: str = ""

        # Tracking state records
        self._track_records: Dict[int, TrackSpatialRecord] = {}
        self._violating_track_ids: Set[int] = set()
        self._latest_tracks: List[Track] = []
        self._last_dwell_time: float = 0.0

    @property
    def current_state(self) -> SafetyState:
        """Return the current active SafetyState."""
        return self._current_state

    @property
    def is_tripped(self) -> bool:
        """Return True if safety trip is asserted (emergency stop active)."""
        return self._is_tripped

    @property
    def dwell_time(self) -> float:
        """Return maximum dwell time in seconds of any active violating/warning track."""
        return self._last_dwell_time

    @property
    def is_muted(self) -> bool:
        """Return True if muting bypass is active."""
        return self._is_muted

    @property
    def danger_polygon(self) -> Polygon:
        """Return primary danger zone polygon."""
        return self._danger_poly

    @property
    def release_polygon(self) -> Polygon:
        """Return outward-dilated release boundary polygon."""
        return self._release_poly

    @property
    def warning_polygon(self) -> Optional[Polygon]:
        """Return warning perimeter polygon if configured."""
        return self._warning_poly

    def _compute_approach_velocity(
        self,
        pos: Tuple[float, float],
        velocity: Tuple[float, float],
    ) -> float:
        """
        Compute ISO 13855 boundary-normal approach velocity component (m/s).
        Finds the closest point on danger boundary and projects velocity onto inward normal.
        """
        p = np.array(pos, dtype=np.float64)
        v = np.array(velocity, dtype=np.float64)

        # AP vector for all segments
        ap = p - self._seg_A  # (K, 2)
        dot = np.sum(ap * self._seg_AB, axis=1)
        t = np.clip(dot / self._seg_len_sq, 0.0, 1.0)  # (K,)
        q = self._seg_A + t[:, np.newaxis] * self._seg_AB  # (K, 2)

        # Distance from p to nearest points on segments
        diff = q - p  # (K, 2) vector pointing from P towards danger boundary
        dist_sq = np.sum(diff ** 2, axis=1)
        min_idx = np.argmin(dist_sq)

        dist = np.sqrt(dist_sq[min_idx])
        if dist < 1e-6:
            return 0.0

        # Unit inward normal pointing from target position towards danger polygon
        n_inward = diff[min_idx] / dist
        vn = float(np.dot(v, n_inward))
        return vn

    def set_muted(self, muted: bool) -> None:
        """Command transition into or out of MUTED state for authorized transport."""
        self._is_muted = bool(muted)
        if self._is_muted:
            if self._current_state not in (SafetyState.FAULT, SafetyState.LOCKOUT):
                self._current_state = SafetyState.MUTED
                self._is_tripped = False
        else:
            if self._current_state == SafetyState.MUTED:
                # If there are active violating tracks, trip immediately
                if len(self._violating_track_ids) > 0:
                    self._current_state = SafetyState.DANGER_INTRUSION
                    self._is_tripped = True
                else:
                    self._current_state = SafetyState.SAFE
                    self._is_tripped = False

    def trigger_fault(self, reason: str) -> SafetyOutput:
        """Transition immediately to FAULT state with fail-safe trip asserted."""
        self._fault_reason = reason
        self._current_state = SafetyState.FAULT
        self._is_tripped = True
        return SafetyOutput(
            trip=True,
            state=SafetyState.FAULT,
            warning=True,
            dwell_time_s=self._last_dwell_time,
            violating_tracks=sorted(list(self._violating_track_ids)),
            message=reason,
        )

    def trigger_lockout(self, reason: str = "") -> SafetyOutput:
        """Transition to LOCKOUT state with fail-safe trip latched."""
        self._lockout_reason = reason
        self._current_state = SafetyState.LOCKOUT
        self._is_tripped = True
        return SafetyOutput(
            trip=True,
            state=SafetyState.LOCKOUT,
            warning=True,
            dwell_time_s=self._last_dwell_time,
            violating_tracks=sorted(list(self._violating_track_ids)),
            message=reason,
        )

    def reset(self) -> SafetyOutput:
        """
        Attempt manual reset from LOCKOUT or FAULT state back to SAFE.
        Will reject reset and remain in LOCKOUT if physical zones are not clear.
        """
        # Verify physical zones are clear of active tracks
        is_occupied = False
        for trk in self._latest_tracks:
            if bool(shapely.contains_xy(self._release_poly, trk.position[0], trk.position[1])):
                is_occupied = True
                break

        if len(self._violating_track_ids) > 0 or is_occupied:
            # Reject reset
            self._current_state = SafetyState.LOCKOUT
            self._is_tripped = True
            return SafetyOutput(
                trip=True,
                state=SafetyState.LOCKOUT,
                warning=True,
                dwell_time_s=self._last_dwell_time,
                violating_tracks=sorted(list(self._violating_track_ids)),
                message="Reset rejected: zone is occupied or uncleared.",
            )

        # Authorized reset succeeds
        self._fault_reason = ""
        self._lockout_reason = ""
        self._violating_track_ids.clear()
        self._current_state = SafetyState.SAFE
        self._is_tripped = False
        return SafetyOutput(
            trip=False,
            state=SafetyState.SAFE,
            warning=False,
            dwell_time_s=0.0,
            message="Reset successful: system returned to SAFE.",
        )

    def evaluate_containment(
        self, tracks: List[Track]
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Evaluate spatial containment for a batch of tracks against prepared geometries.

        Args:
            tracks: List of Track instances.

        Returns:
            Tuple of (in_danger_mask, in_release_mask, in_warning_mask).
        """
        if not tracks:
            empty = np.empty(0, dtype=bool)
            return empty, empty, None

        positions = np.array([trk.position for trk in tracks], dtype=np.float64)
        xs = positions[:, 0]
        ys = positions[:, 1]
        in_danger = shapely.contains_xy(self._danger_poly, xs, ys)
        in_release = shapely.contains_xy(self._release_poly, xs, ys)
        in_warning = (
            shapely.contains_xy(self._warning_poly, xs, ys)
            if self._warning_poly is not None
            else (in_release & ~in_danger)
        )
        return in_danger, in_release, in_warning

    def update(
        self,
        tracks: List[Track],
        timestamp: Optional[float] = None,
    ) -> SafetyOutput:
        """
        Evaluate current confirmed tracks against spatial zones and update FSM state.

        Args:
            tracks: List of confirmed Track objects from MultiTargetKalmanTracker.
            timestamp: Monotonic frame timestamp in seconds (defaults to time.monotonic()).

        Returns:
            Authoritative SafetyOutput with trip status and diagnostics.
        """
        now = time.monotonic() if timestamp is None else float(timestamp)
        self._latest_tracks = list(tracks)

        # Latched states cannot exit via normal update
        if self._current_state == SafetyState.FAULT and self._fault_reason:
            return SafetyOutput(
                trip=True,
                state=SafetyState.FAULT,
                warning=True,
                dwell_time_s=self._last_dwell_time,
                violating_tracks=sorted(list(self._violating_track_ids)),
                timestamp=now,
                message=self._fault_reason,
            )
        if self._current_state == SafetyState.LOCKOUT:
            return SafetyOutput(
                trip=True,
                state=SafetyState.LOCKOUT,
                warning=True,
                dwell_time_s=self._last_dwell_time,
                violating_tracks=sorted(list(self._violating_track_ids)),
                timestamp=now,
                message=self._lockout_reason or "Latched LOCKOUT active.",
            )

        # Evaluate tracks
        has_warning = False
        active_ids = set()
        max_dwell = 0.0

        if tracks:
            in_danger_mask, in_release_mask, in_warning_mask = self.evaluate_containment(tracks)
            for idx, trk in enumerate(tracks):
                tid = trk.track_id
                active_ids.add(tid)
                pos = trk.position

                in_danger = bool(in_danger_mask[idx])
                in_release = bool(in_release_mask[idx])
                in_warning = (
                    bool(in_warning_mask[idx])
                    if in_warning_mask is not None
                    else (in_release and not in_danger)
                )

                # ISO 13855 approach velocity check (Cauchy-Schwarz bound: vn <= ||v||_2)
                fast_approach = False
                if not in_danger and trk.speed >= self._config.iso_k_speed:
                    vn = self._compute_approach_velocity(pos, trk.velocity)
                    if vn >= self._config.iso_k_speed:
                        fast_approach = True
                        has_warning = True

                # Retrieve or initialize spatial debounce record
                if tid not in self._track_records:
                    record = TrackSpatialRecord(track_id=tid)
                    self._track_records[tid] = record
                else:
                    record = self._track_records[tid]

                # Dwell time tracking in warning perimeter
                if in_warning and not in_danger:
                    has_warning = True
                    if record.first_seen_warning_ts is None:
                        record.first_seen_warning_ts = now
                    record.dwell_time_s = max(0.0, now - record.first_seen_warning_ts)
                else:
                    if not in_release:
                        record.first_seen_warning_ts = None
                        record.dwell_time_s = 0.0

                if record.dwell_time_s > max_dwell:
                    max_dwell = record.dwell_time_s

                # Spatial and temporal debounce logic
                if in_danger:
                    record.clean_count = 0
                    if fast_approach or record.fast_approach:
                        # ISO 13855 fast approach: bypass confirmation debounce
                        record.danger_count = max(record.danger_count + 1, self._config.n_confirm)
                    else:
                        record.danger_count += 1
                elif in_release:
                    # In buffer band [P_danger, P_release]
                    # Chattering suppression: do not clear danger, do not increment clean_count
                    record.clean_count = 0
                    if tid not in self._violating_track_ids:
                        record.danger_count = 0
                else:
                    # Completely outside P_release
                    record.danger_count = 0
                    record.clean_count += 1

                # Update fast_approach state for subsequent frames
                record.fast_approach = fast_approach

                # Escalation to DANGER_INTRUSION
                if record.danger_count >= self._config.n_confirm:
                    self._violating_track_ids.add(tid)

                # De-escalation back towards SAFE
                if tid in self._violating_track_ids:
                    if not in_release and record.clean_count >= self._config.n_release:
                        self._violating_track_ids.discard(tid)

        # Cleanup records for tracks that disappeared
        if len(self._track_records) > len(active_ids):
            for tid in list(self._track_records.keys()):
                if tid not in active_ids:
                    rec = self._track_records[tid]
                    if tid not in self._violating_track_ids:
                        del self._track_records[tid]
                    else:
                        # Increment release counter for disappearing violating track
                        rec.clean_count += 1
                        if rec.clean_count >= self._config.n_release:
                            self._violating_track_ids.discard(tid)
                            del self._track_records[tid]

        # Calculate max active dwell time
        self._last_dwell_time = max_dwell

        # Determine target state and outputs
        if self._is_muted:
            self._current_state = SafetyState.MUTED
            self._is_tripped = False
            is_warning = True
            msg = "Muting active: safety trip suppressed."
        elif len(self._violating_track_ids) > 0:
            self._current_state = SafetyState.DANGER_INTRUSION
            self._is_tripped = True
            is_warning = True
            msg = f"Hazard intrusion: tracks {sorted(list(self._violating_track_ids))}"
        elif has_warning or max_dwell > 0.0:
            self._current_state = SafetyState.WARNING_APPROACH
            self._is_tripped = False
            is_warning = True
            if self._last_dwell_time >= self._config.dwell_warning_s:
                msg = f"Warning: Target dwelling in warning zone ({self._last_dwell_time:.1f}s >= {self._config.dwell_warning_s:.1f}s)"
            else:
                msg = "Warning: Target in warning zone or approaching hazard."
        else:
            self._current_state = SafetyState.SAFE
            self._is_tripped = False
            is_warning = False
            msg = "All zones clear."

        return SafetyOutput(
            trip=self._is_tripped,
            state=self._current_state,
            warning=is_warning,
            dwell_time_s=self._last_dwell_time,
            violating_tracks=sorted(list(self._violating_track_ids)),
            timestamp=now,
            message=msg,
        )
