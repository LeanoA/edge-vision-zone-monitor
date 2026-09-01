# Technical Design: BEV Y-Axis Presentation Alignment

**Change ID:** `bev-y-axis-inversion-alignment`  
**Date:** 2026-09-01  
**Status:** DESIGNED  

---

## 1. Mathematical Formulation

Let the canvas have dimensions $(W_{\text{bev}}, H_{\text{bev}})$ in pixels.

For any ground coordinate $(X_w, Y_w) \in [X_{\min}, X_{\max}] \times [Y_{\min}, Y_{\max}]$:

$$u(X_w) = \text{round}\left(\text{offset}_x + (X_w - X_{\min}) \cdot s_{\text{bev}}\right)$$
$$v(Y_w) = \text{round}\left(H_{\text{bev}} - 1 - \text{offset}_y - (Y_w - Y_{\min}) \cdot s_{\text{bev}}\right)$$

### Properties:
- When $Y_w = Y_{\min}$ (closest to camera): $v = H_{\text{bev}} - 1 - \text{offset}_y$ (bottom of canvas).
- When $Y_w = Y_{\max}$ (deepest into scene): $v = \text{offset}_y$ (top of canvas).
- When $X_w$ increases (moving right): $u$ increases (moves right).

---

## 2. Velocity Arrow Rendering

For a track at position $\mathbf{p} = [X_w, Y_w]$ with velocity $\mathbf{v} = [v_x, v_y]$:

$$(u_{\text{start}}, v_{\text{start}}) = \text{world\_to\_bev}(X_w, Y_w)$$
$$(u_{\text{end}}, v_{\text{end}}) = \text{world\_to\_bev}(X_w + v_x \cdot \Delta t, Y_w + v_y \cdot \Delta t)$$

with forward projection horizon $\Delta t = 0.5\text{ s}$.

If $\|\mathbf{v}\| > 0.05\text{ m/s}$, an arrow is rendered from $(u_{\text{start}}, v_{\text{start}})$ to $(u_{\text{end}}, v_{\text{end}})$.
