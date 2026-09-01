# Capability Specification: BEV Y-Axis Presentation Orientation

**Capability:** `bev-y-axis-orientation`  
**Domain:** Visualization & Operator Interface  

---

## 1. Overview
Ensures that the Top-Down Bird's Eye View (BEV) rendering canvas displays the scene with natural forward-facing perspective: the camera baseline is located at the bottom of the screen, and increasing metric distance ($+Y_w$) extends toward the top of the screen.

---

## 2. Requirements & Scenarios

### Requirement 1: Inverted Vertical Pixel Mapping
The transformation `_world_to_bev(X_w, Y_w)` MUST map smaller $Y_w$ values to larger canvas row indices ($v \approx H_{\text{bev}}$) and larger $Y_w$ values to smaller canvas row indices ($v \approx 0$).

#### Scenario 1.1: Relative Depth Comparison
- **Given** two world coordinates $P_{\text{near}} = (5.0, 1.0)\text{ m}$ and $P_{\text{far}} = (5.0, 10.0)\text{ m}$
- **When** mapped to canvas coordinates $(u_{\text{near}}, v_{\text{near}})$ and $(u_{\text{far}}, v_{\text{far}})$
- **Then** $v_{\text{far}} < v_{\text{near}}$ (the farther point is drawn higher on the screen).

### Requirement 2: Coherent Velocity Vector Direction
Velocity vectors with positive forward velocity ($\dot{Y}_w > 0$) MUST point upward on the screen ($v_{\text{end}} < v_{\text{start}}$).

#### Scenario 2.1: Forward Walking Target
- **Given** a target at $(5.0, 4.0)\text{ m}$ moving with velocity $(0.0, 1.5)\text{ m/s}$
- **When** the velocity arrow endpoint is computed
- **Then** $u_{\text{end}} = u_{\text{start}}$ and $v_{\text{end}} < v_{\text{start}}$.
