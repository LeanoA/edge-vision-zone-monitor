# Proposal: Dynamic BEV Viewport & Factory Ground Calibration

**Change ID:** `dynamic-bev-viewport-and-factory-calibration`  
**Date:** 2026-09-01  
**Status:** PROPOSED  

---

## 1. Context & Motivation

In surveillance and industrial plant settings, monitored areas vary widely in physical dimensions—from small $4\text{m} \times 4\text{m}$ machine cells to $15\text{m} \times 20\text{m}$ factory bays or outdoor plazas.

`DualVisualizer` previously assumed a fixed $6\text{m} \times 6\text{m}$ viewport at $100\text{ px/m}$, which caused targets and hazard zones located beyond 6 meters to be clipped outside the right and bottom edges of the Top-Down Bird's Eye View (BEV) canvas.

This proposal introduces automatic dynamic viewport bounds estimation in `DualVisualizer`, ensuring that any configured ground plane geometry and restricted zone is automatically framed, centered, and rendered with metric grid lines and velocity vectors.

---

## 2. Proposed Changes

1. **`src/utils/visualizer.py`:**
   - Enhance `DualVisualizer` to accept optional `world_bounds: Optional[Tuple[float, float, float, float]]` or automatically infer `[X_min, Y_min, X_max, Y_max]` from the union of:
     * Homography calibration world points
     * Spatial FSM Danger Polygon
     * Spatial FSM Release / Warning Polygon
   - Calculate dynamic `bev_scale`, `offset_x`, and `offset_y` so the scene fills the configured canvas size (e.g. $600 \times 600\text{ px}$) with a 10% safety margin.
   - Render metric grid lines dynamically spanning the active world coordinate range.

2. **`configs/datasets/mendeley_industrial.yaml`:**
   - Adjust ground plane coordinates and danger zone to frame the workshop machine station where the operator walks.

3. **`tests/test_visualizer.py`:**
   - Add unit tests validating dynamic auto-scaling, world-to-BEV coordinate transformations across large ($20\text{m} \times 20\text{m}$) and small ($3\text{m} \times 3\text{m}$) ground geometries.

---

## 3. Impact Assessment
- **Zero Core Changes:** Modifies only visualization and dataset configuration.
- **Latency Invariant:** Dynamic bounds and static grid are pre-computed once during visualizer initialization with $O(1)$ runtime overhead per frame.
