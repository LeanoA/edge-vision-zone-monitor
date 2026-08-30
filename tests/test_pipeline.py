"""
tests/test_pipeline.py
Unit and integration tests for the SafetyPipeline orchestrator.
"""

from dataclasses import is_dataclass
import numpy as np
import pytest

from src.core.kalman_filter import Track
from src.core.spatial_fsm import SafetyOutput, SafetyState
from src.pipeline.safety_pipeline import (
    AnchorSource,
    LayoutMode,
    PipelineResult,
    PositionEstimate,
    PoseDetection,
    StageLatencies,
)


def test_stage_latencies_dataclass():
    """StageLatencies stores per-stage latencies and total reaction time."""
    latencies = StageLatencies(
        preprocess_ms=1.2,
        inference_ms=15.0,
        keypoint_extract_ms=0.8,
        projection_ms=0.3,
        tracking_ms=0.5,
        fsm_evaluation_ms=0.4,
        total_t1_ms=18.2,
    )
    assert is_dataclass(latencies)
    assert latencies.preprocess_ms == 1.2
    assert latencies.inference_ms == 15.0
    assert latencies.total_t1_ms == 18.2
    # Ensure immutability (frozen=True)
    with pytest.raises((AttributeError, TypeError)):
        latencies.total_t1_ms = 25.0


def test_pose_detection_dataclass():
    """PoseDetection encapsulates bounding box, keypoints, and ground anchor."""
    kps = np.zeros((17, 3), dtype=np.float32)
    kps[15] = [200.0, 400.0, 0.9]
    kps[16] = [220.0, 400.0, 0.85]

    det = PoseDetection(
        bbox=(100.0, 150.0, 250.0, 420.0),
        keypoints=kps,
        anchor=(210.0, 400.0),
    )
    assert det.bbox == (100.0, 150.0, 250.0, 420.0)
    assert det.anchor == (210.0, 400.0)
    assert det.keypoints.shape == (17, 3)


def test_pipeline_result_dataclass():
    """PipelineResult encapsulates comprehensive frame evaluation result."""
    latencies = StageLatencies(1.0, 10.0, 0.5, 0.2, 0.3, 0.4, 12.4)
    safety_output = SafetyOutput(
        trip=False,
        state=SafetyState.SAFE,
        warning=False,
        dwell_time_s=0.0,
        violating_tracks=[],
        timestamp=100.0,
        message="Nominal",
    )
    result = PipelineResult(
        frame_id=42,
        timestamp=100.0,
        safety_output=safety_output,
        tracks=[],
        detections=[],
        latencies=latencies,
    )
    assert result.frame_id == 42
    assert result.safety_output.state == SafetyState.SAFE
    assert result.latencies.total_t1_ms == 12.4


def test_layout_mode_enum():
    """LayoutMode defines supported visualization compositions."""
    assert LayoutMode.SIDE_BY_SIDE.value == "SIDE_BY_SIDE"
    assert LayoutMode.PIP.value == "PIP"


def test_letterbox_preprocessing():
    """Letterbox resizes image preserving aspect ratio and pads to 640x640."""
    from src.pipeline.safety_pipeline import letterbox_image, unletterbox_point

    # Input: 1280x720 image (16:9)
    img = np.zeros((720, 1280, 3), dtype=np.uint8)
    tensor, scale, pad_x, pad_y = letterbox_image(img, target_size=(640, 640))

    # Scale should be 640 / 1280 = 0.5
    # New height = 720 * 0.5 = 360
    # pad_y = (640 - 360) / 2 = 140
    # pad_x = 0
    assert tensor.shape == (1, 3, 640, 640)
    assert tensor.dtype == np.float32
    assert scale == pytest.approx(0.5)
    assert pad_x == pytest.approx(0.0)
    assert pad_y == pytest.approx(140.0)

    # Test un-letterbox point mapping
    # Point at center of active area: (320, 140 + 180 = 320) in letterbox space
    # Should map back to original image center: (640, 360)
    orig_pt = unletterbox_point(320.0, 320.0, scale, pad_x, pad_y)
    assert orig_pt[0] == pytest.approx(640.0)
    assert orig_pt[1] == pytest.approx(360.0)

    # Point at top-left of active area: (0, 140) -> (0, 0)
    orig_top_left = unletterbox_point(0.0, 140.0, scale, pad_x, pad_y)
    assert orig_top_left[0] == pytest.approx(0.0)
    assert orig_top_left[1] == pytest.approx(0.0)


def test_letterbox_pillarbox_triangulation():
    """Letterbox correctly handles tall images (pillarbox with left/right padding)."""
    from src.pipeline.safety_pipeline import letterbox_image, unletterbox_point

    # Input: 600x1200 image (tall)
    img = np.zeros((1200, 600, 3), dtype=np.uint8)
    tensor, scale, pad_x, pad_y = letterbox_image(img, target_size=(640, 640))

    # scale = 640 / 1200 = 0.53333333
    # new_w = 600 * (640/1200) = 320
    # pad_x = (640 - 320) / 2 = 160
    # pad_y = 0
    assert scale == pytest.approx(640.0 / 1200.0)
    assert pad_y == pytest.approx(0.0)
    assert pad_x == pytest.approx(160.0)

    # Point in letterbox (160 + 160 = 320, 320) -> original (300, 600)
    orig = unletterbox_point(320.0, 320.0, scale, pad_x, pad_y)
    assert orig[0] == pytest.approx(300.0)
    assert orig[1] == pytest.approx(600.0)


def test_ankle_anchor_extraction_dual_midpoint():
    """Dual ankle detections above confidence threshold calculate midpoint."""
    from src.pipeline.safety_pipeline import extract_ankle_anchor

    kps = np.zeros((17, 3), dtype=np.float32)
    kps[15] = [200.0, 400.0, 0.8]  # Left ankle
    kps[16] = [220.0, 400.0, 0.7]  # Right ankle

    # scale = 1.0, pad_x = 0, pad_y = 0 for direct coordinates
    anchor = extract_ankle_anchor(kps, conf_threshold=0.5, scale=1.0, pad_x=0.0, pad_y=0.0)
    assert anchor is not None
    assert anchor[0] == pytest.approx(210.0)
    assert anchor[1] == pytest.approx(400.0)


def test_ankle_anchor_extraction_single_fallback():
    """Single ankle detection above threshold falls back to that ankle."""
    from src.pipeline.safety_pipeline import extract_ankle_anchor

    # Left ankle high conf, right ankle low conf
    kps = np.zeros((17, 3), dtype=np.float32)
    kps[15] = [180.0, 350.0, 0.75]
    kps[16] = [200.0, 350.0, 0.3]

    anchor = extract_ankle_anchor(kps, conf_threshold=0.5, scale=1.0, pad_x=0.0, pad_y=0.0)
    assert anchor is not None
    assert anchor[0] == pytest.approx(180.0)
    assert anchor[1] == pytest.approx(350.0)

    # Right ankle high conf, left ankle low conf
    kps[15] = [180.0, 350.0, 0.2]
    kps[16] = [220.0, 360.0, 0.85]
    anchor2 = extract_ankle_anchor(kps, conf_threshold=0.5, scale=1.0, pad_x=0.0, pad_y=0.0)
    assert anchor2 is not None
    assert anchor2[0] == pytest.approx(220.0)
    assert anchor2[1] == pytest.approx(360.0)


def test_ankle_anchor_extraction_low_confidence_drop():
    """Both ankles below confidence threshold drop measurement (return None)."""
    from src.pipeline.safety_pipeline import extract_ankle_anchor

    kps = np.zeros((17, 3), dtype=np.float32)
    kps[15] = [180.0, 350.0, 0.4]
    kps[16] = [200.0, 350.0, 0.49]

    anchor = extract_ankle_anchor(kps, conf_threshold=0.5, scale=1.0, pad_x=0.0, pad_y=0.0)
    assert anchor is None


def test_extract_ground_anchor_hierarchy():
    """Verify 4-tier graceful degradation hierarchy in extract_ground_anchor."""
    from src.pipeline.safety_pipeline import extract_ground_anchor

    # Scenario 1 (Tier 1 ANKLES_DUAL): Both ankles >= conf_threshold
    kps = np.zeros((17, 3), dtype=np.float32)
    kps[15] = [200.0, 400.0, 0.90]  # Left ankle
    kps[16] = [220.0, 400.0, 0.80]  # Right ankle
    res = extract_ground_anchor(kps, bbox=(100.0, 100.0, 300.0, 410.0), conf_threshold=0.5)
    assert res is not None
    anchor_pt, source, conf = res
    assert anchor_pt == (pytest.approx(210.0), pytest.approx(400.0))
    assert source == AnchorSource.ANKLES_DUAL
    assert conf == pytest.approx(0.85)

    # Scenario 2 (Tier 2 ANKLE_SINGLE): Exactly one ankle >= conf_threshold
    kps[15] = [195.0, 390.0, 0.80]
    kps[16] = [220.0, 390.0, 0.20]  # occluded
    res = extract_ground_anchor(kps, bbox=(100.0, 100.0, 300.0, 410.0), conf_threshold=0.5)
    assert res is not None
    anchor_pt, source, conf = res
    assert anchor_pt == (pytest.approx(195.0), pytest.approx(390.0))
    assert source == AnchorSource.ANKLE_SINGLE
    assert conf == pytest.approx(0.80 * 0.75)  # 0.60

    # Scenario 3 (Tier 3 BBOX_BOTTOM): Both ankles < conf_threshold & allow_bbox_fallback=True
    kps[15] = [195.0, 390.0, 0.15]
    kps[16] = [220.0, 390.0, 0.10]
    bbox = (100.0, 50.0, 200.0, 450.0)  # cx = 150, bottom = 450
    res = extract_ground_anchor(
        kps,
        bbox=bbox,
        conf_threshold=0.5,
        scale=1.0,
        pad_x=0.0,
        pad_y=0.0,
        allow_bbox_fallback=True,
        det_score=0.90,
    )
    assert res is not None
    anchor_pt, source, conf = res
    assert anchor_pt == (pytest.approx(150.0), pytest.approx(450.0))
    assert source == AnchorSource.BBOX_BOTTOM
    assert conf == pytest.approx(0.90 * 0.40)  # 0.36

    # Scenario 4 (Tier 4 Dropout): Both ankles occluded & allow_bbox_fallback=False
    res_no_fallback = extract_ground_anchor(
        kps,
        bbox=bbox,
        conf_threshold=0.5,
        allow_bbox_fallback=False,
    )
    assert res_no_fallback is None

    # Missing bbox with both ankles occluded -> returns None
    res_no_bbox = extract_ground_anchor(kps, bbox=None, conf_threshold=0.5, allow_bbox_fallback=True)
    assert res_no_bbox is None


def test_extract_ankle_anchor_backward_compatibility():
    """Verify extract_ankle_anchor maintains unchanged signature and behavior without bbox fallback."""
    from src.pipeline.safety_pipeline import extract_ankle_anchor

    kps = np.zeros((17, 3), dtype=np.float32)
    # Both ankles occluded
    kps[15] = [180.0, 350.0, 0.2]
    kps[16] = [200.0, 350.0, 0.3]
    # extract_ankle_anchor signature: (keypoints, conf_threshold=0.5, scale=1.0, pad_x=0.0, pad_y=0.0)
    assert extract_ankle_anchor(kps) is None

    # Both ankles valid
    kps[15] = [200.0, 400.0, 0.8]
    kps[16] = [220.0, 400.0, 0.7]
    res = extract_ankle_anchor(kps)
    assert res == (210.0, 400.0)


def test_pose_detection_provenance_extension():
    """Verify PoseDetection dataclass supports optional anchor_source and anchor_confidence."""
    kps = np.zeros((17, 3), dtype=np.float32)
    # Positional backward compatibility
    det_legacy = PoseDetection((10.0, 20.0, 30.0, 40.0), kps, (20.0, 40.0))
    assert det_legacy.anchor_source is None
    assert det_legacy.anchor_confidence == 0.0

    # With provenance metadata
    det_enriched = PoseDetection(
        bbox=(10.0, 20.0, 30.0, 40.0),
        keypoints=kps,
        anchor=(20.0, 40.0),
        anchor_source=AnchorSource.BBOX_BOTTOM,
        anchor_confidence=0.36,
    )
    assert det_enriched.anchor_source == AnchorSource.BBOX_BOTTOM
    assert det_enriched.anchor_confidence == 0.36


def test_safety_pipeline_orchestration_loop(synthetic_onnx_path, tmp_path):
    """SafetyPipeline coordinates all 6 stages synchronously returning PipelineResult."""
    from src.core.homography import HomographyManager
    from src.core.kalman_filter import MultiTargetKalmanTracker
    from src.core.spatial_fsm import SpatialFSM, ZoneConfig
    from src.inference.onnx_engine import OnnxEngine
    from src.pipeline.safety_pipeline import SafetyPipeline

    # Setup components
    engine = OnnxEngine(synthetic_onnx_path)
    img_pts = np.array([[100, 100], [500, 100], [500, 500], [100, 500]], dtype=np.float64)
    world_pts = np.array([[0, 0], [4, 0], [4, 4], [0, 4]], dtype=np.float64)
    homography = HomographyManager(image_points=img_pts, world_points=world_pts)
    tracker = MultiTargetKalmanTracker(dt=0.0333)
    zone_cfg = ZoneConfig(
        name="danger",
        danger_polygon=[(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)],
        hysteresis_buffer_m=0.2,
    )
    fsm = SpatialFSM(zone_cfg)

    pipeline = SafetyPipeline(
        engine=engine,
        homography=homography,
        tracker=tracker,
        fsm=fsm,
        conf_threshold=0.5,
    )

    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    result = pipeline.process_frame(frame)

    assert isinstance(result, PipelineResult)
    assert result.frame_id == 1
    assert result.timestamp > 0.0
    assert result.safety_output is not None
    assert result.safety_output.state in (SafetyState.SAFE, SafetyState.WARNING_APPROACH, SafetyState.DANGER_INTRUSION)
    assert result.latencies.total_t1_ms >= 0.0
    assert result.latencies.preprocess_ms >= 0.0
    assert result.latencies.inference_ms >= 0.0
    assert result.latencies.keypoint_extract_ms >= 0.0
    assert result.latencies.projection_ms >= 0.0
    assert result.latencies.tracking_ms >= 0.0
    assert result.latencies.fsm_evaluation_ms >= 0.0
    # Latency constraint: synthetic model should execute well under 50ms
    assert result.latencies.total_t1_ms <= 50.0


def test_safety_pipeline_zero_detection_frame(synthetic_onnx_path):
    """When frame contains 0 detections, active tracks coast and FSM executes without error."""
    from unittest.mock import MagicMock
    from src.core.homography import HomographyManager
    from src.core.kalman_filter import MultiTargetKalmanTracker
    from src.core.spatial_fsm import SpatialFSM, ZoneConfig
    from src.inference.onnx_engine import OnnxEngine
    from src.pipeline.safety_pipeline import SafetyPipeline

    engine = OnnxEngine(synthetic_onnx_path)
    img_pts = np.array([[100, 100], [500, 100], [500, 500], [100, 500]], dtype=np.float64)
    world_pts = np.array([[0, 0], [4, 0], [4, 4], [0, 4]], dtype=np.float64)
    homography = HomographyManager(image_points=img_pts, world_points=world_pts)
    tracker = MultiTargetKalmanTracker(dt=0.0333)
    zone_cfg = ZoneConfig(
        name="danger",
        danger_polygon=[(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)],
        hysteresis_buffer_m=0.2,
    )
    fsm = SpatialFSM(zone_cfg)
    pipeline = SafetyPipeline(engine, homography, tracker, fsm)

    # Force zero detections from parser
    pipeline.parse_detections = MagicMock(return_value=[])
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    result = pipeline.process_frame(frame)

    assert len(result.detections) == 0
    assert result.safety_output.state == SafetyState.SAFE
    assert result.safety_output.trip is False


def test_safety_pipeline_fail_safe_on_corrupted_frame(synthetic_onnx_path):
    """Corrupted frame or runtime exception triggers fail-safe FAULT state and trip=True."""
    from src.core.homography import HomographyManager
    from src.core.kalman_filter import MultiTargetKalmanTracker
    from src.core.spatial_fsm import SpatialFSM, ZoneConfig
    from src.inference.onnx_engine import OnnxEngine
    from src.pipeline.safety_pipeline import SafetyPipeline

    engine = OnnxEngine(synthetic_onnx_path)
    img_pts = np.array([[100, 100], [500, 100], [500, 500], [100, 500]], dtype=np.float64)
    world_pts = np.array([[0, 0], [4, 0], [4, 4], [0, 4]], dtype=np.float64)
    homography = HomographyManager(image_points=img_pts, world_points=world_pts)
    tracker = MultiTargetKalmanTracker()
    zone_cfg = ZoneConfig(
        name="danger",
        danger_polygon=[(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)],
        hysteresis_buffer_m=0.2,
    )
    fsm = SpatialFSM(zone_cfg)
    pipeline = SafetyPipeline(engine, homography, tracker, fsm)

    # Corrupted frame (invalid shape/dimension)
    corrupted_frame = np.zeros((10,), dtype=np.uint8)
    result = pipeline.process_frame(corrupted_frame)

    assert result.safety_output.trip is True
    assert result.safety_output.state == SafetyState.FAULT
    assert "Fault containment" in result.safety_output.message


def test_safety_pipeline_multi_frame_integration(synthetic_onnx_path):
    """
    Execute full pipeline over 30 consecutive synthetic frames.
    Validates frame monotonicity, latency profiling stability (t1 <= 50ms),
    and safe state evaluation.
    """
    from src.core.homography import HomographyManager
    from src.core.kalman_filter import MultiTargetKalmanTracker
    from src.core.spatial_fsm import SpatialFSM, ZoneConfig
    from src.inference.onnx_engine import OnnxEngine
    from src.pipeline.safety_pipeline import SafetyPipeline

    engine = OnnxEngine(synthetic_onnx_path)
    img_pts = np.array([[100, 100], [500, 100], [500, 500], [100, 500]], dtype=np.float64)
    world_pts = np.array([[0.0, 0.0], [4.0, 0.0], [4.0, 4.0], [0.0, 4.0]], dtype=np.float64)
    homography = HomographyManager(image_points=img_pts, world_points=world_pts)
    tracker = MultiTargetKalmanTracker(dt=0.0333)
    zone_cfg = ZoneConfig(
        name="danger",
        danger_polygon=[(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)],
        hysteresis_buffer_m=0.2,
    )
    fsm = SpatialFSM(zone_cfg)
    pipeline = SafetyPipeline(engine, homography, tracker, fsm)

    latencies = []
    for frame_idx in range(30):
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        result = pipeline.process_frame(frame)

        assert result.frame_id == frame_idx + 1
        assert result.latencies.total_t1_ms >= 0.0
        assert result.latencies.total_t1_ms <= 50.0  # ISO 13855 50ms ceiling
        latencies.append(result.latencies.total_t1_ms)

    # Statistical verification across 30 frames
    mean_latency = float(np.mean(latencies))
    assert mean_latency < 40.0, f"Mean latency {mean_latency}ms exceeds budget"


def test_pipeline_occlusion_confidence_propagation(synthetic_onnx_path):
    """Verify end-to-end metadata propagation of degraded anchors to active tracks."""
    from unittest.mock import MagicMock
    from src.core.homography import HomographyManager
    from src.core.kalman_filter import MultiTargetKalmanTracker
    from src.core.spatial_fsm import SpatialFSM, ZoneConfig
    from src.inference.onnx_engine import OnnxEngine
    from src.pipeline.safety_pipeline import SafetyPipeline

    engine = OnnxEngine(synthetic_onnx_path)
    # Simple 1:1 image to world mapping
    img_pts = np.array([[0, 0], [1000, 0], [1000, 1000], [0, 1000]], dtype=np.float64)
    world_pts = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=np.float64)
    homography = HomographyManager(image_points=img_pts, world_points=world_pts)
    tracker = MultiTargetKalmanTracker(dt=0.0333, n_init=1)
    zone_cfg = ZoneConfig(
        name="danger",
        danger_polygon=[(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)],
    )
    fsm = SpatialFSM(zone_cfg)
    pipeline = SafetyPipeline(engine, homography, tracker, fsm)

    # Mock parse_detections returning a BBOX_BOTTOM degraded detection
    degraded_det = PoseDetection(
        bbox=(200.0, 100.0, 300.0, 500.0),
        keypoints=np.zeros((17, 3), dtype=np.float32),
        anchor=(250.0, 500.0),
        anchor_source=AnchorSource.BBOX_BOTTOM,
        anchor_confidence=0.36,
    )
    pipeline.parse_detections = MagicMock(return_value=[degraded_det])

    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    result = pipeline.process_frame(frame)

    assert len(result.detections) == 1
    assert result.detections[0].anchor_source == AnchorSource.BBOX_BOTTOM
    assert result.detections[0].anchor_confidence == 0.36

    assert len(result.tracks) == 1
    track = result.tracks[0]
    assert track.source == AnchorSource.BBOX_BOTTOM
    assert track.confidence == 0.36
    assert track.estimate.source == AnchorSource.BBOX_BOTTOM
    assert track.estimate.confidence == pytest.approx(0.36)
    assert track.estimate.covariance is not None




