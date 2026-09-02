# SDD Change: mahalanobis-hungarian-mot
Created: 2026-09-01
Status: Initialized (Fase 1 /sdd-new completada)
Mode: Interactive

## Scope
- Implement Mahalanobis distance innovation covariance gating ($\chi^2$ test).
- Implement global combinatorial association with the Hungarian algorithm (Munkres / scipy linear_sum_assignment).
- Implement world-space spatial NMS for track birth suppression ($d < 0.6\text{ m}$).
- Validate against multi-target tracking datasets (e.g. `openvino_people`, `pets2009_s2_l1`).
