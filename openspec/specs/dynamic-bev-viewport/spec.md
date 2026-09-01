# Capability Specification: Dynamic BEV Auto-Scaling Viewport

**Capability:** `dynamic-bev-viewport`  
**Domain:** Visualization & Operator Interface  

---

## 1. Overview
Ensures that the Top-Down Bird's Eye View (BEV) rendering canvas automatically auto-scales to frame any arbitrary ground plane geometry, danger zone, and tracked object without viewport clipping or manual pixel-scale adjustments.

---

## 2. Requirements & Scenarios

### Requirement 1: Automatic Metric Extent Ingestion
`DualVisualizer` MUST dynamically infer the bounding coordinates $[X_{\min}, Y_{\min}, X_{\max}, Y_{\max}]$ from the active spatial FSM polygons and homography configuration when explicit `world_bounds` are omitted.

#### Scenario 1.1: Large Industrial Bay ($15\text{m} \times 20\text{m}$)
- **Given** homography world calibration spanning up to $(15.0, 20.0)\text{ m}$
- **When** `DualVisualizer` is initialized with a $(600, 600)$ pixel canvas
- **Then** the computed `bev_scale` MUST scale down ($s \approx 25\text{ px/m}$) to contain the full $20\text{m}$ span within $600\text{ px}$ with margin.

#### Scenario 1.2: Compact Workcell ($4\text{m} \times 4\text{m}$)
- **Given** homography world calibration spanning $(4.0, 4.0)\text{ m}$
- **When** `DualVisualizer` is initialized with a $(600, 600)$ pixel canvas
- **Then** `bev_scale` MUST scale up ($s \approx 100\text{ px/m}$) to utilize the available canvas resolution.

### Requirement 2: Metric World-to-Canvas Mapping
All metric positions $(X_w, Y_w)$, danger polygons, release bands, and velocity vectors MUST be mapped into the visible canvas space without clipping.

#### Scenario 2.1: Target at Deep Coordinate
- **Given** a tracked person at $(X_w, Y_w) = (5.0, 14.0)\text{ m}$ in a $15\text{m}$ deep workshop
- **When** `render_bev` is executed
- **Then** the canvas coordinates $(u, v)$ MUST be strictly inside $[0, W_{\text{bev}}] \times [0, H_{\text{bev}}]$.
