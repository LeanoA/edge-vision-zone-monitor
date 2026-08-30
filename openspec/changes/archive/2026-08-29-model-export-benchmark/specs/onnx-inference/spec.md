# Specification: ONNX Inference Engine (`onnx-inference`)

## Overview
The `onnx-inference` capability provides an edge-optimized runtime inference wrapper (`OnnxEngine`) in `src/inference/onnx_engine.py` built on top of ONNX Runtime. It encapsulates execution provider negotiation (prioritizing Apple Silicon `CoreMLExecutionProvider` with graceful fallback to multi-threaded `CPUExecutionProvider`), thread configuration, memory allocation, and deterministic forward pass execution.

## ADDED Requirements

### Requirement: Hardware-Accelerated Execution Provider Negotiation
The `OnnxEngine` MUST support automated provider negotiation, attempting to bind `CoreMLExecutionProvider` when running on macOS/Apple Silicon, and falling back gracefully to `CPUExecutionProvider` if CoreML is unavailable or unsupported.

#### Scenario: Initializing engine with CoreML acceleration
- **GIVEN** an environment where `CoreMLExecutionProvider` is registered in `onnxruntime.get_available_providers()`
- **WHEN** `OnnxEngine(model_path)` is initialized without explicit provider override
- **THEN** the session SHALL include `CoreMLExecutionProvider` as the primary execution provider
- **AND** `engine.active_providers` SHALL list `CoreMLExecutionProvider` followed by `CPUExecutionProvider`.

#### Scenario: Graceful fallback when CoreML is unavailable
- **GIVEN** an environment where `CoreMLExecutionProvider` is not available or initialization raises an exception
- **WHEN** `OnnxEngine(model_path)` is instantiated
- **THEN** the engine SHALL fallback to `CPUExecutionProvider`
- **AND** a warning SHALL be logged indicating that CoreML is unavailable and CPU execution will be utilized
- **AND** initialization SHALL complete successfully without raising an uncaught exception.

#### Scenario: Explicit provider override
- **GIVEN** an operator specifying `providers=["CPUExecutionProvider"]`
- **WHEN** `OnnxEngine(model_path, providers=["CPUExecutionProvider"])` is created
- **THEN** the ONNX session SHALL exclusively use `CPUExecutionProvider`.

---

### Requirement: Session Configuration and Thread Affinity Optimization
The `OnnxEngine` SHALL configure `onnxruntime.SessionOptions` to optimize execution performance, setting graph optimization levels to `ORT_ENABLE_ALL` and configuring intra-op and inter-op thread counts.

#### Scenario: Configuring session optimization and thread limits
- **GIVEN** an `OnnxEngine` configuration with `num_threads=4`
- **WHEN** the ONNX Runtime `InferenceSession` is instantiated
- **THEN** `SessionOptions.graph_optimization_level` SHALL be set to `GraphOptimizationLevel.ORT_ENABLE_ALL`
- **AND** `SessionOptions.intra_op_num_threads` SHALL be set to 4
- **AND** `SessionOptions.execution_mode` SHALL be configured for sequential execution (`ExecutionMode.ORT_SEQUENTIAL`).

---

### Requirement: Deterministic Tensor Precondition Validation
The `OnnxEngine` MUST validate input tensor constraints before executing inference to prevent silent memory corruption or execution failures.

#### Scenario: Executing inference with valid input tensor
- **GIVEN** an initialized `OnnxEngine` loaded with a $640 \times 640$ YOLO Pose model
- **WHEN** `engine.infer(tensor)` is invoked with an array of shape `(1, 3, 640, 640)` and dtype `np.float32`
- **THEN** the input tensor SHALL pass validation
- **AND** the engine SHALL dispatch the tensor to the ONNX Runtime session.

#### Scenario: Rejecting invalid tensor shape
- **GIVEN** an initialized `OnnxEngine` expecting input shape `(1, 3, 640, 640)`
- **WHEN** `engine.infer(tensor)` is invoked with a tensor of shape `(1, 3, 320, 320)` or `(2, 3, 640, 640)`
- **THEN** the engine SHALL raise a `ValueError` detailing the expected versus received dimensions
- **AND** no forward pass SHALL be executed on the underlying session.

#### Scenario: Rejecting invalid tensor data type
- **GIVEN** an initialized `OnnxEngine` expecting `float32`
- **WHEN** `engine.infer(tensor)` is invoked with a `uint8` or `float64` tensor
- **THEN** the engine SHALL raise a `TypeError` specifying that `np.float32` is required.

---

### Requirement: Raw Tensor Inference Execution and Output Contract
The `OnnxEngine` forward pass MUST return raw output predictions as a contiguous NumPy array matching the model's output specification `(1, 56, 8400)`.

#### Scenario: Producing standard pose estimation output
- **GIVEN** a preprocessed dummy input tensor of shape `(1, 3, 640, 640)`
- **WHEN** `output = engine.infer(tensor)` completes execution
- **THEN** `output` SHALL be a NumPy ndarray of dtype `float32`
- **AND** `output.shape` SHALL equal `(1, 56, 8400)`
- **AND** `output` SHALL contain bounding box coordinates, confidences, and 17 keypoint predictions.
