# Specification: Dataset Ingestion Runner (`dataset-ingestion-runner`)

## NEW Capabilities

### Capability: Modular Dataset Evaluation and Test Ingestion
The `run_dataset_test.py` CLI script MUST evaluate arbitrary video sequences through `SafetyPipeline` using custom declarative YAML calibration and zone configs:

1. **Config & Source Resolution**:
   - Given `--dataset <name>`, the runner MUST resolve the video source from `data/raw/<name>/` and the calibration config from `configs/datasets/<name>.yaml`.
   - The runner MUST support explicit `--source <path>` and `--config <path>` overrides.
   - The runner MUST parse the `zones` section from the YAML config to instantiate `ZoneConfig` and `SpatialFSM`.

2. **Isolated Execution**:
   - The runner MUST initialize `SafetyPipeline` using `OnnxEngine`, `HomographyManager`, `MultiTargetKalmanTracker`, and `SpatialFSM`.
   - Zero changes MUST be made to core classes in `src/core/`, `src/inference/`, or `src/pipeline/`.

3. **Artifact Generation & Telemetry Logging**:
   - The runner MUST create an output directory `data/results/<dataset_name>/`.
   - The runner MUST record an annotated diagnostic video (`annotated_<dataset_name>.mp4`) containing the dual perspective and BEV visualizations.
   - The runner MUST log frame-by-frame JSONL telemetry (`events.jsonl`) recording timestamps, active tracks, positions, velocities, dwell times, and safety states.
   - The runner MUST export `summary.json` containing aggregate metrics (frames processed, elapsed time, FPS, latency percentiles, safety state distribution).

4. **Headless and CLI Controls**:
   - The runner MUST support `--no-display` for non-interactive test and CI environments.
   - The runner MUST support `--max-frames <N>` to allow bounded execution.

#### Scenario: Running test over clean baseline dataset
- **GIVEN** a downloaded dataset `data/raw/opencv_vtest/vtest.avi` and config `configs/datasets/opencv_vtest.yaml`
- **WHEN** `python scripts/run_dataset_test.py --dataset opencv_vtest --max-frames 50 --no-display` is executed
- **THEN** `SafetyPipeline` SHALL process 50 frames
- **AND** `data/results/opencv_vtest/annotated_opencv_vtest.mp4` SHALL be created and non-empty
- **AND** `data/results/opencv_vtest/events.jsonl` SHALL contain 50 telemetry records
- **AND** `data/results/opencv_vtest/summary.json` SHALL contain latency percentiles and throughput.
