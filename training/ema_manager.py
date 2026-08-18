"""
Exponential Moving Average (EMA) Manager Module
================================================
Manages exponential moving average tracking of PyTorch model parameters.
Supports precision-aware shadow parameter tracking, CPU offloading, dynamic decay warmup,
and exception-safe weight swapping via context managers.
"""

from __future__ import annotations

from contextlib import contextmanager
import logging
import math
from typing import Any, Dict, Iterator, Optional, Union
import torch
import torch.nn as nn

from .exceptions import EMAError
from .interfaces import BaseEMAManager
from .types import EMAConfig, EMADecaySchedule

logger = logging.getLogger(__name__)


class EMAManager(BaseEMAManager):
    """
    Manages Exponential Moving Average (EMA) of model weights for training and inference evaluation.
    Maintains shadow parameter copies and supports zero-copy weight swapping for validation.
    """

    def __init__(
        self,
        decay: float = 0.999,
        model: Optional[torch.nn.Module] = None,
        offload_to_cpu: bool = False,
        ema_config: Optional[Union[Dict[str, Any], EMAConfig]] = None,
        use_dynamic_decay: bool = False,
        warmup_steps: int = 2000,
        **kwargs: Any,
    ) -> None:
        """
        Initialize EMAManager.
        """
        if ema_config is not None:
            if isinstance(ema_config, EMAConfig):
                self.decay = float(ema_config.decay)
                self.offload_to_cpu = bool(ema_config.offload_to_cpu)
                self.enabled = bool(ema_config.enabled)
                self.use_dynamic_decay = (ema_config.schedule != EMADecaySchedule.CONSTANT)
                self.warmup_steps = int(ema_config.warmup_steps)
            elif isinstance(ema_config, dict):
                self.decay = float(ema_config.get("decay", decay))
                self.offload_to_cpu = bool(ema_config.get("offload_to_cpu", offload_to_cpu))
                self.enabled = bool(ema_config.get("enabled", True))
                self.use_dynamic_decay = bool(ema_config.get("use_dynamic_decay", use_dynamic_decay))
                self.warmup_steps = int(ema_config.get("warmup_steps", warmup_steps))
        else:
            self.decay = float(decay)
            self.offload_to_cpu = bool(offload_to_cpu)
            self.enabled = True
            self.use_dynamic_decay = bool(use_dynamic_decay)
            self.warmup_steps = int(warmup_steps)

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
        Initialize shadow parameter tensors matching model trainable parameters.
        """
        target_model = self._get_base_model(model)
        self._shadow.clear()
        for name, param in target_model.named_parameters():
            if param.requires_grad:
                tensor_data = param.detach().clone()
                if self.offload_to_cpu:
                    tensor_data = tensor_data.cpu()
                self._shadow[name] = tensor_data
        self._update_count = 0
        logger.debug(f"Initialized EMA tracking for {len(self._shadow)} parameter tensors.")

    def _compute_current_decay(self, step: Optional[int] = None) -> float:
        """Calculate active decay factor considering dynamic warmup."""
        if not self.use_dynamic_decay:
            return self.decay

        current_step = step if step is not None else self._update_count
        if current_step <= 0:
            return 0.0
        # Smooth asymptotic warmup: decay * (1 - exp(-step / warmup_steps))
        factor = 1.0 - math.exp(-float(current_step) / max(1.0, float(self.warmup_steps)))
        return float(min(self.decay, self.decay * factor))

    def get_decay(self, step: Optional[int] = None) -> float:
        """Get current effective decay factor."""
        return self._compute_current_decay(step)

    def update(self, model: Optional[torch.nn.Module] = None, step: Optional[int] = None) -> None:
        """
        Update shadow parameters with model's current weights.
        """
        if not self.enabled:
            return

        target_model = self._get_base_model(model)
        if not self._shadow:
            self.initialize(target_model)

        self._update_count += 1
        active_decay = self._compute_current_decay(step)

        with torch.no_grad():
            for name, param in target_model.named_parameters():
                if name in self._shadow and param.requires_grad:
                    param_data = param.detach()
                    shadow_data = self._shadow[name]

                    if self.offload_to_cpu:
                        param_data = param_data.to("cpu")

                    if shadow_data.dtype != param_data.dtype:
                        shadow_data = shadow_data.to(param_data.dtype)

                    shadow_data.lerp_(param_data, 1.0 - active_decay)
                    self._shadow[name] = shadow_data

    def apply_shadow(self, model: Optional[torch.nn.Module] = None) -> None:
        """
        Copy shadow weights into model parameters, preserving backup for restoration.
        """
        if not self.enabled or not self._shadow:
            return

        target_model = self._get_base_model(model)
        self._backup = {}

        with torch.no_grad():
            for name, param in target_model.named_parameters():
                if name in self._shadow:
                    self._backup[name] = param.detach().clone()
                    shadow_val = self._shadow[name].to(device=param.device, dtype=param.dtype)
                    param.copy_(shadow_val)

    def restore(self, model: Optional[torch.nn.Module] = None) -> None:
        """
        Restore original model parameters from pre-evaluation backup.
        """
        if self._backup is None:
            return

        target_model = self._get_base_model(model)
        with torch.no_grad():
            for name, param in target_model.named_parameters():
                if name in self._backup:
                    param.copy_(self._backup[name].to(device=param.device, dtype=param.dtype))

        self._backup = None

    def copy_shadow_to_model(self, model: Optional[torch.nn.Module] = None) -> None:
        """Permanently copy shadow weights into model parameters without backup."""
        self.apply_shadow(model)
        self._backup = None

    @contextmanager
    def swap_weights(self, model: Optional[torch.nn.Module] = None) -> Iterator[None]:
        """
        Context manager to evaluate with EMA weights and safely restore original weights afterwards.
        """
        self.apply_shadow(model)
        try:
            yield
        finally:
            self.restore(model)

    @contextmanager
    def ema_scope(self, model: Optional[torch.nn.Module] = None) -> Iterator[None]:
        """Alias for swap_weights context manager."""
        with self.swap_weights(model):
            yield

    def state_dict(self, full: bool = False) -> Dict[str, Any]:
        """
        Serialize EMA manager state for checkpointing.
        """
        if full:
            return {
                "decay": self.decay,
                "update_count": self._update_count,
                "shadow": {k: v.cpu().clone() for k, v in self._shadow.items()},
                "offload_to_cpu": self.offload_to_cpu,
                "use_dynamic_decay": self.use_dynamic_decay,
                "warmup_steps": self.warmup_steps,
            }
        return {k: v.cpu().clone() for k, v in self._shadow.items()}

    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        """
        Restore EMA manager state from checkpoint.
        """
        if "shadow" in state_dict:
            self.decay = state_dict.get("decay", self.decay)
            self._update_count = state_dict.get("update_count", self._update_count)
            self.offload_to_cpu = state_dict.get("offload_to_cpu", self.offload_to_cpu)
            self.use_dynamic_decay = state_dict.get("use_dynamic_decay", self.use_dynamic_decay)
            self.warmup_steps = state_dict.get("warmup_steps", self.warmup_steps)
            shadow_dict = state_dict["shadow"]
        else:
            shadow_dict = state_dict

        self._shadow = {}
        for k, v in shadow_dict.items():
            tensor = v if isinstance(v, torch.Tensor) else torch.tensor(v)
            if not self.offload_to_cpu and self.model is not None and list(self.model.parameters()):
                dev = next(self.model.parameters()).device
                tensor = tensor.to(dev)
            self._shadow[k] = tensor
