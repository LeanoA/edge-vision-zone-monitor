#!/usr/bin/env python3
"""
scripts/run_demo.py
End-to-End Demo Orchestrator CLI for Vision-Based Industrial Safety Monitoring.
"""

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import cv2
import numpy as np
import yaml

# Ensure repository root is on PYTHONPATH
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.homography import HomographyManager
from src.core.kalman_filter import MultiTargetKalmanTracker
from src.core.spatial_fsm import SpatialFSM, ZoneConfig
from src.inference.onnx_engine import OnnxEngine
from src.pipeline.safety_pipeline import LayoutMode, PipelineResult, SafetyPipeline
from src.utils.visualizer import DualVisualizer


def load_zone_config_from_yaml(config_path: Union[str, Path]) -> ZoneConfig:
    """Extract ZoneConfig parameters from YAML configuration file, or fallback to defaults."""
    path = Path(config_path)
    if not path.is_file():
        return ZoneConfig(
            name="IndustrialHazardZone",
            danger_polygon=[(1.0, 2.0), (3.0, 2.0), (3.0, 4.0), (1.0, 4.0)],
            warning_polygon=[(0.8, 1.8), (3.2, 1.8), (3.2, 4.2), (0.8, 4.2)],
            hysteresis_buffer_m=0.20,
            n_confirm=3,
            n_release=5,
            dwell_warning_s=5.0,
            iso_k_speed=1.6,
        )

    with open(path, "r", encoding="utf-8") as f:
        raw_cfg = yaml.safe_load(f) or {}

    zone_data = raw_cfg.get("zones", {})
    danger_poly = [tuple(p) for p in zone_data.get("danger_polygon", [(1.0, 2.0), (3.0, 2.0), (3.0, 4.0), (1.0, 4.0)])]
    warning_poly = [tuple(p) for p in zone_data.get("warning_polygon", [])] if "warning_polygon" in zone_data else None

    return ZoneConfig(
        name=zone_data.get("name", "IndustrialHazardZone"),
        danger_polygon=danger_poly,
        warning_polygon=warning_poly,
        hysteresis_buffer_m=float(zone_data.get("hysteresis_buffer_m", 0.20)),
        n_confirm=int(zone_data.get("n_confirm", 3)),
        n_release=int(zone_data.get("n_release", 5)),
        dwell_warning_s=float(zone_data.get("dwell_warning_s", 5.0)),
        dwell_violation_s=float(zone_data.get("dwell_violation_s", 10.0)),
        iso_k_speed=float(zone_data.get("iso_k_speed", 1.6)),
    )


def compute_file_sha256(filepath: Union[str, Path]) -> str:
    """Compute SHA256 hexadecimal digest of a local file."""
    path = Path(filepath)
    if not path.is_file():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_git_traceability() -> Dict[str, Any]:
    """Retrieve current Git commit, branch, and working tree cleanliness."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), stderr=subprocess.DEVNULL
        ).decode().strip()
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(REPO_ROOT), stderr=subprocess.DEVNULL
        ).decode().strip()
        status = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=str(REPO_ROOT), stderr=subprocess.DEVNULL
        ).decode().strip()
        return {
            "commit": commit,
            "branch": branch,
            "dirty": len(status) > 0,
        }
    except Exception:
        return {
            "commit": "unknown",
            "branch": "unknown",
            "dirty": False,
        }



@dataclass(frozen=True)
class DemoRunnerConfig:
    """Configuration parameters for the DemoRunner execution."""
    source: str
    model_path: str = "models/yolo11n-pose.onnx"
    config_path: str = "configs/default_config.yaml"
    layout: LayoutMode = LayoutMode.SIDE_BY_SIDE
    no_display: bool = False
    realtime: bool = False
    output_video: Optional[Path] = None
    output_events: Optional[Path] = None
    output_summary: Optional[Path] = None
    conf_threshold: float = 0.5
    min_ankle_bbox_height: float = 0.0
    max_frames: Optional[int] = None


@dataclass
class DemoSummary:
    """Aggregate execution statistics compiled at the end of the stream."""
    total_frames: int
    elapsed_time_s: float
    average_fps: float
    latencies_mean_ms: float
    latencies_p50_ms: float
    latencies_p95_ms: float
    latencies_p99_ms: float
    system_latencies_mean_ms: float = 0.0
    system_latencies_p50_ms: float = 0.0
    system_latencies_p95_ms: float = 0.0
    system_latencies_p99_ms: float = 0.0
    event_latency_mean_ms: Optional[float] = None
    event_latency_p50_ms: Optional[float] = None
    event_latency_p95_ms: Optional[float] = None
    event_latency_p99_ms: Optional[float] = None
    state_counts: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def format_text(self) -> str:
        """Format summary into a structured terminal report."""
        lines = [
            "=" * 70,
            "📊 INDUSTRIAL SAFETY GUARD — DEMO RUNNER SUMMARY",
            "=" * 70,
            f"Total Processed Frames : {self.total_frames}",
            f"Total Elapsed Time     : {self.elapsed_time_s:.2f} s",
            f"Average Throughput     : {self.average_fps:.1f} FPS",
            "-" * 70,
            "Pipeline Latency Profile (T1 - Processing Stages):",
            f"  • Mean Latency       : {self.latencies_mean_ms:.2f} ms",
            f"  • p50 (Median)       : {self.latencies_p50_ms:.2f} ms",
            f"  • p95                : {self.latencies_p95_ms:.2f} ms",
            f"  • p99                : {self.latencies_p99_ms:.2f} ms",
        ]
        if self.system_latencies_mean_ms > 0.0:
            lines.extend([
                "-" * 70,
                "System Latency Profile (T_system - Capture + Processing):",
                f"  • Mean System Latency: {self.system_latencies_mean_ms:.2f} ms",
                f"  • p50 (Median)       : {self.system_latencies_p50_ms:.2f} ms",
                f"  • p95                : {self.system_latencies_p95_ms:.2f} ms",
                f"  • p99                : {self.system_latencies_p99_ms:.2f} ms",
            ])
        if self.event_latency_mean_ms is not None:
            lines.extend([
                "-" * 70,
                "Safety Event Reaction Latency Profile (T_event - Physical Incursion to Trip):",
                f"  • Mean Event Latency : {self.event_latency_mean_ms:.2f} ms",
                f"  • p50 (Median)       : {self.event_latency_p50_ms:.2f} ms",
                f"  • p95                : {self.event_latency_p95_ms:.2f} ms",
                f"  • p99                : {self.event_latency_p99_ms:.2f} ms",
            ])
        lines.extend([
            "-" * 70,
            "Safety States Occurrences:",
        ])
        for state, count in sorted(self.state_counts.items()):
            pct = (count / max(1, self.total_frames)) * 100.0
            lines.append(f"  • {state:<20}: {count:5d} frames ({pct:5.1f}%)")

        if self.metadata:
            git_info = self.metadata.get("git", {})
            model_info = self.metadata.get("model", {})
            config_info = self.metadata.get("config", {})
            lines.extend([
                "-" * 70,
                "Traceability & Provenance Metadata:",
                f"  • Generated At (UTC) : {self.metadata.get('generated_at_utc', 'N/A')}",
                f"  • Git Commit         : {git_info.get('commit', 'N/A')[:8]} (dirty: {git_info.get('dirty', False)})",
                f"  • Model SHA256       : {model_info.get('sha256', 'N/A')[:16]}...",
                f"  • Config Source      : {config_info.get('path', 'N/A')}",
            ])
        lines.append("=" * 70)
        return "\n".join(lines)


class DemoRunner:
    """
    Modular orchestrator managing input capture, safety pipeline inference,
    dual visualizer compositing, video recording, and telemetry streaming.
    """

    def __init__(self, config: DemoRunnerConfig) -> None:
        self.config = config
        self.cap: Optional[cv2.VideoCapture] = None
        self.writer: Optional[cv2.VideoWriter] = None
        self.events_file = None
        self.pipeline: Optional[SafetyPipeline] = None
        self.visualizer: Optional[DualVisualizer] = None

        self._frame_count = 0
        self._latencies_t1: List[float] = []
        self._latencies_system: List[float] = []
        self._event_latencies: List[float] = []
        self._state_counts: Dict[str, int] = {}
        self._start_time: float = 0.0
        self._end_time: float = 0.0

    @staticmethod
    def _resolve_source(source_str: str) -> Union[int, str]:
        """Convert integer strings into camera index, otherwise return path/URL string."""
        if source_str.isdigit():
            return int(source_str)
        return source_str

    def initialize(self) -> None:
        """Initialize video capture, safety pipeline, visualizer, and output writers."""
        # 1. Open Video Capture Source
        resolved_src = self._resolve_source(self.config.source)
        self.cap = cv2.VideoCapture(resolved_src)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open video source: '{self.config.source}'")

        # 2. Instantiate Analytical Pipeline
        engine = OnnxEngine(self.config.model_path)
        homography = HomographyManager(config_path=self.config.config_path)
        tracker = MultiTargetKalmanTracker()
        
        # Load industrial safeguarding zone from config (or default fallback)
        zone_cfg = load_zone_config_from_yaml(self.config.config_path)
        fsm = SpatialFSM(config=zone_cfg)

        self.pipeline = SafetyPipeline(
            engine=engine,
            homography=homography,
            tracker=tracker,
            fsm=fsm,
            conf_threshold=self.config.conf_threshold,
            min_ankle_bbox_height=self.config.min_ankle_bbox_height,
        )

        # 3. Instantiate Dual Visualizer
        # Only bypass rendering if both display and video recording are disabled
        is_headless = self.config.no_display and (self.config.output_video is None)
        self.visualizer = DualVisualizer(
            homography=homography,
            fsm=fsm,
            headless=is_headless,
        )

        # 4. Initialize Telemetry Event File
        if self.config.output_events is not None:
            self.config.output_events.parent.mkdir(parents=True, exist_ok=True)
            self.events_file = open(self.config.output_events, "w", encoding="utf-8")

    def process_frame(
        self,
        frame: np.ndarray,
        capture_timestamp: Optional[float] = None,
    ) -> Tuple[PipelineResult, np.ndarray]:
        """
        Execute single frame evaluation, dual compositing, and telemetry logging.
        """
        if self.pipeline is None or self.visualizer is None:
            raise RuntimeError("DemoRunner is not initialized. Call initialize() first.")

        # Run 6-stage Safety Pipeline with optional capture timestamp
        result = self.pipeline.process_frame(frame, capture_timestamp=capture_timestamp)

        # Composite Dual View (Perspective + BEV)
        composite = self.visualizer.render(frame, result, layout=self.config.layout)

        # Record latencies & state telemetry
        self._latencies_t1.append(result.latencies.total_t1_ms)
        self._latencies_system.append(result.latencies.total_system_ms)
        if result.safety_output.event_latency_ms is not None:
            self._event_latencies.append(result.safety_output.event_latency_ms)

        state_name = result.safety_output.state.value
        self._state_counts[state_name] = self._state_counts.get(state_name, 0) + 1

        # Stream Structured Telemetry JSONL
        if self.events_file is not None:
            record = {
                "frame_id": result.frame_id,
                "timestamp": result.timestamp,
                "safety_state": state_name,
                "occupancy_state": result.safety_output.occupancy_state.value,
                "dwell_state": result.safety_output.dwell_state.value,
                "dwell_time_s": round(result.safety_output.dwell_time_s, 2),
                "trip_active": bool(result.safety_output.trip),
                "event_latency_ms": round(result.safety_output.event_latency_ms, 2) if result.safety_output.event_latency_ms is not None else None,
                "tracks": [
                    {
                        "track_id": t.track_id,
                        "pos": [round(float(t.position[0]), 3), round(float(t.position[1]), 3)],
                        "vel": [round(float(t.velocity[0]), 3), round(float(t.velocity[1]), 3)],
                        "status": t.observation_status.value if hasattr(t, "observation_status") else "UNKNOWN",
                        "dwell_s": round(float(t.dwell_time_s), 2) if hasattr(t, "dwell_time_s") else 0.0,
                    }
                    for t in result.tracks
                ],
                "latencies_ms": {
                    "capture": round(result.latencies.capture_ms, 2),
                    "preprocess": round(result.latencies.preprocess_ms, 2),
                    "inference": round(result.latencies.inference_ms, 2),
                    "keypoint_extract": round(result.latencies.keypoint_extract_ms, 2),
                    "projection": round(result.latencies.projection_ms, 2),
                    "tracking": round(result.latencies.tracking_ms, 2),
                    "fsm": round(result.latencies.fsm_evaluation_ms, 2),
                    "total_t1": round(result.latencies.total_t1_ms, 2),
                    "total_system": round(result.latencies.total_system_ms, 2),
                },
            }
            self.events_file.write(json.dumps(record) + "\n")
            self.events_file.flush()

        # Write Video Frame
        if self.config.output_video is not None:
            if self.writer is None:
                self.config.output_video.parent.mkdir(parents=True, exist_ok=True)
                fps = self.cap.get(cv2.CAP_PROP_FPS) if self.cap else 30.0
                if fps <= 0.0 or np.isnan(fps):
                    fps = 30.0
                ch, cw = composite.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                self.writer = cv2.VideoWriter(str(self.config.output_video), fourcc, fps, (cw, ch))
            self.writer.write(composite)

        return result, composite

    def run(self) -> DemoSummary:
        """
        Execute full playback loop with interactive UI controls and headless support.
        """
        if self.cap is None:
            self.initialize()

        assert self.cap is not None
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        frame_interval_s = (1.0 / fps) if (fps and fps > 0) else (1.0 / 30.0)

        window_name = "Industrial Safety Guard — Live Monitor (ISO 13855)"
        if not self.config.no_display:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        self._start_time = time.perf_counter()
        paused = False

        try:
            while True:
                if self.config.max_frames and self._frame_count >= self.config.max_frames:
                    break

                if not paused:
                    t_frame_start = time.perf_counter()
                    ret, frame = self.cap.read()
                    if not ret or frame is None:
                        break

                    self._frame_count += 1
                    result, composite = self.process_frame(frame)

                    if not self.config.no_display:
                        cv2.imshow(window_name, composite)

                    # Frame rate pacing if --realtime is requested
                    if self.config.realtime:
                        elapsed = time.perf_counter() - t_frame_start
                        sleep_time = max(0.001, frame_interval_s - elapsed)
                        time.sleep(sleep_time)

                # Interactive Keyboard Controls
                if not self.config.no_display:
                    wait_ms = 30 if paused else 1
                    key = cv2.waitKey(wait_ms) & 0xFF
                    if key in (ord("q"), ord("Q"), 27):  # 'q' or ESC
                        break
                    elif key == ord(" "):  # Space to pause/resume
                        paused = not paused
                    elif key in (ord("s"), ord("S")):  # 's' to save snapshot
                        snap_name = f"snapshot_frame_{self._frame_count:04d}.png"
                        cv2.imwrite(snap_name, composite)
                        print(f"[*] Snapshot saved: {snap_name}")

        finally:
            self._end_time = time.perf_counter()
            self.close()

        summary = self.get_summary()
        if self.config.output_summary is not None:
            self.config.output_summary.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config.output_summary, "w", encoding="utf-8") as f:
                json.dump(asdict(summary), f, indent=2)

        return summary

    def close(self) -> None:
        """Release video captures, writers, telemetry files, and GUI windows."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.writer is not None:
            self.writer.release()
            self.writer = None
        if self.events_file is not None:
            self.events_file.close()
            self.events_file = None
        if not self.config.no_display:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass

    def _build_traceability_metadata(self) -> Dict[str, Any]:
        """Assemble cryptographic, git, and configuration provenance metadata."""
        return {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "git": get_git_traceability(),
            "command": " ".join(sys.argv),
            "model": {
                "path": str(self.config.model_path),
                "sha256": compute_file_sha256(self.config.model_path),
            },
            "config": {
                "path": str(self.config.config_path),
                "sha256": compute_file_sha256(self.config.config_path),
            },
            "source": {
                "path": str(self.config.source),
                "sha256": compute_file_sha256(self.config.source),
            },
            "parameters": {
                "conf_threshold": self.config.conf_threshold,
                "max_frames": self.config.max_frames,
            },
        }

    def get_summary(self) -> DemoSummary:
        """Compute and return aggregate latency and safety state statistics."""
        elapsed = max(1e-5, self._end_time - self._start_time)
        avg_fps = self._frame_count / elapsed

        if len(self._latencies_t1) > 0:
            arr_t1 = np.array(self._latencies_t1, dtype=np.float64)
            mean_lat = float(np.mean(arr_t1))
            p50 = float(np.percentile(arr_t1, 50))
            p95 = float(np.percentile(arr_t1, 95))
            p99 = float(np.percentile(arr_t1, 99))
        else:
            mean_lat = p50 = p95 = p99 = 0.0

        if len(self._latencies_system) > 0:
            arr_sys = np.array(self._latencies_system, dtype=np.float64)
            sys_mean = float(np.mean(arr_sys))
            sys_p50 = float(np.percentile(arr_sys, 50))
            sys_p95 = float(np.percentile(arr_sys, 95))
            sys_p99 = float(np.percentile(arr_sys, 99))
        else:
            sys_mean = sys_p50 = sys_p95 = sys_p99 = 0.0

        if len(self._event_latencies) > 0:
            arr_evt = np.array(self._event_latencies, dtype=np.float64)
            evt_mean = float(np.mean(arr_evt))
            evt_p50 = float(np.percentile(arr_evt, 50))
            evt_p95 = float(np.percentile(arr_evt, 95))
            evt_p99 = float(np.percentile(arr_evt, 99))
        else:
            evt_mean = evt_p50 = evt_p95 = evt_p99 = None

        metadata = self._build_traceability_metadata()

        return DemoSummary(
            total_frames=self._frame_count,
            elapsed_time_s=elapsed,
            average_fps=avg_fps,
            latencies_mean_ms=mean_lat,
            latencies_p50_ms=p50,
            latencies_p95_ms=p95,
            latencies_p99_ms=p99,
            system_latencies_mean_ms=sys_mean,
            system_latencies_p50_ms=sys_p50,
            system_latencies_p95_ms=sys_p95,
            system_latencies_p99_ms=sys_p99,
            event_latency_mean_ms=evt_mean,
            event_latency_p50_ms=evt_p50,
            event_latency_p95_ms=evt_p95,
            event_latency_p99_ms=evt_p99,
            state_counts=dict(self._state_counts),
            metadata=metadata,
        )


def parse_args(args: Optional[List[str]] = None) -> DemoRunnerConfig:
    """Parse command-line arguments into a DemoRunnerConfig instance."""
    parser = argparse.ArgumentParser(
        description="Industrial Edge AI Safety Guard — End-to-End Demo Runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--source",
        type=str,
        default="data/samples/sequence_a_clean_incursion.mp4",
        help="Input video source: video file path, webcam index ('0', '1'), or RTSP stream URL.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="models/yolo11n-pose.onnx",
        help="Path to YOLO Pose ONNX model file.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/default_config.yaml",
        help="Path to calibration YAML configuration file.",
    )
    parser.add_argument(
        "--layout",
        type=str,
        choices=["side_by_side", "pip"],
        default="side_by_side",
        help="Dual visualization layout mode: 'side_by_side' or 'pip'.",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Headless execution mode: disables all GUI windows for CI and servers.",
    )
    parser.add_argument(
        "--realtime",
        action="store_true",
        help="Pace playback rate to the source's native FPS instead of max throughput.",
    )
    parser.add_argument(
        "--output-video",
        type=Path,
        default=None,
        help="Path to save annotated MP4 video output.",
    )
    parser.add_argument(
        "--output-events",
        type=Path,
        default=None,
        help="Path to save structured safety event telemetry in JSONL format.",
    )
    parser.add_argument(
        "--output-summary",
        type=Path,
        default=None,
        help="Path to save aggregate execution summary in JSON format.",
    )
    parser.add_argument(
        "--conf-threshold",
        type=float,
        default=0.5,
        help="Confidence threshold for pose keypoints and bounding boxes.",
    )
    parser.add_argument(
        "--min-ankle-bbox-height",
        type=float,
        default=0.0,
        help="Minimum bounding box height required for ankle extraction before Tier 3 fallback.",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Maximum number of frames to process before terminating.",
    )

    parsed = parser.parse_args(args)

    layout_enum = (
        LayoutMode.PIP if parsed.layout.lower() == "pip" else LayoutMode.SIDE_BY_SIDE
    )

    return DemoRunnerConfig(
        source=parsed.source,
        model_path=parsed.model,
        config_path=parsed.config,
        layout=layout_enum,
        no_display=parsed.no_display,
        realtime=parsed.realtime,
        output_video=parsed.output_video,
        output_events=parsed.output_events,
        output_summary=parsed.output_summary,
        conf_threshold=parsed.conf_threshold,
        min_ankle_bbox_height=parsed.min_ankle_bbox_height,
        max_frames=parsed.max_frames,
    )


def main() -> None:
    """Main CLI entrypoint."""
    cfg = parse_args()
    print("=" * 70)
    print("🚀 INDUSTRIAL SAFETY GUARD — DEMO RUNNER (ISO 13855 / PL d/e)")
    print("=" * 70)
    print(f"Source         : {cfg.source}")
    print(f"Model          : {cfg.model_path}")
    print(f"Calibration    : {cfg.config_path}")
    print(f"Layout         : {cfg.layout.value}")
    print(f"Headless Mode  : {cfg.no_display}")
    print(f"Output Video   : {cfg.output_video}")
    print(f"Output Events  : {cfg.output_events}")
    print("-" * 70)

    runner = DemoRunner(cfg)
    try:
        runner.initialize()
        print("[*] Pipeline initialized successfully. Running stream loop...")
        summary = runner.run()
        print(summary.format_text())
    except KeyboardInterrupt:
        print("\n[!] Execution interrupted by user (Ctrl+C).")
        runner.close()
        summary = runner.get_summary()
        print(summary.format_text())
    except Exception as e:
        print(f"\n[❌] Fatal Error during demo run: {e}", file=sys.stderr)
        runner.close()
        sys.exit(1)


if __name__ == "__main__":
    main()
