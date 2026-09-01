# Tasks: Dynamic BEV Auto-Scaling Viewport & Factory Ground Calibration

**Change ID:** `dynamic-bev-viewport-and-factory-calibration`  
**Status:** COMPLETED  

---

### Phase 1: Visualizer Dynamic Bounds Implementation
- [x] 1.1 Implement dynamic bounding box, scale, and offset computation in `DualVisualizer` (`src/utils/visualizer.py`)
- [x] 1.2 Implement dynamic metric grid and label rendering spanning arbitrary $[X_{\min}, X_{\max}] \times [Y_{\min}, Y_{\max}]$ in `DualVisualizer`
- [x] 1.3 Update `_world_to_bev` to map world coordinates through dynamic scale and offsets

### Phase 2: Calibration & Profile Tuning
- [x] 2.1 Calibrate `configs/datasets/mendeley_industrial.yaml` danger polygon and world limits for the factory workshop

### Phase 3: Unit Testing & Verification
- [x] 3.1 Update and add unit tests in `tests/test_visualizer.py` verifying dynamic auto-scaling and grid generation
- [x] 3.2 Run full test suite (`pytest`) to confirm 100% pass rate (167/167 passed)
- [x] 3.3 Execute `mendeley_industrial` dataset test and verify BEV rendering
