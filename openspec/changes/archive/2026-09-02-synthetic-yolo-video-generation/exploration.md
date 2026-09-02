# Exploration: Synthetic YOLO Video Generation

## Current State Analysis

### 1. Existing Synthetic Generator (`src/utils/synthetic_generator.py`)
- Renders a 1920x1080 background slate floor with homography grid lines and safety zones.
- Humanoid is drawn using primitive 2D drawing functions:
  - `cv2.line` for limbs and torso.
  - `cv2.rectangle` for safety vest and boots.
  - `cv2.ellipse` and `cv2.circle` for helmet and head.
- **Problem**: YOLOv8/v11 models trained on COCO look for natural gradients, fabric textures, realistic limb anatomy, natural lighting, and skin tones. Synthetic geometric stick figures produce zero detections ($conf = 0.00$).

### 2. Homography & Safety Zones
- Homography projection matrix $H$ maps world coordinates $(X, Y)$ in meters to pixel space $(u, v)$.
- Sequence A tests straight crossing from $(2.0, 0.5)$ to $(2.0, 5.5)$.
- Sequence B tests lower-limb occlusion behind an industrial obstacle at $(2.0, 2.4)$.
- Sequence C tests dwell time / loitering inside the restricted zone $(2.0, 3.0)$ for 6 seconds.

### 3. Requirements for YOLO Detection
- **Photorealism**: Real human textures (work jacket / vest, jeans/work pants, work boots, natural human pose silhouettes).
- **Gait Animation**: Walking gait cycle with at least 8 distinct phase frames to simulate natural foot progression.
- **Perspective Scaling**: Height in pixels must scale with ground distance $Y$ according to $H$.
- **Contact Shadow**: Soft elliptical shadow at the ground contact point to ground the sprite visually and avoid floating artifact edges.
- **Occlusion Handling**: Z-ordering (Y-ordering) so obstacles naturally occlude the lower body while upper torso remains visible.

## Proposed Architecture
1. Store high-resolution RGBA sprite walking frames in `data/assets/sprites/worker/`.
2. `SyntheticVideoGenerator` loads and caches the sprite animation frames on initialization.
3. For each frame:
   - Calculate $(u_{base}, v_{base}) = H(X_{world}, Y_{world})$.
   - Compute body height $H_{px}$ via homography depth delta.
   - Resize matching gait cycle sprite to $(W_{px}, H_{px})$ using `cv2.INTER_LANCZOS4`.
   - Render directional soft contact shadow on floor.
   - Blend RGBA sprite onto background using optimized alpha matting.
   - If obstacle is present and worker is behind it, render obstacle over the worker's lower body.
