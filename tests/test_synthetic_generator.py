"""
tests/test_synthetic_generator.py
Comprehensive unit and integration tests for the SyntheticVideoGenerator utility.
Verifies sprite loading, perspective scaling, alpha blending, occlusion, and YOLO detection compatibility.
"""

from pathlib import Path
import cv2
import numpy as np
import pytest

from src.utils.synthetic_generator import SyntheticVideoGenerator


def test_generator_initialization(tmp_path: Path):
    """SyntheticVideoGenerator initializes properly with default or fallback homography and loads sprites."""
    gen = SyntheticVideoGenerator(config_path=None, width=1280, height=720, fps=25)
    assert gen.width == 1280
    assert gen.height == 720
    assert gen.fps == 25
    assert gen.homography.is_calibrated
    assert len(gen.walk_sprites) > 0 or gen.idle_sprite is not None


def test_render_base_scene():
    """render_base_scene creates a valid 3-channel image with floor markings."""
    gen = SyntheticVideoGenerator(config_path=None, width=640, height=480, fps=30)
    frame = gen.render_base_scene()
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (480, 640, 3)
    assert frame.dtype == np.uint8


def test_render_worker_sprite():
    """render_worker_sprite composites sprite onto frame without clipping errors."""
    gen = SyntheticVideoGenerator(config_path=None, width=1920, height=1080, fps=30)
    frame = gen.render_base_scene()
    orig_sum = np.sum(frame)

    # Render worker at (2.0m, 3.0m)
    gen.render_worker_sprite(frame, world_x=2.0, world_y=3.0, gait_phase=1.0, is_idle=False)
    new_sum = np.sum(frame)

    assert new_sum != orig_sum
    assert frame.shape == (1080, 1920, 3)


def test_pinhole_pixel_scale():
    """Pixel height scaling decreases monotonically with ground distance Y."""
    gen = SyntheticVideoGenerator(config_path=None, width=1920, height=1080, fps=30)
    h_near = gen._get_pixel_scale(0.5)
    h_mid = gen._get_pixel_scale(3.0)
    h_far = gen._get_pixel_scale(5.5)

    assert h_near > h_mid > h_far
    assert h_near >= 400
    assert h_far >= 200


def test_generate_sequence_a(tmp_path: Path):
    """Sequence A produces a readable MP4 video with expected frame count and dimensions."""
    gen = SyntheticVideoGenerator(config_path=None, width=640, height=360, fps=30)
    out_path = tmp_path / "test_seq_a.mp4"
    result_path = gen.generate_sequence_a(out_path, duration_s=1.0)

    assert result_path.exists()
    assert result_path.stat().st_size > 0

    cap = cv2.VideoCapture(str(result_path))
    assert cap.isOpened()
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    assert frame_count == 30  # 1.0s * 30 FPS
    assert width == 640
    assert height == 360


def test_generate_sequence_b_and_c(tmp_path: Path):
    """Sequence B (occlusion) and C (dwell) produce valid video outputs."""
    gen = SyntheticVideoGenerator(config_path=None, width=640, height=360, fps=20)
    out_b = tmp_path / "test_seq_b.mp4"
    out_c = tmp_path / "test_seq_c.mp4"

    res_b = gen.generate_sequence_b(out_b, duration_s=0.5)
    res_c = gen.generate_sequence_c(out_c, duration_s=0.5)

    assert res_b.exists() and res_b.stat().st_size > 0
    assert res_c.exists() and res_c.stat().st_size > 0


def test_generate_all_sequences(tmp_path: Path):
    """generate_all_sequences creates 3 distinct videos in target directory."""
    gen = SyntheticVideoGenerator(config_path=None, width=480, height=270, fps=15)
    generated = gen.generate_all_sequences(tmp_path)
    assert len(generated) == 3
    for p in generated:
        assert p.exists()


def test_yolo_detection_on_synthetic_frame():
    """Verify that YOLO11 pose / detection recognizes synthetic composite worker with confidence >= 0.50."""
    model_path = Path("yolo11n-pose.pt")
    if not model_path.is_file():
        pytest.skip("yolo11n-pose.pt weights not found locally")

    from ultralytics import YOLO

    model = YOLO(str(model_path))
    gen = SyntheticVideoGenerator(config_path="configs/default_config.yaml", width=1920, height=1080)
    frame = gen.render_base_scene()
    gen.render_worker_sprite(frame, world_x=2.0, world_y=2.5, gait_phase=0.0, is_idle=False)

    results = model(frame, verbose=False)[0]
    assert len(results.boxes) >= 1
    top_conf = float(results.boxes.conf[0])
    assert top_conf >= 0.50
