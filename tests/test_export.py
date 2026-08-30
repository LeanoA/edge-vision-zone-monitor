"""
Unit tests for models/export_onnx.py.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import onnx
from onnx import helper, TensorProto

from tests.conftest import create_synthetic_onnx_model
from models.export_onnx import validate_onnx_model, export_model, main


def test_validate_onnx_model_success(synthetic_onnx_path: Path):
    """Synthetic model conforming to contract passes validation."""
    assert validate_onnx_model(synthetic_onnx_path) is True


def test_validate_onnx_model_nonexistent(tmp_path: Path):
    """Validation raises FileNotFoundError when model path does not exist."""
    missing_path = tmp_path / "non_existent.onnx"
    with pytest.raises(FileNotFoundError, match="not found"):
        validate_onnx_model(missing_path)


def test_validate_onnx_model_corrupt(tmp_path: Path):
    """Validation raises ValidationError on corrupted ONNX graph or invalid protobuf."""
    corrupt_file = tmp_path / "corrupt.onnx"
    corrupt_file.write_bytes(b"INVALID_ONNX_HEADER_CORRUPTED_BYTES")
    with pytest.raises(onnx.checker.ValidationError):
        validate_onnx_model(corrupt_file)


def test_validate_onnx_model_input_shape_mismatch(tmp_path: Path):
    """Validation raises ValueError if input shape does not match expected_input_shape."""
    mismatched_model = tmp_path / "mismatched_input.onnx"
    create_synthetic_onnx_model(
        mismatched_model,
        input_shape=(1, 3, 320, 320),
        output_shape=(1, 56, 8400),
    )
    with pytest.raises(ValueError, match="Input shape mismatch"):
        validate_onnx_model(mismatched_model, expected_input_shape=(1, 3, 640, 640))


def test_validate_onnx_model_output_shape_mismatch(tmp_path: Path):
    """Validation raises ValueError if output shape does not match expected_output_shape."""
    mismatched_model = tmp_path / "mismatched_output.onnx"
    create_synthetic_onnx_model(
        mismatched_model,
        input_shape=(1, 3, 640, 640),
        output_shape=(1, 20, 1000),
    )
    with pytest.raises(ValueError, match="Output shape mismatch"):
        validate_onnx_model(mismatched_model, expected_output_shape=(1, 56, 8400))


def test_validate_onnx_model_invalid_dtype(tmp_path: Path):
    """Validation raises ValueError if input tensor is not float32."""
    int_model_path = tmp_path / "int_input.onnx"
    X = helper.make_tensor_value_info("images", TensorProto.INT32, [1, 3, 640, 640])
    Y = helper.make_tensor_value_info("output0", TensorProto.FLOAT, [1, 56, 8400])
    # Identity node mapping requires same type, cast to float
    cast_node = helper.make_node("Cast", ["images"], ["output0"], to=TensorProto.FLOAT)
    graph = helper.make_graph([cast_node], "cast_graph", [X], [Y])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)], ir_version=10)
    onnx.save(model, str(int_model_path))

    with pytest.raises(ValueError, match="data type"):
        validate_onnx_model(int_model_path)


@patch("ultralytics.YOLO")
def test_export_model_invokes_ultralytics(mock_yolo_cls, tmp_path: Path):
    """export_model delegates to Ultralytics YOLO with static shape, opset 17, and simplify=True."""
    mock_model_instance = MagicMock()
    mock_yolo_cls.return_value = mock_model_instance

    # Create dummy target destination
    target_onnx = tmp_path / "yolo11n-pose.onnx"
    create_synthetic_onnx_model(target_onnx)

    mock_model_instance.export.return_value = str(target_onnx)

    out_file = export_model(
        model_name="yolo11n-pose.pt",
        output_path=target_onnx,
        imgsz=640,
        opset=17,
        simplify=True,
    )

    assert out_file == target_onnx
    mock_yolo_cls.assert_called_once_with("yolo11n-pose.pt")
    mock_model_instance.export.assert_called_once_with(
        format="onnx",
        imgsz=640,
        opset=17,
        dynamic=False,
        simplify=True,
    )


@patch("sys.argv", ["export_onnx.py", "--weights", "nonexistent_weights_xyz.pt"])
def test_export_cli_nonexistent_weights(capsys):
    """CLI exits with code 1 when weights file is missing/cannot be loaded."""
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


@patch("ultralytics.YOLO")
def test_export_cli_success(mock_yolo_cls, tmp_path: Path, monkeypatch):
    """CLI successfully exports and exits with 0."""
    target_onnx = tmp_path / "yolo11n-pose.onnx"
    create_synthetic_onnx_model(target_onnx)

    mock_model_instance = MagicMock()
    mock_model_instance.export.return_value = str(target_onnx)
    mock_yolo_cls.return_value = mock_model_instance

    monkeypatch.setattr(
        "sys.argv",
        ["export_onnx.py", "--weights", "yolo11n-pose.pt", "--output", str(target_onnx)],
    )

    # Should exit with code 0 (or return cleanly)
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
