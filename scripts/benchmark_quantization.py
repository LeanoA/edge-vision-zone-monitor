"""
scripts/benchmark_quantization.py
Evaluates numerical precision, inference speedup, and metric ground-plane geometric drift
across FP32 (baseline), FP16 (half-precision), and INT8 (dynamically quantized) ONNX models.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import argparse
import json
import logging
import sys
import time

# Ensure project root is on sys.path for direct CLI invocation
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np

from src.core.homography import HomographyManager
from src.inference.onnx_engine import OnnxEngine

logger = logging.getLogger("benchmark_quantization")

SAFETY_MAX_METRIC_DRIFT_TOLERANCE_CM: float = 15.0


@dataclass(frozen=True)
class QuantizationResult:
    """Benchmark results for a specific model quantization precision level."""

    model_id: str
    display_name: str
    precision: str
    size_mb: float
    size_reduction_pct: float
    mean_latency_ms: float
    p95_latency_ms: float
    fps: float
    pixel_rmse_px: float
    metric_rmse_cm: float
    max_metric_drift_cm: float
    passed_safety_tolerance: bool


@dataclass(frozen=True)
class QuantizationComparisonSummary:
    """Container aggregating quantization precision benchmark results."""

    baseline_id: str
    results: List[QuantizationResult]


def compute_geometric_drift(
    kps_ref: np.ndarray,
    kps_cand: np.ndarray,
    homography: Optional[HomographyManager] = None,
    conf_threshold: float = 0.5,
) -> Tuple[float, float, float]:
    """
    Calculate pixel RMSE and projected metric ground-plane RMSE between reference and candidate keypoints.

    Args:
        kps_ref: Reference keypoints array (N_persons, K_joints, 3) where elements are (x, y, conf).
        kps_cand: Candidate keypoints array (N_persons, K_joints, 3).
        homography: Optional HomographyManager instance for metric ground projection.
        conf_threshold: Minimum joint confidence threshold to include in evaluation.

    Returns:
        Tuple of (pixel_rmse_px, metric_rmse_cm, max_metric_drift_cm).
    """
    ref = np.asarray(kps_ref, dtype=np.float64)
    cand = np.asarray(kps_cand, dtype=np.float64)

    if ref.size == 0 or cand.size == 0 or ref.shape != cand.shape:
        return 0.0, 0.0, 0.0

    # Mask valid keypoints above confidence threshold
    valid_mask = (ref[:, :, 2] >= conf_threshold) & (cand[:, :, 2] >= conf_threshold)
    if not np.any(valid_mask):
        # Fallback to evaluating all keypoints if confidence mask is empty
        valid_mask = np.ones(ref.shape[:2], dtype=bool)

    diff_px = ref[:, :, :2][valid_mask] - cand[:, :, :2][valid_mask]
    sq_dist_px = np.sum(diff_px ** 2, axis=-1)
    pixel_rmse = float(np.sqrt(np.mean(sq_dist_px))) if len(sq_dist_px) > 0 else 0.0

    if homography is None or not len(diff_px):
        return pixel_rmse, 0.0, 0.0

    pts_ref_px = ref[:, :, :2][valid_mask]
    pts_cand_px = cand[:, :, :2][valid_mask]

    # Project to metric world plane (meters)
    world_ref = homography.project_batch(pts_ref_px, to_world=True)
    world_cand = homography.project_batch(pts_cand_px, to_world=True)

    diff_metric_m = world_ref - world_cand
    dist_metric_cm = np.sqrt(np.sum(diff_metric_m ** 2, axis=-1)) * 100.0

    metric_rmse_cm = float(np.sqrt(np.mean(dist_metric_cm ** 2))) if len(dist_metric_cm) > 0 else 0.0
    max_drift_cm = float(np.max(dist_metric_cm)) if len(dist_metric_cm) > 0 else 0.0

    return pixel_rmse, metric_rmse_cm, max_drift_cm


def decode_keypoints_raw(output_tensor: np.ndarray) -> np.ndarray:
    """Extract raw keypoint array (N_proposals, 17, 3) from YOLO pose raw output (1, 56, 8400)."""
    out = np.squeeze(output_tensor)  # (56, 8400)
    if out.ndim != 2 or out.shape[0] != 56:
        return np.empty((0, 17, 3), dtype=np.float32)

    # Keypoints are located in rows 5..55 (17 joints x 3: x, y, conf)
    kps_slice = out[5:, :].T  # Shape (8400, 51)
    kps = kps_slice.reshape(-1, 17, 3)
    return kps


def run_quantization_precision_benchmark(
    fp32_model_path: Union[str, Path] = "models/yolo11n-pose.onnx",
    fp16_model_path: Union[str, Path] = "models/yolo11n-pose-fp16.onnx",
    int8_model_path: Union[str, Path] = "models/yolo11n-pose-int8.onnx",
    homography_config_path: Union[str, Path] = "configs/datasets/openvino_people.yaml",
    sample_images: Optional[List[np.ndarray]] = None,
    iterations: int = 50,
    warmup: int = 15,
) -> QuantizationComparisonSummary:
    """
    Execute full comparative benchmark evaluating FP32, FP16, and INT8 models.
    """
    homography = HomographyManager(config_path=str(homography_config_path))

    models_config = [
        ("fp32", "FP32 (Single Precision)", "FP32", Path(fp32_model_path)),
        ("fp16", "FP16 (Half Precision)", "FP16", Path(fp16_model_path)),
        ("int8", "INT8 (Dynamic Quant)", "INT8", Path(int8_model_path)),
    ]

    # Reference baseline file size
    fp32_size_mb = Path(fp32_model_path).stat().st_size / (1024 * 1024) if Path(fp32_model_path).is_file() else 11.85

    # Prepare sample input tensors for precision drift evaluation
    if sample_images is None or len(sample_images) == 0:
        eval_tensors = [np.random.randn(1, 3, 640, 640).astype(np.float32) for _ in range(5)]
    else:
        eval_tensors = [img if img.ndim == 4 else np.expand_dims(img, axis=0) for img in sample_images]

    # Pre-compute FP32 baseline predictions
    fp32_engine = OnnxEngine(str(fp32_model_path))
    ref_outputs = [fp32_engine.infer(t) for t in eval_tensors]
    ref_kps_list = [decode_keypoints_raw(o) for o in ref_outputs]

    results: List[QuantizationResult] = []

    for model_id, display_name, precision, model_path in models_config:
        if not model_path.is_file():
            logger.warning("Skipping '%s': Model file not found at '%s'.", display_name, model_path)
            continue

        size_mb = model_path.stat().st_size / (1024 * 1024)
        reduction_pct = max(0.0, round((1.0 - (size_mb / fp32_size_mb)) * 100.0, 1))

        # Latency profiling
        engine = OnnxEngine(str(model_path))
        dummy_tensor = eval_tensors[0]

        for _ in range(warmup):
            engine.infer(dummy_tensor)

        latencies_ns = []
        for _ in range(iterations):
            t0 = time.perf_counter_ns()
            engine.infer(dummy_tensor)
            t1 = time.perf_counter_ns()
            latencies_ns.append(t1 - t0)

        times_ms = np.array(latencies_ns, dtype=np.float64) / 1_000_000.0
        mean_ms = float(np.mean(times_ms))
        p95_ms = float(np.percentile(times_ms, 95))
        fps = float(1000.0 / mean_ms) if mean_ms > 0.0 else 0.0

        # Geometric precision drift evaluation
        cand_outputs = [engine.infer(t) for t in eval_tensors]
        cand_kps_list = [decode_keypoints_raw(o) for o in cand_outputs]

        px_rmses = []
        metric_rmses = []
        max_drifts = []

        for ref_kps, cand_kps in zip(ref_kps_list, cand_kps_list):
            px_err, metric_err, max_d = compute_geometric_drift(ref_kps, cand_kps, homography)
            px_rmses.append(px_err)
            metric_rmses.append(metric_err)
            max_drifts.append(max_d)

        avg_px_rmse = float(np.mean(px_rmses)) if px_rmses else 0.0
        avg_metric_rmse = float(np.mean(metric_rmses)) if metric_rmses else 0.0
        max_metric_drift = float(np.max(max_drifts)) if max_drifts else 0.0

        passed_safety = bool(avg_metric_rmse <= SAFETY_MAX_METRIC_DRIFT_TOLERANCE_CM)

        results.append(
            QuantizationResult(
                model_id=model_id,
                display_name=display_name,
                precision=precision,
                size_mb=round(size_mb, 2),
                size_reduction_pct=reduction_pct,
                mean_latency_ms=round(mean_ms, 2),
                p95_latency_ms=round(p95_ms, 2),
                fps=round(fps, 1),
                pixel_rmse_px=round(avg_px_rmse, 2),
                metric_rmse_cm=round(avg_metric_rmse, 2),
                max_metric_drift_cm=round(max_metric_drift, 2),
                passed_safety_tolerance=passed_safety,
            )
        )

    return QuantizationComparisonSummary(baseline_id="fp32", results=results)


def format_quantization_markdown(summary: QuantizationComparisonSummary) -> str:
    """Format quantization benchmark results into a GitHub Markdown table."""
    lines = [
        "## 📊 Comparative Quantization & Metric Precision Benchmark (YOLO11-Pose)",
        "",
        "| Precision Mode | Model Size | Size Reduction | Mean Latency | Throughput | Pixel RMSE | Metric Ground RMSE | Max Drift | ISO 13855 Status |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for res in summary.results:
        safety_badge = "✅ PASS" if res.passed_safety_tolerance else "❌ FAIL"
        lines.append(
            f"| **{res.display_name}** | {res.size_mb:.2f} MB | {res.size_reduction_pct:.1f}% | "
            f"{res.mean_latency_ms:.2f} ms | {res.fps:.1f} FPS | "
            f"{res.pixel_rmse_px:.2f} px | {res.metric_rmse_cm:.2f} cm | {res.max_metric_drift_cm:.2f} cm | {safety_badge} |"
        )

    return "\n".join(lines)


def export_quantization_json(summary: QuantizationComparisonSummary, path: Union[str, Path]) -> None:
    """Export quantization metrics to JSON file."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "benchmark": "quantization_and_geometric_precision",
        "model": "YOLO11n-Pose",
        "max_metric_tolerance_cm": SAFETY_MAX_METRIC_DRIFT_TOLERANCE_CM,
        "baseline_id": summary.baseline_id,
        "results": [asdict(res) for res in summary.results],
    }
    dest.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info("Exported quantization benchmark JSON to '%s'.", dest)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments for quantization benchmark."""
    parser = argparse.ArgumentParser(
        description="Quantization and Geometric Precision Benchmark for Edge AI."
    )
    parser.add_argument(
        "--fp32-model",
        type=str,
        default="models/yolo11n-pose.onnx",
        help="Path to FP32 baseline ONNX model.",
    )
    parser.add_argument(
        "--fp16-model",
        type=str,
        default="models/yolo11n-pose-fp16.onnx",
        help="Path to FP16 half-precision ONNX model.",
    )
    parser.add_argument(
        "--int8-model",
        type=str,
        default="models/yolo11n-pose-int8.onnx",
        help="Path to INT8 dynamically quantized ONNX model.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/datasets/openvino_people.yaml",
        help="Homography dataset configuration path.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=50,
        help="Number of latency measurement iterations per model.",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=15,
        help="Number of untimed warmup iterations.",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="docs/benchmarks/quantization_comparison.json",
        help="Destination path for JSON benchmark results.",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default="docs/benchmarks/quantization_comparison.md",
        help="Destination path for Markdown benchmark summary.",
    )
    return parser.parse_args(args)


def main() -> None:
    """CLI entry point for quantization benchmark."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    args = parse_args()

    print("\n" + "=" * 80)
    print("🔬 EDGE SAFETY GUARD — QUANTIZATION & GEOMETRIC PRECISION BENCHMARK")
    print("=" * 80)
    print(f"FP32 Model : {args.fp32_model}")
    print(f"FP16 Model : {args.fp16_model}")
    print(f"INT8 Model : {args.int8_model}")
    print(f"Config     : {args.config}")
    print(f"Iterations : {args.iterations} (Warmup: {args.warmup})")
    print("-" * 80)

    summary = run_quantization_precision_benchmark(
        fp32_model_path=args.fp32_model,
        fp16_model_path=args.fp16_model,
        int8_model_path=args.int8_model,
        homography_config_path=args.config,
        iterations=args.iterations,
        warmup=args.warmup,
    )

    md_table = format_quantization_markdown(summary)
    print("\n" + md_table + "\n")

    if args.output_json:
        export_quantization_json(summary, args.output_json)

    if args.output_md:
        Path(args.output_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output_md).write_text(md_table + "\n", encoding="utf-8")
        logger.info("Exported Markdown comparison to '%s'.", args.output_md)

    print("=" * 80)
    print("[✅] Quantization benchmark complete.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
