# Specification: Synthetic YOLO Video Generator

## Capability: `synthetic-yolo-video-generator`

The synthetic video generation engine SHALL produce deterministic, perspective-accurate industrial test videos where human workers are rendered with photorealistic RGBA textures and detected by YOLO object and pose estimation models with high confidence ($conf \ge 0.50$).

### Requirement: RGBA Sprite Compositing
The generator SHALL load high-resolution RGBA sprite sequences representing walking and standing workers, scaling them according to calibrated planar homography depth and alpha blending them without visual edge artifacts.

#### Scenario: Sprite scaling and perspective placement
- **GIVEN** a calibrated homography matrix $H$ mapping $(X_{world}, Y_{world})$ to image coordinates $(u, v)$
- **WHEN** rendering a worker at metric position $(X=2.0, Y=3.0)$
- **THEN** the ground contact point of the sprite SHALL align with $H(2.0, 3.0)$
- **AND** the vertical pixel height of the sprite SHALL scale proportionally to the calculated metric distance scale ($h_{px} = \frac{480.0}{1.0 + 0.165 \cdot Y}$).

### Requirement: Directional Contact Shadow
The generator SHALL render a soft contact shadow beneath the worker's feet to ground the actor realistically on the factory floor.

#### Scenario: Shadow rendering
- **GIVEN** a worker placed at ground coordinate $(u_{base}, v_{base})$
- **WHEN** rendering the base shadow pass
- **THEN** an elliptical shadow with Gaussian falloff SHALL be blended with ground opacity between 0.35 and 0.55.

### Requirement: Depth-Ordered Occlusion
The generator SHALL support depth-ordered occlusion rendering where foreground obstacles mask the worker's lower body when the worker passes behind them.

#### Scenario: Lower-limb occlusion in Sequence B
- **GIVEN** an industrial obstacle located at $(X=2.0, Y=2.4)$
- **WHEN** a worker walks along $Y=2.8$ through the interval $X \in [1.5, 2.5]$
- **THEN** the obstacle SHALL be rendered in front of the worker, occluding the lower limbs while preserving visibility of the upper torso and head.

### Requirement: YOLO Detection Compatibility
The generated video frames SHALL be detectable by standard YOLOv8/YOLO11 models.

#### Scenario: YOLO pose detection validation
- **GIVEN** a generated synthetic benchmark video (`sequence_a_clean_incursion.mp4`)
- **WHEN** running YOLO11-pose inference on non-boundary frames
- **THEN** at least 95% of frames SHALL produce a valid bounding box and keypoints for the worker with confidence $\ge 0.50$.
