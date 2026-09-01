"""
tests/test_adaptive_anchor.py
Unit and Integration Tests for Scale-Adaptive Ground Anchor Degradation and Visualizer Badging.
"""

import numpy as np
import pytest

from src.core.kalman_filter import AnchorSource, MultiTargetKalmanTracker, PositionEstimate
from src.core.spatial_fsm import SpatialFSM, ZoneConfig
from src.core.homography import HomographyManager
from src.pipeline.safety_pipeline import (
    LayoutMode,
    PipelineResult,
    PoseDetection,
    SafetyPipeline,
    extract_ground_anchor,
)
from src.utils.visualizer import ANCHOR_COLORS, DualVisualizer


class TestScaleAdaptiveAnchorExtraction:
    """Test suite for min_ankle_bbox_height scale-aware anchor extraction."""

    @pytest.fixture
    def high_conf_keypoints(self) -> np.ndarray:
        kps = np.zeros((17, 3), dtype=np.float32)
        kps[15] = [200.0, 400.0, 0.90]  # Left ankle
        kps[16] = [220.0, 400.0, 0.85]  # Right ankle
        return kps

    def test_large_bbox_uses_dual_ankles(self, high_conf_keypoints: np.ndarray) -> None:
        """Verify bounding box taller than min_ankle_bbox_height uses high-precision dual ankles."""
        bbox = (100.0, 100.0, 300.0, 300.0)  # height = 200px
        res = extract_ground_anchor(
            high_conf_keypoints,
            bbox=bbox,
            conf_threshold=0.5,
            min_ankle_bbox_height=120.0,
            det_score=0.95,
        )
        assert res is not None
        pt, source, conf = res
        assert source == AnchorSource.ANKLES_DUAL
        assert pt == pytest.approx((210.0, 400.0))
        assert conf == pytest.approx(0.875)

    def test_small_bbox_switches_to_bbox_bottom_despite_valid_ankles(
        self, high_conf_keypoints: np.ndarray
    ) -> None:
        """Verify far-field small bbox (< min_ankle_bbox_height) forces Tier 3 BBOX_BOTTOM."""
        bbox = (100.0, 50.0, 200.0, 120.0)  # height = 70px (< 120px threshold)
        res = extract_ground_anchor(
            high_conf_keypoints,
            bbox=bbox,
            conf_threshold=0.5,
            min_ankle_bbox_height=120.0,
            det_score=0.90,
        )
        assert res is not None
        pt, source, conf = res
        assert source == AnchorSource.BBOX_BOTTOM
        assert pt == pytest.approx((150.0, 120.0))  # bottom-center
        assert conf == pytest.approx(0.90 * 0.40)   # 0.36

    def test_default_min_height_zero_preserves_ankles_for_small_bbox(
        self, high_conf_keypoints: np.ndarray
    ) -> None:
        """Verify default min_ankle_bbox_height=0.0 preserves backward compatibility."""
        bbox = (100.0, 50.0, 200.0, 100.0)  # height = 50px
        res = extract_ground_anchor(
            high_conf_keypoints,
            bbox=bbox,
            conf_threshold=0.5,
            min_ankle_bbox_height=0.0,
        )
        assert res is not None
        pt, source, conf = res
        assert source == AnchorSource.ANKLES_DUAL
        assert pt == pytest.approx((210.0, 400.0))

    def test_small_bbox_without_fallback_returns_none(
        self, high_conf_keypoints: np.ndarray
    ) -> None:
        """Verify small bbox returns None when allow_bbox_fallback is False."""
        bbox = (100.0, 50.0, 200.0, 100.0)  # height = 50px
        res = extract_ground_anchor(
            high_conf_keypoints,
            bbox=bbox,
            conf_threshold=0.5,
            min_ankle_bbox_height=120.0,
            allow_bbox_fallback=False,
        )
        assert res is None


class TestVisualizerAnchorPaletteAndBadges:
    """Test suite for DualVisualizer anchor color palette and provenance badging."""

    def test_anchor_colors_mapping_contains_all_sources(self) -> None:
        """Verify ANCHOR_COLORS contains distinct BGR entries for all AnchorSource enum members."""
        for member in AnchorSource:
            assert member in ANCHOR_COLORS
            color = ANCHOR_COLORS[member]
            assert isinstance(color, tuple)
            assert len(color) == 3

        # Distinct colors
        assert ANCHOR_COLORS[AnchorSource.ANKLES_DUAL] != ANCHOR_COLORS[AnchorSource.BBOX_BOTTOM]
        assert ANCHOR_COLORS[AnchorSource.ANKLE_SINGLE] != ANCHOR_COLORS[AnchorSource.BBOX_BOTTOM]

    def test_visualizer_renders_perspective_and_bev_with_anchor_sources(self) -> None:
        """Verify DualVisualizer renders overlays for detections with various anchor sources."""
        homography = HomographyManager(config_path="configs/default_config.yaml")
        zone_cfg = ZoneConfig(
            name="TestZone",
            danger_polygon=[(2.0, 2.0), (4.0, 2.0), (4.0, 4.0), (2.0, 4.0)],
        )
        fsm = SpatialFSM(config=zone_cfg)
        visualizer = DualVisualizer(homography=homography, fsm=fsm, headless=False)

        frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        # Create detections with different anchor sources
        kps = np.zeros((17, 3), dtype=np.float32)
        det_dual = PoseDetection(
            bbox=(100.0, 100.0, 200.0, 300.0),
            keypoints=kps,
            anchor=(150.0, 300.0),
            anchor_source=AnchorSource.ANKLES_DUAL,
            anchor_confidence=0.90,
        )
        det_bbox = PoseDetection(
            bbox=(400.0, 50.0, 450.0, 110.0),
            keypoints=kps,
            anchor=(425.0, 110.0),
            anchor_source=AnchorSource.BBOX_BOTTOM,
            anchor_confidence=0.40,
        )

        from src.pipeline.safety_pipeline import StageLatencies
        from src.core.spatial_fsm import SafetyOutput, SafetyState, OccupancyState, DwellState

        safety_out = SafetyOutput(
            state=SafetyState.SAFE,
            occupancy_state=OccupancyState.OUTSIDE,
            dwell_state=DwellState.NONE,
            dwell_time_s=0.0,
            trip=False,
            warning=False,
        )

        result = PipelineResult(
            frame_id=1,
            timestamp=0.04,
            detections=[det_dual, det_bbox],
            tracks=[],
            safety_output=safety_out,
            latencies=StageLatencies(
                capture_ms=0.5,
                preprocess_ms=1.0,
                inference_ms=10.0,
                keypoint_extract_ms=1.0,
                projection_ms=0.5,
                tracking_ms=0.5,
                fsm_evaluation_ms=0.5,
                total_t1_ms=14.0,
                total_system_ms=14.0,
            ),
        )

        perspective_rendered = visualizer.render_perspective(frame, result)
        assert perspective_rendered.shape == frame.shape

        bev_rendered = visualizer.render_bev(result)
        assert bev_rendered.shape == (visualizer.bev_size[1], visualizer.bev_size[0], 3)

        composite = visualizer.render(frame, result, layout=LayoutMode.SIDE_BY_SIDE)
        assert composite.shape[0] == frame.shape[0]
