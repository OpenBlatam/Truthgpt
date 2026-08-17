"""
Base interfaces (ABCs) for modular architecture.
These define contracts that all implementations must follow.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Iterator, Tuple
import torch
from torch.utils.data import DataLoader


class BaseModelManager(ABC):
    """Interface for model management operations."""
    
    @abstractmethod
    def load_model(self, model_name: str, **kwargs) -> torch.nn.Module:
        """Load a model from name or path."""
        pass
    
    @abstractmethod
    def save_model(self, model: torch.nn.Module, path: str, **kwargs) -> None:
        """Save model to path."""
        pass
    
    @abstractmethod
    def get_model_device(self, model: torch.nn.Module) -> torch.device:
        """Get device where model is located."""
        pass


class BaseDataLoader(ABC):
    """Interface for data loading operations."""
    
    @abstractmethod
    def create_train_loader(
        self,
        dataset: Any,
        batch_size: int,
        **kwargs
    ) -> DataLoader:
        """Create training DataLoader."""
        pass
    
    @abstractmethod
    def create_val_loader(
        self,
        dataset: Any,
        batch_size: int,
        **kwargs
    ) -> DataLoader:
        """Create validation DataLoader."""
        pass


class BaseEvaluator(ABC):
    """Interface for model evaluation."""
    
    @abstractmethod
    def evaluate(
        self,
        model: torch.nn.Module,
        data_loader: DataLoader,
        device: torch.device,
        **kwargs
    ) -> Dict[str, float]:
        """
        Evaluate model on data.
        
        Returns:
            Dictionary of metric names to values
        """
        pass
    
    @abstractmethod
    def compute_metrics(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor,
        **kwargs
    ) -> Dict[str, float]:
        """Compute evaluation metrics."""
        pass


class BaseCheckpointManager(ABC):
    """Interface for checkpoint management."""
    
    @abstractmethod
    def save_checkpoint(
        self,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        scheduler: Any,
        step: int,
        path: str,
        **kwargs
    ) -> None:
        """Save training checkpoint."""
        pass
    
    @abstractmethod
    def load_checkpoint(
        self,
        path: str,
        model: torch.nn.Module,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Load training checkpoint.
        
        Returns:
            Dictionary with loaded state (step, epoch, etc.)
        """
        pass
    
    @abstractmethod
    def find_latest_checkpoint(self, checkpoint_dir: str) -> Optional[str]:
        """Find latest checkpoint in directory."""
        pass


class BaseTrainer(ABC):
    """Interface for training operations."""
    
    @abstractmethod
    def train_step(
        self,
        model: torch.nn.Module,
        batch: Dict[str, torch.Tensor],
        optimizer: torch.optim.Optimizer,
        scaler: Any,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform a single training step.
        
        Returns:
            Dictionary with step metrics (loss, etc.)
        """
        pass
    
    @abstractmethod
    def train_epoch(
        self,
        model: torch.nn.Module,
        train_loader: DataLoader,
        optimizer: torch.optim.Optimizer,
        scheduler: Any,
        scaler: Any,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Train for one epoch.
        
        Returns:
            Dictionary with epoch metrics
        """
        pass
    
    @abstractmethod
    def should_stop_early(
        self,
        current_metric: float,
        best_metric: float,
        patience: int,
        **kwargs
    ) -> bool:
        """Determine if training should stop early."""
        pass


