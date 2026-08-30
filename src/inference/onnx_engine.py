"""
src/inference/onnx_engine.py
Hardware-accelerated ONNX Runtime inference wrapper.
"""

from pathlib import Path
from typing import Any, List, Optional, Tuple, Union
import logging
import numpy as np
import onnxruntime as ort

logger = logging.getLogger("onnx_engine")

DEFAULT_PROVIDERS: List[str] = [
    "CoreMLExecutionProvider",
    "CPUExecutionProvider",
]


class OnnxEngine:
    """
    Encapsulates an ONNX Runtime InferenceSession with automated provider negotiation,
    thread configuration, and tensor verification.
    """

    def __init__(
        self,
        model_path: Union[str, Path],
        providers: Optional[List[str]] = None,
        num_threads: int = 4,
    ) -> None:
        """
        Initialize the ONNX runtime session.

        Args:
            model_path: Path to the ONNX model file.
            providers: Ordered list of preferred execution providers. Defaults to
                       ['CoreMLExecutionProvider', 'CPUExecutionProvider'].
            num_threads: Intra-op thread pool size for CPU execution. Default: 4.

        Raises:
            FileNotFoundError: If model_path does not exist.
            RuntimeError: If ONNX Runtime fails to initialize session.
        """
        self.model_path = Path(model_path)
        if not self.model_path.is_file():
            raise FileNotFoundError(f"ONNX model file not found: {self.model_path}")

        # Configure session options
        self.session_options = ort.SessionOptions()
        self.session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session_options.intra_op_num_threads = num_threads
        self.session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

        # Provider negotiation
        target_providers = self._resolve_providers(providers)
        self._session = self._initialize_session(target_providers)

        # Inspect session IO contracts
        inputs = self._session.get_inputs()
        outputs = self._session.get_outputs()

        if not inputs:
            raise RuntimeError("Loaded ONNX model contains no input tensors.")
        if not outputs:
            raise RuntimeError("Loaded ONNX model contains no output tensors.")

        self.input_name: str = inputs[0].name
        self.input_shape: Tuple[int, ...] = tuple(inputs[0].shape)
        self.input_type: str = inputs[0].type

        self.output_name: str = outputs[0].name
        self.output_shape: Tuple[int, ...] = tuple(outputs[0].shape)
        self.output_type: str = outputs[0].type

        self.active_providers: List[str] = self._session.get_providers()
        logger.info(
            "OnnxEngine initialized successfully for '%s' with providers: %s",
            self.model_path.name,
            self.active_providers,
        )

    def _resolve_providers(self, requested_providers: Optional[List[str]]) -> List[str]:
        """Filter requested providers against available runtime providers."""
        available = ort.get_available_providers()
        candidates = requested_providers if requested_providers is not None else DEFAULT_PROVIDERS

        matched = [p for p in candidates if p in available]
        if not matched:
            logger.warning(
                "None of requested providers %s are available. Falling back to CPUExecutionProvider.",
                candidates,
            )
            matched = ["CPUExecutionProvider"]
        return matched

    def _initialize_session(self, providers: List[str]) -> ort.InferenceSession:
        """Attempt session creation with provider fallback."""
        try:
            return ort.InferenceSession(
                str(self.model_path),
                sess_options=self.session_options,
                providers=providers,
            )
        except Exception as e:
            if "CoreMLExecutionProvider" in providers and "CPUExecutionProvider" in providers:
                logger.warning(
                    "Session init with providers %s failed (%s); falling back to CPUExecutionProvider.",
                    providers,
                    e,
                )
                try:
                    return ort.InferenceSession(
                        str(self.model_path),
                        sess_options=self.session_options,
                        providers=["CPUExecutionProvider"],
                    )
                except Exception as cpu_e:
                    raise RuntimeError(f"CPUExecutionProvider fallback failed: {cpu_e}") from cpu_e
            raise RuntimeError(f"Failed to initialize ONNX Runtime session: {e}") from e

    def infer(self, input_tensor: np.ndarray) -> np.ndarray:
        """
        Execute forward inference pass on input tensor.

        Args:
            input_tensor: Preprocessed numpy ndarray with shape matching self.input_shape
                          (default: (1, 3, 640, 640)) and dtype float32.

        Returns:
            Raw model output numpy ndarray with shape matching self.output_shape
            (default: (1, 56, 8400)) and dtype float32.

        Raises:
            TypeError: If input_tensor is not a numpy array or dtype is not np.float32.
            ValueError: If input_tensor shape does not match model input contract.
            RuntimeError: If execution fails during session.run.
        """
        if not isinstance(input_tensor, np.ndarray):
            raise TypeError(
                f"input_tensor must be a numpy.ndarray, got {type(input_tensor).__name__}"
            )

        if input_tensor.dtype != np.float32:
            raise TypeError(
                f"Invalid tensor dtype {input_tensor.dtype}: np.float32 is required."
            )

        if tuple(input_tensor.shape) != self.input_shape:
            raise ValueError(
                f"Input tensor shape mismatch: expected {self.input_shape}, got {tuple(input_tensor.shape)}"
            )

        # Ensure contiguous memory layout
        if not input_tensor.flags.c_contiguous:
            input_tensor = np.ascontiguousarray(input_tensor)

        try:
            outputs = self._session.run([self.output_name], {self.input_name: input_tensor})
            return outputs[0]
        except Exception as e:
            raise RuntimeError(f"Inference execution failed: {e}") from e

    def get_providers(self) -> List[str]:
        """Return the list of execution providers actively bound to this session."""
        return list(self.active_providers)

    def get_input_details(self) -> dict[str, Any]:
        """Return input node metadata (name, shape, type)."""
        return {
            "name": self.input_name,
            "shape": self.input_shape,
            "type": self.input_type,
        }

    def get_output_details(self) -> dict[str, Any]:
        """Return output node metadata (name, shape, type)."""
        return {
            "name": self.output_name,
            "shape": self.output_shape,
            "type": self.output_type,
        }
