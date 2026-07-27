"""
Domain-specific exceptions for optimization_core.trainers package.

Provides a unified, structured exception hierarchy for training, management, configuration,
and execution errors with full compatibility with built-in PyTorch/Python exceptions.

Enhancements:
- ErrorSeverity classification on every exception
- Automatic timestamps for error forensics
- ``to_dict()`` / ``to_json()`` for structured logging
- ``from_exception()`` factory for wrapping arbitrary errors
- ``chain_context()`` for progressive context enrichment
- Missing exceptions: DistributedError, EarlyStoppingException, SchedulerError,
  TokenizerError, ProfilingError, RegistryError, SerializationError
"""
from __future__ import annotations

import json
import time
import traceback
from typing import Any, Dict, Optional

from .types import ErrorSeverity


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class TrainerError(Exception):
    """
    Base exception for all errors originating in the trainers package.

    Attributes:
        message: The primary error message.
        context: Key-value diagnostic context.
        error_code: Standardized error identifier.
        component: Component or module where the exception occurred.
        suggested_action: Actionable guidance for remediation.
        severity: ErrorSeverity classification.
        timestamp: UTC epoch timestamp when the error was created.
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_TRAINER_GENERIC",
        component: str = "trainers",
        suggested_action: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.error_code = error_code
        self.component = component
        self.suggested_action = suggested_action
        self.severity = severity
        self.timestamp: float = time.time()

    # -- Serialisation helpers ------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize exception details to a dictionary."""
        return {
            "error_code": self.error_code,
            "component": self.component,
            "message": self.message,
            "context": self.context,
            "suggested_action": self.suggested_action,
            "severity": self.severity.value if isinstance(self.severity, ErrorSeverity) else str(self.severity),
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        """Serialize exception to JSON string for structured logging."""
        return json.dumps(self.to_dict(), default=str)

    # -- Context enrichment ---------------------------------------------------

    def chain_context(self, **extra: Any) -> "TrainerError":
        """Return self after adding key-value pairs to the diagnostic context."""
        self.context.update(extra)
        return self

    # -- Factory --------------------------------------------------------------

    @classmethod
    def from_exception(
        cls,
        exc: BaseException,
        component: str = "trainers",
        context: Optional[Dict[str, Any]] = None,
    ) -> "TrainerError":
        """Wrap an arbitrary exception into a ``TrainerError``."""
        ctx = dict(context or {})
        ctx["original_type"] = type(exc).__qualname__
        ctx["original_traceback"] = traceback.format_exception(type(exc), exc, exc.__traceback__)
        return cls(
            message=str(exc),
            context=ctx,
            component=component,
        )

    # -- String representations -----------------------------------------------

    def __str__(self) -> str:
        parts = [f"[{self.error_code}] {self.message}"]
        if self.component:
            parts.append(f"Component: {self.component}")
        if self.context:
            parts.append(f"Context: {self.context}")
        if self.suggested_action:
            parts.append(f"Remedy: {self.suggested_action}")
        return " | ".join(parts)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(code={self.error_code!r}, "
            f"component={self.component!r}, severity={self.severity.value})"
        )


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class ConfigurationError(TrainerError, ValueError):
    """Raised when configuration validation or parsing fails."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_CONFIG_INVALID")
        kwargs.setdefault("component", "TrainerConfig")
        super().__init__(message, context=context, **kwargs)


class ConfigValidationError(ConfigurationError):
    """Raised when specific config fields fail validation constraints."""
    pass


class SerializationError(ConfigurationError):
    """Raised when config serialization (JSON/YAML/TOML) fails."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_SERIALIZATION")
        kwargs.setdefault("component", "ConfigSerialization")
        super().__init__(message, context=context, **kwargs)


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

class ModelManagerError(TrainerError, RuntimeError):
    """Raised when model loading, LoRA application, or target device configuration fails."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_MODEL_MANAGER")
        kwargs.setdefault("component", "ModelManager")
        super().__init__(message, context=context, **kwargs)


class ModelInitializationError(ModelManagerError):
    """Raised when model weight initialisation or architecture construction fails."""
    pass


class TokenizerError(ModelManagerError):
    """Raised when tokenizer loading or configuration fails."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_TOKENIZER")
        kwargs.setdefault("component", "Tokenizer")
        super().__init__(message, context=context, **kwargs)


# ---------------------------------------------------------------------------
# Optimiser
# ---------------------------------------------------------------------------

class OptimizerManagerError(TrainerError, RuntimeError):
    """Raised when optimizer or learning rate scheduler instantiation or execution fails."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_OPTIMIZER_MANAGER")
        kwargs.setdefault("component", "OptimizerManager")
        super().__init__(message, context=context, **kwargs)


class OptimizerError(OptimizerManagerError):
    """Raised during optimizer step execution."""
    pass


class GradientNaNError(OptimizerManagerError):
    """Raised when gradients contain NaN or Inf values during training."""
    def __init__(
        self,
        message: str = "Gradient contains NaN or Inf values.",
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("error_code", "ERR_GRADIENT_NAN")
        kwargs.setdefault("severity", ErrorSeverity.CRITICAL)
        kwargs.setdefault("suggested_action", "Reduce learning rate, enable gradient clipping, or switch mixed precision mode.")
        super().__init__(message, context=context, **kwargs)


class SchedulerError(OptimizerManagerError):
    """Raised when learning-rate scheduler creation or stepping fails."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_SCHEDULER")
        kwargs.setdefault("component", "Scheduler")
        super().__init__(message, context=context, **kwargs)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

class DataManagerError(TrainerError, RuntimeError):
    """Raised when data loading, dataset wrapping, or batch sampling encounters an error."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_DATA_MANAGER")
        kwargs.setdefault("component", "DataManager")
        super().__init__(message, context=context, **kwargs)


class DataLoadingError(DataManagerError):
    """Raised when raw data cannot be loaded or parsed."""
    pass


class DatasetError(DataManagerError):
    """Raised when dataset construction or indexing fails."""
    pass


# ---------------------------------------------------------------------------
# Checkpoint
# ---------------------------------------------------------------------------

class CheckpointError(TrainerError, RuntimeError, IOError):
    """Raised when checkpoint saving, loading, validation, or pruning fails."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_CHECKPOINT_MANAGER")
        kwargs.setdefault("component", "CheckpointManager")
        super().__init__(message, context=context, **kwargs)


class CheckpointCorruptionError(CheckpointError):
    """Raised when a checkpoint file is missing required fields or corrupted."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_CHECKPOINT_CORRUPTED")
        kwargs.setdefault("severity", ErrorSeverity.CRITICAL)
        kwargs.setdefault("suggested_action", "Verify file integrity or load an earlier checkpoint.")
        super().__init__(message, context=context, **kwargs)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

class EvaluationError(TrainerError, RuntimeError):
    """Raised when validation or metric calculation encounters a runtime failure."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_EVALUATOR")
        kwargs.setdefault("component", "Evaluator")
        super().__init__(message, context=context, **kwargs)


# ---------------------------------------------------------------------------
# EMA
# ---------------------------------------------------------------------------

class EMAError(TrainerError, RuntimeError):
    """Raised when Exponential Moving Average (EMA) weight shadow operations fail."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_EMA_MANAGER")
        kwargs.setdefault("component", "EMAManager")
        super().__init__(message, context=context, **kwargs)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

class CallbackError(TrainerError, RuntimeError):
    """Raised when a callback execution hook encounters an unrecoverable failure."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_CALLBACK_EXECUTION")
        kwargs.setdefault("component", "CallbackHandler")
        super().__init__(message, context=context, **kwargs)


class CallbackExecutionError(CallbackError):
    """Raised when a specific callback method raises during dispatch."""
    pass


# ---------------------------------------------------------------------------
# Hardware & distributed
# ---------------------------------------------------------------------------

class HardwareError(TrainerError, RuntimeError):
    """Raised when hardware setup or device allocation encounters an error."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_HARDWARE_CONFIG")
        kwargs.setdefault("component", "HardwareConfig")
        super().__init__(message, context=context, **kwargs)


class OOMError(HardwareError):
    """Raised when GPU/CPU out-of-memory occurs during training or evaluation."""
    def __init__(self, message: str = "Out of Memory encountered.", context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_OUT_OF_MEMORY")
        kwargs.setdefault("severity", ErrorSeverity.CRITICAL)
        kwargs.setdefault("suggested_action", "Decrease batch size, enable gradient checkpointing, or increase gradient accumulation steps.")
        super().__init__(message, context=context, **kwargs)


class DistributedError(TrainerError, RuntimeError):
    """Raised when distributed training setup, communication, or teardown fails."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_DISTRIBUTED")
        kwargs.setdefault("component", "DistributedManager")
        super().__init__(message, context=context, **kwargs)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class StateMismatchError(TrainerError, RuntimeError):
    """Raised when state dict or model parameter shapes do not match."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_STATE_MISMATCH")
        kwargs.setdefault("component", "StateRestoration")
        super().__init__(message, context=context, **kwargs)


# ---------------------------------------------------------------------------
# Early stopping (control-flow exception, not an error)
# ---------------------------------------------------------------------------

class EarlyStoppingException(TrainerError):
    """
    Raised to signal that early stopping criteria have been met.

    This is a *control-flow* exception — it is not an error.  The trainer should
    catch it, save a final checkpoint, and exit cleanly.
    """
    def __init__(
        self,
        message: str = "Early stopping criteria met.",
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("error_code", "EARLY_STOPPING")
        kwargs.setdefault("component", "EarlyStopping")
        kwargs.setdefault("severity", ErrorSeverity.INFO)
        super().__init__(message, context=context, **kwargs)


# ---------------------------------------------------------------------------
# Profiling & Registry
# ---------------------------------------------------------------------------

class ProfilingError(TrainerError, RuntimeError):
    """Raised when profiling initialisation or collection fails."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_PROFILING")
        kwargs.setdefault("component", "Profiler")
        super().__init__(message, context=context, **kwargs)


class RegistryError(TrainerError, KeyError):
    """Raised when component registration or lookup fails."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "ERR_REGISTRY")
        kwargs.setdefault("component", "TrainerRegistry")
        super().__init__(message, context=context, **kwargs)


# ---------------------------------------------------------------------------
# __all__
# ---------------------------------------------------------------------------

__all__ = [
    # Base
    "TrainerError",
    # Config
    "ConfigurationError",
    "ConfigValidationError",
    "SerializationError",
    # Model
    "ModelManagerError",
    "ModelInitializationError",
    "TokenizerError",
    # Optimizer
    "OptimizerManagerError",
    "OptimizerError",
    "GradientNaNError",
    "SchedulerError",
    # Data
    "DataManagerError",
    "DataLoadingError",
    "DatasetError",
    # Checkpoint
    "CheckpointError",
    "CheckpointCorruptionError",
    # Evaluation
    "EvaluationError",
    # EMA
    "EMAError",
    # Callbacks
    "CallbackError",
    "CallbackExecutionError",
    # Hardware & distributed
    "HardwareError",
    "OOMError",
    "DistributedError",
    # State
    "StateMismatchError",
    # Control flow
    "EarlyStoppingException",
    # Profiling & registry
    "ProfilingError",
    "RegistryError",
]
