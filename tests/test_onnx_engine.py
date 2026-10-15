"""
Unit tests for src/inference/onnx_engine.py.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pytest
import onnxruntime as ort

from src.inference.onnx_engine import OnnxEngine


def test_engine_init_success(synthetic_onnx_path: Path):
    """Engine successfully loads a valid ONNX model."""
    engine = OnnxEngine(synthetic_onnx_path)
    assert len(engine.active_providers) > 0
    assert "CPUExecutionProvider" in engine.active_providers or "CoreMLExecutionProvider" in engine.active_providers
    input_details = engine.get_input_details()
    assert input_details["name"] == "images"
    assert tuple(input_details["shape"]) == (1, 3, 640, 640)

    output_details = engine.get_output_details()
    assert output_details["name"] == "output0"
    assert tuple(output_details["shape"]) == (1, 56, 8400)


def test_engine_nonexistent_model(tmp_path: Path):
    """Engine raises FileNotFoundError when model path does not exist."""
    missing_path = tmp_path / "missing.onnx"
    with pytest.raises(FileNotFoundError, match="not found"):
        OnnxEngine(missing_path)


def test_engine_explicit_cpu_provider(synthetic_onnx_path: Path):
    """Engine respects explicit provider configuration."""
    engine = OnnxEngine(synthetic_onnx_path, providers=["CPUExecutionProvider"])
    assert engine.get_providers() == ["CPUExecutionProvider"]


def test_engine_provider_fallback_when_coreml_fails(synthetic_onnx_path: Path, caplog):
    """Engine gracefully falls back to CPUExecutionProvider if CoreML session init fails."""
    original_cls = ort.InferenceSession

    def mock_session_constructor(model_path, *args, **kwargs):
        providers = kwargs.get("providers", args[1] if len(args) > 1 else [])
        if "CoreMLExecutionProvider" in providers:
            raise RuntimeError("CoreML initialization failure simulation")
        return original_cls(model_path, *args, **kwargs)

    with patch("onnxruntime.get_available_providers", return_value=["CoreMLExecutionProvider", "CPUExecutionProvider"]):
        with patch("onnxruntime.InferenceSession", side_effect=mock_session_constructor):
            engine = OnnxEngine(synthetic_onnx_path, providers=["CoreMLExecutionProvider", "CPUExecutionProvider"])
            assert "CPUExecutionProvider" in engine.get_providers()
            assert "CoreML initialization failure simulation" in caplog.text


def test_engine_session_options_applied(synthetic_onnx_path: Path):
    """Engine applies intra_op_num_threads and graph optimizations to SessionOptions."""
    with patch("onnxruntime.InferenceSession") as mock_session_cls:
        mock_instance = MagicMock()
        mock_session_cls.return_value = mock_instance
        mock_instance.get_inputs.return_value = [MagicMock(name="images", shape=[1, 3, 640, 640], type="tensor(float)")]
        mock_instance.get_outputs.return_value = [MagicMock(name="output0", shape=[1, 56, 8400], type="tensor(float)")]
        mock_instance.get_providers.return_value = ["CPUExecutionProvider"]

        OnnxEngine(synthetic_onnx_path, num_threads=6)

        _, kwargs = mock_session_cls.call_args
        sess_options = kwargs.get("sess_options")
        assert sess_options is not None
        assert sess_options.intra_op_num_threads == 6
        assert sess_options.graph_optimization_level == ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        assert sess_options.execution_mode == ort.ExecutionMode.ORT_SEQUENTIAL


def test_engine_infer_forward_pass(synthetic_onnx_path: Path):
    """Engine executes forward pass returning expected output shape and dtype."""
    engine = OnnxEngine(synthetic_onnx_path)
    dummy_input = np.ones((1, 3, 640, 640), dtype=np.float32)
    output = engine.infer(dummy_input)

    assert isinstance(output, np.ndarray)
    assert output.shape == (1, 56, 8400)
    assert output.dtype == np.float32


def test_engine_infer_invalid_shape(synthetic_onnx_path: Path):
    """Engine raises ValueError when input tensor shape does not match model contract."""
    engine = OnnxEngine(synthetic_onnx_path)
    bad_tensor_spatial = np.zeros((1, 3, 320, 320), dtype=np.float32)
    with pytest.raises(ValueError, match="Input tensor shape mismatch"):
        engine.infer(bad_tensor_spatial)

    bad_tensor_batch = np.zeros((2, 3, 640, 640), dtype=np.float32)
    with pytest.raises(ValueError, match="Input tensor shape mismatch"):
        engine.infer(bad_tensor_batch)


def test_engine_infer_invalid_dtype(synthetic_onnx_path: Path):
    """Engine raises TypeError when input tensor dtype is not float32."""
    engine = OnnxEngine(synthetic_onnx_path)
    bad_tensor_uint8 = np.zeros((1, 3, 640, 640), dtype=np.uint8)
    with pytest.raises(TypeError, match="np.float32 is required"):
        engine.infer(bad_tensor_uint8)

    bad_tensor_float64 = np.zeros((1, 3, 640, 640), dtype=np.float64)
    with pytest.raises(TypeError, match="np.float32 is required"):
        engine.infer(bad_tensor_float64)


def test_engine_infer_non_ndarray(synthetic_onnx_path: Path):
    """Engine raises TypeError when input is not a numpy ndarray."""
    engine = OnnxEngine(synthetic_onnx_path)
    with pytest.raises(TypeError, match="must be a numpy.ndarray"):
        engine.infer([[0.0]])
