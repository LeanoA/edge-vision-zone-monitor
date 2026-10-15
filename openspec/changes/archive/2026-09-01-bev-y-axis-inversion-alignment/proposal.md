# Proposal: BEV Y-Axis Orientation Alignment

**Change ID:** `bev-y-axis-inversion-alignment`  
**Date:** 2026-09-01  
**Status:** PROPOSED  

---

## 1. Context & Motivation
In surveillance and industrial spatial safety systems, Top-Down (BEV) situational maps orient the camera viewpoint at the bottom of the display looking upward into the scene.

Currently, `DualVisualizer._world_to_bev` maps $Y_w = 0$ (near camera) to row $v = 0$ (top of screen) and $Y_w = 15$ to row $v = H$, inverting the perceptual depth axis.

This proposal aligns the presentation layer coordinate projection so that the visual motion vectors, danger polygons, and tracked target positions in the BEV view match the forward-facing camera orientation.

---

## 2. Proposed Changes

1. **`src/utils/visualizer.py`:**
   - Update `_world_to_bev` to project depth with vertical inversion:
     $$v = H - 1 - \text{offset}_y - (Y_w - Y_{\min}) \cdot s_{\text{bev}}$$
   - Update velocity arrow endpoint calculation to evaluate $(u_{\text{end}}, v_{\text{end}}) = \text{world-to-bev}(\mathbf{p} + \mathbf{v} \cdot \Delta t)$.
   - Position metric grid labels intuitively (X-axis ticks at bottom, Y-axis ticks along left margin).

2. **`tests/test_visualizer.py`:**
   - Add unit tests verifying that increasing $Y_w$ decreases canvas row $v$ (moving upward on the display).
   - Verify that positive forward velocities $\dot{Y}_w > 0$ point upward in pixel space ($v_{\text{end}} < v_{\text{start}}$).
