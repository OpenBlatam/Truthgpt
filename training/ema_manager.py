"""
Exponential Moving Average (EMA) Manager Module
================================================
Manages exponential moving average tracking of PyTorch model parameters.
Supports precision-aware shadow parameter tracking, CPU offloading, dynamic decay warmup,
and exception-safe weight swapping via context managers.
"""

from contextlib import contextmanager
import logging
from typing import Any, Dict, Iterator, Optional
import torch
import torch.nn as nn

try:
    from ..trainers.interfaces import BaseEMAManager
except ImportError:
    try:
        from optimization_core.trainers.interfaces import BaseEMAManager
    except ImportError:
        from abc import ABC, abstractmethod

        class BaseEMAManager(ABC):  # type: ignore
            """Fallback abstract base class for EMAManager."""
            pass

logger = logging.getLogger(__name__)


class EMAError(RuntimeError):
    """Exception raised when Exponential Moving Average weight update, swap, or initialization fails."""

    pass


class EMAManager(BaseEMAManager):
    """
    Manages Exponential Moving Average (EMA) of model weights for training and inference evaluation.
    Implements the BaseEMAManager interface.
    """

    def __init__(
        self,
        decay: float = 0.999,
        model: Optional[torch.nn.Module] = None,
        offload_to_cpu: bool = False,
        ema_config: Optional[Any] = None,
        use_dynamic_decay: bool = False,
    ) -> None:
        """
        Initialize EMAManager.

        Args:
            decay: EMA decay factor in range [0.0, 1.0) (default: 0.999).
            model: Optional PyTorch module instance to initialize shadow parameters from.
            offload_to_cpu: Whether to offload EMA shadow tensors to CPU memory.
            ema_config: Optional EMA configuration object for compatibility settings.
            use_dynamic_decay: Whether to scale decay dynamically during early training steps.

        Raises:
            ValueError: If decay factor is not in range [0.0, 1.0).
        """
        if ema_config is not None:
            self.decay = float(getattr(ema_config, "decay", decay))
            self.offload_to_cpu = bool(getattr(ema_config, "offload_to_cpu", offload_to_cpu))
            self.enabled = bool(getattr(ema_config, "enabled", True))
            self.use_dynamic_decay = bool(getattr(ema_config, "use_dynamic_decay", use_dynamic_decay))
        else:
            self.decay = float(decay)
            self.offload_to_cpu = bool(offload_to_cpu)
            self.enabled = True
            self.use_dynamic_decay = bool(use_dynamic_decay)

        if not (0.0 <= self.decay < 1.0):
            raise ValueError(f"EMA decay must be in range [0.0, 1.0), got {self.decay}")

        self.model: Optional[torch.nn.Module] = model
        self._shadow: Dict[str, torch.Tensor] = {}
        self._backup: Optional[Dict[str, torch.Tensor]] = None
        self._update_count: int = 0

        if model is not None and self.enabled:
            self.initialize(model)

    def _get_base_model(self, model: Optional[torch.nn.Module] = None) -> torch.nn.Module:
        """
        Unwrap DataParallel or DistributedDataParallel containers cleanly.

        Args:
            model: Optional model module override.

        Returns:
            Unwrapped base nn.Module instance.

        Raises:
            EMAError: If no model instance is provided.
        """
        target_model = model if model is not None else self.model
        if target_model is None:
            raise EMAError("No model provided for EMAManager operation.")

        while isinstance(target_model, (nn.DataParallel, nn.parallel.DistributedDataParallel)):
            target_model = target_model.module
        if hasattr(target_model, "module") and isinstance(getattr(target_model, "module"), nn.Module):
            target_model = target_model.module

        return target_model

    def initialize(self, model: Optional[torch.nn.Module] = None) -> None:
        """
        Initialize EMA shadow parameters from model parameters requiring gradients.

        Args:
            model: Optional model module override.
        """
        base_model = self._get_base_model(model)
        self._shadow = {}
        target_device = torch.device("cpu") if self.offload_to_cpu else None

        for name, param in base_model.named_parameters():
            if param.requires_grad:
                dev = target_device or param.device
                self._shadow[name] = param.detach().clone().to(device=dev, dtype=param.dtype)

        logger.debug(f"EMA initialized with {len(self._shadow)} shadow parameters.")

    def get_decay(self, step: Optional[int] = None) -> float:
        """
        Calculate active EMA decay factor, applying optional dynamic warmup.

        Args:
            step: Optional step count.

        Returns:
            Calculated float decay value.
        """
        if not self.use_dynamic_decay:
            return self.decay
        current_step = step if step is not None else self._update_count
        dynamic_decay = (1.0 + current_step) / (10.0 + current_step)
        return float(min(self.decay, dynamic_decay))

    @torch.no_grad()
    def update(self, model: Optional[torch.nn.Module] = None, step: Optional[int] = None) -> None:
        """
        Update EMA shadow parameters using exponential decay update formula.

        Args:
            model: Optional model module override.
            step: Optional step override for dynamic decay.
        """
        if not self.enabled:
            return

        base_model = self._get_base_model(model)
        if not self._shadow:
            self.initialize(base_model)
            return

        d = self.get_decay(step)
        for name, param in base_model.named_parameters():
            if not param.requires_grad or name not in self._shadow:
                continue
            shadow_tensor = self._shadow[name]
            param_detached = param.detach().to(device=shadow_tensor.device, dtype=shadow_tensor.dtype)
            shadow_tensor.mul_(d).add_(param_detached, alpha=1.0 - d)

        self._update_count += 1

    @torch.no_grad()
    def apply_to_model(self, model: Optional[torch.nn.Module] = None) -> None:
        """
        Swap model parameters with current EMA shadow parameters and back up original weights.

        Args:
            model: Optional model module override.
        """
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
        """
        Restore original model weights from saved backup after evaluation.

        Args:
            model: Optional model module override.
        """
        if not self.enabled or self._backup is None:
            return

        base_model = self._get_base_model(model)

        for name, param in base_model.named_parameters():
            if name in self._backup and param.requires_grad:
                param.data.copy_(self._backup[name].data)

        self._backup = None

    restore_from_ema = restore_from_backup

    @torch.no_grad()
    def copy_shadow_to_model(self, model: Optional[torch.nn.Module] = None) -> None:
        """
        Permanently copy EMA shadow parameters into model parameters without saving backup.

        Args:
            model: Optional model module override.
        """
        if not self.enabled or not self._shadow:
            return

        base_model = self._get_base_model(model)
        for name, param in base_model.named_parameters():
            if name in self._shadow and param.requires_grad:
                shadow_data = self._shadow[name].data.to(device=param.device, dtype=param.dtype)
                param.data.copy_(shadow_data)

    @contextmanager
    def ema_scope(self, model: Optional[torch.nn.Module] = None) -> Iterator[None]:
        """
        Context manager for temporary weight swapping during evaluation routines.
        Ensures original parameters are restored cleanly even if an exception occurs.

        Args:
            model: Optional model module override.
        """
        self.apply_to_model(model)
        try:
            yield
        finally:
            self.restore_from_backup(model)

    def get_shadow_parameters(self) -> Dict[str, torch.Tensor]:
        """
        Return a detached clone dictionary of current EMA shadow parameters.

        Returns:
            Dict mapping parameter names to detached shadow tensors.
        """
        return {k: v.detach().clone() for k, v in self._shadow.items()}

    def state_dict(self, to_cpu: bool = False) -> Dict[str, torch.Tensor]:
        """
        Get EMA state dictionary of shadow parameters.

        Args:
            to_cpu: Whether to force copy all shadow tensors to CPU memory.

        Returns:
            State dictionary mapping parameter names to cloned shadow tensors.
        """
        if to_cpu:
            return {k: v.detach().cpu().clone() for k, v in self._shadow.items()}
        return {k: v.detach().clone() for k, v in self._shadow.items()}

    def load_state_dict(self, state_dict: Dict[str, torch.Tensor]) -> None:
        """
        Load EMA state dictionary into shadow parameters.

        Args:
            state_dict: State dictionary containing shadow tensors.
        """
        self._shadow = {k: v.detach().clone() for k, v in state_dict.items()}


__all__ = ["EMAManager", "EMAError"]
