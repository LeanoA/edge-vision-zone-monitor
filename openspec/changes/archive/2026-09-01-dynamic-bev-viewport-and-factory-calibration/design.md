# Technical Design: Dynamic BEV Auto-Scaling Viewport

**Change ID:** `dynamic-bev-viewport-and-factory-calibration`  
**Date:** 2026-09-01  
**Status:** DESIGNED  

---

## 1. Dynamic Metric Boundary Computation

Let $S_{\text{geom}}$ be the set of all $2D$ metric coordinates defining the monitored spatial footprint:
$$S_{\text{geom}} = P_{\text{danger}} \cup P_{\text{release}} \cup P_{\text{calib-world}}$$

The minimum bounding envelope is determined by:
$$X_{\min} = \min_{(x, y) \in S_{\text{geom}}} x, \quad X_{\max} = \max_{(x, y) \in S_{\text{geom}}} x$$
$$Y_{\min} = \min_{(x, y) \in S_{\text{geom}}} y, \quad Y_{\max} = \max_{(x, y) \in S_{\text{geom}}} y$$

To ensure targets and approach vectors are visible before entering the zone, a margin fraction $\alpha = 0.15$ (or at least $1.0\text{ m}$) is added:
$$W_m = \max(X_{\max} - X_{\min}, 1.0), \quad H_m = \max(Y_{\max} - Y_{\min}, 1.0)$$
$$X_{\min}^{\text{eff}} = X_{\min} - \alpha W_m, \quad X_{\max}^{\text{eff}} = X_{\max} + \alpha W_m$$
$$Y_{\min}^{\text{eff}} = Y_{\min} - \alpha H_m, \quad Y_{\max}^{\text{eff}} = Y_{\max} + \alpha H_m$$
$$\Delta X = X_{\max}^{\text{eff}} - X_{\min}^{\text{eff}}, \quad \Delta Y = Y_{\max}^{\text{eff}} - Y_{\min}^{\text{eff}}$$

---

## 2. Dynamic Scale & Coordinate Mapping

Given canvas dimensions $(W_{\text{bev}}, H_{\text{bev}})$:
$$s_{\text{bev}} = \min\left(\frac{W_{\text{bev}}}{\Delta X}, \frac{H_{\text{bev}}}{\Delta Y}\right)$$
$$\text{offset}_x = \frac{W_{\text{bev}} - \Delta X \cdot s_{\text{bev}}}{2}$$
$$\text{offset}_y = \frac{H_{\text{bev}} - \Delta Y \cdot s_{\text{bev}}}{2}$$

For any metric coordinate $(x_w, y_w)$:
$$u = \text{offset}_x + (x_w - X_{\min}^{\text{eff}}) \cdot s_{\text{bev}}$$
$$v = \text{offset}_y + (y_w - Y_{\min}^{\text{eff}}) \cdot s_{\text{bev}}$$

---

## 3. Dynamic Metric Grid Generation

The BEV background precomputation iterates over integer metric intervals:
$$\text{step}_m = \begin{cases} 1.0\text{ m} & \text{if } \max(\Delta X, \Delta Y) \le 12\text{ m} \\ 2.0\text{ m} & \text{if } 12\text{ m} < \max(\Delta X, \Delta Y) \le 25\text{ m} \\ 5.0\text{ m} & \text{if } \max(\Delta X, \Delta Y) > 25\text{ m} \end{cases}$$

Lines and text labels are rendered at each metric tick within $[X_{\min}^{\text{eff}}, X_{\max}^{\text{eff}}]$ and $[Y_{\min}^{\text{eff}}, Y_{\max}^{\text{eff}}]$.
