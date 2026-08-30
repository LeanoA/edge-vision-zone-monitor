# Specification: Model Export (`model-export`)

## Overview
The `model-export` capability provides an automated, reproducible command-line toolchain to export Ultralytics YOLO Pose models (`yolo11n-pose` / `yolov8n-pose`) into high-performance, statically shaped ONNX models. It enforces industrial edge deployment constraints, ensuring graph topology integrity and standard input/output dimensions required for deterministic real-time inference.

## ADDED Requirements

### Requirement: CLI Model Export with Static Shape
The export utility SHALL provide a command-line interface (`models/export_onnx.py`) that exports YOLO Pose PyTorch checkpoints to ONNX format with fixed, static tensor dimensions $(1, 3, 640, 640)$ and explicit batch size 1.

#### Scenario: Exporting yolo11n-pose to static ONNX
- **GIVEN** a valid model weights identifier or path `yolo11n-pose.pt`
- **WHEN** the operator invokes `python models/export_onnx.py --weights yolo11n-pose.pt --output-dir models/`
- **THEN** an ONNX model file `models/yolo11n-pose.onnx` SHALL be created
- **AND** the ONNX model graph input tensor SHALL have static dimensions `[1, 3, 640, 640]` with no dynamic dimension axes.

#### Scenario: Exporting with custom resolution
- **GIVEN** a valid model checkpoint and an image size specification of 640
- **WHEN** the operator invokes `python models/export_onnx.py --weights yolov8n-pose.pt --imgsz 640`
- **THEN** the resulting ONNX model SHALL enforce static spatial dimensions $640 \times 640$.

---

### Requirement: Export Configuration Constraints (Opset 17 and Simplification)
The export process MUST enforce ONNX opset version 17 and MUST execute ONNX graph simplification (`simplify=True`) to eliminate redundant operations, constant folding, and dead nodes.

#### Scenario: Enforcing Opset 17 and Graph Simplification
- **GIVEN** a YOLO Pose model being exported
- **WHEN** the export routine is triggered
- **THEN** the output ONNX model graph SHALL specify `opset_version = 17`
- **AND** the ONNX model SHALL have constant folding applied, producing a simplified computational graph without unnecessary runtime shape assertions.

---

### Requirement: Post-Export ONNX Graph Topology and Shape Validation
The export toolchain MUST automatically validate the exported ONNX model using `onnx.checker` and `onnx.shape_inference` immediately after generation before declaring success.

#### Scenario: Validating well-formed ONNX model
- **GIVEN** a freshly exported ONNX model file
- **WHEN** the post-export verification step runs
- **THEN** `onnx.checker.check_model` SHALL execute with zero structural or type errors
- **AND** the input tensor SHALL be verified as `float32` with shape `(1, 3, 640, 640)`
- **AND** the output tensor SHALL be verified as `float32` with shape `(1, 56, 8400)`.

#### Scenario: Detecting corrupted or invalid graph
- **GIVEN** an exported model file with an inconsistent graph topology or mismatched output dimensions
- **WHEN** the post-export verification step executes
- **THEN** the toolchain SHALL raise a `ValidationError`
- **AND** the CLI SHALL terminate with a non-zero exit code
- **AND** an actionable diagnostic message SHALL be printed to stderr.

---

### Requirement: CLI Error Handling and Robust Execution
The CLI SHALL gracefully handle missing weights, invalid target directories, and unsupported arguments with clear diagnostic feedback and standard exit codes.

#### Scenario: Handling non-existent model weights
- **GIVEN** a weights path that does not exist and cannot be resolved by Ultralytics
- **WHEN** the export CLI is executed with `--weights invalid_path.pt`
- **THEN** the process SHALL log a descriptive error indicating the file cannot be located
- **AND** the process SHALL terminate with exit code 1 without generating an invalid ONNX file.
