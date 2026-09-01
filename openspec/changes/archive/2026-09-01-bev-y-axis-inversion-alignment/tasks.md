# Tasks: BEV Y-Axis Presentation Alignment

**Change ID:** `bev-y-axis-inversion-alignment`  
**Status:** COMPLETED  

---

### Phase 1: Presentation Layer Coordinate Projection
- [x] 1.1 Invert Y-axis mapping in `DualVisualizer._world_to_bev` in `src/utils/visualizer.py`
- [x] 1.2 Update velocity vector endpoint calculation in `DualVisualizer.render_bev` to project via `_world_to_bev`
- [x] 1.3 Adjust metric grid text label coordinates in `DualVisualizer._precompute_bev_background`

### Phase 2: Unit Testing & Verification
- [x] 2.1 Add unit tests in `tests/test_visualizer.py` for depth inversion ($v_{\text{far}} < v_{\text{near}}$) and velocity vector alignment
- [x] 2.2 Run full test suite (`pytest`) to guarantee 100% pass rate (168/168 passed)

### Phase 3: Verification & Archival
- [x] 3.1 Verify `mendeley_industrial` dataset test
- [x] 3.2 Promote capability spec to `openspec/specs/` and archive change
