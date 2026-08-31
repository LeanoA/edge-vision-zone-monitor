"""
src/core/spatial_fsm.py
Spatial Finite State Machine with Orthogonal Occupancy and Temporal Dwell Statecharts.
Inspired by ISO 13855:2024, ISO 13849-1 (PL d/e), and IEC 61508 fail-safe architecture.
"""

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Dict, List, Optional, Set, Tuple, Union
import numpy as np
import shapely
from shapely.geometry import Point, Polygon
from shapely.prepared import prep, PreparedGeometry

from src.core.kalman_filter import ObservationStatus, Track


class OccupancyState(str, Enum):
    """Discrete spatial occupancy states relative to the safeguarded zone geometry."""
    OUTSIDE = "OUTSIDE"
    ENTER_PENDING = "ENTER_PENDING"
    INSIDE = "INSIDE"
    EXIT_PENDING = "EXIT_PENDING"


class DwellState(str, Enum):
    """Discrete temporal duration classifications for confirmed zone occupants."""
    NONE = "NONE"
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    VIOLATION = "VIOLATION"


class SafetyState(str, Enum):
    """Supervisory safety states of the industrial safeguarding system."""
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
    dwell_violation_s: float = 10.0
    iso_k_speed: float = 1.6  # Human approach speed in m/s (ISO 13855)

    def __post_init__(self) -> None:
        """Validate geometric and debounce parameters."""
        if not (0.15 <= self.hysteresis_buffer_m <= 0.30):
            raise ValueError("hysteresis_buffer_m must be between 0.15m and 0.30m.")
        if self.n_confirm <= 0 or self.n_release <= 0:
            raise ValueError("n_confirm and n_release must be positive integers.")
        if self.dwell_warning_s <= 0.0 or self.dwell_violation_s <= 0.0 or self.iso_k_speed <= 0.0:
            raise ValueError("dwell_warning_s, dwell_violation_s, and iso_k_speed must be positive numbers.")
        if self.dwell_violation_s < self.dwell_warning_s:
            raise ValueError("dwell_violation_s must be greater than or equal to dwell_warning_s.")
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
    occupancy_state: OccupancyState
    dwell_state: DwellState
    dwell_time_s: float
    warning: bool
    state: SafetyState = SafetyState.SAFE
    violating_tracks: List[int] = field(default_factory=list)
    timestamp: float = 0.0
    message: str = ""
    fault_reason: Optional[str] = None
    lockout_active: bool = False


@dataclass
class TrackSpatialRecord:
    """Internal per-track spatial debounce and dwell tracking record."""
    track_id: int
    danger_count: int = 0
    clean_count: int = 0
    fast_approach: bool = False
    first_seen_inside_ts: Optional[float] = None
    first_seen_warning_ts: Optional[float] = None
    dwell_time_s: float = 0.0
    last_observed_dwell_s: float = 0.0


class SpatialFSM:
    """
    Industrial safety state machine enforcing orthogonal Spatial Occupancy and
    Temporal Dwell Statecharts with dual spatial-temporal hysteresis and fail-safe trips.
    """

    def __init__(self, config: ZoneConfig) -> None:
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
        self._occupancy_state: OccupancyState = OccupancyState.OUTSIDE
        self._dwell_state: DwellState = DwellState.NONE
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
        """Return the current supervisory SafetyState."""
        return self._current_state

    @property
    def occupancy_state(self) -> OccupancyState:
        """Return the current active Spatial Occupancy State."""
        return self._occupancy_state

    @property
    def dwell_state(self) -> DwellState:
        """Return the current active Temporal Dwell State."""
        return self._dwell_state

    @property
    def is_tripped(self) -> bool:
        """Return True if safety trip is asserted (emergency stop contactors open)."""
        return self._is_tripped

    @property
    def dwell_time(self) -> float:
        """Return maximum dwell time in seconds of any active inside track."""
        return self._last_dwell_time

    @property
    def danger_polygon(self) -> Polygon:
        return self._danger_poly

    @property
    def release_polygon(self) -> Polygon:
        return self._release_poly

    @property
    def warning_polygon(self) -> Optional[Polygon]:
        return self._warning_poly

    def trigger_fault(self, reason: str = "Hardware or pipeline fault detected") -> SafetyOutput:
        """Assert fail-safe FAULT condition and open safety contactors."""
        self._current_state = SafetyState.FAULT
        self._is_tripped = True
        self._fault_reason = reason
        now = time.monotonic()
        return SafetyOutput(
            trip=True,
            occupancy_state=self._occupancy_state,
            dwell_state=self._dwell_state,
            dwell_time_s=self._last_dwell_time,
            warning=True,
            state=SafetyState.FAULT,
            violating_tracks=sorted(list(self._violating_track_ids)),
            timestamp=now,
            message=reason,
            fault_reason=reason,
        )

    def trigger_lockout(self, reason: str = "Safety interlock triggered") -> SafetyOutput:
        """Latch into safety LOCKOUT requiring manual supervisor reset."""
        self._current_state = SafetyState.LOCKOUT
        self._is_tripped = True
        self._lockout_reason = reason
        now = time.monotonic()
        return SafetyOutput(
            trip=True,
            occupancy_state=self._occupancy_state,
            dwell_state=self._dwell_state,
            dwell_time_s=self._last_dwell_time,
            warning=True,
            state=SafetyState.LOCKOUT,
            violating_tracks=sorted(list(self._violating_track_ids)),
            timestamp=now,
            message=reason,
            lockout_active=True,
        )

    def reset(self) -> SafetyOutput:
        """Manual supervisory reset clearing FAULT and LOCKOUT latches."""
        self._current_state = SafetyState.SAFE
        self._occupancy_state = OccupancyState.OUTSIDE
        self._dwell_state = DwellState.NONE
        self._is_tripped = False
        self._fault_reason = ""
        self._lockout_reason = ""
        self._track_records.clear()
        self._violating_track_ids.clear()
        self._last_dwell_time = 0.0
        now = time.monotonic()
        return SafetyOutput(
            trip=False,
            occupancy_state=OccupancyState.OUTSIDE,
            dwell_state=DwellState.NONE,
            dwell_time_s=0.0,
            warning=False,
            state=SafetyState.SAFE,
            violating_tracks=[],
            timestamp=now,
            message="System reset by supervisor. All zones clear.",
        )

    def set_muted(self, muted: bool) -> None:
        """Enable or disable operational muting."""
        self._is_muted = bool(muted)
        if self._is_muted:
            if self._current_state not in (SafetyState.FAULT, SafetyState.LOCKOUT):
                self._current_state = SafetyState.MUTED
                self._is_tripped = False
        else:
            if self._current_state == SafetyState.MUTED:
                self._current_state = SafetyState.SAFE

    def _compute_approach_velocity(self, pos: Tuple[float, float], vel: Tuple[float, float]) -> float:
        """Compute inward normal approach velocity towards danger polygon."""
        p = np.array([pos[0], pos[1]], dtype=np.float64)
        v = np.array([vel[0], vel[1]], dtype=np.float64)
        speed = float(np.linalg.norm(v))
        if speed < 1e-6:
            return 0.0

        p_minus_A = p - self._seg_A
        t = np.sum(p_minus_A * self._seg_AB, axis=1) / self._seg_len_sq
        t_clamped = np.clip(t, 0.0, 1.0)[:, np.newaxis]
        closest_pts = self._seg_A + t_clamped * self._seg_AB
        diffs = closest_pts - p
        dist_sq = np.sum(diffs ** 2, axis=1)
        min_idx = np.argmin(dist_sq)

        dist = np.sqrt(dist_sq[min_idx])
        if dist < 1e-6:
            return speed

        normal = diffs[min_idx] / dist
        vn = float(np.dot(v, normal))
        return max(0.0, min(vn, speed))

    def evaluate_containment(
        self, tracks: List[Track]
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """Evaluate spatial containment against prepared geometries."""
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
        Execute synchronous evaluation of orthogonal Spatial Occupancy and Temporal Dwell Statecharts.
        """
        now = time.monotonic() if timestamp is None else float(timestamp)
        self._latest_tracks = list(tracks)

        # Latched supervisory states cannot exit via normal update
        if self._current_state == SafetyState.FAULT and self._fault_reason:
            return SafetyOutput(
                trip=True,
                occupancy_state=self._occupancy_state,
                dwell_state=self._dwell_state,
                dwell_time_s=self._last_dwell_time,
                warning=True,
                state=SafetyState.FAULT,
                violating_tracks=sorted(list(self._violating_track_ids)),
                timestamp=now,
                message=self._fault_reason,
                fault_reason=self._fault_reason,
            )
        if self._current_state == SafetyState.LOCKOUT:
            return SafetyOutput(
                trip=True,
                occupancy_state=self._occupancy_state,
                dwell_state=self._dwell_state,
                dwell_time_s=self._last_dwell_time,
                warning=True,
                state=SafetyState.LOCKOUT,
                violating_tracks=sorted(list(self._violating_track_ids)),
                timestamp=now,
                message=self._lockout_reason or "Latched LOCKOUT active.",
                lockout_active=True,
            )

        active_ids = set()
        has_fast_approach = False
        has_warning_zone_presence = False
        any_enter_pending = False
        any_exit_pending = False

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

                if in_warning:
                    has_warning_zone_presence = True

                # ISO 13855 Approach velocity check
                fast_approach = False
                if not in_danger and trk.speed >= self._config.iso_k_speed:
                    vn = self._compute_approach_velocity(pos, trk.velocity)
                    if vn >= self._config.iso_k_speed:
                        fast_approach = True
                        has_fast_approach = True

                # Retrieve or initialize spatial debounce record
                if tid not in self._track_records:
                    record = TrackSpatialRecord(track_id=tid)
                    self._track_records[tid] = record
                else:
                    record = self._track_records[tid]

                obs_status = getattr(trk, "observation_status", ObservationStatus.OBSERVED)

                # 1. Spatial Debounce Logic
                if in_danger:
                    record.clean_count = 0
                    if fast_approach or record.fast_approach:
                        # ISO 13855 fast approach: bypass confirmation debounce
                        record.danger_count = max(record.danger_count + 1, self._config.n_confirm)
                    else:
                        record.danger_count += 1
                elif in_release:
                    # In buffer band [P_danger, P_release]
                    record.clean_count = 0
                    if tid not in self._violating_track_ids:
                        record.danger_count = 0
                else:
                    # Completely outside P_release
                    record.danger_count = 0
                    if obs_status == ObservationStatus.OBSERVED:
                        record.clean_count += 1

                record.fast_approach = fast_approach

                # 2. Update Violation Membership
                if record.danger_count >= self._config.n_confirm:
                    self._violating_track_ids.add(tid)
                elif 0 < record.danger_count < self._config.n_confirm and tid not in self._violating_track_ids:
                    any_enter_pending = True

                if tid in self._violating_track_ids:
                    if in_danger:
                        pass
                    elif not in_release and record.clean_count >= self._config.n_release:
                        self._violating_track_ids.discard(tid)
                        record.first_seen_inside_ts = None
                        record.dwell_time_s = 0.0
                        record.last_observed_dwell_s = 0.0
                    else:
                        any_exit_pending = True

                # 3. Dwell Time Accumulation (Strictly while in INSIDE state)
                if tid in self._violating_track_ids:
                    if obs_status == ObservationStatus.OBSERVED:
                        if record.first_seen_inside_ts is None:
                            record.first_seen_inside_ts = now
                        record.dwell_time_s = max(0.0, now - record.first_seen_inside_ts)
                        record.last_observed_dwell_s = record.dwell_time_s
                    else:
                        # Freeze dwell time during coasting / unobserved
                        if record.first_seen_inside_ts is not None:
                            record.dwell_time_s = record.last_observed_dwell_s
                            record.first_seen_inside_ts = now - record.dwell_time_s
                else:
                    record.first_seen_inside_ts = None
                    record.dwell_time_s = 0.0
                    record.last_observed_dwell_s = 0.0

        # Disappearance Check (ISO 13849-1 Fail-Safe Latch)
        disappeared_violators = False
        disappeared_tid = None
        if len(self._track_records) > len(active_ids):
            for tid in list(self._track_records.keys()):
                if tid not in active_ids:
                    if tid not in self._violating_track_ids:
                        del self._track_records[tid]
                    else:
                        disappeared_violators = True
                        disappeared_tid = tid
                        del self._track_records[tid]

        if disappeared_violators:
            return self.trigger_lockout(
                f"Hazard violation unverified: violating track {disappeared_tid} disappeared inside hazard zone."
            )

        # 4. Resolve Region 1: OccupancyState
        if len(self._violating_track_ids) > 0:
            if any(self._track_records.get(tid, TrackSpatialRecord(tid)).danger_count >= self._config.n_confirm for tid in self._violating_track_ids):
                self._occupancy_state = OccupancyState.INSIDE
            else:
                self._occupancy_state = OccupancyState.EXIT_PENDING
        elif any_exit_pending:
            self._occupancy_state = OccupancyState.EXIT_PENDING
        elif any_enter_pending:
            self._occupancy_state = OccupancyState.ENTER_PENDING
        else:
            self._occupancy_state = OccupancyState.OUTSIDE

        # 5. Resolve Region 2: DwellState (Evaluated over INSIDE tracks)
        max_dwell = 0.0
        for tid in self._violating_track_ids:
            rec = self._track_records.get(tid)
            if rec and rec.dwell_time_s > max_dwell:
                max_dwell = rec.dwell_time_s

        self._last_dwell_time = max_dwell

        if self._occupancy_state == OccupancyState.INSIDE:
            if max_dwell >= self._config.dwell_violation_s:
                self._dwell_state = DwellState.VIOLATION
            elif max_dwell >= self._config.dwell_warning_s:
                self._dwell_state = DwellState.WARNING
            else:
                self._dwell_state = DwellState.NORMAL
        else:
            self._dwell_state = DwellState.NONE
            if self._occupancy_state == OccupancyState.OUTSIDE:
                self._last_dwell_time = 0.0

        # 6. Trip and Warning Signals
        if self._is_muted:
            self._current_state = SafetyState.MUTED
            self._is_tripped = False
            is_warning = True
            msg = "Muting active: safety trip suppressed."
        elif len(self._violating_track_ids) > 0:
            self._current_state = SafetyState.DANGER_INTRUSION
            self._is_tripped = True
            is_warning = True
            msg = f"Hazard intrusion: tracks {sorted(list(self._violating_track_ids))} (Occupancy: {self._occupancy_state.value}, Dwell: {self._dwell_state.value} {self._last_dwell_time:.1f}s)"
        elif self._occupancy_state in (OccupancyState.EXIT_PENDING, OccupancyState.ENTER_PENDING) or has_fast_approach or has_warning_zone_presence:
            self._current_state = SafetyState.WARNING_APPROACH
            self._is_tripped = False
            is_warning = True
            msg = f"Warning: Occupancy {self._occupancy_state.value}"
        else:
            self._current_state = SafetyState.SAFE
            self._is_tripped = False
            is_warning = False
            msg = "All zones clear."

        return SafetyOutput(
            trip=self._is_tripped,
            occupancy_state=self._occupancy_state,
            dwell_state=self._dwell_state,
            dwell_time_s=self._last_dwell_time,
            warning=is_warning,
            state=self._current_state,
            violating_tracks=sorted(list(self._violating_track_ids)),
            timestamp=now,
            message=msg,
        )
