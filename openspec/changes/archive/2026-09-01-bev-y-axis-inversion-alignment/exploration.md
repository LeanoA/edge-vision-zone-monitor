# Exploration: BEV Y-Axis Orientation Alignment

**Change ID:** `bev-y-axis-inversion-alignment`  
**Date:** 2026-09-01  
**Author:** AI Pair Programmer & Senior Architect  

---

## 1. Problem Statement

In the Top-Down Bird's Eye View (BEV) presentation layer:
- The camera baseline ($Y_w = 0\text{ m}$) was mapped to the top of the canvas ($v \approx 0$).
- The background depth ($Y_w = 15\text{ m}$) was mapped to the bottom of the canvas ($v \approx H_{\text{bev}}$).

This inverted the vertical spatial depth relative to intuitive operator perception (where the camera sits at the bottom looking forward into the workspace). Consequently, when a person walked forward toward the camera, their position on the BEV map moved toward the top of the screen instead of downward.

---

## 2. Mathematical Inversion Formulation

Given canvas height $H_{\text{bev}}$, dynamic scale $s_{\text{bev}}$, and vertical padding offset $\text{offset}_y$:

### Standard Graphics Coordinate Mapping:
$$u = \text{round}(\text{offset}_x + (X_w - X_{\min}) \cdot s_{\text{bev}})$$
$$v = \text{round}(H_{\text{bev}} - 1 - \text{offset}_y - (Y_w - Y_{\min}) \cdot s_{\text{bev}})$$

### Velocity Vector Arrow Projection:
Rather than hardcoding arbitrary pixel delta additions, the forward velocity endpoint is computed through the same transformation:
$$(u_{\text{end}}, v_{\text{end}}) = \text{world\_to\_bev}(X_w + v_x \cdot \Delta t, Y_w + v_y \cdot \Delta t)$$
with prediction horizon $\Delta t = 0.5\text{ s}$.
