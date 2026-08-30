"""
src/core package
Geometric calibration, spatial coordinate transformation, and safety zone management.
"""

from src.core.homography import CalibrationConfig, HomographyManager
from src.core.kalman_filter import (
    MetricKalmanFilter,
    MultiTargetKalmanTracker,
    Track,
    TrackState,
)
from src.core.spatial_fsm import (
    SafetyOutput,
    SafetyState,
    SpatialFSM,
    ZoneConfig,
)

__all__ = [
    "CalibrationConfig",
    "HomographyManager",
    "MetricKalmanFilter",
    "MultiTargetKalmanTracker",
    "Track",
    "TrackState",
    "SpatialFSM",
    "SafetyState",
    "SafetyOutput",
    "ZoneConfig",
]
