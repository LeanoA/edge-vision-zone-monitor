"""
src/utils/visualizer.py
Synchronized Dual-Stream Visualization Engine for Vision-Based Restricted Zone Monitoring.
Renders annotated perspective views and orthogonal metric Bird's-Eye Views (BEV) with
ultra-legible, modern industrial HUD status banners and telemetry badges.
"""

from typing import List, Optional, Tuple
import cv2
import numpy as np

from src.core.homography import HomographyManager
from src.core.kalman_filter import AnchorSource
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
    (0, 215, 255),   # Bright Amber/Gold
    (255, 144, 30),  # Deep Sky Blue
    (50, 205, 50),   # Lime Green
    (238, 130, 238), # Violet
    (0, 255, 255),   # Yellow
    (255, 105, 180), # Hot Pink
]

# Anchor Source palette (BGR)
ANCHOR_COLORS = {
    AnchorSource.ANKLES_DUAL: (0, 255, 255),       # Yellow: Dual ankles midpoint
    AnchorSource.ANKLE_SINGLE: (0, 200, 255),      # Amber: Single ankle keypoint
    AnchorSource.BBOX_BOTTOM: (255, 0, 255),       # Magenta: BBox bottom fallback
    AnchorSource.TRACKER_PREDICTED: (0, 140, 255), # Orange: Coasting / Kalman prediction
}


class DualVisualizer:
    """
    Synchronized dual-rendering engine combining perspective camera overlays
    with an orthogonal metric BEV canvas, composited via Side-by-Side or PiP.
    """

    def __init__(
        self,
        homography: HomographyManager,
        fsm: SpatialFSM,
        bev_scale: Optional[float] = None,
        bev_size: Tuple[int, int] = (600, 600),
        world_bounds: Optional[Tuple[float, float, float, float]] = None,
        headless: bool = False,
    ) -> None:
        self.homography = homography
        self.fsm = fsm
        self.bev_size = bev_size  # (width, height)
        self.headless = bool(headless)

        # Compute dynamic world bounds if not explicitly supplied
        if world_bounds is not None:
            self._world_min_x, self._world_min_y, self._world_max_x, self._world_max_y = [
                float(v) for v in world_bounds
            ]
        else:
            pts = []
            try:
                pts.extend(list(self.fsm.danger_polygon.exterior.coords))
            except Exception:
                pass
            try:
                pts.extend(list(self.fsm.release_polygon.exterior.coords))
            except Exception:
                pass
            if hasattr(self.homography, "_world_points") and self.homography._world_points is not None:
                pts.extend(self.homography._world_points.tolist())

            if pts:
                arr = np.array(pts, dtype=np.float64)
                raw_min_x, raw_min_y = float(np.min(arr[:, 0])), float(np.min(arr[:, 1]))
                raw_max_x, raw_max_y = float(np.max(arr[:, 0])), float(np.max(arr[:, 1]))
                span_x = max(raw_max_x - raw_min_x, 1.0)
                span_y = max(raw_max_y - raw_min_y, 1.0)
                margin_x = max(span_x * 0.15, 1.0)
                margin_y = max(span_y * 0.15, 1.0)
                self._world_min_x = float(raw_min_x - margin_x)
                self._world_max_x = float(raw_max_x + margin_x)
                self._world_min_y = float(raw_min_y - margin_y)
                self._world_max_y = float(raw_max_y + margin_y)
            else:
                self._world_min_x, self._world_min_y, self._world_max_x, self._world_max_y = (
                    0.0, 0.0, 6.0, 6.0
                )

        span_w = max(self._world_max_x - self._world_min_x, 0.1)
        span_h = max(self._world_max_y - self._world_min_y, 0.1)
        w_px, h_px = self.bev_size

        if bev_scale is not None:
            self.bev_scale = float(bev_scale)
            self._bev_offset_x = 0.0
            self._bev_offset_y = 0.0
            self._world_min_x = 0.0
            self._world_min_y = 0.0
        else:
            self.bev_scale = float(min(w_px / span_w, h_px / span_h))
            self._bev_offset_x = (w_px - span_w * self.bev_scale) / 2.0
            self._bev_offset_y = (h_px - span_h * self.bev_scale) / 2.0

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
        w, h = self.bev_size
        u = int(round(self._bev_offset_x + (x_w - self._world_min_x) * self.bev_scale))
        v = int(round(h - 1 - self._bev_offset_y - (y_w - self._world_min_y) * self.bev_scale))
        return u, v

    def _precompute_bev_background(self) -> None:
        """Pre-render static orthogonal grid, axes, and hazard zones to background cache."""
        w, h = self.bev_size
        canvas = np.full((h, w, 3), 26, dtype=np.uint8)

        span_max = max(
            self._world_max_x - self._world_min_x,
            self._world_max_y - self._world_min_y,
        )
        if span_max <= 12.0:
            step_m = 1.0
        elif span_max <= 25.0:
            step_m = 2.0
        else:
            step_m = 5.0

        # Draw vertical grid lines (X axis)
        x_start = np.floor(self._world_min_x / step_m) * step_m
        x_curr = x_start
        while x_curr <= self._world_max_x + step_m:
            u, _ = self._world_to_bev(x_curr, self._world_min_y)
            if 0 <= u < w:
                cv2.line(canvas, (u, 0), (u, h), (48, 48, 48), 1, cv2.LINE_AA)
                cv2.putText(
                    canvas,
                    f"{x_curr:.0f}m",
                    (u + 3, h - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.35,
                    (140, 140, 140),
                    1,
                    cv2.LINE_AA,
                )
            x_curr += step_m

        # Draw horizontal grid lines (Y axis - depth)
        y_start = np.floor(self._world_min_y / step_m) * step_m
        y_curr = y_start
        while y_curr <= self._world_max_y + step_m:
            _, v = self._world_to_bev(self._world_min_x, y_curr)
            if 0 <= v < h:
                cv2.line(canvas, (0, v), (w, v), (48, 48, 48), 1, cv2.LINE_AA)
                cv2.putText(
                    canvas,
                    f"{y_curr:.0f}m",
                    (5, v - 4),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.35,
                    (140, 140, 140),
                    1,
                    cv2.LINE_AA,
                )
            y_curr += step_m

        # Draw release polygon (green / yellow boundary)
        try:
            rel_coords = np.array(self.fsm.release_polygon.exterior.coords)
            rel_bev = np.array(
                [self._world_to_bev(pt[0], pt[1]) for pt in rel_coords], dtype=np.int32
            )
            cv2.polylines(canvas, [rel_bev], isClosed=True, color=(0, 200, 255), thickness=2, lineType=cv2.LINE_AA)
        except Exception:
            pass

        # Draw danger polygon (red / orange filled/boundary)
        try:
            dang_coords = np.array(self.fsm.danger_polygon.exterior.coords)
            dang_bev = np.array(
                [self._world_to_bev(pt[0], pt[1]) for pt in dang_coords], dtype=np.int32
            )
            overlay = canvas.copy()
            cv2.fillPoly(overlay, [dang_bev], (20, 20, 180))
            cv2.addWeighted(overlay, 0.35, canvas, 0.65, 0, canvas)
            cv2.polylines(canvas, [dang_bev], isClosed=True, color=(0, 0, 255), thickness=2, lineType=cv2.LINE_AA)
        except Exception:
            pass

        # Header title for BEV
        cv2.putText(canvas, "BIRD'S-EYE VIEW (METRIC GROUND)", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)

        self._bev_background = canvas

    def _draw_pill(
        self,
        img: np.ndarray,
        text: str,
        x: int,
        y: int,
        bg_color: Tuple[int, int, int],
        text_color: Tuple[int, int, int] = (255, 255, 255),
        font_scale: float = 0.55,
        thickness: int = 1,
        pad_x: int = 10,
        pad_y: int = 6,
    ) -> int:
        """Draw a sleek, anti-aliased pill badge with background, returning badge end X."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        (tw, th), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        
        bx1 = x
        by1 = y - th - pad_y
        bx2 = x + tw + pad_x * 2
        by2 = y + pad_y

        h, w = img.shape[:2]
        if bx1 < 0 or by1 < 0 or bx2 > w or by2 > h:
            cv2.putText(img, text, (x, y), font, font_scale, text_color, thickness, cv2.LINE_AA)
            return bx2

        sub = img[by1:by2, bx1:bx2]
        badge = np.full_like(sub, bg_color)
        blended = cv2.addWeighted(badge, 0.90, sub, 0.10, 0)
        img[by1:by2, bx1:bx2] = blended

        cv2.rectangle(img, (bx1, by1), (bx2, by2), (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(img, text, (bx1 + pad_x, y), font, font_scale, text_color, thickness, cv2.LINE_AA)
        return bx2

    def render_perspective(self, frame: np.ndarray, result: PipelineResult) -> np.ndarray:
        """Render inverse homography polygons, skeletons, anchors, and top HUD banner."""
        if self.headless:
            return frame

        canvas = frame.copy()
        h, w = canvas.shape[:2]

        # 1. Draw reprojected zones
        if self._release_img_poly is not None:
            cv2.polylines(canvas, [self._release_img_poly], isClosed=True, color=(0, 200, 255), thickness=2, lineType=cv2.LINE_AA)
        if self._danger_img_poly is not None:
            cv2.polylines(canvas, [self._danger_img_poly], isClosed=True, color=(0, 0, 255), thickness=2, lineType=cv2.LINE_AA)

        # 2. Draw detections (bboxes, skeletons, anchors)
        for det in result.detections:
            x1, y1, x2, y2 = [int(round(v)) for v in det.bbox]
            cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 230, 255), 2, cv2.LINE_AA)

            # Draw skeleton
            kps = det.keypoints
            for p1_idx, p2_idx in SKELETON_CONNECTIONS:
                if p1_idx < len(kps) and p2_idx < len(kps):
                    kp1, kp2 = kps[p1_idx], kps[p2_idx]
                    if kp1[2] >= 0.5 and kp2[2] >= 0.5:
                        pt1 = (int(round(kp1[0])), int(round(kp1[1])))
                        pt2 = (int(round(kp2[0])), int(round(kp2[1])))
                        cv2.line(canvas, pt1, pt2, (0, 255, 120), 2, cv2.LINE_AA)

            # Draw keypoint dots
            for kp in kps:
                if kp[2] >= 0.5:
                    pt = (int(round(kp[0])), int(round(kp[1])))
                    cv2.circle(canvas, pt, 4, (0, 255, 255), -1, cv2.LINE_AA)

            # Draw ground anchor with provenance-based color and high-contrast tag
            if det.anchor is not None:
                ax, ay = int(round(det.anchor[0])), int(round(det.anchor[1]))
                color = ANCHOR_COLORS.get(det.anchor_source, (0, 0, 255))
                cv2.drawMarker(canvas, (ax, ay), color, cv2.MARKER_TILTED_CROSS, 14, 2, cv2.LINE_AA)
                if det.anchor_source is not None:
                    tag = f"ANCHOR: {det.anchor_source.value}"
                    self._draw_pill(canvas, tag, ax + 10, ay - 6, (20, 20, 20), color, font_scale=0.38, pad_x=6, pad_y=4)

        # 3. Top HUD Banner (Clean, dark translucent header bar)
        banner_h = 56
        banner_sub = canvas[:banner_h, :]
        banner_bg = np.zeros_like(banner_sub)
        cv2.addWeighted(banner_bg, 0.88, banner_sub, 0.12, 0, banner_sub)
        cv2.line(canvas, (0, banner_h), (w, banner_h), (70, 70, 70), 1, cv2.LINE_AA)

        is_tripped = result.safety_output.trip
        occ = result.safety_output.occupancy_state
        dwell = result.safety_output.dwell_state
        dwell_s = result.safety_output.dwell_time_s
        state = result.safety_output.state

        # Primary Safety State Badge (Left side)
        if is_tripped or state in (SafetyState.FAULT, SafetyState.LOCKOUT):
            badge_bg = (0, 0, 190)
            if state == SafetyState.LOCKOUT:
                status_text = "CRITICAL TRIP: LOCKOUT (LATCHED)"
            elif state == SafetyState.FAULT:
                status_text = "CRITICAL TRIP: FAULT"
            else:
                status_text = f"SAFETY TRIP: {occ.value}"
        elif occ in (OccupancyState.ENTER_PENDING, OccupancyState.EXIT_PENDING) or result.safety_output.warning:
            badge_bg = (0, 140, 230)
            status_text = f"WARNING: {occ.value}"
        else:
            badge_bg = (20, 140, 40)
            status_text = f"SYSTEM NORMAL: {occ.value}"

        self._draw_pill(canvas, status_text, 16, 38, badge_bg, (255, 255, 255), font_scale=0.60, thickness=2, pad_x=14, pad_y=8)

        # Telemetry Badges (Right side)
        fps = 1000.0 / result.latencies.total_t1_ms if result.latencies.total_t1_ms > 0 else 0.0
        cur_x = w - 20
        
        # 1. Tracks Badge
        tracks_txt = f"TRACKS: {len(result.tracks)}"
        (tw1, _), _ = cv2.getTextSize(tracks_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.50, 1)
        cur_x -= (tw1 + 24)
        self._draw_pill(canvas, tracks_txt, cur_x, 38, (45, 45, 45), (0, 230, 255), font_scale=0.50, pad_x=8, pad_y=6)

        # 2. Latency / FPS Badge
        t1_txt = f"T1: {result.latencies.total_t1_ms:.1f}ms ({fps:.0f} FPS)"
        (tw2, _), _ = cv2.getTextSize(t1_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.50, 1)
        cur_x -= (tw2 + 32)
        self._draw_pill(canvas, t1_txt, cur_x, 38, (45, 45, 45), (255, 255, 255), font_scale=0.50, pad_x=8, pad_y=6)

        # 3. Dwell Badge (if active)
        if dwell_s > 0.0 or dwell != DwellState.NONE:
            dwell_color = (0, 0, 255) if dwell_s >= 5.0 else (0, 180, 255)
            dwell_txt = f"DWELL: {dwell_s:.1f}s"
            (tw3, _), _ = cv2.getTextSize(dwell_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.50, 1)
            cur_x -= (tw3 + 32)
            self._draw_pill(canvas, dwell_txt, cur_x, 38, (30, 30, 30), dwell_color, font_scale=0.50, pad_x=8, pad_y=6)

        return canvas

    def render_bev(self, result: PipelineResult) -> np.ndarray:
        """Render dynamic tracks, velocity vectors, and dwell times over cached BEV background."""
        if self.headless:
            return np.empty((0, 0, 3), dtype=np.uint8)

        canvas = self._bev_background.copy() if self._bev_background is not None else np.zeros((self.bev_size[1], self.bev_size[0], 3), dtype=np.uint8)

        for track in result.tracks:
            color = TRACK_COLORS[track.track_id % len(TRACK_COLORS)]
            pos = track.position
            vel = track.velocity
            speed = float(np.linalg.norm(vel))

            u, v = self._world_to_bev(pos[0], pos[1])
            # Glow circle
            cv2.circle(canvas, (u, v), 10, color, 1, cv2.LINE_AA)
            cv2.circle(canvas, (u, v), 6, color, -1, cv2.LINE_AA)
            cv2.circle(canvas, (u, v), 2, (255, 255, 255), -1, cv2.LINE_AA)

            # Draw velocity vector arrow
            if speed > 0.05:
                dt = 0.6
                u_end, v_end = self._world_to_bev(pos[0] + vel[0] * dt, pos[1] + vel[1] * dt)
                cv2.arrowedLine(canvas, (u, v), (u_end, v_end), color, 2, tipLength=0.25, line_type=cv2.LINE_AA)

            # High-contrast track pill
            source_tag = f" [{track.anchor_source.value[:4]}]" if hasattr(track, "anchor_source") and track.anchor_source else ""
            label = f"ID:{track.track_id} | {speed:.1f}m/s{source_tag}"
            self._draw_pill(canvas, label, u + 12, v - 6, (20, 20, 20), (255, 255, 255), font_scale=0.42, pad_x=6, pad_y=4)

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
            if bh != ph:
                scale = ph / bh
                new_bw = int(round(bw * scale))
                bev_scaled = cv2.resize(bev, (new_bw, ph), interpolation=cv2.INTER_LINEAR)
            else:
                bev_scaled = bev
            
            # Vertical separator line between views
            cv2.line(bev_scaled, (0, 0), (0, ph), (80, 80, 80), 2, cv2.LINE_AA)
            return np.hstack([perspective, bev_scaled])

        elif layout == LayoutMode.PIP:
            pip_h = ph // 3
            pip_w = int(round(bw * (pip_h / bh)))
            bev_pip = cv2.resize(bev, (pip_w, pip_h), interpolation=cv2.INTER_LINEAR)

            out = perspective.copy()
            margin = 15
            y1 = ph - pip_h - margin
            y2 = ph - margin
            x1 = pw - pip_w - margin
            x2 = pw - margin

            cv2.rectangle(out, (x1 - 2, y1 - 2), (x2 + 2, y2 + 2), (255, 255, 255), 2, cv2.LINE_AA)
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
