"""
Unified Exponential Moving Average (EMA) manager for PyTorch model weights.
Supports precision-aware shadow parameter tracking, CPU offload, and context manager weight swapping.
"""
import logging
from typing import Dict, Optional, Iterator, Union, Any
from contextlib import contextmanager
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class EMAManager:
    """
    Manages Exponential Moving Average (EMA) of model weights for training and inference evaluation.
    """

    def __init__(
        self,
        decay: float = 0.999,
        model: Optional[torch.nn.Module] = None,
        offload_to_cpu: bool = False,
        ema_config: Optional[Any] = None,
    ) -> None:
        """
        Initialize EMAManager.

        Args:
            decay: EMA decay factor (default: 0.999)
            model: Optional PyTorch module to initialize shadow parameters from
            offload_to_cpu: Whether to offload EMA shadow tensors to CPU memory
            ema_config: Optional EMA configuration object for compatibility
        """
        if ema_config is not None:
            self.decay = getattr(ema_config, "decay", decay)
            self.offload_to_cpu = getattr(ema_config, "offload_to_cpu", offload_to_cpu)
            self.enabled = getattr(ema_config, "enabled", True)
        else:
            self.decay = decay
            self.offload_to_cpu = offload_to_cpu
            self.enabled = True

        self.model = model
        self._shadow: Dict[str, torch.Tensor] = {}
        self._backup: Optional[Dict[str, torch.Tensor]] = None
        self._update_count: int = 0

        if model is not None and self.enabled:
            self.initialize(model)

    def _get_base_model(self, model: Optional[torch.nn.Module] = None) -> torch.nn.Module:
        """Unwrap DataParallel or DistributedDataParallel containers."""
        target_model = model if model is not None else self.model
        if target_model is None:
            raise ValueError("No model provided for EMAManager operation.")
        if isinstance(target_model, (nn.DataParallel, nn.parallel.DistributedDataParallel)):
            target_model = target_model.module
        if hasattr(target_model, "module"):
            target_model = target_model.module
        return target_model

    def initialize(self, model: Optional[torch.nn.Module] = None) -> None:
        """Initialize EMA shadow parameters from a model."""
        base_model = self._get_base_model(model)
        self._shadow = {}
        target_device = torch.device("cpu") if self.offload_to_cpu else None

        for name, param in base_model.named_parameters():
            if param.requires_grad:
                dev = target_device or param.device
                self._shadow[name] = param.detach().clone().to(device=dev, dtype=param.dtype)

        logger.debug(f"EMA initialized with {len(self._shadow)} shadow parameters.")

    @torch.no_grad()
    def update(self, model: Optional[torch.nn.Module] = None) -> None:
        """Update EMA shadow parameters using exponential decay."""
        if not self.enabled:
            return

        base_model = self._get_base_model(model)
        if not self._shadow:
            self.initialize(base_model)
            return

        d = self.decay
        for name, param in base_model.named_parameters():
            if not param.requires_grad or name not in self._shadow:
                continue
            shadow_tensor = self._shadow[name]
            param_detached = param.detach().to(device=shadow_tensor.device, dtype=shadow_tensor.dtype)
            shadow_tensor.mul_(d).add_(param_detached, alpha=1.0 - d)

        self._update_count += 1

    @torch.no_grad()
    def apply_to_model(self, model: Optional[torch.nn.Module] = None) -> None:
        """Swap model parameters with current EMA shadow parameters."""
        if not self.enabled or not self._shadow:
            return

        base_model = self._get_base_model(model)
        self._backup = {}

        for name, param in base_model.named_parameters():
            if name in self._shadow and param.requires_grad:
                self._backup[name] = param.detach().clone()
                shadow_data = self._shadow[name].data.to(device=param.device, dtype=param.dtype)
                param.data.copy_(shadow_data)

    apply_ema = apply_to_model

    @torch.no_grad()
    def restore_from_backup(self, model: Optional[torch.nn.Module] = None) -> None:
        """Restore original model weights from backup after evaluation."""
        if not self.enabled or self._backup is None:
            return

        base_model = self._get_base_model(model)

        for name, param in base_model.named_parameters():
            if name in self._backup and param.requires_grad:
                param.data.copy_(self._backup[name].data)

        self._backup = None

    restore_from_ema = restore_from_backup

    @contextmanager
    def ema_scope(self, model: Optional[torch.nn.Module] = None) -> Iterator[None]:
        """Context manager for temporary weight swapping during evaluation."""
        self.apply_to_model(model)
        try:
            yield
        finally:
            self.restore_from_backup(model)

    def state_dict(self, to_cpu: bool = False) -> Dict[str, torch.Tensor]:
        """Get EMA state dictionary."""
        if to_cpu:
            return {k: v.detach().cpu().clone() for k, v in self._shadow.items()}
        return {k: v.detach().clone() for k, v in self._shadow.items()}

    def load_state_dict(self, state_dict: Dict[str, torch.Tensor]) -> None:
        """Load EMA state dictionary."""
        self._shadow = {k: v.detach().clone() for k, v in state_dict.items()}


__all__ = ["EMAManager"]
