# Proposal: Model Export & Latency Benchmark

## Intent
Establish a high-performance, edge-compliant human pose estimation baseline by exporting YOLO Pose (`yolo11n-pose` / `yolov8n-pose`) to an optimized ONNX graph and validating real-time inference latency ($t_{\text{infer}} \le 30\text{ ms}$) on Apple Silicon (M1 arm64).

## Scope

### In Scope
- CLI utility (`models/export_onnx.py`) to download pretrained weights and export to static ONNX (`imgsz=640`, `dynamic=False`, `opset=17`, `simplify=True`).
- ONNX model validation verifying graph topology, data types, and tensor dimensions `(1, 3, 640, 640)`.
- Reusable ONNX inference engine (`src/inference/onnx_engine.py`) supporting provider negotiation (`CoreMLExecutionProvider`, fallback to `CPUExecutionProvider` with ARM NEON).
- Benchmark profiler (`scripts/benchmark.py`) computing warmup cycles, mean, p50, p95, p99 latency, and throughput (FPS).
- Comprehensive unit tests covering export integrity and runtime execution.

### Out of Scope
- DLT Homography calibration and BEV coordinate transformation (Module 3).
- Spatial FSM zone intrusion and dwell tracking (Module 4).
- RTSP ingestion, OpenCV rendering, and GUI overlays (Module 5).

## Capabilities

### New Capabilities
- `model-export`: Automated export and integrity validation of YOLO Pose ONNX models.
- `onnx-inference`: Hardware-accelerated inference wrapper with flexible Execution Provider selection.
- `latency-benchmark`: Latency profiling CLI reporting statistical percentiles against edge safety budgets.

### Modified Capabilities
- None (baseline implementation).

## Approach
1. **Export Pipeline**: Use Ultralytics API to export YOLO Pose to ONNX with static shapes and opset 17. Verify graph using `onnx.checker` and `onnx.shape_inference`.
2. **Inference Engine**: Encapsulate ONNX Runtime `InferenceSession` in `OnnxEngine`. Prioritize `CoreMLExecutionProvider` followed by `CPUExecutionProvider`.
3. **Statistical Profiler**: Implement warmup phase (>=50 runs) and measurement phase (>=200 runs) using monotonic high-resolution timers (`time.perf_counter_ns`).

## Affected Areas
| File | Change Type | Purpose |
| :--- | :--- | :--- |
| `models/export_onnx.py` | New | Model download, ONNX export, and structural validation |
| `src/inference/onnx_engine.py` | New | ONNX Runtime session manager and inference executor |
| `scripts/benchmark.py` | New | Percentile latency and throughput profiling CLI |
| `tests/test_onnx_engine.py` | New | Tests for inference session, tensor shapes, and fallbacks |
| `tests/test_export.py` | New | Tests for export arguments and ONNX graph validity |

## Risks & Mitigation
- **CoreML Compilation Latency / Compatibility**: First-run compilation overhead or unsupported ops.
  *Mitigation*: Support graceful fallback to multi-threaded `CPUExecutionProvider` (ARM NEON).
- **Inference Latency Spike**: OS scheduling jitter causing p99 threshold breach.
  *Mitigation*: Include robust warmup iterations and thread affinity tuning in `onnxruntime.SessionOptions`.

## Rollback Plan
Revert the commit introducing the new standalone files in `models/`, `src/inference/`, and `scripts/`. No existing code or schemas are broken.

## Dependencies
- `ultralytics>=8.0.0`
- `onnx>=1.14.0`
- `onnxruntime>=1.16.0`
- `numpy>=1.24.0`
- `pytest>=7.0.0`

## Success Criteria
- [ ] Export script produces valid ONNX model matching shape `(1, 3, 640, 640)`.
- [ ] `OnnxEngine` loads model and executes forward pass with expected output tensor layout.
- [ ] Benchmark CLI reports p50, p95, p99, mean latency, and FPS.
- [ ] Safety Budget: $t_{\text{infer}} \le 30\text{ ms}$ ($\ge 33.3\text{ FPS}$) at p95 on M1 arm64.
- [ ] 100% test pass rate under `pytest tests/`.
