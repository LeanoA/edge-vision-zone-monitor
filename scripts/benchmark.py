"""
scripts/benchmark.py
Latency and throughput statistical benchmarking suite for edge safety inference.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union
import argparse
import json
import logging
import sys
import time

# Ensure project root is on sys.path for direct CLI invocation
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from src.inference.onnx_engine import OnnxEngine

logger = logging.getLogger("benchmark")

LATENCY_BUDGET_P95_MS: float = 30.0


@dataclass(frozen=True)
class BenchmarkMetrics:
    """Immutable container for statistical benchmark results."""

    model_path: str
    active_providers: List[str]
    warmup_iterations: int
    iterations: int
    mean_ms: float
    min_ms: float
    max_ms: float
    std_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    fps: float
    passed_budget: bool


def run_benchmark(
    engine: OnnxEngine,
    iterations: int = 200,
    warmup: int = 50,
    input_shape: Tuple[int, ...] = (1, 3, 640, 640),
) -> BenchmarkMetrics:
    """
    Execute statistical latency profiling over synthetic inputs.

    Args:
        engine: Initialized OnnxEngine instance.
        iterations: Number of timed measurement iterations. Default: 200.
        warmup: Number of untimed warmup iterations. Default: 50.
        input_shape: Dimensions of the synthetic input tensor. Default: (1, 3, 640, 640).

    Returns:
        BenchmarkMetrics containing computed percentiles and safety budget status.
    """
    if iterations <= 0:
        raise ValueError("iterations must be greater than 0")
    if warmup < 0:
        raise ValueError("warmup must be non-negative")

    # Generate synthetic input tensor matching engine input requirements
    synthetic_input = np.random.randn(*input_shape).astype(np.float32)
    synthetic_input = np.ascontiguousarray(synthetic_input)

    logger.info("Executing %d warmup iterations...", warmup)
    for _ in range(warmup):
        engine.infer(synthetic_input)

    logger.info("Executing %d measured iterations...", iterations)
    latencies_ns: List[int] = []
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        engine.infer(synthetic_input)
        t1 = time.perf_counter_ns()
        latencies_ns.append(t1 - t0)

    # Convert to milliseconds
    times_arr = np.array(latencies_ns, dtype=np.float64) / 1_000_000.0

    mean_ms = float(np.mean(times_arr))
    min_ms = float(np.min(times_arr))
    max_ms = float(np.max(times_arr))
    std_ms = float(np.std(times_arr, ddof=1)) if len(times_arr) > 1 else 0.0
    p50_ms = float(np.percentile(times_arr, 50))
    p95_ms = float(np.percentile(times_arr, 95))
    p99_ms = float(np.percentile(times_arr, 99))
    fps = float(1000.0 / mean_ms) if mean_ms > 0.0 else 0.0

    passed_budget = bool(p95_ms <= LATENCY_BUDGET_P95_MS)

    return BenchmarkMetrics(
        model_path=str(engine.model_path),
        active_providers=engine.get_providers(),
        warmup_iterations=warmup,
        iterations=iterations,
        mean_ms=round(mean_ms, 3),
        min_ms=round(min_ms, 3),
        max_ms=round(max_ms, 3),
        std_ms=round(std_ms, 3),
        p50_ms=round(p50_ms, 3),
        p95_ms=round(p95_ms, 3),
        p99_ms=round(p99_ms, 3),
        fps=round(fps, 2),
        passed_budget=passed_budget,
    )


def format_benchmark_table(metrics: BenchmarkMetrics) -> str:
    """Format benchmark metrics into an aligned text summary table."""
    status = "PASS (p95 <= 30.0 ms)" if metrics.passed_budget else "FAIL (p95 > 30.0 ms)"
    providers_str = ", ".join(metrics.active_providers)

    lines = [
        "=" * 72,
        f"{'EDGE SAFETY INFERENCE BENCHMARK REPORT':^72}",
        "=" * 72,
        f"Model Path:         {metrics.model_path}",
        f"Active Provider(s): {providers_str}",
        f"Warmup / Iterations: {metrics.warmup_iterations} / {metrics.iterations}",
        "-" * 72,
        f"{'Metric':<25} {'Value':>20}",
        "-" * 72,
        f"{'Mean Latency:':<25} {metrics.mean_ms:>17.2f} ms",
        f"{'Std Deviation:':<25} {metrics.std_ms:>17.2f} ms",
        f"{'Min Latency:':<25} {metrics.min_ms:>17.2f} ms",
        f"{'p50 Latency (Median):':<25} {metrics.p50_ms:>17.2f} ms",
        f"{'p95 Latency:':<25} {metrics.p95_ms:>17.2f} ms",
        f"{'p99 Latency:':<25} {metrics.p99_ms:>17.2f} ms",
        f"{'Max Latency:':<25} {metrics.max_ms:>17.2f} ms",
        f"{'Throughput:':<25} {metrics.fps:>17.2f} FPS",
        "-" * 72,
        f"ISO 13855 Budget:   {status}",
        "=" * 72,
    ]
    return "\n".join(lines)


def export_benchmark_json(metrics: BenchmarkMetrics, json_path: Union[str, Path]) -> None:
    """Write benchmark metrics to a JSON file."""
    path = Path(json_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    primary_provider = metrics.active_providers[0] if metrics.active_providers else "Unknown"

    report = {
        "model_path": metrics.model_path,
        "provider": primary_provider,
        "active_providers": metrics.active_providers,
        "warmup_iterations": metrics.warmup_iterations,
        "iterations": metrics.iterations,
        "metrics": {
            "mean_ms": metrics.mean_ms,
            "min_ms": metrics.min_ms,
            "max_ms": metrics.max_ms,
            "std_ms": metrics.std_ms,
            "p50_ms": metrics.p50_ms,
            "p95_ms": metrics.p95_ms,
            "p99_ms": metrics.p99_ms,
            "fps": metrics.fps,
        },
        "budget_ms": LATENCY_BUDGET_P95_MS,
        "passed": metrics.passed_budget,
    }
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.info("Exported JSON report to '%s'.", path)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments for latency benchmark."""
    parser = argparse.ArgumentParser(
        description="Edge Safety Guard inference latency benchmark suite."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="models/yolo11n-pose.onnx",
        help="Path to ONNX model file (default: models/yolo11n-pose.onnx).",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=200,
        help="Number of timed benchmark iterations (default: 200).",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=50,
        help="Number of untimed warmup iterations (default: 50).",
    )
    parser.add_argument(
        "--num-threads",
        type=int,
        default=4,
        help="Intra-op thread pool size for CPU execution (default: 4).",
    )
    parser.add_argument(
        "--providers",
        type=str,
        default=None,
        help="Comma-separated execution providers (e.g. CoreMLExecutionProvider,CPUExecutionProvider).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with non-zero code if p95 latency exceeds 30.0 ms budget.",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default=None,
        help="Path to write JSON benchmark report.",
    )
    return parser.parse_args(args)


def main() -> None:
    """CLI entry point for benchmark."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    args = parse_args()

    providers = [p.strip() for p in args.providers.split(",")] if args.providers else None

    try:
        engine = OnnxEngine(
            model_path=args.model,
            providers=providers,
            num_threads=args.num_threads,
        )
    except Exception as e:
        logger.error("Failed to initialize OnnxEngine: %s", e)
        sys.exit(1)

    try:
        metrics = run_benchmark(
            engine=engine,
            iterations=args.iterations,
            warmup=args.warmup,
        )
    except Exception as e:
        logger.error("Benchmark run failed: %s", e)
        sys.exit(1)

    print("\n" + format_benchmark_table(metrics) + "\n")

    if args.json_out:
        export_benchmark_json(metrics, args.json_out)

    if args.strict and not metrics.passed_budget:
        logger.error(
            "Latency budget violated: p95=%.2f ms > %.1f ms",
            metrics.p95_ms,
            LATENCY_BUDGET_P95_MS,
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
