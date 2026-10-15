# Specification Delta: Metric Kalman Tracking (`kalman-tracking`)

## MODIFIED Requirements

### Requirement: Multi-Target Lifecycle Management and Optimal Bipartite Association
The `MultiTargetKalmanTracker` MUST manage simultaneous tracking of multiple targets across consecutive video frames using globally optimal bipartite matching and Bayesian validation gating:
1. **Validation Gating**: Candidate detections MUST be evaluated against each active track using the squared Mahalanobis distance with innovation covariance $S_i = P_{i[:2, :2]} + R$. Detections exceeding the validation gate threshold $\gamma = 9.210$ ($\chi^2$ distribution with 2 degrees of freedom at $99\%$ confidence) MUST be excluded from association with track $i$.
2. **Global Assignment**: Association between active track predictions and incoming detections MUST be computed globally using the Hungarian algorithm (Munkres / `scipy.optimize.linear_sum_assignment`), minimizing the sum of squared Mahalanobis distances across all assigned pairs.
3. **World-Space Spatial Birth Non-Maximum Suppression**: Unmatched detections MUST NOT instantiate new tracks if their metric Euclidean distance to any existing active or confirmed track is less than $d_{\text{birth-min}} = 0.6\text{ m}$, nor if they are within $0.6\text{ m}$ of another track spawned in the same frame.

#### Scenario: Mahalanobis validation gate rejects statistically incompatible detections
- **GIVEN** an active track with state covariance $P_{pos} = \text{diag}([0.01, 0.01])$ and measurement noise $R = \text{diag}([0.05, 0.05])$ ($S = \text{diag}([0.06, 0.06])$)
- **WHEN** a detection arrives with innovation residue $\|\tilde{\mathbf{y}}\|_2 = 0.8\text{ m}$ ($d_M^2 = 0.8^2 / 0.06 = 10.67 > 9.210$)
- **THEN** the validation gate SHALL reject the candidate detection
- **AND** the track SHALL NOT update with this measurement and SHALL increment its missed frame counter.

#### Scenario: Hungarian global assignment resolves trajectory crossings without ID swap
- **GIVEN** Track 1 at $(2.0, 3.0)$ moving right at $+1.0\text{ m/s}$ and Track 2 at $(2.2, 3.0)$ moving left at $-1.0\text{ m/s}$
- **AND** incoming detections at $(2.1, 3.0)$ and $(2.1, 3.0)$
- **WHEN** `tracker.update()` executes Hungarian bipartite assignment
- **THEN** the assignment SHALL minimize global cost according to predicted velocity vectors
- **AND** Track 1 and Track 2 SHALL retain their distinct identities without ID switching.

#### Scenario: World-space spatial birth NMS suppresses duplicate limb detections
- **GIVEN** an active confirmed track at position $(3.0, 4.0)$
- **AND** two candidate detections in the frame: Detection A at $(3.0, 4.0)$ (matched to track) and Detection B at $(3.15, 4.0)$ ($d = 0.15\text{ m} < 0.6\text{ m}$, duplicate proposal from second leg)
- **WHEN** `tracker.update()` processes unmatched detections
- **THEN** Detection B SHALL be suppressed by spatial birth NMS
- **AND** NO new tentative track SHALL be spawned for Detection B.

#### Scenario: Spatial birth NMS deduplicates simultaneous newborn proposals
- **GIVEN** an empty scene with no active tracks
- **AND** two close detections arriving simultaneously at $(1.0, 1.0)$ and $(1.2, 1.0)$ ($d = 0.2\text{ m} < 0.6\text{ m}$)
- **WHEN** `tracker.update()` instantiates newborn tracks
- **THEN** exactly 1 new track SHALL be created for the first detection
- **AND** the second detection SHALL be suppressed by spatial birth NMS.

#### Scenario: Association latency remains strictly under real-time budget
- **GIVEN** 10 active tracks and 10 candidate detections
- **WHEN** `tracker.associate()` executes Mahalanobis gating and Hungarian bipartite matching
- **THEN** the total execution time SHALL be strictly less than $0.15\text{ ms}$.
