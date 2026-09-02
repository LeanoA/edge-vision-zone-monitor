# Proposal: Mahalanobis Innovation Gating, Hungarian Matching & Spatial NMS (`kalman-tracking`)

## Intent
Replace the naive greedy Euclidean data association in `MultiTargetKalmanTracker` with statistically grounded Mahalanobis innovation covariance gating ($\chi^2_2$), globally optimal Hungarian bipartite matching, and world-space spatial NMS on track birth to eliminate ID switching, ghost tracks, and coasting re-acquisition failures in crowded industrial scenes.

## Scope

### In Scope
- **Mahalanobis Validation Gate**: Compute innovation covariance $S = H P_{k|k-1} H^T + R$ and quadratic distance $d_M^2 = \tilde{\mathbf{y}}^T S^{-1} \tilde{\mathbf{y}}$ with configurable $\chi^2_2$ threshold ($\gamma = 9.21$ for $99\%$ confidence).
- **Hungarian Global Assignment**: Form bounded cost matrix $C \in \mathbb{R}^{N \times M}$ and solve globally minimal bipartite matching via `scipy.optimize.linear_sum_assignment`.
- **World-Space Spatial Birth NMS**: Enforce minimum distance threshold ($d_{\text{birth}} \ge 0.6\text{ m}$) preventing duplicate "ghost track" initialization from near-duplicate YOLO detections.
- **Dependency Integration**: Add `scipy>=1.10.0` to project dependencies.

### Out of Scope
- Multi-camera joint track fusion or visual appearance Re-ID feature embeddings.
- Non-linear motion models (Unscented / Extended Kalman Filters).

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `kalman-tracking`: Modifies spatial data association requirements to use Mahalanobis innovation gating ($\chi^2$), optimal Hungarian assignment, and spatial birth NMS.

## Approach
1. Expose `innovation_covariance(R=None) -> np.ndarray` from `MetricKalmanFilter` / `Track`.
2. Update `MultiTargetKalmanTracker.associate()` to construct Mahalanobis cost matrix with $\chi^2$ gate mask.
3. Solve optimal assignment with `scipy.optimize.linear_sum_assignment`.
4. Filter newborn tracks using pairwise spatial distance against existing active tracks ($d \ge 0.6\text{ m}$).

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/core/kalman_filter.py` | Modified | Update `MetricKalmanFilter`, `Track`, and `MultiTargetKalmanTracker` association & birth logic |
| `requirements.txt` | Modified | Add `scipy>=1.10.0` |
| `tests/test_kalman.py` | Modified | Add unit tests for Mahalanobis gate, Hungarian matching, and birth NMS |
| `docs/decisions/adr-011-mahalanobis-hungarian-mot.md` | New | Architecture decision record for Bayesian validation gating |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Numerical singularity in $S$ inversion | Low | Analytical $2\times2$ inversion with positive definite floor and pseudoinverse fallback |
| Association latency spike | Low | $\mathcal{O}(N^3)$ Hungarian runs in $< 0.10\text{ ms}$ for factory scene target counts ($N \le 20$) |

## Rollback Plan
Revert commit `feat(tracking): implement mahalanobis gating and hungarian matching` to restore greedy Euclidean association.

## Dependencies
- `scipy>=1.10.0` (`scipy.optimize.linear_sum_assignment`)

## Success Criteria
- [ ] Mahalanobis gating rejects detections outside $\chi^2_2 \le 9.21$ ($99\%$ confidence).
- [ ] Hungarian assignment achieves globally optimal biunívoc match on crossing trajectories without greedy bias.
- [ ] Newborn tracks within $0.6\text{ m}$ of active tracks are suppressed.
- [ ] 100% of unit tests pass in `tests/test_kalman.py` with mean association latency $< 0.15\text{ ms}$.
- [ ] Full test suite (180+ tests) remains green.
