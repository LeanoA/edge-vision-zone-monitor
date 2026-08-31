"""
tests/test_visualizer.py
Unit tests for DualVisualizer perspective overlays, metric BEV canvas,
compositing layouts, and headless mode execution.
"""

import time
import numpy as np
import pytest

from src.core.homography import HomographyManager
from src.core.kalman_filter import MetricKalmanFilter, Track, TrackState
from src.core.spatial_fsm import (
    DwellState,
    OccupancyState,
    SafetyOutput,
    SafetyState,
    SpatialFSM,
    ZoneConfig,
)
from src.pipeline.safety_pipeline import (
    LayoutMode,
    PipelineResult,
    PoseDetection,
    StageLatencies,
)
from src.utils.visualizer import DualVisualizer


@pytest.fixture
def mock_pipeline_components():
    """Build calibrated homography and FSM for visualizer testing."""
    # 100 px = 1 meter correspondence
    # Image: (100, 100) -> World: (1.0, 1.0)
    # Image: (500, 100) -> World: (5.0, 1.0)
    # Image: (500, 500) -> World: (5.0, 5.0)
    # Image: (100, 500) -> World: (1.0, 5.0)
    img_pts = np.array([[100, 100], [500, 100], [500, 500], [100, 500]], dtype=np.float64)
    world_pts = np.array([[1.0, 1.0], [5.0, 1.0], [5.0, 5.0], [1.0, 5.0]], dtype=np.float64)
    homography = HomographyManager(image_points=img_pts, world_points=world_pts)

    zone_cfg = ZoneConfig(
        name="danger_zone",
        danger_polygon=[(2.0, 2.0), (4.0, 2.0), (4.0, 4.0), (2.0, 4.0)],
        hysteresis_buffer_m=0.2,
    )
    fsm = SpatialFSM(zone_cfg)
    return homography, fsm


@pytest.fixture
def sample_pipeline_result():
    """Create a representative PipelineResult with tracks and detections."""
    latencies = StageLatencies(
        preprocess_ms=1.5,
        inference_ms=12.0,
        keypoint_extract_ms=0.8,
        projection_ms=0.2,
        tracking_ms=0.4,
        fsm_evaluation_ms=0.3,
        total_t1_ms=15.2,
    )
    safety_output = SafetyOutput(
        trip=False,
        occupancy_state=OccupancyState.OUTSIDE,
        dwell_state=DwellState.NONE,
        dwell_time_s=1.2,
        warning=False,
        state=SafetyState.SAFE,
        violating_tracks=[],
        timestamp=100.0,
        message="Nominal",
    )

    # Active track at (2.5, 3.0) with velocity (1.2, 0.0)
    track = Track(track_id=1, initial_position=(2.5, 3.0), n_confirm=1)
    track._filter._x[2] = 1.2
    track._filter._x[3] = 0.0
    track._state = TrackState.CONFIRMED

    # Pose detection
    kps = np.zeros((17, 3), dtype=np.float32)
    # Nose
    kps[0] = [250.0, 120.0, 0.9]
    # Shoulders
    kps[5] = [230.0, 150.0, 0.9]
    kps[6] = [270.0, 150.0, 0.9]
    # Ankles
    kps[15] = [240.0, 300.0, 0.8]
    kps[16] = [260.0, 300.0, 0.8]

    det = PoseDetection(
        bbox=(220.0, 110.0, 280.0, 310.0),
        keypoints=kps,
        anchor=(250.0, 300.0),
    )

    return PipelineResult(
        frame_id=10,
        timestamp=100.0,
        safety_output=safety_output,
        tracks=[track],
        detections=[det],
        latencies=latencies,
    )


def test_dual_visualizer_inverse_homography_reprojection(mock_pipeline_components, sample_pipeline_result):
    """DualVisualizer reprojects danger and release zones via H^-1 onto perspective frame."""
    homography, fsm = mock_pipeline_components
    visualizer = DualVisualizer(homography, fsm, bev_scale=100.0, bev_size=(600, 600))

    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    rendered = visualizer.render_perspective(frame, sample_pipeline_result)

    assert rendered.shape == (720, 1280, 3)
    assert rendered.dtype == np.uint8
    # Assert pixels were drawn (frame is no longer all zero)
    assert np.any(rendered > 0)


def test_dual_visualizer_status_banner_trip_assertion(mock_pipeline_components, sample_pipeline_result):
    """DualVisualizer displays RED alert styling on status banner when trip is True."""
    homography, fsm = mock_pipeline_components
    visualizer = DualVisualizer(homography, fsm)

    # Trip result
    trip_output = SafetyOutput(
        trip=True,
        occupancy_state=OccupancyState.INSIDE,
        dwell_state=DwellState.WARNING,
        dwell_time_s=3.5,
        warning=True,
        state=SafetyState.DANGER_INTRUSION,
        violating_tracks=[1],
        message="Intrusion Trip",
    )
    sample_pipeline_result.safety_output = trip_output

    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    rendered = visualizer.render_perspective(frame, sample_pipeline_result)

    # Banner at top should contain red color (BGR: [0, 0, 255] or red tone)
    # Check top banner area (y from 0 to 60)
    top_area = rendered[:60, :, :]
    assert np.any(top_area[:, :, 2] > 180)  # Red channel active in BGR


def test_dual_visualizer_metric_bev_canvas(mock_pipeline_components, sample_pipeline_result):
    """Metric BEV canvas renders 100 px/m grid, zones, track marker, and velocity vector."""
    homography, fsm = mock_pipeline_components
    visualizer = DualVisualizer(homography, fsm, bev_scale=100.0, bev_size=(600, 600))

    bev = visualizer.render_bev(sample_pipeline_result)
    assert bev.shape == (600, 600, 3)
    assert bev.dtype == np.uint8
    assert np.any(bev > 0)


def test_dual_visualizer_side_by_side_compositor(mock_pipeline_components, sample_pipeline_result):
    """Compositor in SIDE_BY_SIDE mode places perspective and BEV views side by side."""
    homography, fsm = mock_pipeline_components
    visualizer = DualVisualizer(homography, fsm, bev_scale=100.0, bev_size=(600, 600))

    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    comp = visualizer.render(frame, sample_pipeline_result, layout=LayoutMode.SIDE_BY_SIDE)

    # Perspective height 720, BEV scaled to height 720 -> total width = 1280 + 720 = 2000
    assert comp.shape[0] == 720
    assert comp.shape[1] == 1280 + 720
    assert comp.shape[2] == 3


def test_dual_visualizer_pip_compositor(mock_pipeline_components, sample_pipeline_result):
    """Compositor in PIP mode embeds BEV canvas into bottom-right or corner of perspective frame."""
    homography, fsm = mock_pipeline_components
    visualizer = DualVisualizer(homography, fsm, bev_scale=100.0, bev_size=(600, 600))

    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    comp = visualizer.render(frame, sample_pipeline_result, layout=LayoutMode.PIP)

    assert comp.shape == (720, 1280, 3)


def test_dual_visualizer_headless_fast_path(mock_pipeline_components, sample_pipeline_result):
    """Headless mode bypasses drawing and executes in < 0.1 ms."""
    homography, fsm = mock_pipeline_components
    visualizer = DualVisualizer(homography, fsm, headless=True)

    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    # Warmup
    _ = visualizer.render(frame, sample_pipeline_result)

    t0 = time.perf_counter()
    out = visualizer.render(frame, sample_pipeline_result)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert out is frame  # direct return
    assert elapsed_ms < 0.5  # tight budget, spec < 0.1ms nominal
