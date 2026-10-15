# Design: Mahalanobis Innovation Gating, Hungarian Matching & Spatial NMS (`kalman-tracking`)

## Technical Approach
Upgrade the data association engine of `MultiTargetKalmanTracker` from naive Euclidean greedy nearest-neighbor to Bayesian validation gating and globally optimal assignment:
1. **Innovation Covariance Estimation**: Compute $S_i = H P_{i|k-1} H^T + R = P_{i[:2, :2]} + R \in \mathbb{R}^{2 \times 2}$ for every active track $i$, with fast analytical $2 \times 2$ determinant inversion and positive-definite floor protection.
2. **Mahalanobis Validation Gate**: For every track-detection pair $(i, j)$, evaluate the squared Mahalanobis distance:
   $$d_M^2(i, j) = (\mathbf{z}_j - \hat{\mathbf{x}}_{i,pos})^T S_i^{-1} (\mathbf{z}_j - \hat{\mathbf{x}}_{i,pos})$$
   Apply a statistical gate $\gamma = 9.210$ (the 99th percentile of a $\chi^2$ distribution with 2 degrees of freedom, $\chi^2_2(0.99)$).
3. **Global Combinatorial Matching**: Construct cost matrix $C \in \mathbb{R}^{N \times M}$ where $C_{i, j} = d_M^2(i, j)$ if $d_M^2(i, j) \le \gamma$ else $10^5$. Solve the optimal bipartite matching problem via `scipy.optimize.linear_sum_assignment(C)` and reject assigned pairs where $C_{i, j} > \gamma$.
4. **World-Space Spatial Birth NMS**: Before instantiating a new tentative track for an unmatched detection $\mathbf{z}_j$, verify that $\min_{t \in \text{active}} \|\mathbf{z}_j - \mathbf{p}_t\|_2 \ge d_{\text{birth-min}}$ ($0.6\text{ m}$) and that it is not within $0.6\text{ m}$ of any other track spawned in the same frame.

---

## Architecture Decisions

| Decision | Choice | Alternatives Considered | Rationale |
| :--- | :--- | :--- | :--- |
| **Inversion of $S_i$** | Analytical $2\times2$ Cramer's rule inversion | `np.linalg.inv`, `scipy.linalg.inv` | $2\times2$ analytical inversion takes $< 30\text{ ns}$, has zero heap allocations, and allows explicit zero-determinant conditioning checks. |
| **Bipartite Assignment** | `scipy.optimize.linear_sum_assignment` | Custom Python Munkres / Jonker-Volgenant, Greedy sorted pairs | SciPy's implementation is written in C ($\mathcal{O}(N^3)$), robustly tested, and executes in $< 0.05\text{ ms}$ for $N \le 20$. |
| **Gating Criterion** | Squared Mahalanobis distance with $\chi^2_2(0.99) = 9.21$ | Fixed Euclidean radius, Normalized Innovation Squared (NIS) batch | Adapts search window to velocity uncertainty and coasting history ($P_{k|k-1}$ expansion), providing anisotropic ellipsoidal validation. |
| **Birth Suppression** | Metric World-Space Spatial NMS ($0.6\text{ m}$) | Pixel-space 2D IoU NMS, Confidence thresholding | Ground-plane metric distance directly models physical human body radius, suppressing duplicate limbs/boxes regardless of camera perspective distortion. |

---

## Data Flow

```
Detections z_j (PositionEstimate / Coordinates)
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│ MultiTargetKalmanTracker.update()                      │
│                                                        │
│ 1. Track Prediction: x_i, P_i for all active tracks    │
│ 2. Innovation Covariance: S_i = P_i[:2, :2] + R        │
│ 3. Cost Matrix Construction:                           │
│      d_M^2(i,j) = y_ij^T * S_i^-1 * y_ij               │
│      C_ij = d_M^2(i,j) if d_M^2 <= 9.21 else 10^5      │
│ 4. Hungarian Assignment:                               │
│      row_ind, col_ind = linear_sum_assignment(C)      │
│ 5. Gating Filter: matches = [(i,j) if C_ij <= 9.21]    │
│ 6. Kalman Updates for matched tracks                   │
│ 7. Coasting (mark_missed) for unmatched tracks         │
│ 8. World-Space Spatial NMS on unmatched detections     │
│      Spawn new Track only if min_dist >= 0.6m          │
└────────────────────────────────────────────────────────┘
                 │
                 ▼
Active Confirmed & Coasting Tracks
```

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `requirements.txt` | Modify | Add `scipy>=1.10.0` |
| `src/core/kalman_filter.py` | Modify | Implement `innovation_covariance`, Mahalanobis cost matrix, Hungarian assignment, and spatial birth NMS in `MultiTargetKalmanTracker` |
| `tests/test_kalman.py` | Modify | Add unit tests for Mahalanobis gating, $\chi^2$ threshold rejection, Hungarian optimality on trajectory crossings, and birth suppression |
| `openspec/specs/kalman-tracking/spec.md` | Modify | Update capability spec with Mahalanobis gating, Hungarian assignment, and birth NMS requirements |

---

## Interfaces / Contracts

```python
class MultiTargetKalmanTracker:
    def __init__(
        self,
        dt: float = 0.0333,
        gating_threshold_m: float = 1.0,  # Retained for backward compat / fallback
        max_missed: int = 5,
        n_init: int = 2,
        q_pos: float = 0.01,
        q_vel: float = 0.1,
        r_pos: float = 0.05,
        mahalanobis_gate_chi2: float = 9.210,  # 99% confidence for chi2(2)
        birth_min_distance_m: float = 0.6,    # Spatial NMS radius
    ) -> None: ...

    def compute_mahalanobis_cost_matrix(
        self,
        active_tracks: List[Track],
        detections: np.ndarray,
        r_mat: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Compute (N, M) Mahalanobis squared distance matrix and boolean validity gate mask."""
        ...

    def associate(
        self,
        track_positions: Union[np.ndarray, Sequence[Sequence[float]]],
        detections: Union[np.ndarray, Sequence[Sequence[float]]],
        active_tracks: Optional[List[Track]] = None,
        r_mat: Optional[np.ndarray] = None,
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """Perform optimal bipartite Hungarian association with Mahalanobis validation gating."""
        ...
```

---

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | $\chi^2_2$ Gating Threshold | Verify detection at $d_M^2 > 9.21$ is rejected even if within $1.0\text{ m}$ Euclidean distance. |
| Unit | Anisotropic Uncertainty Orientation | Verify elongated covariance ellipse accepts forward velocity incursion while rejecting perpendicular jump. |
| Unit | Hungarian Global Assignment Optimality | Simulate crossing trajectories where greedy matching would fail and verify Hungarian preserves correct IDs. |
| Unit | World-Space Spatial Birth NMS | Feed two duplicate detections at $(1.0, 1.0)$ and $(1.1, 1.0)$ ($d = 0.1\text{ m} < 0.6\text{ m}$) and verify only 1 track is spawned. |
| Performance | Association Latency Benchmark | Verify $10 \times 10$ target-detection Hungarian assignment takes $< 0.10\text{ ms}$. |
| Regression | Full Test Suite | Ensure all 180 existing tests continue to pass. |

---

## Threat Matrix
`N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.`

## Migration / Rollout
No migration required. The updated tracker maintains full backward compatibility with `PositionEstimate` and raw coordinate tuple inputs.
