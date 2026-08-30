"""
Pytest configuration and shared test fixtures for vision-restricted-zone-monitor.
"""

from pathlib import Path
from typing import Tuple
import pytest
import onnx
from onnx import helper, TensorProto


def create_synthetic_onnx_model(
    output_path: Path,
    input_shape: Tuple[int, ...] = (1, 3, 640, 640),
    output_shape: Tuple[int, ...] = (1, 56, 8400),
) -> Path:
    """
    Generate a lightweight, valid synthetic ONNX model mapping input_shape to output_shape.
    Requires no external downloads and executes in <50ms.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    input_elem_count = 1
    for dim in input_shape:
        input_elem_count *= dim

    output_elem_count = 1
    for dim in output_shape:
        output_elem_count *= dim

    # Input and output tensor info
    X = helper.make_tensor_value_info("images", TensorProto.FLOAT, list(input_shape))
    Y = helper.make_tensor_value_info("output0", TensorProto.FLOAT, list(output_shape))

    # Flatten input to 1D vector along axis 1: (1, input_elem_count)
    flat_node = helper.make_node("Flatten", ["images"], ["flat"], axis=1)

    # Slice or Pad to output_elem_count
    if input_elem_count >= output_elem_count:
        starts = helper.make_tensor("starts", TensorProto.INT64, [1], [0])
        ends = helper.make_tensor("ends", TensorProto.INT64, [1], [output_elem_count])
        axes = helper.make_tensor("axes", TensorProto.INT64, [1], [1])
        steps = helper.make_tensor("steps", TensorProto.INT64, [1], [1])
        slice_node = helper.make_node("Slice", ["flat", "starts", "ends", "axes", "steps"], ["transformed"])
        initializers = [starts, ends, axes, steps]
        nodes = [flat_node, slice_node]
    else:
        # Pad with zeros if input is smaller than output
        pad_size = output_elem_count - input_elem_count
        pads = helper.make_tensor("pads", TensorProto.INT64, [4], [0, 0, 0, pad_size])
        pad_node = helper.make_node("Pad", ["flat", "pads"], ["transformed"], mode="constant")
        initializers = [pads]
        nodes = [flat_node, pad_node]

    # Reshape to target output shape
    shape_tensor = helper.make_tensor("shape", TensorProto.INT64, [len(output_shape)], list(output_shape))
    initializers.append(shape_tensor)
    reshape_node = helper.make_node("Reshape", ["transformed", "shape"], ["output0"])
    nodes.append(reshape_node)

    graph = helper.make_graph(
        nodes,
        "synthetic_yolo_pose",
        [X],
        [Y],
        initializers,
    )

    # Set opset 17 and ir_version 10 for broad ONNX Runtime compatibility
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)], ir_version=10)
    onnx.checker.check_model(model)
    onnx.save(model, str(output_path))
    return output_path


@pytest.fixture
def synthetic_onnx_path(tmp_path: Path) -> Path:
    """Fixture providing the path to a verified synthetic ONNX YOLO Pose model."""
    model_file = tmp_path / "synthetic_yolo_pose.onnx"
    return create_synthetic_onnx_model(model_file)
