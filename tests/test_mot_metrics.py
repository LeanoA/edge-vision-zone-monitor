"""
tests/test_mot_metrics.py
Unit tests for multi-object tracking and metric evaluation metrics.
"""

import pytest
from src.utils.mot_metrics import (
    GroundTruthObject,
    TrackObservation,
    MOTEvaluator,
)


def test_mot_evaluator_perfect_tracking():
    """Verify MOTA=1.0 and IDF1=1.0 under perfect ground truth tracking."""
    evaluator = MOTEvaluator(gate_distance_m=0.5)

    # Simulate 10 frames with 2 objects
    for f in range(10):
        gt1 = GroundTruthObject(obj_id=1, pos_world=(1.0, 2.0 + f * 0.1), anchor_image=(100.0, 200.0 + f * 10.0))
        gt2 = GroundTruthObject(obj_id=2, pos_world=(3.0, 1.0 + f * 0.1), anchor_image=(300.0, 100.0 + f * 10.0))

        tr1 = TrackObservation(track_id=101, pos_world=(1.0, 2.0 + f * 0.1), anchor_image=(100.0, 200.0 + f * 10.0))
        tr2 = TrackObservation(track_id=102, pos_world=(3.0, 1.0 + f * 0.1), anchor_image=(300.0, 100.0 + f * 10.0))

        evaluator.evaluate_frame(frame_id=f, gt_objects=[gt1, gt2], tracks=[tr1, tr2])

    summary = evaluator.compute_summary()
    assert summary.total_frames == 10
    assert summary.total_gt_objects == 20
    assert summary.total_tp == 20
    assert summary.total_fp == 0
    assert summary.total_fn == 0
    assert summary.total_id_switches == 0
    assert summary.mota == 1.0
    assert summary.idf1 == 1.0
    assert summary.precision == 1.0
    assert summary.recall == 1.0
    assert summary.mean_pixel_rmse_px == pytest.approx(0.0, abs=1e-3)
    assert summary.mean_metric_rmse_cm == pytest.approx(0.0, abs=1e-3)
    assert summary.ghost_tracks_count == 0


def test_mot_evaluator_with_id_switch_and_ghost():
    """Verify ID switch detection and ghost track accounting."""
    evaluator = MOTEvaluator(gate_distance_m=0.8)

    # Frame 0: GT 1 matched to Track 10
    gt = GroundTruthObject(obj_id=1, pos_world=(2.0, 3.0), anchor_image=(200.0, 300.0))
    tr1 = TrackObservation(track_id=10, pos_world=(2.0, 3.0), anchor_image=(200.0, 300.0))
    tr_ghost = TrackObservation(track_id=99, pos_world=(8.0, 8.0), anchor_image=(800.0, 800.0))
    evaluator.evaluate_frame(0, [gt], [tr1, tr_ghost])

    # Frame 1: GT 1 switches to Track 20
    tr2 = TrackObservation(track_id=20, pos_world=(2.1, 3.1), anchor_image=(205.0, 305.0))
    evaluator.evaluate_frame(1, [gt], [tr2])

    summary = evaluator.compute_summary()
    assert summary.total_id_switches == 1
    assert summary.total_fp == 1  # 1 ghost track in frame 0
    assert summary.total_fn == 0
    assert summary.ghost_tracks_count == 1
    assert summary.mota < 1.0
