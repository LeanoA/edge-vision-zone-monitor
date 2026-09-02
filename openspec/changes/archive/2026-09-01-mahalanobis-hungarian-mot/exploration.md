# Exploration: Mahalanobis Innovation Gating, Hungarian Assignment & World-Space Spatial NMS

## Current State
The multi-target tracking system in [`src/core/kalman_filter.py`](../../src/core/kalman_filter.py) uses a [`MultiTargetKalmanTracker`](../../src/core/kalman_filter.py#L579) that executes data association via `associate()`:
1. **Greedy Euclidean Distance**: Computes an $N \times M$ pairwise Euclidean distance matrix $d = \|\mathbf{p}_{\text{track}} - \mathbf{z}_{\text{det}}\|_2$.
2. **Rigid Circular Gating**: Uses a fixed scalar threshold (`gating_threshold_m = 1.0 m`) regardless of track kinematics, track age, or uncertainty.
3. **Greedy Pair Sorting**: Sorts valid pairs $(d, i, j)$ ascending and greedily assigns matches.
4. **Unconstrained Track Birth**: Every unmatched detection instantly spawns a new tentative track without checking metric proximity to active tracks or other newborn tracks in the same frame.

### Key Limitations Discovered
- **Isotropic Uncertainty Fallacy**: Treats covariance as an isotropic circle rather than an anisotropic ellipse aligned with the velocity vector.
- **Coasting Inflexibility**: When a track misses frames (coasting), its state covariance $P$ expands through $F P F^T + Q$, but the search gate stays strictly at $1.0\text{ m}$, leading to false track drops or premature ID switching during re-acquisition.
- **Suboptimal Global Matching**: Greedy assignment can match a close false positive to track $A$, forcing a legitimate detection to be dropped or assigned suboptimally to track $B$.
- **Ghost Track Proliferation**: When YOLO outputs multiple close proposals on a single person (e.g., separate feet or near-duplicate bounding boxes), unmatched proposals spawn duplicate parallel tracks ("ghost tracks").

---

## Affected Areas
- `src/core/kalman_filter.py` — Update `MultiTargetKalmanTracker.associate()` and `update()` to support Mahalanobis innovation covariance calculation ($S_i = H P_{i} H^T + R$), $\chi^2$ gating, global Hungarian assignment (`scipy.optimize.linear_sum_assignment`), and world-space spatial NMS for newborn tracks.
- `requirements.txt` — Add `scipy>=1.10.0` for high-performance Hungarian bipartite matching.
- `tests/test_kalman.py` — Add unit tests for Mahalanobis ellipsoidal gating, $\chi^2$ rejection thresholds, Hungarian assignment optimality, and spatial birth NMS.
- `docs/decisions/adr-011-mahalanobis-hungarian-mot.md` — Document architecture decision record for Bayesian validation gating and combinatorial matching.

---

## Approaches

### 1. Pure Euclidean Gating + Greedy Assignment (Current Baseline)
- **Description**: Fixed $1.0\text{ m}$ circular gate with sorted greedy matching.
- **Pros**: Zero external dependencies, extremely fast ($< 0.05\text{ ms}$).
- **Cons**: High ID switching on dense crossings; ghost tracks on duplicate detections; fails to adapt gating radius during coasting.
- **Effort**: Low (Current state).

### 2. Mahalanobis Innovation Gating + Hungarian Global Assignment + Spatial Birth NMS (Recommended)
- **Description**:
  1. Compute innovation covariance $S_i = P_{i[:2, :2]} + R$ and analytical $2 \times 2$ inverse $S_i^{-1}$.
  2. Compute squared Mahalanobis distance $d_M^2(i, j) = (\mathbf{z}_j - \hat{\mathbf{x}}_{i,pos})^T S_i^{-1} (\mathbf{z}_j - \hat{\mathbf{x}}_{i,pos})$.
  3. Form cost matrix $C \in \mathbb{R}^{N \times M}$ with gate threshold $\gamma = 9.21$ ($\chi^2_2$ at $99\%$ confidence) and $C_{i,j} = \infty$ for gated pairs.
  4. Solve bipartite matching via `scipy.optimize.linear_sum_assignment(C)`.
  5. Enforce World-Space Spatial NMS on unmatched detections ($d_{\text{birth}} \ge 0.6\text{ m}$ from existing active tracks).
- **Pros**:
  - Statistically rigorous validation gate adapting to state uncertainty and coasting duration.
  - Globally optimal multi-target association minimizing overall tracking cost.
  - Direct elimination of duplicate "ghost" tracks.
  - Preserves sub-millisecond execution time ($< 0.15\text{ ms}$ for typical factory scenes).
- **Cons**: Adds `scipy` dependency.
- **Effort**: Medium.

### 3. JPDAF (Joint Probabilistic Data Association Filter)
- **Description**: Soft association computing marginal association probabilities across all hypothesis trees.
- **Pros**: Handles high clutter and dense tracking.
- **Cons**: Significant computational overhead, combinatorial explosion, high implementation complexity, unnecessary for factory safety monitoring where personnel density is bounded.
- **Effort**: High.

---

## Recommendation
Implement **Approach 2 (Mahalanobis Innovation Gating + Hungarian Global Assignment + Spatial Birth NMS)**:
- Leverage $2 \times 2$ analytical matrix inversion for $S^{-1}$ for maximum vectorization and zero numeric instability.
- Use `scipy.optimize.linear_sum_assignment` which is implemented in C and runs in $\mathcal{O}(N^3)$ (microsecond latency for $N \le 20$ workers).
- Retain backward compatibility in `MultiTargetKalmanTracker` while exposing configurable parameters (`mahalanobis_gate_chi2: float = 9.21`, `birth_min_distance_m: float = 0.6`).

---

## Risks & Mitigations
- **Risk 1**: Degenerate or singular innovation covariance $S$.
  - *Mitigation*: $P$ and $R$ are positive definite by construction ($R \ge r_{\min} I$). We add defensive fallback to pseudoinverse or diagonal floor if $\det(S) < 10^{-12}$.
- **Risk 2**: Computational latency overhead in real-time pipeline.
  - *Mitigation*: For $N, M \le 10$, $2 \times 2$ Mahalanobis distance and `linear_sum_assignment` execute in $< 0.10\text{ ms}$, well within the $50\text{ ms}$ ISO 13855 real-time budget.
- **Risk 3**: Existing tests expecting strict Euclidean gating threshold of 1.0m.
  - *Mitigation*: Provide default $\chi^2$ gate matching expected empirical scales and update tests to validate Mahalanobis gating semantics.

---

## Ready for Proposal
**Yes**. The architecture and mathematical foundations are clear and ready to proceed to `/sdd-propose` and `/sdd-design`.
