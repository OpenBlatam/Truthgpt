"""
Training System Exception Hierarchy
===================================
Typed exception classes for all training, checkpointing, EMA, evaluation,
tracking, and pipeline execution failures.
"""

from typing import Any, Dict, Optional


class TrainingBaseException(Exception):
    """Base exception for all errors within the optimization_core.training module."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        if self.context:
            ctx_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            return f"{self.message} (Context: {ctx_str})"
        return self.message


class TrainingError(TrainingBaseException, RuntimeError):
    """Exception raised when a training loop or execution step fails."""

    pass


class TrainingConfigurationError(TrainingBaseException, ValueError):
    """Exception raised when invalid training parameters or configuration are supplied."""

    pass


class GradientOverflowError(TrainingError):
    """Exception raised when gradients produce Inf or NaN values during optimization."""

    pass


class DeviceTransferError(TrainingError):
    """Exception raised when transferring batch data or models across devices fails."""

    pass


class EarlyStoppingTriggered(TrainingBaseException):
    """Exception/signal raised when early stopping criteria are met."""

    def __init__(
        self,
        message: str = "Early stopping triggered.",
        patience: int = 0,
        best_metric: Optional[float] = None,
        current_metric: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        ctx = context or {}
        ctx.update({"patience": patience, "best_metric": best_metric, "current_metric": current_metric})
        super().__init__(message, context=ctx)
        self.patience = patience
        self.best_metric = best_metric
        self.current_metric = current_metric


class CheckpointError(TrainingBaseException, RuntimeError):
    """Exception raised when saving, loading, or managing a model checkpoint fails."""

    pass


class CheckpointNotFoundError(CheckpointError, FileNotFoundError):
    """Exception raised when a requested checkpoint path does not exist."""

    pass


class CheckpointCorruptedError(CheckpointError, ValueError):
    """Exception raised when a checkpoint file is incomplete, unreadable, or corrupted."""

    pass


class EMAError(TrainingBaseException, RuntimeError):
    """Exception raised when Exponential Moving Average operations fail."""

    pass


class EvaluationError(TrainingBaseException, RuntimeError):
    """Exception raised when model validation or metric calculation fails."""

    pass


class ExperimentTrackerError(TrainingBaseException, RuntimeError):
    """Exception raised when logging metrics, parameters, or artifacts to a tracker fails."""

    pass


class PipelineError(TrainingBaseException, RuntimeError):
    """Exception raised when an end-to-end training pipeline fails."""

    pass
