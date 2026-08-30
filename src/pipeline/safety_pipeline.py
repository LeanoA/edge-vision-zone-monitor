"""
src/pipeline/safety_pipeline.py
End-to-End Safety Pipeline Orchestrator for Vision-Based Restricted Zone Monitoring.
Inspired by ISO 13855:2024 reaction latency and fail-safe safety integrity.
"""

from dataclasses import dataclass
from enum import Enum
import time
from typing import TYPE_CHECKING, List, Optional, Tuple
import cv2
import numpy as np

from src.core.kalman_filter import AnchorSource, PositionEstimate, Track
from src.core.spatial_fsm import SafetyOutput

if TYPE_CHECKING:
    from src.core.homography import HomographyManager
    from src.core.kalman_filter import MultiTargetKalmanTracker
    from src.core.spatial_fsm import SpatialFSM
    from src.inference.onnx_engine import OnnxEngine


@dataclass(frozen=True)
class StageLatencies:
    """High-resolution per-stage and total reaction latencies in milliseconds."""
    preprocess_ms: float
    inference_ms: float
    keypoint_extract_ms: float
    projection_ms: float
    tracking_ms: float
    fsm_evaluation_ms: float
    total_t1_ms: float


@dataclass
class PoseDetection:
    """Extracted pose detection containing bounding box, keypoints, and ground anchor."""
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    keypoints: np.ndarray                    # (17, 3) [x, y, conf]
    anchor: Optional[Tuple[float, float]] = None  # (u, v) in original frame coords
    anchor_source: Optional[AnchorSource] = None
    anchor_confidence: float = 0.0


@dataclass
class PipelineResult:
    """Result emitted by the SafetyPipeline for each processed frame."""
    frame_id: int
    timestamp: float
    safety_output: SafetyOutput
    tracks: List[Track]
    detections: List[PoseDetection]
    latencies: StageLatencies


class LayoutMode(str, Enum):
    """Layout modes for dual-stream visualization compositor."""
    SIDE_BY_SIDE = "SIDE_BY_SIDE"
    PIP = "PIP"


def letterbox_image(
    image: np.ndarray,
    target_size: Tuple[int, int] = (640, 640),
    fill_value: int = 114,
) -> Tuple[np.ndarray, float, float, float]:
    """
    Resize image with aspect ratio preservation and symmetrical padding.

    Args:
        image: Original input frame as uint8 BGR array of shape (H, W, 3).
        target_size: Target dimension tuple (width, height). Default (640, 640).
        fill_value: Pixel padding value (default 114 per YOLO standard).

    Returns:
        Tuple of:
        - normalized_tensor: (1, 3, target_h, target_w) float32 array scaled to [0, 1].
        - scale: Uniform scaling factor applied.
        - pad_x: Left horizontal padding in pixels.
        - pad_y: Top vertical padding in pixels.
    """
    h, w = image.shape[:2]
    target_w, target_h = target_size

    scale = min(target_w / w, target_h / h)
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))

    pad_x = (target_w - new_w) / 2.0
    pad_y = (target_h - new_h) / 2.0

    if (w, h) != (new_w, new_h):
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    else:
        resized = image

    top = int(round(pad_y - 0.1))
    bottom = target_h - (top + new_h)
    left = int(round(pad_x - 0.1))
    right = target_w - (left + new_w)

    padded = cv2.copyMakeBorder(
        resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(fill_value, fill_value, fill_value)
    )

    # Convert BGR to RGB, HWC to CHW, normalize to [0, 1]
    rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
    chw = np.transpose(rgb, (2, 0, 1)).astype(np.float32) / 255.0
    tensor = np.expand_dims(chw, axis=0)

    return tensor, scale, float(left), float(top)


def unletterbox_point(
    x: float,
    y: float,
    scale: float,
    pad_x: float,
    pad_y: float,
) -> Tuple[float, float]:
    """
    Map point from letterboxed coordinates back to original frame coordinates.

    Args:
        x: X coordinate in letterboxed canvas space.
        y: Y coordinate in letterboxed canvas space.
        scale: Uniform scale factor from letterbox transformation.
        pad_x: Left padding offset.
        pad_y: Top padding offset.

    Returns:
        Tuple (orig_x, orig_y) in original frame pixel space.
    """
    if scale <= 0.0:
        raise ValueError(f"Scale must be positive, got {scale}.")
    orig_x = (x - pad_x) / scale
    orig_y = (y - pad_y) / scale
    return float(orig_x), float(orig_y)


def extract_ground_anchor(
    keypoints: np.ndarray,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    conf_threshold: float = 0.5,
    scale: float = 1.0,
    pad_x: float = 0.0,
    pad_y: float = 0.0,
    allow_bbox_fallback: bool = True,
    det_score: float = 1.0,
) -> Optional[Tuple[Tuple[float, float], AnchorSource, float]]:
    """
    Extract ground anchor point with 4-tier graceful degradation hierarchy.

    Tiers:
    1. ANKLES_DUAL: Both ankles >= conf_threshold -> midpoint, avg conf.
    2. ANKLE_SINGLE: Exactly one ankle >= conf_threshold -> single ankle, conf * 0.75.
    3. BBOX_BOTTOM: Both ankles < conf_threshold & allow_bbox_fallback=True & valid bbox ->
       bottom-center ((x1+x2)/2, y2), det_score * 0.40.
    4. Dropout: Both ankles < conf_threshold & no bbox/fallback disabled -> None.

    Returns:
        Tuple of ((u, v), AnchorSource, confidence) in original frame coords, or None.
    """
    left_ankle = keypoints[15]
    right_ankle = keypoints[16]

    left_valid = float(left_ankle[2]) >= conf_threshold
    right_valid = float(right_ankle[2]) >= conf_threshold

    if left_valid and right_valid:
        # Tier 1: Dual ankles midpoint
        mid_x = (float(left_ankle[0]) + float(right_ankle[0])) / 2.0
        mid_y = (float(left_ankle[1]) + float(right_ankle[1])) / 2.0
        anchor_pt = unletterbox_point(mid_x, mid_y, scale, pad_x, pad_y)
        avg_conf = (float(left_ankle[2]) + float(right_ankle[2])) / 2.0
        return anchor_pt, AnchorSource.ANKLES_DUAL, float(avg_conf)
    elif left_valid:
        # Tier 2: Left ankle
        anchor_pt = unletterbox_point(float(left_ankle[0]), float(left_ankle[1]), scale, pad_x, pad_y)
        conf = float(left_ankle[2]) * 0.75
        return anchor_pt, AnchorSource.ANKLE_SINGLE, conf
    elif right_valid:
        # Tier 2: Right ankle
        anchor_pt = unletterbox_point(float(right_ankle[0]), float(right_ankle[1]), scale, pad_x, pad_y)
        conf = float(right_ankle[2]) * 0.75
        return anchor_pt, AnchorSource.ANKLE_SINGLE, conf
    elif allow_bbox_fallback and bbox is not None:
        # Tier 3: Bounding box bottom-center proxy
        x1, y1, x2, y2 = bbox
        bottom_cx = (x1 + x2) / 2.0
        bottom_cy = y2
        # Note: if bbox is already in original frame coordinates, no unletterbox is needed;
        # but if scale/pad are non-trivial and bbox is in letterbox space, it would unletterbox.
        # Following spec: un-letterbox coordinate mapping applied across all tiers.
        # If bbox is already passed unletterboxed (or scale=1.0, pad=0.0), unletterbox_point is identity.
        anchor_pt = unletterbox_point(bottom_cx, bottom_cy, scale, pad_x, pad_y)
        conf = float(det_score) * 0.40
        return anchor_pt, AnchorSource.BBOX_BOTTOM, conf
    else:
        # Tier 4: Dropout
        return None


def extract_ankle_anchor(
    keypoints: np.ndarray,
    conf_threshold: float = 0.5,
    scale: float = 1.0,
    pad_x: float = 0.0,
    pad_y: float = 0.0,
) -> Optional[Tuple[float, float]]:
    """
    Extract ground anchor point from pose keypoints using ankles (indices 15 & 16).

    Args:
        keypoints: Array of shape (17, 3) with [x, y, conf].
        conf_threshold: Minimum confidence required for valid ankle (default: 0.5).
        scale: Letterbox scale factor.
        pad_x: Letterbox horizontal pad.
        pad_y: Letterbox vertical pad.

    Returns:
        Tuple (u, v) in original frame coordinates, or None if both ankles < conf_threshold.
    """
    left_ankle = keypoints[15]
    right_ankle = keypoints[16]

    left_valid = left_ankle[2] >= conf_threshold
    right_valid = right_ankle[2] >= conf_threshold

    if left_valid and right_valid:
        # Midpoint of both ankles
        mid_x = (float(left_ankle[0]) + float(right_ankle[0])) / 2.0
        mid_y = (float(left_ankle[1]) + float(right_ankle[1])) / 2.0
        return unletterbox_point(mid_x, mid_y, scale, pad_x, pad_y)
    elif left_valid:
        return unletterbox_point(float(left_ankle[0]), float(left_ankle[1]), scale, pad_x, pad_y)
    elif right_valid:
        return unletterbox_point(float(right_ankle[0]), float(right_ankle[1]), scale, pad_x, pad_y)
    else:
        return None


class SafetyPipeline:
    """
    Coordinates synchronous frame processing:
    1. preprocess (letterbox 640x640)
    2. inference (OnnxEngine)
    3. keypoint_extract (YOLO Pose output parsing + ankle anchor extraction)
    4. projection (HomographyManager)
    5. tracking (MultiTargetKalmanTracker)
    6. fsm_evaluation (SpatialFSM)
    """

    def __init__(
        self,
        engine: "OnnxEngine",
        homography: "HomographyManager",
        tracker: "MultiTargetKalmanTracker",
        fsm: "SpatialFSM",
        conf_threshold: float = 0.5,
    ) -> None:
        self.engine = engine
        self.homography = homography
        self.tracker = tracker
        self.fsm = fsm
        self.conf_threshold = float(conf_threshold)
        self._frame_id = 0

    def parse_detections(
        self,
        output: np.ndarray,
        scale: float,
        pad_x: float,
        pad_y: float,
        orig_w: int,
        orig_h: int,
    ) -> List[PoseDetection]:
        """
        Parse raw YOLO Pose output tensor of shape (1, 56, 8400) or similar.
        Output format per YOLOv8/11 pose:
        Row 0..3: cx, cy, w, h
        Row 4: class/person score
        Row 5..55: 17 keypoints x 3 (x, y, conf)
        """
        detections: List[PoseDetection] = []
        if output is None or output.size == 0:
            return detections

        # Remove batch dim if present
        if output.ndim == 3:
            raw = output[0]  # (56, 8400)
        else:
            raw = output

        if raw.shape[0] < 5:
            return detections

        # Check candidate proposals above confidence threshold
        scores = raw[4, :]
        valid_indices = np.where(scores >= self.conf_threshold)[0]
        if len(valid_indices) == 0:
            return detections

        # Limit to top detections if too many
        if len(valid_indices) > 50:
            order = np.argsort(scores[valid_indices])[::-1][:50]
            valid_indices = valid_indices[order]

        for idx in valid_indices:
            cx, cy, bw, bh = raw[0, idx], raw[1, idx], raw[2, idx], raw[3, idx]
            # Convert center bbox to top-left / bottom-right in original coordinates
            lx1 = cx - bw / 2.0
            ly1 = cy - bh / 2.0
            lx2 = cx + bw / 2.0
            ly2 = cy + bh / 2.0

            x1, y1 = unletterbox_point(lx1, ly1, scale, pad_x, pad_y)
            x2, y2 = unletterbox_point(lx2, ly2, scale, pad_x, pad_y)

            # Clamp bbox
            x1 = max(0.0, min(float(x1), float(orig_w)))
            y1 = max(0.0, min(float(y1), float(orig_h)))
            x2 = max(0.0, min(float(x2), float(orig_w)))
            y2 = max(0.0, min(float(y2), float(orig_h)))

            # Keypoints: 17 * 3 = 51 values from row 5 to 55
            kps = np.zeros((17, 3), dtype=np.float32)
            if raw.shape[0] >= 56:
                kp_data = raw[5:56, idx].reshape(17, 3)
                kps[:] = kp_data

            # Extract anchor with graceful degradation hierarchy
            # Passing unletterboxed bbox coords
            extracted = extract_ground_anchor(
                kps,
                bbox=(x1, y1, x2, y2),
                conf_threshold=self.conf_threshold,
                scale=1.0,  # x1, y1, x2, y2 already unletterboxed
                pad_x=0.0,
                pad_y=0.0,
                allow_bbox_fallback=True,
                det_score=float(scores[idx]),
            )

            if extracted is not None:
                anchor, anchor_source, anchor_conf = extracted
            else:
                anchor, anchor_source, anchor_conf = None, None, 0.0

            detections.append(
                PoseDetection(
                    bbox=(x1, y1, x2, y2),
                    keypoints=kps,
                    anchor=anchor,
                    anchor_source=anchor_source,
                    anchor_confidence=anchor_conf,
                )
            )

        return detections

    def process_frame(self, frame: np.ndarray) -> PipelineResult:
        """
        Execute synchronous 6-stage frame processing with high-res latency profiling
        and fail-safe fault containment.
        """
        self._frame_id += 1
        t_start = time.perf_counter()

        try:
            if not isinstance(frame, np.ndarray) or frame.ndim != 3 or frame.shape[2] != 3:
                raise ValueError(f"Invalid frame: expected 3-channel image ndarray, got {type(frame)}")

            orig_h, orig_w = frame.shape[:2]

            # Stage 1: Preprocess (Letterbox)
            t0 = time.perf_counter()
            tensor, scale, pad_x, pad_y = letterbox_image(frame, target_size=(640, 640))
            t_preprocess = (time.perf_counter() - t0) * 1000.0

            # Stage 2: Inference
            t0 = time.perf_counter()
            model_out = self.engine.infer(tensor)
            t_infer = (time.perf_counter() - t0) * 1000.0

            # Stage 3: Keypoint & Detection Extraction
            t0 = time.perf_counter()
            detections = self.parse_detections(model_out, scale, pad_x, pad_y, orig_w, orig_h)
            # Collect ground anchors and metadata for homography projection
            valid_detections = [det for det in detections if det.anchor is not None]
            t_kp = (time.perf_counter() - t0) * 1000.0

            # Stage 4: Homography Projection & PositionEstimate packaging
            t0 = time.perf_counter()
            if len(valid_detections) > 0:
                anchors_arr = np.array([det.anchor for det in valid_detections], dtype=np.float64)
                world_positions = self.homography.project_batch(anchors_arr, to_world=True)
                position_estimates = [
                    PositionEstimate(
                        xy_m=(float(world_positions[i, 0]), float(world_positions[i, 1])),
                        confidence=valid_detections[i].anchor_confidence,
                        source=valid_detections[i].anchor_source or AnchorSource.ANKLES_DUAL,
                    )
                    for i in range(len(valid_detections))
                ]
            else:
                position_estimates = []
            t_proj = (time.perf_counter() - t0) * 1000.0

            # Stage 5: Multi-Target Kalman Tracking
            t0 = time.perf_counter()
            active_tracks = self.tracker.update(position_estimates)
            t_track = (time.perf_counter() - t0) * 1000.0

            # Stage 6: Spatial FSM Evaluation
            t0 = time.perf_counter()
            # If tracking returns confirmed tracks, pass them to FSM; else pass active_tracks
            tracks_for_fsm = active_tracks if active_tracks else self.tracker.get_tracks()
            safety_output = self.fsm.update(tracks_for_fsm, timestamp=t_start)
            t_fsm = (time.perf_counter() - t0) * 1000.0

            t_total = (time.perf_counter() - t_start) * 1000.0

            latencies = StageLatencies(
                preprocess_ms=t_preprocess,
                inference_ms=t_infer,
                keypoint_extract_ms=t_kp,
                projection_ms=t_proj,
                tracking_ms=t_track,
                fsm_evaluation_ms=t_fsm,
                total_t1_ms=t_total,
            )

            return PipelineResult(
                frame_id=self._frame_id,
                timestamp=t_start,
                safety_output=safety_output,
                tracks=tracks_for_fsm,
                detections=detections,
                latencies=latencies,
            )

        except Exception as e:
            t_total = (time.perf_counter() - t_start) * 1000.0
            # Fail-safe fault containment: set FSM to FAULT, assert trip=True
            fault_output = self.fsm.trigger_fault(f"Fault containment caught exception: {e}")
            latencies = StageLatencies(
                preprocess_ms=0.0,
                inference_ms=0.0,
                keypoint_extract_ms=0.0,
                projection_ms=0.0,
                tracking_ms=0.0,
                fsm_evaluation_ms=0.0,
                total_t1_ms=t_total,
            )
            return PipelineResult(
                frame_id=self._frame_id,
                timestamp=t_start,
                safety_output=fault_output,
                tracks=[],
                detections=[],
                latencies=latencies,
            )



