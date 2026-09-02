# Synthetic Benchmark Video Generation Architecture

## Overview
The **Industrial Vision Safety Guard** incorporates a deterministic, high-fidelity synthetic benchmark video generator (`src/utils/synthetic_generator.py`). It produces perspective-calibrated test streams with exact metric ground-truth kinematics, soft contact shadows, depth-ordered physical occlusions, single-identity walking gait cycles, and ISO 13855 safety zones.

---

## Technical Evolution: Before vs. After (Storytelling)

| Metric / Aspect | Before (Vector Primitives) | Intermediate (Mixed Candidates) | Final (Single-Identity Pinhole Compositing) | Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Actor Representation** | Flat 2D vector shapes (`cv2.line`, `cv2.rectangle`) | Multi-subject segmented crops (variable clothing) | **Single-Identity Tracklet** normalized on $160 \times 320\text{ RGBA}$ canonical canvas | 100% appearance & texture stability (no clothing jumps) |
| **Perspective Scaling** | Linear depth delta ($h \in [90, 300]\text{ px}$) | Pinhole scale ($h \in [240, 480]\text{ px}$) | **Calibrated Pinhole Scale** ($h = \frac{480}{1.0 + 0.165 \cdot Y}$) | Preserves anthropomorphic scale across all $Y \in [0.5, 5.5]\text{ m}$ |
| **Ground Contact Realism** | Flat solid ellipse | Directional blurred shadow | **Gaussian Soft Shadow** + Bottom-aligned baseline | Natural grounding without edge halos or vertical jitter |
| **YOLO Detection Rate (Seq A)** | **0.0%** (0 / 180 frames) | 100.0% (180 / 180 frames) | **100.0%** (180 / 180 frames) | Complete stream detection coverage |
| **YOLO Mean Confidence** | **0.00** | 0.816 | **0.835** (Seq A) / **0.820** (Seq B) / **0.861** (Seq C) | Maximum spatial feature activation & tracking stability |
| **UI HUD & Text Overlays** | Overlapping at $y=50\text{ px}$ | Overlapping top banner | **Decoupled HUD**: Top Safety Banner (56px) + Bottom Simulation Badge | Ultra-crisp, high-contrast, zero-overlap readability |
| **Occlusion Tracking (Seq B)** | N/A (undetected) | 100.0% tracked | **100.0%** (180 / 180 frames tracked) | Lower-limb coasting validation under pallet barrier |
| **Dwell Violation Trip (Seq C)** | N/A (undetected) | 100.0% tracked | **100.0%** (300 / 300 frames tracked) | Strict ISO 13855 dwell violation trip at $t \ge 5.0\text{s}$ |

---

## Key Architectural Solutions

### 1. Single-Identity Tracklet Extraction & Normalization
To prevent visual flickering or clothing variations during gait cycling, [`scripts/prepare_sprites.py`](../../scripts/prepare_sprites.py) tracks a single continuous individual across 35 frames:
1. **Continuous Spatial Tracking:** IoU-based single-target tracking isolates one pedestrian.
2. **Instance Segmentation:** Extracts 4-channel RGBA cutout with morphological alpha feathering.
3. **Canonical Canvas Normalization ($160 \times 320\text{ px}$):** Rescales the isolated worker to a standardized height and anchors the lowest contact foot to the bottom center of the canvas $(80, 316)$, eliminating bounding box wobble and vertical jitter.

### 2. Pinhole Vertical Height Scaling
For a standing human of height $H_{obj} = 1.75\text{ m}$, the visual height in screen pixels $h_{px}(Y)$ at ground depth $Y \in [0.0, 6.0]\text{ m}$ is computed via the calibrated perspective scale:

$$h_{px}(Y) = \frac{480.0}{1.0 + 0.165 \cdot Y}$$

* At near boundary ($Y = 0.5\text{ m}$): $h_{px} \approx 443\text{ px}$.
* At center zone ($Y = 3.0\text{ m}$): $h_{px} \approx 321\text{ px}$.
* At far boundary ($Y = 5.5\text{ m}$): $h_{px} \approx 251\text{ px}$.

### 3. Decoupled UI & High-Contrast HUD Architecture
- **Top HUD Banner (Safety Pipeline):** 56px height, dark acrylic background, containing solid-color status pill badges (`CRITICAL TRIP: LOCKOUT`, `WARNING`, `SYSTEM NORMAL`) and isolated telemetry capsules (`T1 Latency`, `FPS`, `Tracks`, `Dwell`).
- **Bottom Telemetry Badge (Simulation Metadata):** Positioned at $y=1040\text{ px}$ in the camera view to avoid any collision with the top safety overlay.
- **Ground & BEV Anchors:** Text tags rendered with contrasting dark pill backgrounds for 100% legibility on any background.

---

## Benchmark Sequences

1. **Sequence A (`sequence_a_clean_incursion.mp4`)**:
   * *Scenario*: Straight pedestrian crossing across the factory floor from $(2.0, 0.5)\text{ m}$ to $(2.0, 5.5)\text{ m}$.
   * *Expected Safety Transitions*: `SAFE` $\rightarrow$ `WARNING_APPROACH` $\rightarrow$ `DANGER_INTRUSION` $\rightarrow$ `LOCKOUT`.

2. **Sequence B (`sequence_b_occlusion_coasting.mp4`)**:
   * *Scenario*: Worker walks along $Y = 2.8\text{ m}$ passing behind a wooden crate barrier at $Y = 2.4\text{ m}$.
   * *Expected Behavior*: Lower-limb keypoint loss triggers Kalman Filter occlusion coasting while maintaining confirmed track ID.

3. **Sequence C (`sequence_c_dwell_loitering.mp4`)**:
   * *Scenario*: Worker enters danger zone $(2.0, 3.0)\text{ m}$, remains stationary for 6.0 seconds, then departs.
   * *Expected Behavior*: Spatial FSM accumulates dwell time, triggers `DWELLING` alert at $t > 0.0\text{s}$, and asserts `DWELL_VIOLATION` at $t \ge 5.0\text{s}$.

---

## CLI Execution

```bash
# 1. Extract and normalize single-identity sprite walking cycle
python scripts/prepare_sprites.py

# 2. Generate all 3 synthetic benchmark videos
python scripts/generate_samples.py --sequence all --fps 30

# 3. Run interactive demo with dual-stream visualizer
python scripts/run_demo.py --source data/samples/sequence_a_clean_incursion.mp4 --realtime
python scripts/run_demo.py --source data/samples/sequence_b_occlusion_coasting.mp4 --realtime
python scripts/run_demo.py --source data/samples/sequence_c_dwell_loitering.mp4 --realtime
```
