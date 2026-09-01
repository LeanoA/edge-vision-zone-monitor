# Capability Specification: Keypoint Coordinate Inversion & Ground Anchor Extraction

**Capability:** `keypoint-unletterbox`  
**Domain:** Perception & Geometric Alignment  

---

## 1. Overview
Ensures that all keypoint coordinates extracted from letterboxed inference canvases $(640 \times 640)$ are mapped into the original frame pixel space with spatial accuracy across all aspect ratios (16:9, 4:3, tall, wide), preserving confidence values and enabling ground anchor extraction.

---

## 2. Requirements & Scenarios

### Requirement 1: Vectorized Keypoint Coordinate Inversion
The system MUST transform $(N, 3)$ keypoint arrays from letterboxed canvas space to original frame space using the scale factor and padding offsets computed during preprocessing.

#### Scenario 1.1: 16:9 Full HD Frame (Letterbox with Vertical Padding)
- **Given** an image of dimensions $1920 \times 1080$ letterboxed to $640 \times 640$ ($\text{scale} = 0.3333$, $\text{pad}_y = 140.0\text{ px}$, $\text{pad}_x = 0.0\text{ px}$)
- **When** a keypoint at $(320.0, 320.0, 0.9)$ in canvas space is unletterboxed
- **Then** the transformed coordinate MUST equal $(960.0, 540.0, 0.9)$ within float tolerance ($\pm 0.1\text{ px}$).

#### Scenario 1.2: Tall Frame (Pillarbox with Horizontal Padding)
- **Given** an image of dimensions $600 \times 1200$ letterboxed to $640 \times 640$ ($\text{scale} = 0.5333$, $\text{pad}_x = 160.0\text{ px}$, $\text{pad}_y = 0.0\text{ px}$)
- **When** a keypoint at $(320.0, 320.0, 0.85)$ in canvas space is unletterboxed
- **Then** the transformed coordinate MUST equal $(300.0, 600.0, 0.85)$ within float tolerance.

### Requirement 2: Graceful Degradation Ground Anchor Extraction
Ground anchor extraction MUST operate on unletterboxed keypoints and unletterboxed bounding boxes directly.

#### Scenario 2.1: Dual Ankles Valid
- **Given** dual ankles at $(950.0, 1000.0, 0.88)$ and $(970.0, 1000.0, 0.92)$
- **When** `extract_ground_anchor` is called
- **Then** anchor coordinate MUST equal midpoint $(960.0, 1000.0)$ with source `AnchorSource.ANKLES_DUAL` and confidence $0.90$.

#### Scenario 2.2: Single Ankle Valid Fallback
- **Given** left ankle valid $(950.0, 1000.0, 0.80)$ and right ankle occluded $(0.0, 0.0, 0.10)$
- **When** `extract_ground_anchor` is called with `conf_threshold = 0.5`
- **Then** anchor coordinate MUST equal single ankle $(950.0, 1000.0)$ with source `AnchorSource.ANKLE_SINGLE` and confidence $0.80 \times 0.75 = 0.60$.
