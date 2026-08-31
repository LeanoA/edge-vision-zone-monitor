# Design: End-to-End Demo Orchestrator CLI (`scripts/run_demo.py`)

## Technical Approach
Implement a decoupled `DemoRunner` class inside `scripts/run_demo.py` configured via `DemoRunnerConfig` dataclass and driven by an `argparse` CLI entrypoint. The orchestrator unifies stream decoding, pipeline evaluation, dual visualization rendering, live display interaction, video recording, and telemetry streaming.

## Architecture Decisions

| Decision | Options Considered | Selected Option & Rationale | Tradeoffs |
| :--- | :--- | :--- | :--- |
| **CLI Architecture** | A: Procedural script with global while loop.<br>B: Modular `DemoRunner` class. | **Option B: `DemoRunner` class.** Encapsulates stream lifecycle (`initialize`, `process_frame`, `run`, `close`, `get_summary`), making the orchestrator directly unit-testable in CI without subprocesses. | Adds minimal class boilerplate over raw procedural code. |
| **Video Ingestion** | A: File-only decoder.<br>B: Unified source resolver (file, webcam index, RTSP). | **Option B: Unified source resolver.** Tests if input is integer string (`"0"`) for webcam, or string path/URL for files and RTSP streams. Fallbacks to 30.0 FPS if stream metadata reports non-positive FPS. | None; expands operational utility. |
| **Headless Safety** | A: Try-catch around `cv2.imshow`.<br>B: Explicit `--no-display` flag with complete GUI bypass. | **Option B: `--no-display` flag.** Guarantees zero GUI API calls in headless CI/server environments, eliminating X11/Wayland runtime crashes. | Interactive controls unavailable when headless. |
| **Telemetry Serialization** | A: Monolithic JSON dump at exit.<br>B: Streaming JSONL (newline-delimited JSON). | **Option B: Streaming JSONL.** Appends per-frame records immediately, preventing memory ballooning on long streams and preserving logs if interrupted. | Slightly larger disk footprint than compressed binary. |

## Data Flow

```
[ Video / Webcam / RTSP Source ]
             │ (cv2.VideoCapture.read)
             ▼
      [ Frame (H, W, 3) ]
             │
             ▼
   [ SafetyPipeline.process_frame ]
   ├── Preprocess (Letterbox)
   ├── Ingest / Infeence (OnnxEngine)
   ├── Keypoints / Anchors
   ├── Homography (DLT Projection)
   ├── Tracking (MultiTargetKalmanTracker)
   └── SpatialFSM Evaluation
             │
             ▼
      [ PipelineResult ] ──→ [ JSONL Telemetry Writer ]
             │
             ▼
   [ DualVisualizer.render ]
             │
             ├─ (if --output-video) ──→ [ cv2.VideoWriter (.mp4) ]
             └─ (if not --no-display) ─→ [ cv2.imshow & Key Handling ]
```

## File Changes

| File | Action | Description |
| :--- | :--- | :--- |
| `scripts/run_demo.py` | Create | Modular `DemoRunner` class, `DemoRunnerConfig`, and CLI entrypoint |
| `openspec/specs/demo-orchestrator/spec.md` | Create | Canonical OpenSpec specification for CLI orchestrator |
| `openspec/changes/demo-orchestrator-cli/specs/demo-orchestrator/spec.md` | Create | Delta/new capability specification in change folder |
| `tests/test_demo_runner.py` | Create | Unit and integration test suite |
| `README.md` | Modify | Update Paso 7 in Roadmap and CLI execution instructions |

## Interfaces / Contracts

```python
@dataclass(frozen=True)
class DemoRunnerConfig:
    source: str
    model_path: str = "models/yolo11n-pose.onnx"
    config_path: str = "configs/default_config.yaml"
    layout: LayoutMode = LayoutMode.SIDE_BY_SIDE
    no_display: bool = False
    realtime: bool = False
    output_video: Optional[Path] = None
    output_events: Optional[Path] = None
    conf_threshold: float = 0.5
    max_frames: Optional[int] = None

@dataclass
class DemoSummary:
    total_frames: int
    elapsed_time_s: float
    average_fps: float
    latencies_mean_ms: float
    latencies_p50_ms: float
    latencies_p95_ms: float
    latencies_p99_ms: float
    state_counts: Dict[str, int]
```

### Telemetry JSONL Record Schema
```json
{
  "frame_id": 142,
  "timestamp": 1725123456.789,
  "safety_state": "DANGER_INTRUSION",
  "trip_active": true,
  "tracks": [
    {"track_id": 1, "pos": [2.15, 3.42], "vel": [0.02, 1.15], "status": "OBSERVED", "dwell_s": 1.2}
  ],
  "latencies_ms": {
    "preprocess": 1.1,
    "inference": 8.4,
    "keypoint_extract": 0.6,
    "projection": 0.2,
    "tracking": 0.4,
    "fsm": 0.3,
    "total_t1": 11.0
  }
}
```

## Testing Strategy

| Layer | What to Test | Approach |
| :--- | :--- | :--- |
| **Unit** | `DemoRunnerConfig` parsing and argument defaults | PyTest verifying all CLI flags and validation rules |
| **Unit** | Telemetry serialization and metrics calculation | Test `DemoSummary` percentiles against known synthetic latency arrays |
| **Integration** | Headless playback on synthetic video | Run `DemoRunner` with synthetic ONNX model on `data/samples/sequence_a_clean_incursion.mp4` with `--no-display` |
| **Integration** | Output recording and telemetry generation | Verify written `.mp4` dimensions and `.jsonl` schema validity |

## Threat Matrix
`N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.`

## Migration / Rollout
No migration required. Non-breaking additive CLI tool.

## Open Questions
None.
