"""
tests/test_demo_runner.py
Unit and integration tests for the DemoRunner CLI and orchestrator.
"""

import json
from pathlib import Path
import cv2
import numpy as np
import pytest

from scripts.run_demo import DemoRunner, DemoRunnerConfig, DemoSummary, parse_args
from src.pipeline.safety_pipeline import LayoutMode


def test_parse_args_defaults():
    """parse_args uses sensible defaults matching project specification."""
    cfg = parse_args([])
    assert cfg.source == "data/samples/sequence_a_clean_incursion.mp4"
    assert cfg.model_path == "models/yolo11n-pose.onnx"
    assert cfg.config_path == "configs/default_config.yaml"
    assert cfg.layout == LayoutMode.SIDE_BY_SIDE
    assert cfg.no_display is False
    assert cfg.realtime is False
    assert cfg.output_video is None
    assert cfg.output_events is None
    assert cfg.conf_threshold == 0.5
    assert cfg.max_frames is None


def test_parse_args_custom(tmp_path: Path):
    """parse_args correctly parses custom CLI flags and options."""
    out_vid = tmp_path / "out.mp4"
    out_evt = tmp_path / "events.jsonl"
    args = [
        "--source", "0",
        "--model", "custom_model.onnx",
        "--config", "custom_config.yaml",
        "--layout", "pip",
        "--no-display",
        "--realtime",
        "--output-video", str(out_vid),
        "--output-events", str(out_evt),
        "--conf-threshold", "0.7",
        "--max-frames", "50",
    ]
    cfg = parse_args(args)
    assert cfg.source == "0"
    assert cfg.model_path == "custom_model.onnx"
    assert cfg.config_path == "custom_config.yaml"
    assert cfg.layout == LayoutMode.PIP
    assert cfg.no_display is True
    assert cfg.realtime is True
    assert cfg.output_video == out_vid
    assert cfg.output_events == out_evt
    assert cfg.conf_threshold == 0.7
    assert cfg.max_frames == 50


def test_demo_runner_resolve_source():
    """_resolve_source converts integer strings to int camera index and keeps file paths."""
    assert DemoRunner._resolve_source("0") == 0
    assert DemoRunner._resolve_source("1") == 1
    assert DemoRunner._resolve_source("video.mp4") == "video.mp4"
    assert DemoRunner._resolve_source("rtsp://192.168.1.50/stream") == "rtsp://192.168.1.50/stream"


def test_demo_summary_percentiles():
    """DemoSummary compiles accurate latency percentiles and text formatting."""
    summary = DemoSummary(
        total_frames=100,
        elapsed_time_s=3.33,
        average_fps=30.0,
        latencies_mean_ms=15.0,
        latencies_p50_ms=14.5,
        latencies_p95_ms=22.0,
        latencies_p99_ms=28.5,
        state_counts={"SAFE": 80, "DANGER_INTRUSION": 20},
    )
    formatted = summary.format_text()
    assert "Total Processed Frames : 100" in formatted
    assert "Average Throughput     : 30.0 FPS" in formatted
    assert "Mean Latency       : 15.00 ms" in formatted
    assert "p95                : 22.00 ms" in formatted
    assert "SAFE                :    80 frames ( 80.0%)" in formatted
    assert "DANGER_INTRUSION    :    20 frames ( 20.0%)" in formatted


def test_demo_runner_headless_execution(synthetic_onnx_path: Path, tmp_path: Path):
    """DemoRunner runs headless on synthetic video sample without GUI errors."""
    sample_path = Path("data/samples/sequence_a_clean_incursion.mp4")
    if not sample_path.exists():
        pytest.skip("Sample video sequence_a_clean_incursion.mp4 not generated.")

    cfg = DemoRunnerConfig(
        source=str(sample_path),
        model_path=str(synthetic_onnx_path),
        config_path="configs/default_config.yaml",
        no_display=True,
        max_frames=10,
    )
    runner = DemoRunner(cfg)
    summary = runner.run()

    assert summary.total_frames == 10
    assert summary.average_fps > 0.0
    assert summary.latencies_mean_ms > 0.0
    assert "SAFE" in summary.state_counts or len(summary.state_counts) > 0


def test_demo_runner_video_and_events_output(synthetic_onnx_path: Path, tmp_path: Path):
    """DemoRunner writes valid MP4 video and structured JSONL telemetry."""
    sample_path = Path("data/samples/sequence_a_clean_incursion.mp4")
    if not sample_path.exists():
        pytest.skip("Sample video sequence_a_clean_incursion.mp4 not generated.")

    out_video = tmp_path / "demo_output.mp4"
    out_events = tmp_path / "demo_events.jsonl"

    cfg = DemoRunnerConfig(
        source=str(sample_path),
        model_path=str(synthetic_onnx_path),
        config_path="configs/default_config.yaml",
        no_display=True,
        output_video=out_video,
        output_events=out_events,
        max_frames=5,
    )
    runner = DemoRunner(cfg)
    summary = runner.run()

    assert summary.total_frames == 5

    # 1. Verify output video existence and properties
    assert out_video.exists()
    assert out_video.stat().st_size > 0
    cap = cv2.VideoCapture(str(out_video))
    assert cap.isOpened()
    assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) == 5
    cap.release()

    # 2. Verify JSONL telemetry schema
    assert out_events.exists()
    with open(out_events, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    assert len(lines) == 5
    for record in lines:
        assert "frame_id" in record
        assert "timestamp" in record
        assert "safety_state" in record
        assert "trip_active" in record
        assert "tracks" in record
        assert "latencies_ms" in record
        assert "total_t1" in record["latencies_ms"]
