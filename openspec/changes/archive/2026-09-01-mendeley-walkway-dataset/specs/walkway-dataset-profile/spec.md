# Specification: Mendeley Walkway Dataset Profile (`walkway-dataset-profile`)

## NEW Capabilities

### Capability: Declarative Walkway Dataset Calibration and Evaluation
The system MUST provide a declarative YAML calibration profile for the `mendeley_walkway_violation.mp4` sequence and register it as an executable benchmark:

1. **Camera Specification**:
   - MUST define resolution $1920\times 1080$ and native FPS of 24 (or 24.83).
   - Camera identifier MUST be `mendeley_walkway_violation_cctv`.

2. **Homography Calibration (DLT)**:
   - MUST provide 4 coplanar ground reference points mapping pixel coordinates to metric coordinates $[X, Y]$ in meters.
   - Homography reprojection RMSE error MUST be $\le 0.05\text{ m}$.
   - Image points:
     - Point 1 (bottom-left): $[250.0, 1020.0] \rightarrow [0.0, 0.0]\text{ m}$
     - Point 2 (bottom-right): $[1680.0, 1020.0] \rightarrow [10.0, 0.0]\text{ m}$
     - Point 3 (top-right): $[1400.0, 480.0] \rightarrow [10.0, 15.0]\text{ m}$
     - Point 4 (top-left): $[520.0, 480.0] \rightarrow [0.0, 15.0]\text{ m}$

3. **Restricted Zone & Safety Parameters**:
   - `danger_polygon`: $[[2.5, 3.0], [7.5, 3.0], [7.5, 10.0], [2.5, 10.0]]$.
   - `warning_polygon`: $[[1.8, 2.2], [8.2, 2.2], [8.2, 10.8], [1.8, 10.8]]$.
   - `hysteresis_buffer_m`: $0.20\text{ m}$.
   - `n_confirm`: 3 frames.
   - `n_release`: 5 frames.
   - `dwell_warning_s`: $3.0\text{ s}$.
   - `dwell_violation_s`: $6.0\text{ s}$.
   - `iso_k_speed`: $1.6\text{ m/s}$.

4. **Integration & Automated Testing**:
   - `DATASET_REGISTRY` in `scripts/download_datasets.py` MUST contain the entry `mendeley_walkway_violation`.
   - `tests/test_dataset_walkway.py` MUST verify YAML schema validity, DLT reprojection tolerance, and pipeline evaluation on the sequence.

#### Scenario: Full Pipeline Evaluation on Walkway Dataset
- **GIVEN** `configs/datasets/mendeley_walkway_violation.yaml` and `data/raw/mendeley_industrial/mendeley_walkway_violation.mp4`
- **WHEN** `python scripts/run_dataset_test.py --dataset mendeley_walkway_violation --no-display` is executed
- **THEN** all 348 frames MUST be processed with average throughput $\ge 30\text{ FPS}$
- **AND** mean latency $T_1$ MUST be $\le 40\text{ ms}$
- **AND** `annotated_mendeley_walkway_violation.mp4`, `events.jsonl`, and `summary.json` MUST be created in `data/results/mendeley_walkway_violation/`.
