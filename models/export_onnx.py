"""
models/export_onnx.py
YOLO Pose ONNX model export and validation utility.
"""

from pathlib import Path
from typing import Optional, Union, Tuple
import argparse
import logging
import shutil
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import onnx
from onnx import shape_inference, TensorProto

logger = logging.getLogger("export_onnx")


def validate_onnx_model(
    model_path: Union[str, Path],
    expected_input_shape: Tuple[int, ...] = (1, 3, 640, 640),
    expected_output_shape: Optional[Tuple[int, ...]] = (1, 56, 8400),
) -> bool:
    """
    Validate the structural and dimensional integrity of an ONNX model graph.

    Args:
        model_path: Path to the exported ONNX model file.
        expected_input_shape: Expected dimensions for the primary input tensor.
        expected_output_shape: Optional expected dimensions for the primary output tensor.

    Returns:
        True if the model passes validation.

    Raises:
        FileNotFoundError: If model_path does not exist.
        onnx.checker.ValidationError: If graph topology violates the ONNX standard.
        ValueError: If tensor dimensions or data types do not match expectations.
    """
    path = Path(model_path)
    if not path.is_file():
        raise FileNotFoundError(f"Model file not found: {path}")

    try:
        model = onnx.load(str(path))
    except Exception as e:
        raise onnx.checker.ValidationError(f"Failed to parse ONNX protobuf: {e}") from e

    # Structural topology validation
    onnx.checker.check_model(model)

    # Dimensional shape inference
    try:
        inferred = shape_inference.infer_shapes(model)
    except Exception as e:
        raise onnx.checker.ValidationError(f"Shape inference failed: {e}") from e

    if not inferred.graph.input:
        raise ValueError("Model contains no input tensors.")

    primary_input = inferred.graph.input[0]
    input_type = primary_input.type.tensor_type

    if input_type.elem_type != TensorProto.FLOAT:
        raise ValueError(
            f"Input tensor data type mismatch: expected float32 ({TensorProto.FLOAT}), got {input_type.elem_type}"
        )

    actual_input_shape = tuple(
        dim.dim_value for dim in input_type.shape.dim
    )
    if actual_input_shape != expected_input_shape:
        raise ValueError(
            f"Input shape mismatch: expected {expected_input_shape}, got {actual_input_shape}"
        )

    if expected_output_shape is not None and inferred.graph.output:
        primary_output = inferred.graph.output[0]
        output_type = primary_output.type.tensor_type
        if output_type.elem_type != TensorProto.FLOAT:
            raise ValueError(
                f"Output tensor data type mismatch: expected float32 ({TensorProto.FLOAT}), got {output_type.elem_type}"
            )
        actual_output_shape = tuple(
            dim.dim_value for dim in output_type.shape.dim
        )
        if actual_output_shape != expected_output_shape:
            raise ValueError(
                f"Output shape mismatch: expected {expected_output_shape}, got {actual_output_shape}"
            )

    logger.info("ONNX model '%s' successfully validated.", path.name)
    return True


def export_model(
    model_name: str = "yolo11n-pose.pt",
    output_path: Optional[Union[str, Path]] = None,
    imgsz: int = 640,
    opset: int = 17,
    simplify: bool = True,
) -> Path:
    """
    Download (if necessary) and export a YOLO-Pose PyTorch checkpoint to static ONNX.

    Args:
        model_name: Ultralytics model identifier or local .pt checkpoint path.
        output_path: Optional custom destination path for the exported .onnx file.
                     Defaults to models/{model_stem}.onnx.
        imgsz: Input image dimension (square height and width). Default: 640.
        opset: Target ONNX operator set version. Default: 17.
        simplify: Whether to run onnxsim graph simplification. Default: True.

    Returns:
        Path to the verified exported ONNX model file.

    Raises:
        FileNotFoundError: If model_name is a non-existent local file.
        RuntimeError: If Ultralytics export or validation fails.
    """
    model_path = Path(model_name)
    # Check if a custom file path was passed that does not exist
    if ("/" in model_name or "\\" in model_name) and not model_path.is_file():
        raise FileNotFoundError(f"Weights file not found: {model_name}")

    # Determine destination path
    stem = model_path.stem if model_path.suffix else model_name
    if output_path is not None:
        dest = Path(output_path)
        if dest.is_dir() or str(output_path).endswith("/") or str(output_path).endswith("\\"):
            dest = dest / f"{stem}.onnx"
    else:
        dest = Path("models") / f"{stem}.onnx"

    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        from ultralytics import YOLO  # lazy import
    except ImportError as e:
        raise RuntimeError(f"Ultralytics is not installed: {e}") from e

    logger.info("Loading model '%s'...", model_name)
    try:
        model = YOLO(str(model_name))
    except Exception as e:
        raise RuntimeError(f"Failed to load weights '{model_name}': {e}") from e

    logger.info("Exporting to ONNX (imgsz=%d, opset=%d, simplify=%s)...", imgsz, opset, simplify)
    try:
        exported_str = model.export(
            format="onnx",
            imgsz=imgsz,
            opset=opset,
            dynamic=False,
            simplify=simplify,
        )
    except Exception as e:
        raise RuntimeError(f"Ultralytics export failed: {e}") from e

    exported_file = Path(exported_str)
    if not exported_file.is_file():
        raise RuntimeError(f"Export output file was not created: {exported_str}")

    if exported_file.resolve() != dest.resolve():
        shutil.copy2(str(exported_file), str(dest))
        logger.info("Moved exported model to '%s'.", dest)
    else:
        dest = exported_file

    # Validate the exported ONNX model
    validate_onnx_model(dest, expected_input_shape=(1, 3, imgsz, imgsz))
    return dest


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments for model export."""
    parser = argparse.ArgumentParser(
        description="Export Ultralytics YOLO Pose models to static ONNX format."
    )
    parser.add_argument(
        "--weights",
        "--model",
        dest="weights",
        type=str,
        default="yolo11n-pose.pt",
        help="Path to weights file or Ultralytics model identifier (default: yolo11n-pose.pt).",
    )
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        type=str,
        default=None,
        help="Destination directory for exported ONNX file.",
    )
    parser.add_argument(
        "--output",
        dest="output",
        type=str,
        default=None,
        help="Destination file path for exported ONNX file.",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Square input dimension for image width and height (default: 640).",
    )
    parser.add_argument(
        "--opset",
        type=int,
        default=17,
        help="Target ONNX opset version (default: 17).",
    )
    parser.add_argument(
        "--simplify",
        action="store_true",
        default=True,
        help="Run ONNX graph simplification (default: True).",
    )
    parser.add_argument(
        "--no-simplify",
        dest="simplify",
        action="store_false",
        help="Disable ONNX graph simplification.",
    )
    return parser.parse_args(args)


def main() -> None:
    """CLI entry point for export_onnx."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    args = parse_args()

    # Determine destination path
    dest_path = None
    if args.output:
        dest_path = Path(args.output)
    elif args.output_dir:
        dest_path = Path(args.output_dir)

    try:
        out = export_model(
            model_name=args.weights,
            output_path=dest_path,
            imgsz=args.imgsz,
            opset=args.opset,
            simplify=args.simplify,
        )
        logger.info("Successfully exported and validated ONNX model: %s", out)
        sys.exit(0)
    except Exception as e:
        logger.error("Export process failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
