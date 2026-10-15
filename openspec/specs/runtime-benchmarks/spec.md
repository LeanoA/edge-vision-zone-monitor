# Specification: Runtime Engine Benchmarking (`runtime-benchmarks`)

## Purpose
Define the behavioral contracts and metric requirements for comparative execution profiling of deep learning inference runtimes (PyTorch CPU/MPS and ONNX CPU/CoreML).

---

### Requirement: Unified Inference Engine Interface
All inference engine abstractions (`OnnxEngine`, `TorchEngine`) MUST implement a consistent inference contract:
1. Method `infer(image: np.ndarray) -> np.ndarray` accepting a contiguous CHW or NCHW float32 image array and returning raw model tensor outputs.
2. Method `get_device_info() -> str` or `get_providers() -> List[str]` reporting the active execution backend (e.g. `cpu`, `mps`, `CoreMLExecutionProvider`, `CPUExecutionProvider`).

#### Scenario: TorchEngine CPU inference
- **GIVEN** a valid PyTorch model path or YOLO pose weights `yolo11n-pose.pt`
- **WHEN** `TorchEngine(model_path, device="cpu")` executes `infer(synthetic_tensor)`
- **THEN** it SHALL return raw output tensor shape `(1, 56, 8400)` or matching YOLO11-pose format
- **AND** `engine.device` SHALL equal `"cpu"`.

#### Scenario: TorchEngine MPS inference
- **GIVEN** an Apple Silicon system with MPS availability
- **WHEN** `TorchEngine(model_path, device="mps")` executes `infer(synthetic_tensor)`
- **THEN** inference SHALL execute on the Metal GPU device without errors
- **AND** output SHALL be returned as a standard NumPy ndarray on CPU host memory.

---

### Requirement: Multi-Runtime Statistical Latency Profiling
The comparative benchmark suite MUST profile inference latency across isolated warmup and timed measurement runs, computing:
1. Statistical moments: `mean_ms`, `std_ms`, `variance_ms2`, `min_ms`, `max_ms`.
2. Percentiles: `p50_ms`, `p95_ms`, `p99_ms`, `iqr_ms`.
3. Throughput: `fps` ($1000 / \text{mean-ms}$).
4. Speedup factor: $S_{\text{engine}} = \frac{\text{mean}_{\text{pytorch-cpu}}}{\text{mean}_{\text{engine}}}$.
5. ISO 13855 safety budget verification: `passed_budget = (p95_ms <= 30.0)`.

#### Scenario: Comparing multiple runtimes
- **GIVEN** PyTorch and ONNX models and 4 target configurations (`pytorch_cpu`, `pytorch_mps`, `onnx_cpu`, `onnx_coreml`)
- **WHEN** `run_runtime_comparison(models, iterations=50, warmup=10)` executes
- **THEN** it SHALL return a structured comparison dictionary mapping each runtime key to its `BenchmarkMetrics`
- **AND** each entry SHALL contain valid latency percentiles satisfying $\text{min} \le p50 \le p95 \le p99 \le \text{max}$.

#### Scenario: Formatting comparative table and exporting JSON
- **GIVEN** a completed comparison result
- **WHEN** `format_comparison_markdown(results)` and `export_comparison_json(results, path)` execute
- **THEN** the Markdown output SHALL include columns for Runtime, Provider/Device, Mean, p50, p95, p99, Jitter (Std), FPS, Speedup, and ISO Budget Status
- **AND** the JSON file SHALL contain all numeric metrics and configuration metadata.
