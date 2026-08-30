# Specification: Synchronized Dual-Stream Visualization (`dual-visualization`)

## Purpose
The `dual-visualization` capability provides synchronized dual rendering combining perspective camera overlays ($P_{\text{danger}}$, $P_{\text{release}}$ reprojected via $H^{-1}$, skeletons, and banners) with an orthogonal metric bird's-eye view (BEV canvas at 100 px/m rendering grid, machine footprint, danger/release zones, tracks, velocity vectors, and dwell times). It supports side-by-side and picture-in-picture (PiP) compositing.

## Requirements

### Requirement: Perspective Camera Overlay Rendering
The `DualVisualizer` MUST render an annotated perspective view on the input camera frame:
1. Reproject metric hazard polygons $P_{\text{danger}}$ and $P_{\text{release}}$ into image space using $H^{-1}$ and draw colored polygon boundaries.
2. Draw detected bounding boxes, skeleton links, and ground anchor markers.
3. Render an industrial status banner indicating `SafetyState`, trip status, track count, and pipeline latency $t_1$.

#### Scenario: Inverse homography zone reprojection
- **GIVEN** calibrated inverse homography $H^{-1}$ and metric polygons $P_{\text{danger}}$ and $P_{\text{release}}$
- **WHEN** `visualizer.render_perspective(frame, pipeline_result)` executes
- **THEN** zone vertices SHALL be projected to pixel space via $H^{-1}$ and drawn on the frame.

#### Scenario: Status banner trip assertion styling
- **GIVEN** `PipelineResult` with `safety_output.trip == True`
- **WHEN** perspective overlay is rendered
- **THEN** the status banner SHALL display red alert styling with text indicating trip assertion.

---

### Requirement: Metric Bird's-Eye View (BEV) Orthogonal Rendering
The `DualVisualizer` MUST generate an orthogonal top-down canvas ($Z_w = 0$):
1. Scale canvas at $100\text{ px/m}$ (1 cm per pixel) covering monitored factory area.
2. Render 1-meter major grid lines and distance markers.
3. Draw machine footprint, danger zone $P_{\text{danger}}$, and release zone $P_{\text{release}}$.
4. Render each active track at $(X_w, Y_w)$ with a color keyed by `track_id`.
5. Render a velocity vector arrow scaled to instantaneous speed $\|\vec{v}\|_2$.
6. Render target labels showing ID, speed ($v\text{ m/s}$), and dwell time ($t_{\text{dwell}}\text{ s}$).

#### Scenario: Metric canvas scaling and grid rendering
- **GIVEN** a $6.0\text{ m} \times 6.0\text{ m}$ monitored ground plane
- **WHEN** `visualizer.render_bev(pipeline_result)` executes
- **THEN** the canvas dimensions SHALL be $600\times600$ pixels with 100-pixel grid lines.

#### Scenario: Track position and velocity rendering
- **GIVEN** an active track at $(2.5, 3.0)\text{ m}$ with velocity $\vec{v} = [1.2, 0.0]\text{ m/s}$
- **WHEN** BEV canvas is generated
- **THEN** a marker SHALL be drawn at canvas coordinates $(250, 300)$ with a 1.2 m/s velocity arrow and telemetry label.

---

### Requirement: Multi-Stream View Compositing
The `DualVisualizer` MUST composite perspective and BEV views into a unified image:
1. `SIDE_BY_SIDE`: Perspective frame and BEV canvas positioned side-by-side with matched heights.
2. `PICTURE_IN_PICTURE` (PiP): BEV canvas scaled and overlaid as an inset with a contrasting border.

#### Scenario: Side-by-side view compositing
- **GIVEN** a perspective frame and BEV canvas
- **WHEN** `visualizer.composite(perspective, bev, layout="SIDE_BY_SIDE")` executes
- **THEN** the composite frame SHALL display both views horizontally adjacent.

#### Scenario: Picture-in-picture view compositing
- **GIVEN** a perspective frame and BEV canvas
- **WHEN** `visualizer.composite(perspective, bev, layout="PIP")` executes
- **THEN** the composite frame SHALL embed the scaled BEV canvas in the designated corner.

---

### Requirement: Headless Mode and Rendering Performance
The `DualVisualizer` MUST support headless mode bypassing drawing when displays are disabled. When active, rendering MUST complete within $\le 10.0\text{ ms}$.

#### Scenario: Headless rendering bypass
- **GIVEN** `DualVisualizer(headless=True)`
- **WHEN** `visualizer.render(frame, pipeline_result)` executes
- **THEN** drawing SHALL be bypassed and execution time SHALL be $< 0.1\text{ ms}$.

#### Scenario: Rendering latency ceiling
- **GIVEN** enabled visualizer with side-by-side compositing
- **WHEN** `visualizer.render(frame, pipeline_result)` executes
- **THEN** execution duration SHALL NOT exceed $10.0\text{ ms}$.
