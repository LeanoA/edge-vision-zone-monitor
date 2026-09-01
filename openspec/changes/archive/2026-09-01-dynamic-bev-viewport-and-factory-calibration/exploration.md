# Exploration: Dynamic BEV Viewport & Factory Ground Calibration

**Change ID:** `dynamic-bev-viewport-and-factory-calibration`  
**Date:** 2026-09-01  
**Author:** AI Pair Programmer & Senior Architect  

---

## 1. Problem Identification

1. **Fixed Viewport Clipping in DualVisualizer:**
   `DualVisualizer` in `src/utils/visualizer.py` assumes a fixed $600 \times 600\text{ px}$ canvas with `bev_scale = 100.0 px/m` and origin at $(0, 0)$.
   - This hardcodes the visible area to $0.0\text{ m} \le X_w \le 6.0\text{ m}$ and $0.0\text{ m} \le Y_w \le 6.0\text{ m}$.
   - For real industrial shop floors (e.g. `mendeley_industrial` $10\text{m} \times 15\text{m}$, or `pets2009_s2_l1` $12\text{m} \times 20\text{m}$), points with $Y_w > 6\text{m}$ are clipped outside the bottom canvas edge.

2. **Ground Plane Calibration Alignment for Mendeley Industrial:**
   In `configs/datasets/mendeley_industrial.yaml`, the danger zone coordinates must align precisely with the metal stamping / machine tool station on the factory floor so that when the operator approaches the machine in `mendeley_unauthorized_intervention.mp4`, their ground track $(X_w, Y_w)$ is visible stepping directly toward and into the safety zone.

---

## 2. Proposed Architectural Solution

1. **Dynamic Bounding Box & Scale Computation:**
   `DualVisualizer` will compute or receive `world_bounds: Optional[Tuple[float, float, float, float]]` (defaulting to bounding box encompassing calibrated world points, danger polygon, and release polygon + padding margin):
   $$\text{width}_m = X_{\max} - X_{\min}, \quad \text{height}_m = Y_{\max} - Y_{\min}$$
   $$\text{scale} = \min\left(\frac{W_{\text{bev}} - 2 \cdot \text{margin}}{\text{width}_m}, \frac{H_{\text{bev}} - 2 \cdot \text{margin}}{\text{height}_m}\right)$$
   $$\text{offset}_x = \frac{W_{\text{bev}} - \text{width}_m \cdot \text{scale}}{2}, \quad \text{offset}_y = \frac{H_{\text{bev}} - \text{height}_m \cdot \text{scale}}{2}$$

2. **Coordinate Mapping:**
   $$u = \text{offset}_x + (X_w - X_{\min}) \cdot \text{scale}$$
   $$v = \text{offset}_y + (Y_w - Y_{\min}) \cdot \text{scale}$$

3. **Dynamic Metric Grid Rendering:**
   Draw major 1-meter or 2-meter grid lines spanning $[X_{\min}, X_{\max}] \times [Y_{\min}, Y_{\max}]$ with explicit meter labels.

4. **Factory Calibration Profile Update:**
   Tune `configs/datasets/mendeley_industrial.yaml` so the machine envelope and walkway boundaries match the visual perspective of the shop floor.
