"""
Optimizer adapters for abstracting optimizer implementations.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Iterator
import torch

logger = logging.getLogger(__name__)


class OptimizerAdapter(ABC):
    """Base adapter for optimizer operations."""
    
    @abstractmethod
    def create_optimizer(
        self,
        parameters: Iterator[torch.nn.Parameter],
        **kwargs
    ) -> torch.optim.Optimizer:
        """Create an optimizer."""
        pass
    
    @abstractmethod
    def get_optimizer_state(self, optimizer: torch.optim.Optimizer) -> Dict[str, Any]:
        """Get optimizer state."""
        pass


class PyTorchOptimizerAdapter(OptimizerAdapter):
    """Adapter for PyTorch optimizers."""
    
    def create_optimizer(
        self,
        parameters: Iterator[torch.nn.Parameter],
        optimizer_type: str = "adamw",
        **kwargs
    ) -> torch.optim.Optimizer:
        """Create PyTorch optimizer."""
        optimizer_map = {
            "adam": torch.optim.Adam,
            "adamw": torch.optim.AdamW,
            "sgd": torch.optim.SGD,
            "rmsprop": torch.optim.RMSprop,
        }
        
        if optimizer_type not in optimizer_map:
            raise ValueError(f"Unknown optimizer type: {optimizer_type}")
        
        optimizer_class = optimizer_map[optimizer_type]
        return optimizer_class(parameters, **kwargs)
    
    def get_optimizer_state(self, optimizer: torch.optim.Optimizer) -> Dict[str, Any]:
        """Get optimizer state."""
        return {
            "type": type(optimizer).__name__,
            "param_groups": len(optimizer.param_groups),
            "state_dict": optimizer.state_dict(),
        }


