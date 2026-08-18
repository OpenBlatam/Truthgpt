"""
Training System Interfaces and Protocols
========================================
Abstract base classes and interfaces defining contracts for training loops,
checkpoint managers, EMA tracking, evaluation, experiment tracking, callbacks,
and training pipelines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import torch
import torch.nn as nn
from torch.utils.data import DataLoader


class BaseCallback(ABC):
    """
    Abstract base class for training lifecycle callbacks.
    Provides hooks for key training, evaluation, saving, and error events.
    """

    def on_train_begin(self, state: Dict[str, Any]) -> None:
        """Called at the beginning of the entire training run."""
        pass

    def on_train_end(self, state: Dict[str, Any]) -> None:
        """Called at the end of the entire training run."""
        pass

    def on_epoch_begin(self, epoch: int, state: Dict[str, Any]) -> None:
        """Called before starting each epoch."""
        pass

    def on_epoch_end(self, epoch: int, state: Dict[str, Any]) -> None:
        """Called upon completion of each epoch."""
        pass

    def on_step_begin(self, step: int, state: Dict[str, Any]) -> None:
        """Called before starting each optimization step."""
        pass

    def on_step_end(self, step: int, state: Dict[str, Any]) -> None:
        """Called after completing each optimization step."""
        pass

    def on_log(self, metrics: Dict[str, Any], state: Dict[str, Any]) -> None:
        """Called when metrics are logged."""
        pass

    def on_eval(self, eval_metrics: Dict[str, Any], state: Dict[str, Any]) -> None:
        """Called after an evaluation run completes."""
        pass

    def on_save(self, checkpoint_path: str, state: Dict[str, Any]) -> None:
        """Called after a checkpoint has been written to disk."""
        pass

    def on_exception(self, exception: Exception, state: Dict[str, Any]) -> None:
        """Called when an unhandled error occurs during training."""
        pass


class BaseTrainingLoop(ABC):
    """
    Abstract interface for training loop execution.
    Orchestrates step-level forward/backward passes, optimizer steps,
    gradient clipping, and epoch iteration.
    """

    @abstractmethod
    def train_step(
        self,
        model: nn.Module,
        batch: Any,
        optimizer: torch.optim.Optimizer,
        scaler: Any,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute a single forward-backward pass and parameter update.

        Args:
            model: PyTorch module.
            batch: Input batch data.
            optimizer: PyTorch optimizer.
            scaler: Gradient scaler for mixed precision.
            **kwargs: Additional step parameters (e.g., step index).

        Returns:
            Dictionary with step metrics (e.g., 'loss', 'skipped').
        """
        pass

    @abstractmethod
    def train_epoch(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        optimizer: torch.optim.Optimizer,
        scheduler: Optional[Any] = None,
        scaler: Optional[Any] = None,
        step_callback: Optional[Callable[..., Any]] = None,
        epoch_callback: Optional[Callable[..., Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute training for one full epoch over train_loader.

        Args:
            model: PyTorch module.
            train_loader: Training data loader.
            optimizer: PyTorch optimizer.
            scheduler: Optional learning rate scheduler.
            scaler: Optional GradScaler.
            step_callback: Step hook.
            epoch_callback: Epoch hook.
            **kwargs: Extra parameters.

        Returns:
            Dictionary with epoch summary metrics.
        """
        pass

    @abstractmethod
    def train(self, *args: Any, **kwargs: Any) -> Any:
        """High-level training entry point."""
        pass

    @abstractmethod
    def evaluate(self, *args: Any, **kwargs: Any) -> Dict[str, float]:
        """Evaluate model against validation data."""
        pass


class BaseCheckpointManager(ABC):
    """
    Abstract interface for model checkpoint lifecycle management.
    Handles atomic saves, RNG state preservation, manifests, loading, and pruning.
    """

    @abstractmethod
    def save(
        self,
        epoch: int,
        step: int,
        metrics: Optional[Dict[str, float]] = None,
        checkpoint_name: Optional[str] = None,
        is_best: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Save checkpoint with metadata and RNG states.

        Returns:
            File path of saved checkpoint.
        """
        pass

    @abstractmethod
    def load(
        self,
        checkpoint_path: Optional[str] = None,
        load_best: bool = False,
        map_location: Optional[Union[str, torch.device]] = None,
        strict: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Load checkpoint and restore model/optimizer/RNG states.

        Returns:
            Loaded checkpoint dictionary.
        """
        pass

    @abstractmethod
    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List all tracked checkpoints with metadata."""
        pass

    @abstractmethod
    def prune(self, max_to_keep: Optional[int] = None) -> List[str]:
        """Prune older/lower-performing checkpoints according to retention policy."""
        pass


class BaseEMAManager(ABC):
    """
    Abstract interface for Exponential Moving Average (EMA) parameter tracking.
    """

    @abstractmethod
    def update(self, model: Optional[nn.Module] = None, step: Optional[int] = None) -> None:
        """Update shadow parameters with current model weights."""
        pass

    @abstractmethod
    def apply_shadow(self, model: Optional[nn.Module] = None) -> None:
        """Apply shadow weights to model parameters."""
        pass

    @abstractmethod
    def restore(self, model: Optional[nn.Module] = None) -> None:
        """Restore original weights to model parameters."""
        pass

    @abstractmethod
    def state_dict(self) -> Dict[str, Any]:
        """Return shadow weights state dict for checkpointing."""
        pass

    @abstractmethod
    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        """Load shadow weights from state dict."""
        pass


class BaseEvaluator(ABC):
    """
    Abstract interface for model evaluation engines.
    """

    @abstractmethod
    def evaluate(
        self,
        model: nn.Module,
        data_loader: DataLoader,
        device: Optional[Union[str, torch.device]] = None,
        **kwargs: Any,
    ) -> Dict[str, float]:
        """
        Evaluate model on data_loader and compute evaluation metrics.

        Returns:
            Dictionary mapping metric names to numerical values.
        """
        pass

    @abstractmethod
    def add_metric(self, name: str, metric_fn: Callable[[Any, Any], float]) -> None:
        """Register custom evaluation metric."""
        pass


class BaseExperimentTracker(ABC):
    """
    Abstract interface for experiment tracking integrations (WandB, TensorBoard, MLFlow, Console).
    """

    @abstractmethod
    def log_metrics(self, metrics: Dict[str, Any], step: Optional[int] = None) -> None:
        """Log metric values at given step."""
        pass

    @abstractmethod
    def log_hyperparams(self, params: Dict[str, Any]) -> None:
        """Log configuration hyperparameters."""
        pass

    @abstractmethod
    def log_artifact(self, artifact_path: str, artifact_type: Optional[str] = None) -> None:
        """Log file/directory artifact."""
        pass

    @abstractmethod
    def finish(self) -> None:
        """Safely flush and finalize tracking session."""
        pass


class BaseTrainingPipeline(ABC):
    """
    Abstract interface for complete training pipeline orchestrators.
    """

    @abstractmethod
    def fit(self, epochs: int, **kwargs: Any) -> Dict[str, Any]:
        """Run full training lifecycle over given number of epochs."""
        pass

    @abstractmethod
    def evaluate(self, **kwargs: Any) -> Dict[str, float]:
        """Evaluate current model state."""
        pass
