"""
src/utils/synthetic_generator.py
Synthetic Video and Frame Generator for Vision-Based Industrial Safety Monitoring.
Generates deterministic ground-truth video sequences matching calibrated floor geometry
using perspective-scaled photorealistic RGBA worker sprites compatible with YOLO models.
"""

from dataclasses import dataclass
import math
from pathlib import Path
from typing import List, Optional, Tuple, Union
import cv2
import numpy as np

from src.core.homography import HomographyManager


@dataclass(frozen=True)
class SyntheticScenarioConfig:
    """Configuration metadata for a synthetic video generation run."""
    name: str
    description: str
    width: int = 1920
    height: int = 1080
    fps: int = 30
    duration_s: float = 6.0
    danger_polygon: Tuple[Tuple[float, float], ...] = (
        (1.0, 2.0),
        (3.0, 2.0),
        (3.0, 4.0),
        (1.0, 4.0),
    )
    warning_polygon: Tuple[Tuple[float, float], ...] = (
        (0.8, 1.8),
        (3.2, 1.8),
        (3.2, 4.2),
        (0.8, 4.2),
    )


class SyntheticVideoGenerator:
    """
    High-fidelity synthetic video generator for industrial safety zone testing.
    Uses calibrated planar homography to render perspective-accurate floor grids,
    safety zones, photorealistic RGBA humanoid sprites, and physical occlusion obstacles.
    """

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = "configs/default_config.yaml",
        homography_manager: Optional[HomographyManager] = None,
        sprite_dir: Optional[Union[str, Path]] = None,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
    ) -> None:
        """
        Initialize synthetic video generator.

        Args:
            config_path: Optional path to calibration YAML.
            homography_manager: Optional pre-calibrated HomographyManager instance.
            sprite_dir: Directory containing RGBA worker walking sprites.
            width: Frame width in pixels.
            height: Frame height in pixels.
            fps: Frame rate in frames per second.
        """
        self.width = width
        self.height = height
        self.fps = fps

        if homography_manager is not None:
            self.homography = homography_manager
        elif config_path is not None and Path(config_path).exists():
            self.homography = HomographyManager(config_path=config_path)
        else:
            # Fallback default calibration points
            img_pts = np.array([[480.0, 920.0], [1440.0, 920.0], [1200.0, 480.0], [720.0, 480.0]])
            wld_pts = np.array([[0.0, 0.0], [4.0, 0.0], [4.0, 6.0], [0.0, 6.0]])
            self.homography = HomographyManager(image_points=img_pts, world_points=wld_pts)

        # Precompute static background with floor grid and safety zones
        self._danger_polygon = ((1.0, 2.0), (3.0, 2.0), (3.0, 4.0), (1.0, 4.0))
        self._warning_polygon = ((0.8, 1.8), (3.2, 1.8), (3.2, 4.2), (0.8, 4.2))

        # Sprite Library Setup
        if sprite_dir is not None:
            self.sprite_dir = Path(sprite_dir)
        else:
            repo_root = Path(__file__).resolve().parent.parent.parent
            self.sprite_dir = repo_root / "data" / "assets" / "sprites" / "worker"

        self.walk_sprites: List[np.ndarray] = []
        self.idle_sprite: Optional[np.ndarray] = None
        self._load_sprites()

    def _load_sprites(self) -> None:
        """Load RGBA sprite walking cycle and idle sprite into memory."""
        if not self.sprite_dir.exists():
            return

        walk_files = sorted(list(self.sprite_dir.glob("walk_*.png")))
        for wf in walk_files:
            sprite = cv2.imread(str(wf), cv2.IMREAD_UNCHANGED)
            if sprite is not None and sprite.ndim == 3 and sprite.shape[2] == 4:
                self.walk_sprites.append(sprite)

        idle_file = self.sprite_dir / "idle_00.png"
        if idle_file.is_file():
            self.idle_sprite = cv2.imread(str(idle_file), cv2.IMREAD_UNCHANGED)
        elif self.walk_sprites:
            self.idle_sprite = self.walk_sprites[0]

    def _get_pixel_scale(self, world_y: float) -> float:
        """
        Compute perspective height scale in pixels for a 1.75m standing human.
        Follows pinhole perspective camera projection calibrated to ground coordinates.
        """
        clamped_y = max(0.0, min(8.0, world_y))
        scale = 480.0 / (1.0 + 0.165 * clamped_y)
        return scale

    def render_base_scene(
        self,
        danger_poly: Optional[Tuple[Tuple[float, float], ...]] = None,
        warning_poly: Optional[Tuple[Tuple[float, float], ...]] = None,
    ) -> np.ndarray:
        """
        Render static industrial plant background with perspective floor grid and zone markings.
        """
        danger = danger_poly or self._danger_polygon
        warning = warning_poly or self._warning_polygon

        # Create slate gray industrial factory floor
        frame = np.full((self.height, self.width, 3), (45, 42, 38), dtype=np.uint8)

        # Draw wall/horizon boundary at top
        cv2.rectangle(frame, (0, 0), (self.width, int(self.height * 0.35)), (30, 28, 26), -1)
        cv2.line(frame, (0, int(self.height * 0.35)), (self.width, int(self.height * 0.35)), (70, 68, 64), 2)

        # Draw metric ground grid (lines every 0.5 meter)
        grid_color = (65, 60, 55)
        # X-lines (along Y from 0 to 6)
        for x in np.arange(0.0, 4.1, 0.5):
            pts = []
            for y in np.arange(0.0, 6.1, 0.2):
                u, v = self.homography.project_to_image(x, y)
                pts.append((int(u), int(v)))
            for i in range(len(pts) - 1):
                cv2.line(frame, pts[i], pts[i + 1], grid_color, 1, cv2.LINE_AA)

        # Y-lines (along X from 0 to 4)
        for y in np.arange(0.0, 6.1, 1.0):
            pts = []
            for x in np.arange(0.0, 4.1, 0.2):
                u, v = self.homography.project_to_image(x, y)
                pts.append((int(u), int(v)))
            for i in range(len(pts) - 1):
                cv2.line(frame, pts[i], pts[i + 1], grid_color, 1, cv2.LINE_AA)

        # Draw Calibration Reference Markers at corners
        calib_corners = [(0.0, 0.0), (4.0, 0.0), (4.0, 6.0), (0.0, 6.0)]
        for idx, (cx, cy) in enumerate(calib_corners):
            cu, cv = self.homography.project_to_image(cx, cy)
            pt = (int(cu), int(cv))
            cv2.circle(frame, pt, 6, (0, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(frame, pt, 8, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, f"CAL-{idx+1} ({cx:.0f},{cy:.0f}m)", (pt[0] + 10, pt[1] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 230, 255), 1, cv2.LINE_AA)

        # Draw Warning Zone Polygon (Amber overlay)
        if warning:
            warn_px = np.array([self.homography.project_to_image(px, py) for px, py in warning], dtype=np.int32)
            overlay = frame.copy()
            cv2.fillPoly(overlay, [warn_px], (20, 140, 220))  # Amber
            cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
            cv2.polylines(frame, [warn_px], True, (0, 180, 255), 2, cv2.LINE_AA)

        # Draw Danger Zone Polygon (Red overlay)
        if danger:
            danger_px = np.array([self.homography.project_to_image(px, py) for px, py in danger], dtype=np.int32)
            overlay = frame.copy()
            cv2.fillPoly(overlay, [danger_px], (20, 20, 180))  # Red
            cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)
            cv2.polylines(frame, [danger_px], True, (0, 0, 240), 3, cv2.LINE_AA)

            # Label Danger Zone
            d_center_u, d_center_v = self.homography.project_to_image(2.0, 3.0)
            cv2.putText(
                frame,
                "RESTRICTED ZONE (ISO 13855)",
                (int(d_center_u) - 140, int(d_center_v)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

        return frame

    def render_worker_sprite(
        self,
        frame: np.ndarray,
        world_x: float,
        world_y: float,
        gait_phase: float = 0.0,
        is_idle: bool = False,
    ) -> None:
        """
        Render a perspective-accurate, photorealistic RGBA humanoid worker sprite onto the frame
        with directional soft contact shadow and sub-pixel alpha blending.
        """
        u_base, v_base = self.homography.project_to_image(world_x, world_y)
        u_base, v_base = int(u_base), int(v_base)

        height_scale = self._get_pixel_scale(world_y)
        target_h = max(60, int(height_scale))

        if is_idle and self.idle_sprite is not None:
            src_sprite = self.idle_sprite
        elif self.walk_sprites:
            num_sprites = len(self.walk_sprites)
            normalized_phase = (gait_phase % (2.0 * math.pi)) / (2.0 * math.pi)
            sprite_idx = int(normalized_phase * num_sprites) % num_sprites
            src_sprite = self.walk_sprites[sprite_idx]
        else:
            self._draw_fallback_geometric(frame, world_x, world_y, gait_phase)
            return

        orig_h, orig_w = src_sprite.shape[:2]
        target_w = max(20, int(target_h * (orig_w / orig_h)))

        # 1. Render Directional Soft Contact Shadow
        shadow_w = int(target_w * 0.55)
        shadow_h = max(6, int(target_w * 0.20))
        shadow_y = v_base - int(shadow_h * 0.15)

        shadow_overlay = frame.copy()
        cv2.ellipse(
            shadow_overlay,
            (u_base, shadow_y),
            (shadow_w, shadow_h),
            0,
            0,
            360,
            (10, 10, 10),
            -1,
            cv2.LINE_AA,
        )
        cv2.addWeighted(shadow_overlay, 0.40, frame, 0.60, 0, frame)

        # 2. Resize Sprite with Bilinear / Lanczos interpolation
        sprite_resized = cv2.resize(
            src_sprite,
            (target_w, target_h),
            interpolation=cv2.INTER_LANCZOS4 if target_h >= orig_h else cv2.INTER_AREA,
        )

        # 3. Canvas Coordinates (Feet aligned with u_base, v_base)
        y1 = v_base - target_h
        y2 = v_base
        x1 = u_base - target_w // 2
        x2 = x1 + target_w

        clip_y1 = max(0, y1)
        clip_y2 = min(self.height, y2)
        clip_x1 = max(0, x1)
        clip_x2 = min(self.width, x2)

        if clip_x1 >= clip_x2 or clip_y1 >= clip_y2:
            return

        s_y1 = clip_y1 - y1
        s_y2 = s_y1 + (clip_y2 - clip_y1)
        s_x1 = clip_x1 - x1
        s_x2 = s_x1 + (clip_x2 - clip_x1)

        sprite_crop = sprite_resized[s_y1:s_y2, s_x1:s_x2]
        sprite_rgb = sprite_crop[:, :, :3]
        sprite_alpha = sprite_crop[:, :, 3:4] / 255.0

        bg_crop = frame[clip_y1:clip_y2, clip_x1:clip_x2]
        blended = (sprite_alpha * sprite_rgb + (1.0 - sprite_alpha) * bg_crop).astype(np.uint8)
        frame[clip_y1:clip_y2, clip_x1:clip_x2] = blended

    def _draw_fallback_geometric(
        self,
        frame: np.ndarray,
        world_x: float,
        world_y: float,
        gait_phase: float = 0.0,
    ) -> None:
        """Fallback geometric drawing if sprite assets are missing."""
        u_base, v_base = self.homography.project_to_image(world_x, world_y)
        u_base, v_base = int(u_base), int(v_base)
        height_scale = self._get_pixel_scale(world_y)
        body_h = int(height_scale)

        cv2.circle(frame, (u_base, v_base - body_h + 15), 15, (0, 200, 255), -1)
        cv2.line(frame, (u_base, v_base - body_h + 30), (u_base, v_base - int(body_h * 0.4)), (200, 150, 0), 6)
        cv2.line(frame, (u_base, v_base - int(body_h * 0.4)), (u_base, v_base), (100, 60, 40), 5)

    def draw_industrial_obstacle(
        self,
        frame: np.ndarray,
        world_x_center: float,
        world_y_center: float,
        width_m: float = 1.0,
        depth_m: float = 0.6,
    ) -> None:
        """
        Draw an industrial pallet with shipping crates acting as a lower-limb physical occluder.
        """
        x1 = world_x_center - width_m / 2.0
        x2 = world_x_center + width_m / 2.0
        y1 = world_y_center - depth_m / 2.0
        y2 = world_y_center + depth_m / 2.0

        p1 = self.homography.project_to_image(x1, y1)
        p2 = self.homography.project_to_image(x2, y1)
        p3 = self.homography.project_to_image(x2, y2)
        p4 = self.homography.project_to_image(x1, y2)

        base_poly = np.array([p1, p2, p3, p4], dtype=np.int32)
        crate_h = int(self._get_pixel_scale(world_y_center) * 0.32)
        top_poly = np.array([(pt[0], pt[1] - crate_h) for pt in base_poly], dtype=np.int32)

        front_poly = np.array([p1, p2, (p2[0], p2[1] - crate_h), (p1[0], p1[1] - crate_h)], dtype=np.int32)
        side_poly = np.array([p2, p3, (p3[0], p3[1] - crate_h), (p2[0], p2[1] - crate_h)], dtype=np.int32)

        cv2.fillPoly(frame, [front_poly], (60, 90, 130))
        cv2.fillPoly(frame, [side_poly], (45, 70, 105))
        cv2.fillPoly(frame, [top_poly], (80, 110, 150))

        cv2.polylines(frame, [front_poly], True, (20, 35, 60), 2, cv2.LINE_AA)
        cv2.polylines(frame, [side_poly], True, (20, 35, 60), 2, cv2.LINE_AA)
        cv2.polylines(frame, [top_poly], True, (20, 35, 60), 2, cv2.LINE_AA)

        stripe_center_u = int((p1[0] + p2[0]) / 2)
        stripe_center_v = int((p1[1] + p2[1]) / 2) - int(crate_h * 0.2)
        cv2.putText(frame, "BARRIER / CRATE", (stripe_center_u - 60, stripe_center_v),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 230, 255), 1, cv2.LINE_AA)

    def _render_bottom_badge(self, frame: np.ndarray, text: str, bg_color: Tuple[int, int, int]) -> None:
        """Render discrete, high-contrast bottom telemetry pill badge (avoids top HUD collisions)."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.55
        thickness = 1
        (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)
        
        pad_x = 14
        pad_y = 8
        bx1 = 20
        by2 = self.height - 20
        by1 = by2 - th - pad_y * 2
        bx2 = bx1 + tw + pad_x * 2

        # Translucent dark rounded badge
        sub_img = frame[by1:by2, bx1:bx2]
        badge_bg = np.full_like(sub_img, bg_color)
        blended = cv2.addWeighted(badge_bg, 0.85, sub_img, 0.15, 0)
        frame[by1:by2, bx1:bx2] = blended
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), (255, 255, 255), 1, cv2.LINE_AA)

        # Text
        cv2.putText(frame, text, (bx1 + pad_x, by2 - pad_y - baseline // 2), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

    def generate_sequence_a(self, output_path: Union[str, Path], duration_s: float = 6.0) -> Path:
        """Sequence A: Clean incursion crossing."""
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        total_frames = int(duration_s * self.fps)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_file), fourcc, self.fps, (self.width, self.height))

        if not writer.isOpened():
            raise RuntimeError(f"Could not open VideoWriter for {out_file}")

        y_start, y_end = 0.5, 5.5
        x_pos = 2.0

        for frame_idx in range(total_frames):
            alpha = frame_idx / max(1, total_frames - 1)
            cur_y = y_start + alpha * (y_end - y_start)
            gait = frame_idx * 0.35

            frame = self.render_base_scene()
            self.render_worker_sprite(frame, x_pos, cur_y, gait_phase=gait, is_idle=False)

            # Bottom discrete badge (avoids top HUD collision)
            info_text = f"SIMULATION [SEQ-A: INCLINED CROSSING] | Frame {frame_idx + 1:03d}/{total_frames} | Ground Pos: ({x_pos:.2f}, {cur_y:.2f}m)"
            self._render_bottom_badge(frame, info_text, (40, 40, 40))

            writer.write(frame)

        writer.release()
        return out_file

    def generate_sequence_b(self, output_path: Union[str, Path], duration_s: float = 6.0) -> Path:
        """Sequence B: Partial lower-limb occlusion test."""
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        total_frames = int(duration_s * self.fps)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_file), fourcc, self.fps, (self.width, self.height))

        if not writer.isOpened():
            raise RuntimeError(f"Could not open VideoWriter for {out_file}")

        x_start, x_end = 0.5, 3.5
        y_pos = 2.8

        obstacle_x = 2.0
        obstacle_y = 2.4
        obstacle_w = 1.0

        for frame_idx in range(total_frames):
            alpha = frame_idx / max(1, total_frames - 1)
            cur_x = x_start + alpha * (x_end - x_start)
            gait = frame_idx * 0.35

            is_occluded = (obstacle_x - obstacle_w / 2.0 - 0.1) <= cur_x <= (obstacle_x + obstacle_w / 2.0 + 0.1)

            frame = self.render_base_scene()
            self.render_worker_sprite(frame, cur_x, y_pos, gait_phase=gait, is_idle=False)
            self.draw_industrial_obstacle(frame, obstacle_x, obstacle_y, width_m=obstacle_w, depth_m=0.5)

            # Bottom discrete badge
            status_text = "OCCLUDED (FEET HIDDEN - COASTING)" if is_occluded else "CLEAR VIEW (DIRECT TRACKING)"
            bg_color = (0, 90, 180) if is_occluded else (30, 90, 30)
            info_text = f"SIMULATION [SEQ-B: OCCLUSION TEST] | Frame {frame_idx + 1:03d}/{total_frames} | State: {status_text}"
            self._render_bottom_badge(frame, info_text, bg_color)

            writer.write(frame)

        writer.release()
        return out_file

    def generate_sequence_c(self, output_path: Union[str, Path], duration_s: float = 10.0) -> Path:
        """Sequence C: Dwell time and loitering test."""
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        total_frames = int(duration_s * self.fps)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_file), fourcc, self.fps, (self.width, self.height))

        if not writer.isOpened():
            raise RuntimeError(f"Could not open VideoWriter for {out_file}")

        f_enter = int(2.0 * self.fps)
        f_dwell_end = int(8.0 * self.fps)

        for frame_idx in range(total_frames):
            if frame_idx < f_enter:
                alpha = frame_idx / f_enter
                cur_y = 0.5 + alpha * 2.5
                gait = frame_idx * 0.35
                is_idle = False
                dwell_sec = 0.0
            elif frame_idx < f_dwell_end:
                cur_y = 3.0
                gait = 0.0
                is_idle = True
                dwell_sec = (frame_idx - f_enter) / self.fps
            else:
                alpha = (frame_idx - f_dwell_end) / (total_frames - f_dwell_end)
                cur_y = 3.0 + alpha * 2.5
                gait = frame_idx * 0.35
                is_idle = False
                dwell_sec = (f_dwell_end - f_enter) / self.fps

            cur_x = 2.0
            frame = self.render_base_scene()
            self.render_worker_sprite(frame, cur_x, cur_y, gait_phase=gait, is_idle=is_idle)

            # Bottom discrete badge
            if dwell_sec >= 5.0:
                dwell_bg = (0, 0, 180)
                dwell_msg = f"DWELL VIOLATION ({dwell_sec:.1f}s >= 5.0s TRIP)"
            elif dwell_sec > 0.0:
                dwell_bg = (0, 120, 200)
                dwell_msg = f"LOITERING / DWELLING ({dwell_sec:.1f}s)"
            else:
                dwell_bg = (30, 90, 30)
                dwell_msg = "APPROACHING CELL"

            info_text = f"SIMULATION [SEQ-C: DWELL TIME] | Frame {frame_idx + 1:03d}/{total_frames} | {dwell_msg}"
            self._render_bottom_badge(frame, info_text, dwell_bg)

            writer.write(frame)

        writer.release()
        return out_file

    def generate_all_sequences(self, output_dir: Union[str, Path]) -> List[Path]:
        """Generate all 3 benchmark sequences into the specified directory."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        seq_a = self.generate_sequence_a(out_dir / "sequence_a_clean_incursion.mp4", duration_s=6.0)
        seq_b = self.generate_sequence_b(out_dir / "sequence_b_occlusion_coasting.mp4", duration_s=6.0)
        seq_c = self.generate_sequence_c(out_dir / "sequence_c_dwell_loitering.mp4", duration_s=10.0)

        return [seq_a, seq_b, seq_c]
