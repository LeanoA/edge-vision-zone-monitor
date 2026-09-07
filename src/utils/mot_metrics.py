"""
src/utils/mot_metrics.py
Multi-Object Tracking (MOT) and Keypoint Geometric Evaluation Suite.
Implements CLEAR MOT metrics (MOTA, ID switches, FP, FN), IDF1,
and localized ground-plane metric / pixel error analysis.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple
import numpy as np
from scipy.optimize import linear_sum_assignment


@dataclass
class GroundTruthObject:
    """Ground truth state for an object in a frame."""
    obj_id: int
    pos_world: Tuple[float, float]                      # (X, Y) in meters
    anchor_image: Optional[Tuple[float, float]] = None  # (u, v) in pixels
    bbox: Optional[Tuple[float, float, float, float]] = None


@dataclass
class TrackObservation:
    """Hypothesized track state in a frame."""
    track_id: int
    pos_world: Tuple[float, float]                      # (X, Y) in meters
    anchor_image: Optional[Tuple[float, float]] = None  # (u, v) in pixels
    bbox: Optional[Tuple[float, float, float, float]] = None
    status: str = "ACTIVE"


@dataclass
class FrameEvaluationResult:
    """Evaluation result for a single frame."""
    frame_id: int
    num_gt: int
    num_tracks: int
    true_positives: int
    false_positives: int
    false_negatives: int
    id_switches: int
    matches: List[Tuple[int, int]]                      # List of (gt_id, track_id)
    pixel_errors: List[float]                           # Error in pixels for matches
    metric_errors_cm: List[float]                       # Error in cm for matches
    metric_errors_near_cm: List[float]                  # Y < 2.5m
    metric_errors_mid_cm: List[float]                   # 2.5 <= Y <= 4.0m
    metric_errors_far_cm: List[float]                   # Y > 4.0m


@dataclass
class MOTSummary:
    """Aggregate multi-object tracking and metric precision summary."""
    total_frames: int
    total_gt_objects: int
    total_detections: int
    total_tp: int
    total_fp: int
    total_fn: int
    total_id_switches: int
    mota: float
    idf1: float
    precision: float
    recall: float
    mean_pixel_rmse_px: float
    mean_metric_rmse_cm: float
    max_metric_drift_cm: float
    near_field_rmse_cm: float
    mid_field_rmse_cm: float
    far_field_rmse_cm: float
    ghost_tracks_count: int


class MOTEvaluator:
    """
    Evaluates tracking performance and geometric precision against ground truth annotations.
    """

    def __init__(self, gate_distance_m: float = 1.0) -> None:
        self.gate_distance_m = float(gate_distance_m)
        self.reset()

    def reset(self) -> None:
        """Reset internal accumulator state."""
        self.frame_results: List[FrameEvaluationResult] = []
        self._last_gt_to_track_map: Dict[int, int] = {}
        # For IDF1 trajectory-level assignment
        self._gt_frame_counts: Dict[int, int] = {}
        self._track_frame_counts: Dict[int, int] = {}
        self._overlap_matrix: Dict[Tuple[int, int], int] = {}
        self._all_observed_track_ids = set()
        self._matched_track_ids = set()

    def evaluate_frame(
        self,
        frame_id: int,
        gt_objects: Sequence[GroundTruthObject],
        tracks: Sequence[TrackObservation],
    ) -> FrameEvaluationResult:
        """
        Evaluate tracking and precision for a single frame.
        """
        num_gt = len(gt_objects)
        num_tr = len(tracks)

        for gt in gt_objects:
            self._gt_frame_counts[gt.obj_id] = self._gt_frame_counts.get(gt.obj_id, 0) + 1

        for tr in tracks:
            self._track_frame_counts[tr.track_id] = self._track_frame_counts.get(tr.track_id, 0) + 1
            self._all_observed_track_ids.add(tr.track_id)

        if num_gt == 0 and num_tr == 0:
            res = FrameEvaluationResult(
                frame_id=frame_id,
                num_gt=0,
                num_tracks=0,
                true_positives=0,
                false_positives=0,
                false_negatives=0,
                id_switches=0,
                matches=[],
                pixel_errors=[],
                metric_errors_cm=[],
                metric_errors_near_cm=[],
                metric_errors_mid_cm=[],
                metric_errors_far_cm=[],
            )
            self.frame_results.append(res)
            return res

        if num_gt == 0:
            res = FrameEvaluationResult(
                frame_id=frame_id,
                num_gt=0,
                num_tracks=num_tr,
                true_positives=0,
                false_positives=num_tr,
                false_negatives=0,
                id_switches=0,
                matches=[],
                pixel_errors=[],
                metric_errors_cm=[],
                metric_errors_near_cm=[],
                metric_errors_mid_cm=[],
                metric_errors_far_cm=[],
            )
            self.frame_results.append(res)
            return res

        if num_tr == 0:
            res = FrameEvaluationResult(
                frame_id=frame_id,
                num_gt=num_gt,
                num_tracks=0,
                true_positives=0,
                false_positives=0,
                false_negatives=num_gt,
                id_switches=0,
                matches=[],
                pixel_errors=[],
                metric_errors_cm=[],
                metric_errors_near_cm=[],
                metric_errors_mid_cm=[],
                metric_errors_far_cm=[],
            )
            self.frame_results.append(res)
            return res

        # Build distance matrix (in meters)
        cost_matrix = np.zeros((num_gt, num_tr), dtype=np.float64)
        for i, gt in enumerate(gt_objects):
            for j, tr in enumerate(tracks):
                dx = gt.pos_world[0] - tr.pos_world[0]
                dy = gt.pos_world[1] - tr.pos_world[1]
                cost_matrix[i, j] = np.sqrt(dx * dx + dy * dy)

        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        matched_pairs: List[Tuple[int, int]] = []
        matched_gt_indices = set()
        matched_tr_indices = set()
        pixel_errors: List[float] = []
        metric_errors_cm: List[float] = []
        metric_near: List[float] = []
        metric_mid: List[float] = []
        metric_far: List[float] = []
        id_switches = 0

        for r, c in zip(row_ind, col_ind):
            dist = cost_matrix[r, c]
            if dist <= self.gate_distance_m:
                gt_obj = gt_objects[r]
                tr_obj = tracks[c]
                matched_pairs.append((gt_obj.obj_id, tr_obj.track_id))
                matched_gt_indices.add(r)
                matched_tr_indices.add(c)
                self._matched_track_ids.add(tr_obj.track_id)

                # Overlap for IDF1
                key = (gt_obj.obj_id, tr_obj.track_id)
                self._overlap_matrix[key] = self._overlap_matrix.get(key, 0) + 1

                # Check ID Switch
                prev_tr_id = self._last_gt_to_track_map.get(gt_obj.obj_id)
                if prev_tr_id is not None and prev_tr_id != tr_obj.track_id:
                    id_switches += 1
                self._last_gt_to_track_map[gt_obj.obj_id] = tr_obj.track_id

                # Metric error
                err_cm = dist * 100.0
                metric_errors_cm.append(err_cm)
                w_y = gt_obj.pos_world[1]
                if w_y < 2.5:
                    metric_near.append(err_cm)
                elif w_y <= 4.0:
                    metric_mid.append(err_cm)
                else:
                    metric_far.append(err_cm)

                # Pixel error if anchors are available
                if gt_obj.anchor_image is not None and tr_obj.anchor_image is not None:
                    pdx = gt_obj.anchor_image[0] - tr_obj.anchor_image[0]
                    pdy = gt_obj.anchor_image[1] - tr_obj.anchor_image[1]
                    pixel_errors.append(float(np.sqrt(pdx * pdx + pdy * pdy)))

        tp = len(matched_pairs)
        fp = num_tr - tp
        fn = num_gt - tp

        frame_eval = FrameEvaluationResult(
            frame_id=frame_id,
            num_gt=num_gt,
            num_tracks=num_tr,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            id_switches=id_switches,
            matches=matched_pairs,
            pixel_errors=pixel_errors,
            metric_errors_cm=metric_errors_cm,
            metric_errors_near_cm=metric_near,
            metric_errors_mid_cm=metric_mid,
            metric_errors_far_cm=metric_far,
        )
        self.frame_results.append(frame_eval)
        return frame_eval

    def compute_summary(self) -> MOTSummary:
        """Compute aggregate summary metrics across all evaluated frames."""
        total_frames = len(self.frame_results)
        total_gt = sum(r.num_gt for r in self.frame_results)
        total_tr = sum(r.num_tracks for r in self.frame_results)
        total_tp = sum(r.true_positives for r in self.frame_results)
        total_fp = sum(r.false_positives for r in self.frame_results)
        total_fn = sum(r.false_negatives for r in self.frame_results)
        total_ids = sum(r.id_switches for r in self.frame_results)

        # MOTA = 1 - (FN + FP + IDS) / GT
        if total_gt > 0:
            mota = max(0.0, 1.0 - (total_fn + total_fp + total_ids) / total_gt)
            recall = total_tp / total_gt
        else:
            mota = 1.0
            recall = 1.0

        precision = total_tp / total_tr if total_tr > 0 else 1.0

        # IDF1 Calculation
        unique_gts = list(self._gt_frame_counts.keys())
        unique_trs = list(self._track_frame_counts.keys())

        if unique_gts and unique_trs:
            cost_m = np.zeros((len(unique_gts), len(unique_trs)), dtype=np.float64)
            for i, gid in enumerate(unique_gts):
                for j, tid in enumerate(unique_trs):
                    cost_m[i, j] = -self._overlap_matrix.get((gid, tid), 0)

            r_ind, c_ind = linear_sum_assignment(cost_m)
            idtp = sum(self._overlap_matrix.get((unique_gts[r], unique_trs[c]), 0) for r, c in zip(r_ind, c_ind))
            idfp = total_tr - idtp
            idfn = total_gt - idtp
            denom = 2 * idtp + idfp + idfn
            idf1 = (2 * idtp) / denom if denom > 0 else 0.0
        else:
            idf1 = 0.0

        # Aggregated geometric errors
        all_px = [p for r in self.frame_results for p in r.pixel_errors]
        all_cm = [m for r in self.frame_results for m in r.metric_errors_cm]
        all_near = [m for r in self.frame_results for m in r.metric_errors_near_cm]
        all_mid = [m for r in self.frame_results for m in r.metric_errors_mid_cm]
        all_far = [m for r in self.frame_results for m in r.metric_errors_far_cm]

        px_rmse = float(np.sqrt(np.mean(np.array(all_px) ** 2))) if all_px else 0.0
        cm_rmse = float(np.sqrt(np.mean(np.array(all_cm) ** 2))) if all_cm else 0.0
        max_drift = float(np.max(all_cm)) if all_cm else 0.0
        near_rmse = float(np.sqrt(np.mean(np.array(all_near) ** 2))) if all_near else 0.0
        mid_rmse = float(np.sqrt(np.mean(np.array(all_mid) ** 2))) if all_mid else 0.0
        far_rmse = float(np.sqrt(np.mean(np.array(all_far) ** 2))) if all_far else 0.0

        ghost_tracks = len(self._all_observed_track_ids - self._matched_track_ids)

        return MOTSummary(
            total_frames=total_frames,
            total_gt_objects=total_gt,
            total_detections=total_tr,
            total_tp=total_tp,
            total_fp=total_fp,
            total_fn=total_fn,
            total_id_switches=total_ids,
            mota=round(float(mota), 4),
            idf1=round(float(idf1), 4),
            precision=round(float(precision), 4),
            recall=round(float(recall), 4),
            mean_pixel_rmse_px=round(px_rmse, 2),
            mean_metric_rmse_cm=round(cm_rmse, 2),
            max_metric_drift_cm=round(max_drift, 2),
            near_field_rmse_cm=round(near_rmse, 2),
            mid_field_rmse_cm=round(mid_rmse, 2),
            far_field_rmse_cm=round(far_rmse, 2),
            ghost_tracks_count=ghost_tracks,
        )
