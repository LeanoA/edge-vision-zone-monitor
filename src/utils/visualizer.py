"""
src/utils/visualizer.py
Synchronized Dual-Stream Visualization Engine for Vision-Based Restricted Zone Monitoring.
Renders annotated perspective views and orthogonal metric Bird's-Eye Views (BEV).
"""

from typing import List, Optional, Tuple
import cv2
import numpy as np

from src.core.homography import HomographyManager
from src.core.spatial_fsm import DwellState, OccupancyState, SafetyState, SpatialFSM
from src.pipeline.safety_pipeline import LayoutMode, PipelineResult


# Standard COCO 17-keypoint skeleton connections
SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),           # Head
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # Upper body / Arms
    (5, 11), (6, 12), (11, 12),               # Torso
    (11, 13), (13, 15), (12, 14), (14, 16),   # Lower body / Legs
]

# Track ID colors (BGR)
TRACK_COLORS = [
    (255, 128, 0),   # Cyan/Orange
    (0, 255, 255),   # Yellow
    (255, 0, 255),   # Magenta
    (0, 255, 0),     # Lime
    (255, 255, 0),   # Cyan
    (128, 0, 255),   # Violet
]


class DualVisualizer:
    """
    Synchronized dual-rendering engine combining perspective camera overlays
    with an orthogonal metric BEV canvas, composited via Side-by-Side or PiP.
    """

    def __init__(
        self,
        homography: HomographyManager,
        fsm: SpatialFSM,
        bev_scale: float = 100.0,
        bev_size: Tuple[int, int] = (600, 600),
        headless: bool = False,
    ) -> None:
        self.homography = homography
        self.fsm = fsm
        self.bev_scale = float(bev_scale)
        self.bev_size = bev_size  # (width, height)
        self.headless = bool(headless)

        # Precompute static H^-1 reprojections of zones for perspective overlay
        self._danger_img_poly: Optional[np.ndarray] = None
        self._release_img_poly: Optional[np.ndarray] = None
        self._precompute_perspective_zones()

        # Pre-render static BEV background canvas (grid, distance markers, zones)
        self._bev_background: Optional[np.ndarray] = None
        self._precompute_bev_background()

    def _precompute_perspective_zones(self) -> None:
        """Reproject metric danger and release polygons once using H^-1."""
        try:
            danger_coords = np.array(self.fsm.danger_polygon.exterior.coords)
            self._danger_img_poly = np.round(
                self.homography.project_batch(danger_coords, to_world=False)
            ).astype(np.int32)
        except Exception:
            self._danger_img_poly = None

        try:
            release_coords = np.array(self.fsm.release_polygon.exterior.coords)
            self._release_img_poly = np.round(
                self.homography.project_batch(release_coords, to_world=False)
            ).astype(np.int32)
        except Exception:
            self._release_img_poly = None

    def _world_to_bev(self, x_w: float, y_w: float) -> Tuple[int, int]:
        """Convert metric ground world coordinates (m) to BEV canvas pixels."""
        u = int(round(x_w * self.bev_scale))
        v = int(round(y_w * self.bev_scale))
        return u, v

    def _precompute_bev_background(self) -> None:
        """Pre-render static orthogonal grid, axes, and hazard zones to background cache."""
        w, h = self.bev_size
        canvas = np.full((h, w, 3), 30, dtype=np.uint8)  # Dark gray background

        # 1-meter major grid lines (100 px/m)
        step = int(round(self.bev_scale))
        for x in range(0, w, step):
            cv2.line(canvas, (x, 0), (x, h), (55, 55, 55), 1)
            cv2.putText(
                canvas, f"{x / self.bev_scale:.0f}m", (x + 3, 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 120, 120), 1
            )
        for y in range(0, h, step):
            cv2.line(canvas, (0, y), (w, y), (55, 55, 55), 1)
            cv2.putText(
                canvas, f"{y / self.bev_scale:.0f}m", (3, y + 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 120, 120), 1
            )

        # Draw release polygon (green / yellow boundary)
        try:
            rel_coords = np.array(self.fsm.release_polygon.exterior.coords)
            rel_bev = np.array(
                [self._world_to_bev(pt[0], pt[1]) for pt in rel_coords], dtype=np.int32
            )
            cv2.polylines(canvas, [rel_bev], isClosed=True, color=(0, 200, 200), thickness=2)
        except Exception:
            pass

        # Draw danger polygon (red / orange filled/boundary)
        try:
            dang_coords = np.array(self.fsm.danger_polygon.exterior.coords)
            dang_bev = np.array(
                [self._world_to_bev(pt[0], pt[1]) for pt in dang_coords], dtype=np.int32
            )
            # Semi-transparent danger overlay
            overlay = canvas.copy()
            cv2.fillPoly(overlay, [dang_bev], (0, 0, 160))
            cv2.addWeighted(overlay, 0.3, canvas, 0.7, 0, canvas)
            cv2.polylines(canvas, [dang_bev], isClosed=True, color=(0, 0, 255), thickness=2)
        except Exception:
            pass

        self._bev_background = canvas

    def render_perspective(self, frame: np.ndarray, result: PipelineResult) -> np.ndarray:
        """Render inverse homography polygons, skeletons, anchors, and status banner."""
        if self.headless:
            return frame

        canvas = frame.copy()
        h, w = canvas.shape[:2]

        # 1. Draw reprojected zones
        if self._release_img_poly is not None:
            cv2.polylines(canvas, [self._release_img_poly], isClosed=True, color=(0, 200, 200), thickness=2)
        if self._danger_img_poly is not None:
            cv2.polylines(canvas, [self._danger_img_poly], isClosed=True, color=(0, 0, 255), thickness=2)

        # 2. Draw detections (bboxes, skeletons, anchors)
        for det in result.detections:
            x1, y1, x2, y2 = [int(round(v)) for v in det.bbox]
            cv2.rectangle(canvas, (x1, y1), (x2, y2), (255, 200, 0), 2)

            # Draw skeleton
            kps = det.keypoints
            for p1_idx, p2_idx in SKELETON_CONNECTIONS:
                if p1_idx < len(kps) and p2_idx < len(kps):
                    kp1, kp2 = kps[p1_idx], kps[p2_idx]
                    if kp1[2] >= 0.5 and kp2[2] >= 0.5:
                        pt1 = (int(round(kp1[0])), int(round(kp1[1])))
                        pt2 = (int(round(kp2[0])), int(round(kp2[1])))
                        cv2.line(canvas, pt1, pt2, (0, 255, 0), 2)

            # Draw keypoint dots
            for kp in kps:
                if kp[2] >= 0.5:
                    pt = (int(round(kp[0])), int(round(kp[1])))
                    cv2.circle(canvas, pt, 3, (0, 255, 255), -1)

            # Draw ground anchor
            if det.anchor is not None:
                ax, ay = int(round(det.anchor[0])), int(round(det.anchor[1]))
                cv2.drawMarker(canvas, (ax, ay), (0, 0, 255), cv2.MARKER_TILTED_CROSS, 12, 2)

        # 3. Render Status Banner
        banner_h = 45
        banner = np.zeros((banner_h, w, 3), dtype=np.uint8)

        is_tripped = result.safety_output.trip
        occ = result.safety_output.occupancy_state
        dwell = result.safety_output.dwell_state
        dwell_s = result.safety_output.dwell_time_s
        state = result.safety_output.state

        if is_tripped or state in (SafetyState.FAULT, SafetyState.LOCKOUT):
            banner_bg = (0, 0, 200)      # Alert Red
            text_color = (255, 255, 255)
            if state == SafetyState.LOCKOUT:
                status_text = "SAFETY TRIP: LOCKOUT (LATCHED)"
            elif state == SafetyState.FAULT:
                status_text = "SAFETY TRIP: FAULT"
            else:
                dwell_suffix = f" | DWELL: {dwell.value} ({dwell_s:.1f}s)" if dwell != DwellState.NONE else ""
                status_text = f"SAFETY TRIP: {occ.value}{dwell_suffix}"
        elif occ in (OccupancyState.ENTER_PENDING, OccupancyState.EXIT_PENDING) or result.safety_output.warning:
            banner_bg = (0, 165, 255)    # Amber Warning
            text_color = (0, 0, 0)
            status_text = f"WARNING: {occ.value}"
        else:
            banner_bg = (0, 140, 0)      # Safe Green
            text_color = (255, 255, 255)
            status_text = f"SYSTEM SAFE: {occ.value}"

        banner[:] = banner_bg
        cv2.addWeighted(banner, 0.85, canvas[:banner_h, :], 0.15, 0, canvas[:banner_h, :])

        fps = 1000.0 / result.latencies.total_t1_ms if result.latencies.total_t1_ms > 0 else 0.0
        telemetry = f"t1: {result.latencies.total_t1_ms:.1f}ms ({fps:.0f} FPS) | Tracks: {len(result.tracks)}"

        cv2.putText(canvas, status_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, text_color, 2)
        cv2.putText(canvas, telemetry, (w - 380, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, text_color, 1)

        return canvas

    def render_bev(self, result: PipelineResult) -> np.ndarray:
        """Render dynamic tracks, velocity vectors, and dwell times over cached BEV background."""
        if self.headless:
            return np.empty((0, 0, 3), dtype=np.uint8)

        canvas = self._bev_background.copy() if self._bev_background is not None else np.zeros((self.bev_size[1], self.bev_size[0], 3), dtype=np.uint8)

        for track in result.tracks:
            color = TRACK_COLORS[track.track_id % len(TRACK_COLORS)]
            pos = track.position  # (X_w, Y_w)
            vel = track.velocity  # (vx, vy)
            speed = float(np.linalg.norm(vel))

            u, v = self._world_to_bev(pos[0], pos[1])
            # Draw track point
            cv2.circle(canvas, (u, v), 6, color, -1)
            cv2.circle(canvas, (u, v), 8, (255, 255, 255), 1)

            # Draw velocity vector arrow (scaled: 1 m/s = 50 pixels)
            arrow_scale = 50.0
            u_end = int(round(u + vel[0] * arrow_scale))
            v_end = int(round(v + vel[1] * arrow_scale))
            if speed > 0.05:
                cv2.arrowedLine(canvas, (u, v), (u_end, v_end), color, 2, tipLength=0.3)

            # Track label: ID, speed, dwell time
            label = f"ID:{track.track_id} {speed:.1f}m/s"
            cv2.putText(canvas, label, (u + 10, v - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        return canvas

    def composite(
        self,
        perspective: np.ndarray,
        bev: np.ndarray,
        layout: LayoutMode = LayoutMode.SIDE_BY_SIDE,
    ) -> np.ndarray:
        """Composite perspective frame and metric BEV canvas."""
        if self.headless:
            return perspective

        ph, pw = perspective.shape[:2]
        bh, bw = bev.shape[:2]

        if layout == LayoutMode.SIDE_BY_SIDE:
            # Scale BEV canvas to match perspective height
            if bh != ph:
                scale = ph / bh
                new_bw = int(round(bw * scale))
                bev_scaled = cv2.resize(bev, (new_bw, ph), interpolation=cv2.INTER_LINEAR)
            else:
                bev_scaled = bev
            return np.hstack([perspective, bev_scaled])

        elif layout == LayoutMode.PIP:
            # Picture-in-Picture: embed BEV in bottom-right corner
            pip_h = ph // 3
            pip_w = int(round(bw * (pip_h / bh)))
            bev_pip = cv2.resize(bev, (pip_w, pip_h), interpolation=cv2.INTER_LINEAR)

            out = perspective.copy()
            margin = 15
            y1 = ph - pip_h - margin
            y2 = ph - margin
            x1 = pw - pip_w - margin
            x2 = pw - margin

            # Contrasting border
            cv2.rectangle(out, (x1 - 2, y1 - 2), (x2 + 2, y2 + 2), (255, 255, 255), 2)
            out[y1:y2, x1:x2] = bev_pip
            return out

        else:
            return perspective

    def render(
        self,
        frame: np.ndarray,
        result: PipelineResult,
        layout: LayoutMode = LayoutMode.SIDE_BY_SIDE,
    ) -> np.ndarray:
        """Top-level render entry point with fast headless bypass."""
        if self.headless:
            return frame

        perspective = self.render_perspective(frame, result)
        bev = self.render_bev(result)
        return self.composite(perspective, bev, layout=layout)
