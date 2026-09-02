"""
scripts/benchmark_runtimes.py
Comparative latency, jitter, and throughput benchmarking suite across deep learning inference runtimes.
Evaluates PyTorch Eager (CPU/MPS), ONNX Runtime (CPU), and ONNX Runtime (CoreML/ANE).
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

import numpy as np
import torch

from src.inference.onnx_engine import OnnxEngine
from src.inference.torch_engine import TorchEngine

logger = logging.getLogger("benchmark_runtimes")

ISO_LATENCY_BUDGET_P95_MS: float = 30.0


@dataclass(frozen=True)
class RuntimeBenchmarkResult:
    """Statistical measurement results for a single inference engine runtime."""

    runtime_id: str
    display_name: str
    provider_or_device: str
    warmup: int
    iterations: int
    mean_ms: float
    min_ms: float
    max_ms: float
    std_ms: float
    variance_ms2: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    fps: float
    passed_iso_budget: bool


@dataclass(frozen=True)
class ComparativeBenchmarkSummary:
    """Container aggregating comparative benchmark results across multiple runtimes."""

    baseline_id: str
    results: List[RuntimeBenchmarkResult]

    def get_speedups(self) -> Dict[str, float]:
        """Calculate relative speedup factor for each runtime relative to the baseline."""
        baseline_result = next((r for r in self.results if r.runtime_id == self.baseline_id), None)
        if baseline_result is None or baseline_result.mean_ms <= 0.0:
            return {r.runtime_id: 1.0 for r in self.results}

        base_mean = baseline_result.mean_ms
        return {r.runtime_id: round(base_mean / r.mean_ms, 2) for r in self.results}


def run_runtime_benchmark(
    engine: Any,
    runtime_id: str,
    display_name: str,
    iterations: int = 100,
    warmup: int = 20,
    input_shape: Tuple[int, ...] = (1, 3, 640, 640),
) -> RuntimeBenchmarkResult:
    """
    Execute high-resolution latency profiling on a specified inference engine.

    Args:
        engine: Instantiated inference engine with .infer(ndarray) method.
        runtime_id: Unique string identifier for runtime.
        display_name: Human-readable display label.
        iterations: Number of timed iterations.
        warmup: Number of untimed warmup iterations.
        input_shape: Dimensions of synthetic input tensor.

    Returns:
        RuntimeBenchmarkResult with computed statistical percentiles and jitter.
    """
    if iterations <= 0:
        raise ValueError("iterations must be greater than 0")
    if warmup < 0:
        raise ValueError("warmup must be non-negative")

    # Generate synthetic input tensor
    dummy_input = np.random.randn(*input_shape).astype(np.float32)
    dummy_input = np.ascontiguousarray(dummy_input)

    logger.info("[%s] Running %d warmup iterations...", display_name, warmup)
    for _ in range(warmup):
        engine.infer(dummy_input)

    logger.info("[%s] Running %d measured iterations...", display_name, iterations)
    latencies_ns: List[int] = []
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        engine.infer(dummy_input)
        t1 = time.perf_counter_ns()
        latencies_ns.append(t1 - t0)

    times_arr = np.array(latencies_ns, dtype=np.float64) / 1_000_000.0

    mean_ms = float(np.mean(times_arr))
    min_ms = float(np.min(times_arr))
    max_ms = float(np.max(times_arr))
    std_ms = float(np.std(times_arr, ddof=1)) if len(times_arr) > 1 else 0.0
    var_ms2 = float(np.var(times_arr, ddof=1)) if len(times_arr) > 1 else 0.0
    p50_ms = float(np.percentile(times_arr, 50))
    p95_ms = float(np.percentile(times_arr, 95))
    p99_ms = float(np.percentile(times_arr, 99))
    fps = float(1000.0 / mean_ms) if mean_ms > 0.0 else 0.0

    # Provider / device string
    if hasattr(engine, "get_providers"):
        providers = engine.get_providers()
        prov_str = providers[0] if providers else "Unknown"
    elif hasattr(engine, "get_device_info"):
        prov_str = engine.get_device_info()
    else:
        prov_str = "Generic"

    passed_budget = bool(p95_ms <= ISO_LATENCY_BUDGET_P95_MS)

    return RuntimeBenchmarkResult(
        runtime_id=runtime_id,
        display_name=display_name,
        provider_or_device=prov_str,
        warmup=warmup,
        iterations=iterations,
        mean_ms=round(mean_ms, 3),
        min_ms=round(min_ms, 3),
        max_ms=round(max_ms, 3),
        std_ms=round(std_ms, 3),
        variance_ms2=round(var_ms2, 4),
        p50_ms=round(p50_ms, 3),
        p95_ms=round(p95_ms, 3),
        p99_ms=round(p99_ms, 3),
        fps=round(fps, 2),
        passed_iso_budget=passed_budget,
    )


def run_multi_runtime_comparison(
    pytorch_model_path: Union[str, Path] = "yolo11n-pose.pt",
    onnx_model_path: Union[str, Path] = "models/yolo11n-pose.onnx",
    iterations: int = 100,
    warmup: int = 20,
    num_threads: int = 4,
    runtimes_to_test: Optional[List[str]] = None,
) -> ComparativeBenchmarkSummary:
    """
    Execute full comparative benchmark suite across all supported runtime targets.
    """
    if runtimes_to_test is None:
        runtimes_to_test = ["pytorch_cpu", "pytorch_mps", "onnx_cpu", "onnx_coreml"]

    results: List[RuntimeBenchmarkResult] = []

    # 1. PyTorch CPU
    if "pytorch_cpu" in runtimes_to_test:
        try:
            logger.info("Initializing PyTorch (CPU)...")
            engine = TorchEngine(model_path=pytorch_model_path, device="cpu")
            res = run_runtime_benchmark(
                engine, "pytorch_cpu", "PyTorch Eager (CPU)", iterations, warmup
            )
            results.append(res)
        except Exception as e:
            logger.warning("Failed to benchmark PyTorch CPU: %s", e)

    # 2. PyTorch MPS (Apple Silicon GPU)
    if "pytorch_mps" in runtimes_to_test:
        if torch.backends.mps.is_available():
            try:
                logger.info("Initializing PyTorch (MPS GPU)...")
                engine = TorchEngine(model_path=pytorch_model_path, device="mps")
                res = run_runtime_benchmark(
                    engine, "pytorch_mps", "PyTorch Eager (MPS)", iterations, warmup
                )
                results.append(res)
            except Exception as e:
                logger.warning("Failed to benchmark PyTorch MPS: %s", e)
        else:
            logger.info("Skipping PyTorch MPS: Device not available.")

    # 3. ONNX CPU
    if "onnx_cpu" in runtimes_to_test:
        try:
            logger.info("Initializing ONNX Runtime (CPUExecutionProvider)...")
            engine = OnnxEngine(
                model_path=onnx_model_path,
                providers=["CPUExecutionProvider"],
                num_threads=num_threads,
            )
            res = run_runtime_benchmark(
                engine, "onnx_cpu", "ONNX Runtime (CPU)", iterations, warmup
            )
            results.append(res)
        except Exception as e:
            logger.warning("Failed to benchmark ONNX CPU: %s", e)

    # 4. ONNX CoreML / ANE
    if "onnx_coreml" in runtimes_to_test:
        try:
            logger.info("Initializing ONNX Runtime (CoreMLExecutionProvider)...")
            engine = OnnxEngine(
                model_path=onnx_model_path,
                providers=["CoreMLExecutionProvider", "CPUExecutionProvider"],
            )
            res = run_runtime_benchmark(
                engine, "onnx_coreml", "ONNX Runtime (CoreML/ANE)", iterations, warmup
            )
            results.append(res)
        except Exception as e:
            logger.warning("Failed to benchmark ONNX CoreML: %s", e)

    return ComparativeBenchmarkSummary(baseline_id="pytorch_cpu", results=results)


def format_comparison_markdown(summary: ComparativeBenchmarkSummary) -> str:
    """Format comparative benchmark results as a GitHub Markdown table."""
    speedups = summary.get_speedups()

    lines = [
        "## 📊 Comparative Runtime Engine Benchmark (YOLO11-Pose)",
        "",
        "| Runtime Engine | Backend / Device | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Jitter $\\sigma$ (ms) | Throughput (FPS) | Speedup vs CPU | ISO 13855 ($\\le 30\\text{ms}$) |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for res in summary.results:
        speedup = speedups.get(res.runtime_id, 1.0)
        speedup_str = f"**{speedup:.2f}x**" if speedup > 1.05 else f"{speedup:.2f}x"
        budget_status = "✅ PASS" if res.passed_iso_budget else "❌ FAIL"
        lines.append(
            f"| **{res.display_name}** | `{res.provider_or_device}` | "
            f"{res.mean_ms:.2f} | {res.p50_ms:.2f} | {res.p95_ms:.2f} | {res.p99_ms:.2f} | "
            f"±{res.std_ms:.2f} | {res.fps:.1f} FPS | {speedup_str} | {budget_status} |"
        )

    return "\n".join(lines)


def export_comparison_json(summary: ComparativeBenchmarkSummary, path: Union[str, Path]) -> None:
    """Export comparative metrics to a JSON file."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    speedups = summary.get_speedups()

    data = {
        "benchmark": "runtime_engine_showdown",
        "model": "YOLO11n-Pose",
        "target_iso_budget_p95_ms": ISO_LATENCY_BUDGET_P95_MS,
        "baseline_id": summary.baseline_id,
        "results": [
            {
                **asdict(res),
                "speedup_vs_baseline": speedups.get(res.runtime_id, 1.0),
            }
            for res in summary.results
        ],
    }
    dest.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info("Exported comparative benchmark JSON to '%s'.", dest)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments for comparative benchmark."""
    parser = argparse.ArgumentParser(
        description="Comparative Runtime Engine Benchmarking Suite for Edge AI."
    )
    parser.add_argument(
        "--pytorch-model",
        type=str,
        default="yolo11n-pose.pt",
        help="Path to PyTorch weights file (default: yolo11n-pose.pt).",
    )
    parser.add_argument(
        "--onnx-model",
        type=str,
        default="models/yolo11n-pose.onnx",
        help="Path to ONNX model file (default: models/yolo11n-pose.onnx).",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of timed benchmark iterations per engine (default: 100).",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=20,
        help="Number of untimed warmup iterations per engine (default: 20).",
    )
    parser.add_argument(
        "--num-threads",
        type=int,
        default=4,
        help="Thread count for CPU execution (default: 4).",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="docs/benchmarks/runtime_comparison.json",
        help="Destination path for JSON benchmark results.",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default="docs/benchmarks/runtime_comparison.md",
        help="Destination path for Markdown benchmark summary.",
    )
    return parser.parse_args(args)


def main() -> None:
    """CLI entry point for comparative runtime benchmarking."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    args = parse_args()

    print("\n" + "=" * 78)
    print("🚀 EDGE SAFETY GUARD — RUNTIME ENGINE BENCHMARK SHOWDOWN")
    print("=" * 78)
    print(f"PyTorch Model : {args.pytorch_model}")
    print(f"ONNX Model    : {args.onnx_model}")
    print(f"Iterations    : {args.iterations} (Warmup: {args.warmup})")
    print("-" * 78)

    summary = run_multi_runtime_comparison(
        pytorch_model_path=args.pytorch_model,
        onnx_model_path=args.onnx_model,
        iterations=args.iterations,
        warmup=args.warmup,
        num_threads=args.num_threads,
    )

    md_table = format_comparison_markdown(summary)
    print("\n" + md_table + "\n")

    if args.output_json:
        export_comparison_json(summary, args.output_json)

    if args.output_md:
        Path(args.output_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output_md).write_text(md_table + "\n", encoding="utf-8")
        logger.info("Exported Markdown comparison to '%s'.", args.output_md)

    print("=" * 78)
    print("[✅] Runtime benchmark comparison complete.")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    main()
