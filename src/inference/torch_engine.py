"""
src/inference/torch_engine.py
PyTorch eager execution engine for comparative benchmarking and inference.
"""

from pathlib import Path
from typing import Any, List, Optional, Tuple, Union
import logging
import numpy as np
import torch

logger = logging.getLogger(__name__)


class TorchEngine:
    """
    Encapsulates PyTorch eager model inference, providing an interface
    matching OnnxEngine for unified benchmarking and evaluation.
    """

    def __init__(
        self,
        model_path: Union[str, Path],
        device: Optional[str] = None,
    ) -> None:
        """
        Initialize PyTorch eager engine.

        Args:
            model_path: Path to PyTorch model weights (.pt).
            device: Target device string ('cpu', 'mps', 'cuda'). Defaults to auto-detect.
        """
        self.model_path = Path(model_path)
        if not self.model_path.is_file():
            raise FileNotFoundError(f"PyTorch model weights not found at '{self.model_path}'")

        # Resolve device
        if device is None:
            if torch.backends.mps.is_available():
                self.device_str = "mps"
            elif torch.cuda.is_available():
                self.device_str = "cuda"
            else:
                self.device_str = "cpu"
        else:
            self.device_str = device.lower()

        self.device = torch.device(self.device_str)
        self.model = self._load_model()
        self.model.to(self.device)
        self.model.float()
        self.model.eval()

        logger.info(
            "Initialized TorchEngine with model '%s' on device '%s'.",
            self.model_path.name,
            self.device_str,
        )

    def _load_model(self) -> torch.nn.Module:
        """Load PyTorch model from checkpoint or Ultralytics wrapper."""
        try:
            # First try loading as raw torch model / state dict
            loaded = torch.load(self.model_path, map_location="cpu", weights_only=False)
            if isinstance(loaded, torch.nn.Module):
                return loaded
            if isinstance(loaded, dict) and "model" in loaded and isinstance(loaded["model"], torch.nn.Module):
                return loaded["model"]
        except Exception:
            pass

        # Fallback to Ultralytics YOLO loader
        try:
            from ultralytics import YOLO
            yolo = YOLO(str(self.model_path))
            return yolo.model
        except Exception as e:
            raise RuntimeError(f"Failed to load PyTorch model from '{self.model_path}': {e}") from e

    def get_device_info(self) -> str:
        """Return active execution device name."""
        return self.device_str

    def get_providers(self) -> List[str]:
        """Return provider-like identifier for consistency with OnnxEngine."""
        return [f"PyTorch_{self.device_str.upper()}"]

    def infer(self, image: np.ndarray) -> np.ndarray:
        """
        Execute forward inference pass on input image array.

        Args:
            image: Pre-processed image array in CHW (3, H, W) or NCHW (1, 3, H, W) format, float32 [0.0, 1.0].

        Returns:
            Raw NumPy output tensor on CPU.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError("image must be a numpy.ndarray")

        # Ensure batch dimension
        if image.ndim == 3:
            image = np.expand_dims(image, axis=0)
        elif image.ndim != 4:
            raise ValueError(f"image must be 3D or 4D array, got shape {image.shape}")

        param = next(self.model.parameters(), None)
        target_dtype = param.dtype if param is not None else torch.float32

        # Convert to contiguous PyTorch Tensor on target device
        tensor = torch.from_numpy(np.ascontiguousarray(image)).to(device=self.device, dtype=target_dtype)

        with torch.inference_mode():
            out = self.model(tensor)
            if self.device_str == "mps":
                torch.mps.synchronize()
            elif self.device_str == "cuda":
                torch.cuda.synchronize()

        # Handle Ultralytics tuple/list outputs or single tensor
        if isinstance(out, (list, tuple)):
            out_tensor = out[0]
        else:
            out_tensor = out

        return out_tensor.detach().cpu().to(torch.float32).numpy()
