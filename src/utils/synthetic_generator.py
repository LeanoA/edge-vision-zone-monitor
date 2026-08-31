"""
src/utils/synthetic_generator.py
Synthetic Video and Frame Generator for Vision-Based Industrial Safety Monitoring.
Generates deterministic ground-truth video sequences matching calibrated floor geometry.
"""

from dataclasses import dataclass
import math
from pathlib import Path
from typing import List, Optional, Tuple, Union
import cv2
import numpy as np

from src.core.homography import CalibrationConfig, HomographyManager


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
    safety zones, humanoid workers, and physical occlusion obstacles.
    """

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = "configs/default_config.yaml",
        homography_manager: Optional[HomographyManager] = None,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
    ) -> None:
        """
        Initialize synthetic video generator.

        Args:
            config_path: Optional path to calibration YAML.
            homography_manager: Optional pre-calibrated HomographyManager instance.
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

    def _get_pixel_scale(self, world_y: float) -> float:
        """
        Compute perspective height scale factor in pixels per meter of vertical height.
        Based on ground position distance.
        """
        # Calculate local pixel height by evaluating projection delta
        u1, v1 = self.homography.project_to_image(2.0, max(0.0, world_y))
        u2, v2 = self.homography.project_to_image(2.0, max(0.0, world_y + 0.5))
        # Distance on screen for 0.5m ground depth
        dy_screen = abs(v1 - v2)
        # Empirical scaling for 1.75m humanoid
        scale = max(70.0, dy_screen * 3.5)
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

        # Draw metric ground grid (lines every 1.0 meter)
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
            cv2.circle(frame, pt, 7, (0, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(frame, pt, 10, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, f"CAL-{idx+1} ({cx:.0f},{cy:.0f}m)", (pt[0] + 12, pt[1] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)

        # Draw Warning Zone Polygon (Amber overlay)
        if warning:
            warn_px = np.array([self.homography.project_to_image(px, py) for px, py in warning], dtype=np.int32)
            overlay = frame.copy()
            cv2.fillPoly(overlay, [warn_px], (20, 140, 220))  # Amber
            cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
            cv2.polylines(frame, [warn_px], True, (0, 180, 255), 2, cv2.LINE_AA)

        # Draw Danger Zone Polygon (Hazard striped / Red overlay)
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
                (int(d_center_u) - 150, int(d_center_v)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

        return frame

    def draw_humanoid(
        self,
        frame: np.ndarray,
        world_x: float,
        world_y: float,
        gait_phase: float = 0.0,
        occlude_feet: bool = False,
    ) -> None:
        """
        Draw an anatomically consistent perspective humanoid with high-contrast boots,
        safety trousers, high-visibility vest, and safety hardhat.
        """
        u_base, v_base = self.homography.project_to_image(world_x, world_y)
        u_base, v_base = int(u_base), int(v_base)

        height_scale = self._get_pixel_scale(world_y)
        body_h = int(height_scale)
        body_w = int(height_scale * 0.32)

        # Joint coordinates along vertical body axis
        head_y = v_base - body_h
        neck_y = v_base - int(body_h * 0.85)
        shoulder_y = v_base - int(body_h * 0.80)
        hip_y = v_base - int(body_h * 0.48)
        knee_y = v_base - int(body_h * 0.24)
        ankle_y = v_base - int(body_h * 0.06)
        foot_y = v_base

        # Gait stride offsets (pixels)
        stride = math.sin(gait_phase) * (body_w * 0.4)
        leg_l_x = u_base - int(body_w * 0.25) + int(stride)
        leg_r_x = u_base + int(body_w * 0.25) - int(stride)

        # 1. Shadow on ground
        cv2.ellipse(frame, (u_base, v_base), (int(body_w * 0.6), int(body_w * 0.25)), 0, 0, 360, (20, 20, 20), -1)

        # 2. Legs & Boots (Unless occluded)
        if not occlude_feet:
            # Trousers (Work blue/navy)
            cv2.line(frame, (u_base - int(body_w * 0.15), hip_y), (leg_l_x, knee_y), (100, 60, 40), int(body_w * 0.24), cv2.LINE_AA)
            cv2.line(frame, (leg_l_x, knee_y), (leg_l_x, ankle_y), (100, 60, 40), int(body_w * 0.20), cv2.LINE_AA)
            cv2.line(frame, (u_base + int(body_w * 0.15), hip_y), (leg_r_x, knee_y), (100, 60, 40), int(body_w * 0.24), cv2.LINE_AA)
            cv2.line(frame, (leg_r_x, knee_y), (leg_r_x, ankle_y), (100, 60, 40), int(body_w * 0.20), cv2.LINE_AA)

            # High-contrast work boots (Black leather with fluorescent yellow ankle trim)
            boot_radius = max(3, int(body_w * 0.14))
            cv2.circle(frame, (leg_l_x, ankle_y), boot_radius + 2, (0, 230, 255), -1, cv2.LINE_AA)  # Yellow ankle accent
            cv2.circle(frame, (leg_r_x, ankle_y), boot_radius + 2, (0, 230, 255), -1, cv2.LINE_AA)
            cv2.rectangle(frame, (leg_l_x - boot_radius, ankle_y), (leg_l_x + boot_radius + 3, foot_y), (25, 25, 25), -1)
            cv2.rectangle(frame, (leg_r_x - boot_radius, ankle_y), (leg_r_x + boot_radius + 3, foot_y), (25, 25, 25), -1)
        else:
            # Upper thighs only
            cv2.line(frame, (u_base - int(body_w * 0.15), hip_y), (leg_l_x, hip_y + int(body_h * 0.1)), (100, 60, 40), int(body_w * 0.22), cv2.LINE_AA)
            cv2.line(frame, (u_base + int(body_w * 0.15), hip_y), (leg_r_x, hip_y + int(body_h * 0.1)), (100, 60, 40), int(body_w * 0.22), cv2.LINE_AA)

        # 3. Torso with High-Visibility Safety Vest (Fluorescent Lime / Neon Orange)
        vest_color = (0, 215, 255)  # Hi-Vis safety orange/yellow in BGR
        cv2.rectangle(frame, (u_base - int(body_w * 0.45), shoulder_y), (u_base + int(body_w * 0.45), hip_y), vest_color, -1)
        
        # Reflective silver stripes on vest
        cv2.rectangle(frame, (u_base - int(body_w * 0.45), shoulder_y + int(body_h * 0.08)),
                      (u_base + int(body_w * 0.45), shoulder_y + int(body_h * 0.14)), (220, 220, 220), -1)
        cv2.rectangle(frame, (u_base - int(body_w * 0.45), shoulder_y + int(body_h * 0.20)),
                      (u_base + int(body_w * 0.45), shoulder_y + int(body_h * 0.26)), (220, 220, 220), -1)

        # 4. Arms
        arm_swing = math.sin(gait_phase + math.pi) * (body_w * 0.3)
        cv2.line(frame, (u_base - int(body_w * 0.45), shoulder_y), (u_base - int(body_w * 0.5) - int(arm_swing), hip_y), (80, 50, 30), max(2, int(body_w * 0.15)), cv2.LINE_AA)
        cv2.line(frame, (u_base + int(body_w * 0.45), shoulder_y), (u_base + int(body_w * 0.5) + int(arm_swing), hip_y), (80, 50, 30), max(2, int(body_w * 0.15)), cv2.LINE_AA)

        # 5. Head & Safety Hardhat
        head_radius = max(5, int(body_w * 0.25))
        # Face/Head
        cv2.circle(frame, (u_base, head_y + head_radius), head_radius, (160, 190, 220), -1, cv2.LINE_AA)
        # Yellow Safety Helmet
        cv2.ellipse(frame, (u_base, head_y + int(head_radius * 0.7)), (int(head_radius * 1.25), int(head_radius * 0.9)), 0, 180, 360, (0, 240, 255), -1, cv2.LINE_AA)
        cv2.line(frame, (u_base - int(head_radius * 1.3), head_y + int(head_radius * 0.7)), (u_base + int(head_radius * 1.3), head_y + int(head_radius * 0.7)), (0, 200, 220), 2, cv2.LINE_AA)

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
        
        # Height of crate in screen pixels
        crate_h = int(self._get_pixel_scale(world_y_center) * 0.55)
        top_poly = np.array([(pt[0], pt[1] - crate_h) for pt in base_poly], dtype=np.int32)

        # Front face
        front_poly = np.array([p1, p2, (p2[0], p2[1] - crate_h), (p1[0], p1[1] - crate_h)], dtype=np.int32)
        # Side face
        side_poly = np.array([p2, p3, (p3[0], p3[1] - crate_h), (p2[0], p2[1] - crate_h)], dtype=np.int32)

        # Draw wooden pallet / crate structure
        cv2.fillPoly(frame, [front_poly], (60, 90, 130))  # Cardboard / Wood brown
        cv2.fillPoly(frame, [side_poly], (45, 70, 105))   # Darker side face
        cv2.fillPoly(frame, [top_poly], (80, 110, 150))   # Lighter top face

        # Crate border outlines
        cv2.polylines(frame, [front_poly], True, (20, 35, 60), 2, cv2.LINE_AA)
        cv2.polylines(frame, [side_poly], True, (20, 35, 60), 2, cv2.LINE_AA)
        cv2.polylines(frame, [top_poly], True, (20, 35, 60), 2, cv2.LINE_AA)

        # Industrial Hazard Striping on obstacle base
        stripe_center_u = int((p1[0] + p2[0]) / 2)
        stripe_center_v = int((p1[1] + p2[1]) / 2) - int(crate_h * 0.2)
        cv2.putText(frame, "BARRIER / CRATE", (stripe_center_u - 60, stripe_center_v),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 230, 255), 1, cv2.LINE_AA)

    def generate_sequence_a(self, output_path: Union[str, Path], duration_s: float = 6.0) -> Path:
        """
        Generate Sequence A: Clean incursion and straight crossing over ground grid.
        Worker walks steadily from (2.0, 0.5) to (2.0, 5.5) across the danger zone.
        """
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
            gait = frame_idx * 0.45

            frame = self.render_base_scene()
            self.draw_humanoid(frame, x_pos, cur_y, gait_phase=gait, occlude_feet=False)

            # Metadata header overlay
            cv2.putText(frame, f"SEQ-A: CLEAN INCURSION | Frame: {frame_idx:03d}/{total_frames} | Pos: ({x_pos:.2f}, {cur_y:.2f}m)",
                        (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)

            writer.write(frame)

        writer.release()
        return out_file

    def generate_sequence_b(self, output_path: Union[str, Path], duration_s: float = 6.0) -> Path:
        """
        Generate Sequence B: Partial lower-limb occlusion test.
        Worker walks horizontally from (0.5, 2.8) to (3.5, 2.8) behind an obstacle at (2.0, 2.5).
        """
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        total_frames = int(duration_s * self.fps)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_file), fourcc, self.fps, (self.width, self.height))

        if not writer.isOpened():
            raise RuntimeError(f"Could not open VideoWriter for {out_file}")

        x_start, x_end = 0.5, 3.5
        y_pos = 2.8  # Worker walks behind obstacle at Y=2.5

        obstacle_x = 2.0
        obstacle_y = 2.4
        obstacle_w = 1.0

        for frame_idx in range(total_frames):
            alpha = frame_idx / max(1, total_frames - 1)
            cur_x = x_start + alpha * (x_end - x_start)
            gait = frame_idx * 0.45

            # Feet occluded when passing behind obstacle (1.5 <= cur_x <= 2.5)
            is_occluded = (obstacle_x - obstacle_w / 2.0 - 0.1) <= cur_x <= (obstacle_x + obstacle_w / 2.0 + 0.1)

            frame = self.render_base_scene()

            # Render worker first (behind obstacle)
            self.draw_humanoid(frame, cur_x, y_pos, gait_phase=gait, occlude_feet=is_occluded)

            # Render obstacle on top of worker's lower body
            self.draw_industrial_obstacle(frame, obstacle_x, obstacle_y, width_m=obstacle_w, depth_m=0.5)

            # Metadata header overlay
            status_text = "OCCLUDED (FEET HIDDEN - COASTING)" if is_occluded else "CLEAR VIEW (OBSERVED)"
            status_color = (0, 140, 255) if is_occluded else (0, 255, 0)
            cv2.putText(frame, f"SEQ-B: LOWER-LIMB OCCLUSION | Frame: {frame_idx:03d} | Status: {status_text}",
                        (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2, cv2.LINE_AA)

            writer.write(frame)

        writer.release()
        return out_file

    def generate_sequence_c(self, output_path: Union[str, Path], duration_s: float = 10.0) -> Path:
        """
        Generate Sequence C: Dwell time and loitering test.
        Worker walks into danger zone (2.0, 3.0), stops for 6 seconds (triggering dwell warning & violation),
        then exits.
        """
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        total_frames = int(duration_s * self.fps)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_file), fourcc, self.fps, (self.width, self.height))

        if not writer.isOpened():
            raise RuntimeError(f"Could not open VideoWriter for {out_file}")

        # Timeline:
        # 0.0s - 2.0s (0 to 60 frames): Walk from Y=0.5 to Y=3.0
        # 2.0s - 8.0s (60 to 240 frames): Stopped inside at (2.0, 3.0) -> Dwell time accumulates 6s
        # 8.0s - 10.0s (240 to 300 frames): Walk from Y=3.0 to Y=5.5 (Exit)
        f_enter = int(2.0 * self.fps)
        f_dwell_end = int(8.0 * self.fps)

        for frame_idx in range(total_frames):
            if frame_idx < f_enter:
                alpha = frame_idx / f_enter
                cur_y = 0.5 + alpha * 2.5
                gait = frame_idx * 0.45
                dwell_sec = 0.0
            elif frame_idx < f_dwell_end:
                cur_y = 3.0
                gait = 0.0  # Standing still
                dwell_sec = (frame_idx - f_enter) / self.fps
            else:
                alpha = (frame_idx - f_dwell_end) / (total_frames - f_dwell_end)
                cur_y = 3.0 + alpha * 2.5
                gait = frame_idx * 0.45
                dwell_sec = (f_dwell_end - f_enter) / self.fps

            cur_x = 2.0
            frame = self.render_base_scene()
            self.draw_humanoid(frame, cur_x, cur_y, gait_phase=gait, occlude_feet=False)

            # Metadata header overlay with dwell timer
            if dwell_sec >= 5.0:
                dwell_color = (0, 0, 255)
                dwell_status = "DWELL VIOLATION (>5.0s)"
            elif dwell_sec > 0.0:
                dwell_color = (0, 165, 255)
                dwell_status = f"DWELLING ({dwell_sec:.1f}s)"
            else:
                dwell_color = (0, 255, 0)
                dwell_status = "APPROACHING"

            cv2.putText(frame, f"SEQ-C: DWELL TIME & LOITERING | Frame: {frame_idx:03d} | State: {dwell_status}",
                        (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, dwell_color, 2, cv2.LINE_AA)

            writer.write(frame)

        writer.release()
        return out_file

    def generate_all_sequences(self, output_dir: Union[str, Path]) -> List[Path]:
        """
        Generate all 3 benchmark sequences into the specified directory.
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        seq_a = self.generate_sequence_a(out_dir / "sequence_a_clean_incursion.mp4", duration_s=6.0)
        seq_b = self.generate_sequence_b(out_dir / "sequence_b_occlusion_coasting.mp4", duration_s=6.0)
        seq_c = self.generate_sequence_c(out_dir / "sequence_c_dwell_loitering.mp4", duration_s=10.0)

        return [seq_a, seq_b, seq_c]
