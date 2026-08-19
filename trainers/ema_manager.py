"""
EMA Manager - Handles Exponential Moving Average weights.

Provides precision-aware tracking and weight swapping for model evaluation and inference.
"""
import logging
from typing import Dict, Optional, Iterator
from contextlib import contextmanager
import torch
import torch.nn as nn

from .config import EMAConfig
from .interfaces import BaseEMAManager
from .exceptions import EMAError

logger = logging.getLogger(__name__)


class EMAManager(BaseEMAManager):
    """
    Manages Exponential Moving Average (EMA) of model weights.
    
    Responsibilities:
    - Maintain shadow parameters matching model device and precision (or CPU offload)
    - Update EMA parameters on each optimizer step
    - Swap/restore model weights for evaluation and inference
    - Provide context manager for safe temporary weight swapping
    """
    
    def __init__(self, ema_config: EMAConfig, model: nn.Module) -> None:
        """
        Initialize EMAManager.
        
        Args:
            ema_config: EMA configuration
            model: PyTorch model instance
        """
        if model is None:
            raise EMAError("Model cannot be None for EMAManager.")
        self.ema_config = ema_config
        self.model = model
        self._ema_shadow: Optional[Dict[str, torch.Tensor]] = None
        self._ema_backup: Optional[Dict[str, torch.Tensor]] = None
        self._update_count: int = 0
        
        if getattr(ema_config, "enabled", True):
            self._init_ema()
            logger.info(f"EMA initialized with decay={getattr(ema_config, 'decay', 0.999)}")
    
    def _get_base_model(self) -> nn.Module:
        """Get base model unwrap parallel containers."""
        model = self.model
        if isinstance(model, (nn.DataParallel, nn.parallel.DistributedDataParallel)):
            model = model.module
        if hasattr(model, "module"):
            model = model.module
        return model
    
    def _init_ema(self) -> None:
        """Initialize shadow parameter dictionary matching precision and device."""
        try:
            self._ema_shadow = {}
            model = self._get_base_model()
            offload_cpu = getattr(self.ema_config, "offload_to_cpu", False)
            for name, param in model.named_parameters():
                if param.requires_grad:
                    target_device = torch.device("cpu") if offload_cpu else param.device
                    self._ema_shadow[name] = param.detach().clone().to(device=target_device, dtype=param.dtype)
        except Exception as e:
            raise EMAError(f"Failed to initialize EMA shadow parameters: {e}") from e
    
    @torch.no_grad()
    def update(self) -> None:
        """Update EMA shadow weights using exponential decay."""
        if not getattr(self.ema_config, "enabled", True) or self._ema_shadow is None:
            return
        
        decay = getattr(self.ema_config, "decay", 0.999)
        model = self._get_base_model()
        
        for name, param in model.named_parameters():
            if not param.requires_grad or name not in self._ema_shadow:
                continue
            shadow_tensor = self._ema_shadow[name]
            param_detached = param.detach().to(device=shadow_tensor.device)
            shadow_tensor.mul_(decay).add_(param_detached, alpha=1.0 - decay)
        
        self._update_count += 1
    
    @torch.no_grad()
    def apply_ema(self) -> None:
        """Swap model weights with EMA shadow parameters."""
        if not getattr(self.ema_config, "enabled", True) or self._ema_shadow is None:
            return
        
        self._ema_backup = {}
        model = self._get_base_model()
        
        for name, param in model.named_parameters():
            if name in self._ema_shadow and param.requires_grad:
                self._ema_backup[name] = param.detach().clone()
                shadow_data = self._ema_shadow[name].data.to(device=param.device)
                param.data.copy_(shadow_data)
    
    @torch.no_grad()
    def restore_from_ema(self) -> None:
        """Restore original model weights from backup after evaluation."""
        if not getattr(self.ema_config, "enabled", True) or self._ema_backup is None:
            return
        
        model = self._get_base_model()
        
        for name, param in model.named_parameters():
            if name in self._ema_backup and param.requires_grad:
                param.data.copy_(self._ema_backup[name].data)
        
        self._ema_backup = None

    @contextmanager
    def ema_scope(self) -> Iterator[None]:
        """Context manager to apply EMA weights and restore original weights on exit."""
        self.apply_ema()
        try:
            yield
        finally:
            self.restore_from_ema()
    
    def get_ema_state_dict(self, to_cpu: bool = False) -> Dict[str, torch.Tensor]:
        """Get EMA shadow state dictionary."""
        if self._ema_shadow is None:
            return {}
        if to_cpu:
            return {k: v.detach().cpu().clone() for k, v in self._ema_shadow.items()}
        return {k: v.detach().clone() for k, v in self._ema_shadow.items()}


__all__ = ["EMAManager"]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.trainers."):
        sys.modules["trainers." + __name__[len("optimization_core.trainers."):]] = _mod
    elif __name__.startswith("trainers."):
        sys.modules["optimization_core.trainers." + __name__[len("trainers."):]] = _mod
