# Design: Synthetic YOLO Video Generation

## Architecture Overview

The enhanced `SyntheticVideoGenerator` incorporates a sprite-based compositing pipeline that maps photorealistic RGBA human worker sprites into calibrated metric ground coordinates, projecting them onto a perspective floor with soft shadows and physical occlusions.

```
+-------------------------------------------------------------+
|               SyntheticVideoGenerator Engine                |
+-------------------------------------------------------------+
                               |
                               v
               +-------------------------------+
               | 1. Metric Trajectory Planning |
               |    (X_world, Y_world, gait)   |
               +-------------------------------+
                               |
                               v
               +-------------------------------+
               | 2. Homography Projection &    |
               |    Perspective Scale Delta    |
               +-------------------------------+
                               |
                               v
               +-------------------------------+
               | 3. Soft Contact Shadow Pass   |
               |    (Gaussian Ellipse Blending)|
               +-------------------------------+
                               |
                               v
               +-------------------------------+
               | 4. RGBA Sprite Alpha Blending |
               |    (Lanczos4 Rescaling)       |
               +-------------------------------+
                               |
                               v
               +-------------------------------+
               | 5. Depth-Ordered Obstacle     |
               |    Occlusion Rendering        |
               +-------------------------------+
                               |
                               v
               +-------------------------------+
               | 6. Telemetry & Zone Overlay   |
               +-------------------------------+
                               |
                               v
                     Output MP4 Video Stream
```

## Component Design

### 1. Sprite Asset Bank (`data/assets/sprites/worker/`)
- Contains 8-12 walking cycle frames: `walk_00.png` through `walk_07.png`.
- Contains 1 standing/idle frame: `idle_00.png`.
- High resolution (approx 600x1200 px), 4-channel RGBA (8-bit per channel).
- Features realistic worker clothing: Hi-vis vest, denim work trousers, leather boots, and hardhat with natural photorealistic textures.

### 2. Alpha Blending Engine
- Calculates bounding box $(u_{min}, v_{min}, u_{max}, v_{max})$ on the canvas.
- Clamps coordinates to canvas boundaries $(0, 0, W, H)$.
- Vectorized alpha compositing:
  $$I_{out} = \alpha \cdot I_{sprite} + (1 - \alpha) \cdot I_{bg}$$

### 3. Contact Shadow Generation
- Elliptical shadow centered at $(u_{base}, v_{base})$ with major axis $W_{sprite} \times 0.6$ and minor axis $W_{sprite} \times 0.2$.
- Gaussian blur kernel applied to shadow alpha channel with opacity $\approx 0.45$.

### 4. Occlusion Handling
- For Sequence B, obstacle is rendered at metric coordinate $(X=2.0, Y=2.4)$.
- Worker walks along $Y=2.8$ (behind obstacle).
- Worker is rendered first; the crate/pallet obstacle is rendered on top, naturally masking the lower limbs while leaving the upper torso and head visible.

## Interfaces & Contracts

### `SyntheticVideoGenerator` Class
```python
class SyntheticVideoGenerator:
    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = "configs/default_config.yaml",
        homography_manager: Optional[HomographyManager] = None,
        sprite_dir: Optional[Union[str, Path]] = None,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
    ) -> None: ...

    def render_worker_sprite(
        self,
        frame: np.ndarray,
        world_x: float,
        world_y: float,
        gait_phase: float = 0.0,
        is_idle: bool = False,
    ) -> None: ...

    def generate_sequence_a(self, output_path: Union[str, Path], duration_s: float = 6.0) -> Path: ...
    def generate_sequence_b(self, output_path: Union[str, Path], duration_s: float = 6.0) -> Path: ...
    def generate_sequence_c(self, output_path: Union[str, Path], duration_s: float = 10.0) -> Path: ...
    def generate_all_sequences(self, output_dir: Union[str, Path]) -> List[Path]: ...
```
