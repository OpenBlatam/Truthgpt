"""
Abstract interfaces, base classes, and protocols for trainers components.

Enforces clean architectural boundaries and dependency inversion across managers,
trackers, callbacks, and trainers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List, Union
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from .types import StepState, EvalMetrics, TrainerState


class BaseCallback(ABC):
    """Abstract interface for training event callbacks."""

    def on_train_begin(self, state: Dict[str, Any]) -> None:
        """Called at the beginning of training."""
        pass

    def on_train_end(self, state: Dict[str, Any]) -> None:
        """Called at the end of training."""
        pass

    def on_epoch_begin(self, epoch: int, state: Dict[str, Any]) -> None:
        """Called at the beginning of each epoch."""
        pass

    def on_epoch_end(self, epoch: int, state: Dict[str, Any]) -> None:
        """Called at the end of each epoch."""
        pass

    def on_step_begin(self, step: int, state: Dict[str, Any]) -> None:
        """Called before step computation."""
        pass

    def on_step_end(self, step: int, state: Dict[str, Any]) -> None:
        """Called after step computation."""
        pass

    def on_log(self, state: Dict[str, Any]) -> None:
        """Called when logging step metrics."""
        pass

    def on_eval(self, state: Dict[str, Any]) -> None:
        """Called after validation evaluation."""
        pass

    def on_save(self, state: Dict[str, Any]) -> None:
        """Called when a checkpoint is saved."""
        pass

    def on_exception(self, exception: Exception, state: Dict[str, Any]) -> None:
        """Called when an unhandled exception occurs during training."""
        pass


class BaseExperimentTracker(ABC):
    """Abstract interface for experiment tracking integrations."""

    @abstractmethod
    def log_metrics(self, metrics: Dict[str, Any], step: int) -> None:
        """Log metric dictionary at step."""
        pass

    @abstractmethod
    def log_hyperparams(self, params: Dict[str, Any]) -> None:
        """Log hyperparameter configuration."""
        pass

    @abstractmethod
    def finish(self) -> None:
        """Close tracker resources."""
        pass


class BaseModelManager(ABC):
    """Abstract interface for model loading and configuration management."""

    @abstractmethod
    def load_tokenizer(self) -> Any:
        """Load and return tokenizer."""
        pass

    @abstractmethod
    def load_model(self) -> nn.Module:
        """Load, configure, and return model."""
        pass

    @abstractmethod
    def get_model_for_operations(self) -> nn.Module:
        """Get the base unwrapped model."""
        pass

    @abstractmethod
    def get_total_params(self) -> Tuple[int, int]:
        """Get total and trainable parameter counts."""
        pass


class BaseOptimizerManager(ABC):
    """Abstract interface for optimizer and scheduler management."""

    @abstractmethod
    def create_optimizer(self, optimizer_type: str = "adamw") -> torch.optim.Optimizer:
        """Create and return optimizer."""
        pass

    @abstractmethod
    def create_scheduler(self, num_training_steps: int) -> Any:
        """Create and return learning rate scheduler."""
        pass

    @abstractmethod
    def create_scaler(self) -> Any:
        """Create and return gradient scaler."""
        pass

    @abstractmethod
    def zero_grad(self, set_to_none: bool = True) -> None:
        """Zero out model gradients."""
        pass

    @abstractmethod
    def get_lr(self) -> float:
        """Get current learning rate."""
        pass


class BaseDataManager(ABC):
    """Abstract interface for dataset loading and DataLoader construction."""

    @abstractmethod
    def create_loaders(
        self, train_texts: List[str], val_texts: List[str]
    ) -> Tuple[DataLoader, DataLoader]:
        """Create and return training and validation DataLoaders."""
        pass


class BaseCheckpointManager(ABC):
    """Abstract interface for checkpoint saving, loading, and pruning."""

    @abstractmethod
    def save(
        self,
        filename: str,
        step: int = 0,
        is_best: bool = False,
        metrics: Optional[Dict[str, float]] = None,
    ) -> str:
        """Save training checkpoint."""
        pass

    @abstractmethod
    def load(self, checkpoint_path: str) -> Dict[str, Any]:
        """Load training checkpoint."""
        pass

    @abstractmethod
    def prune_checkpoints(self) -> None:
        """Prune outdated checkpoints based on retention policy."""
        pass


class BaseEMAManager(ABC):
    """Abstract interface for Exponential Moving Average weight management."""

    @abstractmethod
    def update(self) -> None:
        """Update shadow parameters."""
        pass

    @abstractmethod
    def apply_ema(self) -> None:
        """Apply EMA weights to model."""
        pass

    @abstractmethod
    def restore_from_ema(self) -> None:
        """Restore original model weights from backup."""
        pass


class BaseEvaluator(ABC):
    """Abstract interface for model evaluation."""

    @abstractmethod
    def evaluate(self) -> Dict[str, float]:
        """Evaluate model performance on validation set."""
        pass

    @abstractmethod
    def select_best_metric(self, metrics: Dict[str, float]) -> float:
        """Select target metric value based on evaluation criteria."""
        pass


class BaseTrainer(ABC):
    """Abstract interface for training orchestrator."""

    @abstractmethod
    def train(self) -> None:
        """Execute full training loop."""
        pass

    @abstractmethod
    def evaluate(self) -> Dict[str, float]:
        """Evaluate current model performance."""
        pass

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from prompt."""
        pass


# Explicit 'I'-prefixed interface aliases for strict interface compliance
ICallback = BaseCallback
IExperimentTracker = BaseExperimentTracker
IModelManager = BaseModelManager
IOptimizerManager = BaseOptimizerManager
IDataManager = BaseDataManager
ICheckpointManager = BaseCheckpointManager
IEMAManager = BaseEMAManager
IEvaluator = BaseEvaluator
ITrainer = BaseTrainer


__all__ = [
    "BaseCallback",
    "BaseExperimentTracker",
    "BaseModelManager",
    "BaseOptimizerManager",
    "BaseDataManager",
    "BaseCheckpointManager",
    "BaseEMAManager",
    "BaseEvaluator",
    "BaseTrainer",
    "ICallback",
    "IExperimentTracker",
    "IModelManager",
    "IOptimizerManager",
    "IDataManager",
    "ICheckpointManager",
    "IEMAManager",
    "IEvaluator",
    "ITrainer",
]
