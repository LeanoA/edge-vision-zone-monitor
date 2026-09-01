#!/usr/bin/env python3
"""
scripts/run_dataset_test.py
Modular, Decoupled Ingestion and Evaluation Test Runner for Empirical Surveillance Datasets.
"""

import argparse
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import cv2
import numpy as np
import yaml

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.download_datasets import DATASET_REGISTRY
from src.core.homography import HomographyManager
from src.core.kalman_filter import MultiTargetKalmanTracker
from src.core.spatial_fsm import SpatialFSM, ZoneConfig
from src.inference.onnx_engine import OnnxEngine
from src.pipeline.safety_pipeline import LayoutMode, PipelineResult, SafetyPipeline
from src.utils.visualizer import DualVisualizer


@dataclass(frozen=True)
class DatasetTestConfig:
    """Execution parameters for dataset evaluation."""
    source: str
    config_path: str
    dataset_name: str
    model_path: str = "models/yolo11n-pose.onnx"
    output_dir: Path = REPO_ROOT / "data" / "results"
    layout: LayoutMode = LayoutMode.SIDE_BY_SIDE
    no_display: bool = True
    realtime: bool = False
    conf_threshold: float = 0.4
    max_frames: Optional[int] = None


@dataclass
class DatasetTestSummary:
    """Aggregate statistics compiled across the dataset video evaluation."""
    dataset_name: str
    total_frames: int
    elapsed_time_s: float
    average_fps: float
    latencies_mean_ms: float
    latencies_p50_ms: float
    latencies_p95_ms: float
    latencies_p99_ms: float
    state_counts: Dict[str, int] = field(default_factory=dict)
    total_tracks: int = 0
    danger_events_count: int = 0
    dwell_violations_count: int = 0

    def format_text(self) -> str:
        """Format summary into a structured terminal report."""
        lines = [
            "=" * 76,
            f"📊 DATASET EVALUATION REPORT: {self.dataset_name.upper()}",
            "=" * 76,
            f"Processed Frames       : {self.total_frames}",
            f"Elapsed Time           : {self.elapsed_time_s:.2f} s",
            f"Throughput             : {self.average_fps:.1f} FPS",
            f"Unique Tracks Observed : {self.total_tracks}",
            f"Danger Intrusions      : {self.danger_events_count}",
            f"Dwell Violations       : {self.dwell_violations_count}",
            "-" * 76,
            "Latency Profile (T1 - Processing Stages):",
            f"  • Mean Latency       : {self.latencies_mean_ms:.2f} ms",
            f"  • p50 (Median)       : {self.latencies_p50_ms:.2f} ms",
            f"  • p95                : {self.latencies_p95_ms:.2f} ms",
            f"  • p99                : {self.latencies_p99_ms:.2f} ms",
            "-" * 76,
            "Safety State Distribution:",
        ]
        for state, count in sorted(self.state_counts.items()):
            pct = (count / max(1, self.total_frames)) * 100.0
            lines.append(f"  • {state:<22}: {count:5d} frames ({pct:5.1f}%)")
        lines.append("=" * 76)
        return "\n".join(lines)


def load_zone_config_from_yaml(config_path: Union[str, Path]) -> ZoneConfig:
    """Extract ZoneConfig parameters from YAML configuration file."""
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Dataset config file not found: {path.resolve()}")

    with open(path, "r", encoding="utf-8") as f:
        raw_cfg = yaml.safe_load(f)

    zone_data = raw_cfg.get("zones", {})
    danger_poly = [tuple(p) for p in zone_data.get("danger_polygon", [(1.0, 2.0), (3.0, 2.0), (3.0, 4.0), (1.0, 4.0)])]
    warning_poly = [tuple(p) for p in zone_data.get("warning_polygon", [])] if "warning_polygon" in zone_data else None

    return ZoneConfig(
        name=zone_data.get("name", "DatasetSafetyZone"),
        danger_polygon=danger_poly,
        warning_polygon=warning_poly,
        hysteresis_buffer_m=float(zone_data.get("hysteresis_buffer_m", 0.20)),
        n_confirm=int(zone_data.get("n_confirm", 3)),
        n_release=int(zone_data.get("n_release", 5)),
        dwell_warning_s=float(zone_data.get("dwell_warning_s", 5.0)),
        dwell_violation_s=float(zone_data.get("dwell_violation_s", 10.0)),
        iso_k_speed=float(zone_data.get("iso_k_speed", 1.6)),
    )


class DatasetTestRunner:
    """
    Decoupled orchestrator executing the SafetyPipeline over empirical datasets,
    generating structured telemetry JSONL, aggregate summary JSON, and annotated composite videos.
    """

    def __init__(self, config: DatasetTestConfig) -> None:
        self.config = config
        self.cap: Optional[cv2.VideoCapture] = None
        self.writer: Optional[cv2.VideoWriter] = None
        self.events_file = None
        self.pipeline: Optional[SafetyPipeline] = None
        self.visualizer: Optional[DualVisualizer] = None

        self.dataset_results_dir = self.config.output_dir / self.config.dataset_name
        self.video_output_path = self.dataset_results_dir / f"annotated_{self.config.dataset_name}.mp4"
        self.events_output_path = self.dataset_results_dir / "events.jsonl"
        self.summary_output_path = self.dataset_results_dir / "summary.json"

        self._frame_count = 0
        self._latencies_t1: List[float] = []
        self._state_counts: Dict[str, int] = {}
        self._observed_track_ids = set()
        self._danger_events = 0
        self._dwell_violations = 0
        self._start_time: float = 0.0
        self._end_time: float = 0.0

    def initialize(self) -> None:
        """Initialize input capture, SafetyPipeline, visualizer, and telemetry loggers."""
        self.dataset_results_dir.mkdir(parents=True, exist_ok=True)

        self.cap = cv2.VideoCapture(self.config.source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open dataset video source: '{self.config.source}'")

        engine = OnnxEngine(self.config.model_path)
        homography = HomographyManager(config_path=self.config.config_path)
        tracker = MultiTargetKalmanTracker()
        zone_cfg = load_zone_config_from_yaml(self.config.config_path)
        fsm = SpatialFSM(config=zone_cfg)

        self.pipeline = SafetyPipeline(
            engine=engine,
            homography=homography,
            tracker=tracker,
            fsm=fsm,
            conf_threshold=self.config.conf_threshold,
        )

        self.visualizer = DualVisualizer(
            homography=homography,
            fsm=fsm,
            headless=self.config.no_display,
        )

        self.events_file = open(self.events_output_path, "w", encoding="utf-8")

    def process_frame(self, frame: np.ndarray) -> Tuple[PipelineResult, np.ndarray]:
        """Process frame through pipeline and render composite overlay."""
        if self.pipeline is None or self.visualizer is None:
            raise RuntimeError("DatasetTestRunner is not initialized.")

        result = self.pipeline.process_frame(frame)
        composite = self.visualizer.render(frame, result, layout=self.config.layout)

        self._latencies_t1.append(result.latencies.total_t1_ms)
        state_name = result.safety_output.state.value
        self._state_counts[state_name] = self._state_counts.get(state_name, 0) + 1

        if result.safety_output.state.value == "DANGER_INTRUSION":
            self._danger_events += 1
        if result.safety_output.dwell_state.value == "VIOLATION":
            self._dwell_violations += 1

        for t in result.tracks:
            self._observed_track_ids.add(t.track_id)

        # Write telemetry record
        if self.events_file is not None:
            record = {
                "frame_id": result.frame_id,
                "timestamp": result.timestamp,
                "safety_state": state_name,
                "occupancy_state": result.safety_output.occupancy_state.value,
                "dwell_state": result.safety_output.dwell_state.value,
                "dwell_time_s": round(result.safety_output.dwell_time_s, 2),
                "trip": bool(result.safety_output.trip),
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
                    "inference": round(result.latencies.inference_ms, 2),
                    "tracking": round(result.latencies.tracking_ms, 2),
                    "fsm": round(result.latencies.fsm_evaluation_ms, 2),
                    "total_t1": round(result.latencies.total_t1_ms, 2),
                },
            }
            self.events_file.write(json.dumps(record) + "\n")

        # Write video frame
        if self.writer is None:
            fps = self.cap.get(cv2.CAP_PROP_FPS) if self.cap else 25.0
            if fps <= 0.0 or np.isnan(fps):
                fps = 25.0
            ch, cw = composite.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.writer = cv2.VideoWriter(str(self.video_output_path), fourcc, fps, (cw, ch))

        self.writer.write(composite)
        return result, composite

    def run(self) -> DatasetTestSummary:
        """Run full evaluation loop."""
        if self.cap is None:
            self.initialize()

        assert self.cap is not None
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        frame_interval_s = (1.0 / fps) if (fps and fps > 0) else (1.0 / 25.0)

        window_name = f"Dataset Test: {self.config.dataset_name}"
        if not self.config.no_display:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        self._start_time = time.perf_counter()
        paused = False

        try:
            while True:
                if self.config.max_frames and self._frame_count >= self.config.max_frames:
                    break

                if not paused:
                    t_start = time.perf_counter()
                    ret, frame = self.cap.read()
                    if not ret or frame is None:
                        break

                    self._frame_count += 1
                    result, composite = self.process_frame(frame)

                    if not self.config.no_display:
                        cv2.imshow(window_name, composite)

                    if self.config.realtime:
                        elapsed = time.perf_counter() - t_start
                        sleep_time = max(0.001, frame_interval_s - elapsed)
                        time.sleep(sleep_time)

                if not self.config.no_display:
                    wait_ms = 30 if paused else (1 if not self.config.realtime else max(1, int(frame_interval_s * 1000)))
                    key = cv2.waitKey(wait_ms) & 0xFF
                    if key in (ord("q"), ord("Q"), 27):  # 'q' or ESC
                        break
                    elif key == ord(" "):  # Space to pause/resume
                        paused = not paused
                    elif key in (ord("s"), ord("S")):  # 's' to save snapshot
                        snap_name = self.dataset_results_dir / f"snapshot_frame_{self._frame_count:04d}.png"
                        cv2.imwrite(str(snap_name), composite)
                        print(f"[*] Snapshot saved: {snap_name}")

        finally:
            self._end_time = time.perf_counter()
            self.close()

        summary = self.get_summary()

        # Save summary JSON
        with open(self.summary_output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(summary), f, indent=2)

        return summary

    def close(self) -> None:
        """Release resources."""
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

    def get_summary(self) -> DatasetTestSummary:
        """Compile execution statistics."""
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

        return DatasetTestSummary(
            dataset_name=self.config.dataset_name,
            total_frames=self._frame_count,
            elapsed_time_s=round(elapsed, 2),
            average_fps=round(avg_fps, 1),
            latencies_mean_ms=round(mean_lat, 2),
            latencies_p50_ms=round(p50, 2),
            latencies_p95_ms=round(p95, 2),
            latencies_p99_ms=round(p99, 2),
            state_counts=dict(self._state_counts),
            total_tracks=len(self._observed_track_ids),
            danger_events_count=self._danger_events,
            dwell_violations_count=self._dwell_violations,
        )


def parse_args() -> DatasetTestConfig:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Dataset Test Ingestion Runner for Industrial Edge Safety Guard",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="opencv_vtest",
        help="Dataset name in registry or configs/datasets/ (e.g. 'opencv_vtest', 'openvino_people', 'pets2009_s2_l1').",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Optional explicit path to video file (overrides dataset registry path).",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Optional explicit path to YAML configuration file.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="models/yolo11n-pose.onnx",
        help="Path to YOLO Pose ONNX model file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data" / "results",
        help="Directory to save evaluation artifacts.",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        default=True,
        help="Run headlessly without GUI windows.",
    )
    parser.add_argument(
        "--display",
        action="store_false",
        dest="no_display",
        help="Enable interactive visual window during execution.",
    )
    parser.add_argument(
        "--realtime",
        action="store_true",
        help="Pace playback to native video frame rate.",
    )
    parser.add_argument(
        "--conf-threshold",
        type=float,
        default=0.4,
        help="Keypoint/box confidence threshold.",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Maximum frames to evaluate.",
    )

    parsed = parser.parse_args()

    # Resolve paths
    dataset_name = parsed.dataset
    if parsed.source is not None:
        source_path = parsed.source
    else:
        if dataset_name in DATASET_REGISTRY:
            meta = DATASET_REGISTRY[dataset_name]
            source_path = str(REPO_ROOT / "data" / "raw" / meta.name / meta.filename)
        else:
            source_path = str(REPO_ROOT / "data" / "raw" / dataset_name / f"{dataset_name}.mp4")

    if parsed.config is not None:
        config_path = parsed.config
    else:
        if dataset_name in DATASET_REGISTRY and DATASET_REGISTRY[dataset_name].default_config:
            config_path = DATASET_REGISTRY[dataset_name].default_config
        else:
            config_path = f"configs/datasets/{dataset_name}.yaml"

    return DatasetTestConfig(
        source=source_path,
        config_path=config_path,
        dataset_name=dataset_name,
        model_path=parsed.model,
        output_dir=parsed.output_dir,
        layout=LayoutMode.SIDE_BY_SIDE,
        no_display=parsed.no_display,
        realtime=parsed.realtime,
        conf_threshold=parsed.conf_threshold,
        max_frames=parsed.max_frames,
    )


def main() -> None:
    """CLI Main Entrypoint."""
    cfg = parse_args()
    print("=" * 76)
    print("🚀 INDUSTRIAL SAFETY GUARD — DATASET TEST INGESTION HARNESS")
    print("=" * 76)
    print(f"Dataset Name   : {cfg.dataset_name}")
    print(f"Video Source   : {cfg.source}")
    print(f"Config Profile : {cfg.config_path}")
    print(f"Model Path     : {cfg.model_path}")
    print(f"Output Dir     : {cfg.output_dir / cfg.dataset_name}")
    print(f"Headless Mode  : {cfg.no_display}")
    print(f"Max Frames     : {cfg.max_frames if cfg.max_frames else 'Full Stream'}")
    print("-" * 76)

    # Check if source exists before running
    if not Path(cfg.source).is_file():
        print(f"[❌] Error: Video file not found: {cfg.source}")
        print(f"[ℹ️] Please download it first using: python scripts/download_datasets.py --dataset {cfg.dataset_name}")
        sys.exit(1)

    runner = DatasetTestRunner(cfg)
    try:
        runner.initialize()
        print("[*] Processing dataset video frames through SafetyPipeline...")
        summary = runner.run()
        print(summary.format_text())
        print(f"[✅] Evaluation complete. Results saved to: {runner.dataset_results_dir.resolve()}/")
    except KeyboardInterrupt:
        print("\n[!] Execution interrupted by user.")
        runner.close()
    except Exception as err:
        print(f"\n[❌] Fatal Error during dataset test: {err}", file=sys.stderr)
        runner.close()
        sys.exit(1)


if __name__ == "__main__":
    main()
