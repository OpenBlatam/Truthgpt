import torch.nn as nn
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class PyTorchSubOptimizer(ABC):
    """Abstract base class for PyTorch sub-optimizers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
    @abstractmethod
    def optimize(self, model: nn.Module) -> nn.Module:
        """Apply optimization to the model."""
        pass
