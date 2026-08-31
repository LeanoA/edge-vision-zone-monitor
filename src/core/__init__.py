"""
src/core package
Geometric calibration, spatial coordinate transformation, and safety zone management.
"""

from src.core.homography import CalibrationConfig, HomographyManager
from src.core.kalman_filter import (
    AnchorSource,
    MetricKalmanFilter,
    MultiTargetKalmanTracker,
    ObservationStatus,
    PositionEstimate,
    Track,
    TrackState,
)
from src.core.spatial_fsm import (
    DwellState,
    OccupancyState,
    SafetyOutput,
    SafetyState,
    SpatialFSM,
    ZoneConfig,
)

__all__ = [
    "AnchorSource",
    "CalibrationConfig",
    "DwellState",
    "HomographyManager",
    "MetricKalmanFilter",
    "MultiTargetKalmanTracker",
    "ObservationStatus",
    "OccupancyState",
    "PositionEstimate",
    "Track",
    "TrackState",
    "SpatialFSM",
    "SafetyState",
    "SafetyOutput",
    "ZoneConfig",
]
