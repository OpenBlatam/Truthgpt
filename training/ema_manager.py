"""
EMA (Exponential Moving Average) manager for model weights.
"""
import logging
import torch
import torch.nn as nn
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class EMAManager:
    """
    Manages Exponential Moving Average of model weights.
    """
    
    def __init__(self, decay: float = 0.999, model: Optional[torch.nn.Module] = None):
        """
        Initialize EMA manager.
        
        Args:
            decay: EMA decay factor
            model: Optional model to initialize from
        """
        self.decay = decay
        self._shadow: Dict[str, torch.Tensor] = {}
        self._backup: Dict[str, torch.Tensor] = {}
        self._is_parallel = False
        
        if model is not None:
            self.initialize(model)
    
    def _get_base_model(self, model: torch.nn.Module) -> torch.nn.Module:
        """Get base model (handle DataParallel)."""
        if isinstance(model, nn.DataParallel):
            self._is_parallel = True
            return model.module
        return model
    
    def initialize(self, model: torch.nn.Module) -> None:
        """
        Initialize EMA shadow parameters from model.
        
        Args:
            model: Model to initialize from
        """
        base_model = self._get_base_model(model)
        self._shadow = {}
        
        for name, param in base_model.named_parameters():
            if param.requires_grad:
                self._shadow[name] = param.detach().clone().to(device=param.device)
        
        logger.debug(f"EMA initialized with {len(self._shadow)} parameters")
    
    def update(self, model: torch.nn.Module) -> None:
        """
        Update EMA shadow parameters.
        
        Args:
            model: Model with current weights
        """
        if not self._shadow:
            return
        
        base_model = self._get_base_model(model)
        d = self.decay
        
        for name, param in base_model.named_parameters():
            if not param.requires_grad or name not in self._shadow:
                continue
            
            # EMA update: shadow = decay * shadow + (1 - decay) * param
            self._shadow[name].mul_(d).add_(param.detach(), alpha=1.0 - d)
    
    def apply_to_model(self, model: torch.nn.Module) -> None:
        """
        Apply EMA shadow parameters to model.
        Saves current parameters in backup.
        
        Args:
            model: Model to apply EMA to
        """
        if not self._shadow:
            return
        
        base_model = self._get_base_model(model)
        self._backup = {}
        
        for name, param in base_model.named_parameters():
            if name in self._shadow and param.requires_grad:
                # Backup current parameters
                self._backup[name] = param.detach().clone()
                # Apply EMA shadow
                param.data.copy_(self._shadow[name].data)
    
    def restore_from_backup(self, model: torch.nn.Module) -> None:
        """
        Restore model parameters from backup.
        
        Args:
            model: Model to restore
        """
        if not self._backup:
            return
        
        base_model = self._get_base_model(model)
        
        for name, param in base_model.named_parameters():
            if name in self._backup and param.requires_grad:
                param.data.copy_(self._backup[name].data)
        
        self._backup = {}
    
    def state_dict(self) -> Dict[str, torch.Tensor]:
        """Get EMA state dictionary."""
        return self._shadow.copy()
    
    def load_state_dict(self, state_dict: Dict[str, torch.Tensor]) -> None:
        """Load EMA state dictionary."""
        self._shadow = state_dict.copy()


