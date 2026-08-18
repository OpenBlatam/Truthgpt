"""
Exceptions for TruthGPT Models Module
======================================
Comprehensive exception hierarchy for model loading, saving, compilation,
inference, attention mechanisms, diffusion pipelines, and device management.
"""

from typing import Any, Dict, Optional


class ModelError(Exception):
    """Base exception for all model errors in optimization_core."""

    def __init__(
        self,
        message: str,
        original_exception: Optional[Exception] = None,
        model_name: Optional[str] = None,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.original_exception = original_exception
        self.model_name = model_name
        self.component = component or "Model"
        self.details = details or {}
        if kwargs:
            self.details.update(kwargs)

    def __str__(self) -> str:
        ctx = []
        if self.model_name:
            ctx.append(f"model='{self.model_name}'")
        if self.component:
            ctx.append(f"component='{self.component}'")
        if self.original_exception:
            ctx.append(f"caused_by={self.original_exception.__class__.__name__}: {self.original_exception}")
        suffix = f" [{', '.join(ctx)}]" if ctx else ""
        return f"{self.message}{suffix}"


class ModelNotFoundError(ModelError):
    """Raised when a requested model, checkpoint, or configuration cannot be found."""

    def __init__(
        self,
        message: str = "Model not found",
        original_exception: Optional[Exception] = None,
        model_name: Optional[str] = None,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message,
            original_exception=original_exception,
            model_name=model_name,
            component=component or "ModelRegistry",
            details=details,
            **kwargs,
        )


class ModelInitializationError(ModelError):
    """Raised when a model fails to instantiate or initialize its architecture."""

    def __init__(
        self,
        message: str = "Failed to initialize model",
        original_exception: Optional[Exception] = None,
        model_name: Optional[str] = None,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message,
            original_exception=original_exception,
            model_name=model_name,
            component=component or "ModelInit",
            details=details,
            **kwargs,
        )


class ModelLoadError(ModelError):
    """Raised when loading model weights, tokenizers, or configurations fails."""

    def __init__(
        self,
        message: str = "Failed to load model weights or config",
        original_exception: Optional[Exception] = None,
        model_name: Optional[str] = None,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message,
            original_exception=original_exception,
            model_name=model_name,
            component=component or "ModelLoader",
            details=details,
            **kwargs,
        )


class ModelSaveError(ModelError):
    """Raised when saving model weights, checkpoints, or state dictionaries fails."""

    def __init__(
        self,
        message: str = "Failed to save model",
        original_exception: Optional[Exception] = None,
        model_name: Optional[str] = None,
        path: Optional[str] = None,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        d = details or {}
        if path:
            d["path"] = path
        super().__init__(
            message,
            original_exception=original_exception,
            model_name=model_name,
            component=component or "ModelSaver",
            details=d,
            **kwargs,
        )


class ModelInferenceError(ModelError):
    """Raised when an error occurs during model forward pass, generation, or decoding."""

    def __init__(
        self,
        message: str = "Inference execution error",
        original_exception: Optional[Exception] = None,
        model_name: Optional[str] = None,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message,
            original_exception=original_exception,
            model_name=model_name,
            component=component or "ModelInference",
            details=details,
            **kwargs,
        )


class ModelConfigurationError(ModelError, ValueError):
    """Raised when model hyperparameters or settings are invalid or incompatible."""

    def __init__(
        self,
        message: str = "Invalid model configuration",
        original_exception: Optional[Exception] = None,
        model_name: Optional[str] = None,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message,
            original_exception=original_exception,
            model_name=model_name,
            component=component or "ModelConfig",
            details=details,
            **kwargs,
        )


class ModelOptimizationError(ModelError):
    """Raised when applying optimizations (LoRA, torch.compile, pruning, SDPA) fails."""

    def __init__(
        self,
        message: str = "Optimization pass failed",
        original_exception: Optional[Exception] = None,
        model_name: Optional[str] = None,
        optimization_type: Optional[str] = None,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        d = details or {}
        if optimization_type:
            d["optimization_type"] = optimization_type
        super().__init__(
            message,
            original_exception=original_exception,
            model_name=model_name,
            component=component or "ModelOptimization",
            details=d,
            **kwargs,
        )


class DeviceAllocationError(ModelError):
    """Raised when device allocation, memory allocation, or offloading fails."""

    def __init__(
        self,
        message: str = "Device placement error",
        original_exception: Optional[Exception] = None,
        model_name: Optional[str] = None,
        target_device: Optional[str] = None,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        d = details or {}
        if target_device:
            d["target_device"] = str(target_device)
        super().__init__(
            message,
            original_exception=original_exception,
            model_name=model_name,
            component=component or "DeviceManager",
            details=d,
            **kwargs,
        )


# Alias for backward compatibility
DevicePlacementError = DeviceAllocationError


class UnsupportedArchitectureError(ModelError):
    """Raised when an unsupported model architecture or pipeline type is requested."""

    def __init__(
        self,
        message: str = "Unsupported model architecture",
        original_exception: Optional[Exception] = None,
        architecture: Optional[str] = None,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        d = details or {}
        if architecture:
            d["architecture"] = str(architecture)
        super().__init__(
            message,
            original_exception=original_exception,
            model_name=architecture,
            component=component or "ArchitectureResolver",
            details=d,
            **kwargs,
        )


class DependencyMissingError(ModelError):
    """Raised when an optional dependency (e.g. diffusers, transformers, xformers) is missing."""

    def __init__(
        self,
        message: str = "Required dependency is missing",
        original_exception: Optional[Exception] = None,
        package_name: Optional[str] = None,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        d = details or {}
        if package_name:
            d["package_name"] = str(package_name)
        super().__init__(
            message,
            original_exception=original_exception,
            component=component or "DependencyManager",
            details=d,
            **kwargs,
        )


class QuantizationError(ModelOptimizationError):
    """Raised when model quantization (4-bit, 8-bit, AWQ, GPTQ, FP8) fails."""

    def __init__(
        self,
        message: str = "Model quantization failed",
        original_exception: Optional[Exception] = None,
        model_name: Optional[str] = None,
        quantization_type: Optional[str] = None,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message,
            original_exception=original_exception,
            model_name=model_name,
            optimization_type=quantization_type or "quantization",
            component=component or "QuantizationManager",
            details=details,
            **kwargs,
        )


class AttentionError(ModelOptimizationError):
    """Raised when attention mechanism configuration or kernel execution fails."""

    def __init__(
        self,
        message: str = "Attention mechanism error",
        original_exception: Optional[Exception] = None,
        backend: Optional[str] = None,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        d = details or {}
        if backend:
            d["backend"] = backend
        super().__init__(
            message,
            original_exception=original_exception,
            component=component or "AttentionEngine",
            optimization_type="attention",
            details=d,
            **kwargs,
        )


class DiffusionError(ModelError):
    """Raised when diffusion pipeline creation, scheduling, or generation fails."""

    def __init__(
        self,
        message: str = "Diffusion pipeline error",
        original_exception: Optional[Exception] = None,
        pipeline_type: Optional[str] = None,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        d = details or {}
        if pipeline_type:
            d["pipeline_type"] = pipeline_type
        super().__init__(
            message,
            original_exception=original_exception,
            component=component or "DiffusionManager",
            details=d,
            **kwargs,
        )


__all__ = [
    "ModelError",
    "ModelNotFoundError",
    "ModelInitializationError",
    "ModelLoadError",
    "ModelSaveError",
    "ModelInferenceError",
    "ModelConfigurationError",
    "ModelOptimizationError",
    "DeviceAllocationError",
    "DevicePlacementError",
    "UnsupportedArchitectureError",
    "DependencyMissingError",
    "QuantizationError",
    "AttentionError",
    "DiffusionError",
]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.models."):
        sys.modules["models." + __name__[len("optimization_core.models."):]] = _mod
    elif __name__.startswith("models."):
        sys.modules["optimization_core.models." + __name__[len("models."):]] = _mod
