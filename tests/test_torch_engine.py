"""
tests/test_torch_engine.py
Unit tests for PyTorch eager inference engine wrapper (src/inference/torch_engine.py).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pytest
import torch

from src.inference.torch_engine import TorchEngine


class DummyNet(torch.nn.Module):
    """Synthetic PyTorch module for test fixture."""
    def __init__(self):
        super().__init__()
        self.conv = torch.nn.Conv2d(3, 56, kernel_size=1)

    def forward(self, x):
        batch = x.shape[0]
        features = self.conv(x)
        out = features.flatten(2)
        if out.shape[2] != 8400:
            if out.shape[2] < 8400:
                pad = torch.zeros((batch, 56, 8400 - out.shape[2]), dtype=x.dtype, device=x.device)
                out = torch.cat([out, pad], dim=2)
            else:
                out = out[:, :, :8400]
        return out


@pytest.fixture
def mock_torch_model(tmp_path: Path) -> Path:
    """Create a dummy PyTorch model checkpoint for testing."""
    model = DummyNet()
    model_path = tmp_path / "dummy_model.pt"
    torch.save(model, model_path)
    return model_path


def test_torch_engine_initialization_cpu(mock_torch_model: Path):
    """TorchEngine initializes properly on CPU."""
    engine = TorchEngine(model_path=str(mock_torch_model), device="cpu")
    assert engine.device_str == "cpu"
    assert engine.device == torch.device("cpu")
    assert engine.get_device_info() == "cpu"
    assert engine.model is not None


def test_torch_engine_infer_shape_and_type(mock_torch_model: Path):
    """TorchEngine executes inference and returns a contiguous CPU NumPy array."""
    engine = TorchEngine(model_path=str(mock_torch_model), device="cpu")
    dummy_input = np.random.randn(1, 3, 640, 640).astype(np.float32)

    output = engine.infer(dummy_input)
    assert isinstance(output, np.ndarray)
    assert output.ndim == 3
    assert output.shape[0] == 1
    assert output.shape[1] == 56
    assert output.shape[2] == 8400
    assert output.dtype == np.float32


def test_torch_engine_input_tensor_handling(mock_torch_model: Path):
    """TorchEngine correctly accepts both 3D (CHW) and 4D (NCHW) NumPy arrays."""
    engine = TorchEngine(model_path=str(mock_torch_model), device="cpu")

    chw_input = np.random.randn(3, 640, 640).astype(np.float32)
    output = engine.infer(chw_input)
    assert output.shape == (1, 56, 8400)


def test_torch_engine_mps_availability_or_fallback(mock_torch_model: Path):
    """TorchEngine requests MPS when available on macOS."""
    if torch.backends.mps.is_available():
        engine = TorchEngine(model_path=str(mock_torch_model), device="mps")
        assert engine.device_str == "mps"
        assert engine.device == torch.device("mps")
        dummy_input = np.random.randn(1, 3, 640, 640).astype(np.float32)
        output = engine.infer(dummy_input)
        assert isinstance(output, np.ndarray)
        assert output.shape == (1, 56, 8400)
    else:
        pytest.skip("MPS not available on this platform.")


def test_torch_engine_invalid_path():
    """TorchEngine raises FileNotFoundError for non-existent model."""
    with pytest.raises(FileNotFoundError):
        TorchEngine(model_path="non_existent_weights.pt")
