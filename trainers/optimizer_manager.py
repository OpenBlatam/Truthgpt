"""
Optimizer Manager - Handles optimizer creation, parameter decay grouping, learning rate schedulers, and AMP scaler.

Refactored with weight decay parameter grouping best practices, multi-scheduler support, exception safety, and relative imports.
"""
import sys
import logging
from typing import Optional, List, Dict, Any, Union
import torch
import torch.nn as nn
from torch.optim import Optimizer

logger = logging.getLogger(__name__)

try:
    from torch.cuda.amp import GradScaler
except ImportError:
    GradScaler = Any

try:
    from transformers import (
        get_cosine_schedule_with_warmup,
        get_linear_schedule_with_warmup,
        get_cosine_with_hard_restarts_schedule_with_warmup,
        get_polynomial_decay_schedule_with_warmup,
        get_constant_schedule_with_warmup,
    )
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False

from .config import TrainingConfig
from .interfaces import BaseOptimizerManager
from .exceptions import OptimizerManagerError, GradientNaNError
from .registry import TrainerRegistry

try:
    from factories.optimizer import OPTIMIZERS
    _FACTORIES_OPTIMIZERS_AVAILABLE = True
except Exception as e:
    logger.debug(f"factories.optimizer registry not available: {e}")
    _FACTORIES_OPTIMIZERS_AVAILABLE = False
    OPTIMIZERS = None


class OptimizerManager(BaseOptimizerManager):
    """
    Manages model parameter optimization, decay group splitting, schedulers, and AMP scalers.
    """

    def __init__(
        self,
        training_config: TrainingConfig,
        model: nn.Module,
        use_amp: bool = False,
    ):
        if model is None:
            raise OptimizerManagerError("Model cannot be None for OptimizerManager.")
        self.training_config = training_config
        self.model = model
        self.use_amp = use_amp
        self.optimizer: Optional[Optimizer] = None
        self.scheduler: Optional[Any] = None
        self.scaler: Optional[Any] = None

    def create_parameter_groups(self) -> List[Dict[str, Any]]:
        """Public alias for _create_decay_param_groups."""
        return self._create_decay_param_groups()

    def _create_decay_param_groups(self) -> List[Dict[str, Any]]:
        """
        Split parameters into decay and no-decay groups.
        
        Biases, LayerNorm/RMSNorm weights, and 1D parameters get 0.0 weight decay.
        """
        decay_params: List[nn.Parameter] = []
        no_decay_params: List[nn.Parameter] = []

        no_decay_keywords = ("bias", "layer_norm", "layernorm", "rmsnorm", "ln_", "embedding")

        for name, param in self.model.named_parameters():
            if not param.requires_grad:
                continue

            name_lower = name.lower()
            if param.ndim < 2 or any(nd in name_lower for nd in no_decay_keywords):
                no_decay_params.append(param)
            else:
                decay_params.append(param)

        logger.info(
            f"Parameter decay groups created: {len(decay_params)} decay params, "
            f"{len(no_decay_params)} no-decay params."
        )

        return [
            {
                "params": decay_params,
                "weight_decay": getattr(self.training_config, "weight_decay", 0.01),
            },
            {
                "params": no_decay_params,
                "weight_decay": 0.0,
            },
        ]

    def create_optimizer(self, optimizer_type: str = "adamw") -> Optimizer:
        """Create optimizer using parameter decay grouping with fallbacks."""
        param_groups = self._create_decay_param_groups()

        # 1. Check TrainerRegistry first
        custom_opt_cls = TrainerRegistry.get_optimizer(optimizer_type)
        if custom_opt_cls is not None:
            try:
                optimizer = custom_opt_cls(param_groups, lr=self.training_config.learning_rate)
                logger.info(f"Created '{optimizer_type}' optimizer via TrainerRegistry.")
                self.optimizer = optimizer
                return optimizer
            except Exception as e:
                logger.warning(f"TrainerRegistry optimizer build failed ({e}). Falling back.")

        # 2. Check factories.optimizer
        if _FACTORIES_OPTIMIZERS_AVAILABLE and OPTIMIZERS is not None:
            try:
                optimizer = OPTIMIZERS.build(
                    optimizer_type,
                    param_groups,
                    lr=self.training_config.learning_rate,
                    fused=True,
                )
                logger.info(f"Created {optimizer_type} optimizer via registry with decay groups.")
                self.optimizer = optimizer
                return optimizer
            except Exception as e:
                logger.warning(f"Registry optimizer build failed ({e}). Using native fallback.")

        # 3. Built-in PyTorch fallback
        try:
            opt_lower = optimizer_type.lower()
            if opt_lower == "sgd":
                optimizer = torch.optim.SGD(
                    param_groups,
                    lr=self.training_config.learning_rate,
                    momentum=0.9,
                )
            elif opt_lower == "adam":
                optimizer = torch.optim.Adam(
                    param_groups,
                    lr=self.training_config.learning_rate,
                )
            else:
                # Native PyTorch AdamW fallback
                optimizer = torch.optim.AdamW(
                    param_groups,
                    lr=self.training_config.learning_rate,
                )
            self.optimizer = optimizer
            return optimizer
        except Exception as ex:
            raise OptimizerManagerError(f"Failed to create optimizer '{optimizer_type}': {ex}") from ex

    def create_scheduler(self, num_training_steps: int) -> Any:
        """Create learning rate scheduler based on training config."""
        if self.optimizer is None:
            raise OptimizerManagerError("Must create optimizer before creating learning rate scheduler.")

        num_warmup_steps = int(getattr(self.training_config, "warmup_ratio", 0.06) * max(1, num_training_steps))
        sched_type = getattr(self.training_config, "scheduler", "cosine").lower()

        try:
            if _TRANSFORMERS_AVAILABLE:
                if sched_type == "cosine":
                    scheduler = get_cosine_schedule_with_warmup(
                        self.optimizer,
                        num_warmup_steps=num_warmup_steps,
                        num_training_steps=num_training_steps,
                    )
                elif sched_type == "linear":
                    scheduler = get_linear_schedule_with_warmup(
                        self.optimizer,
                        num_warmup_steps=num_warmup_steps,
                        num_training_steps=num_training_steps,
                    )
                elif sched_type in ("cosine_with_restarts", "cosine_restarts"):
                    scheduler = get_cosine_with_hard_restarts_schedule_with_warmup(
                        self.optimizer,
                        num_warmup_steps=num_warmup_steps,
                        num_training_steps=num_training_steps,
                        num_cycles=3,
                    )
                elif sched_type == "polynomial":
                    scheduler = get_polynomial_decay_schedule_with_warmup(
                        self.optimizer,
                        num_warmup_steps=num_warmup_steps,
                        num_training_steps=num_training_steps,
                        lr_end=1e-7,
                    )
                elif sched_type in ("constant", "constant_with_warmup"):
                    scheduler = get_constant_schedule_with_warmup(
                        self.optimizer,
                        num_warmup_steps=num_warmup_steps,
                    )
                else:
                    logger.warning(f"Unknown scheduler type '{sched_type}'. Defaulting to cosine.")
                    scheduler = get_cosine_schedule_with_warmup(
                        self.optimizer,
                        num_warmup_steps=num_warmup_steps,
                        num_training_steps=num_training_steps,
                    )
            else:
                # PyTorch native scheduler fallback
                scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                    self.optimizer, T_max=max(1, num_training_steps)
                )

            logger.info(f"Created '{sched_type}' scheduler with {num_warmup_steps} warmup steps out of {num_training_steps} total steps.")
            self.scheduler = scheduler
            return scheduler
        except Exception as e:
            raise OptimizerManagerError(f"Failed to create scheduler '{sched_type}': {e}") from e

    def create_scaler(self) -> Any:
        """Create automatic mixed precision GradScaler."""
        try:
            if hasattr(torch, "amp") and hasattr(torch.amp, "GradScaler"):
                device_str = "cuda" if torch.cuda.is_available() else "cpu"
                scaler = torch.amp.GradScaler(
                    device_str,
                    enabled=self.use_amp,
                    init_scale=2.0**16,
                    growth_factor=2.0,
                    backoff_factor=0.5,
                    growth_interval=2000,
                )
            else:
                scaler = GradScaler(
                    enabled=self.use_amp,
                    init_scale=2.0**16,
                    growth_factor=2.0,
                    backoff_factor=0.5,
                    growth_interval=2000,
                )
            self.scaler = scaler
            return scaler
        except Exception as e:
            raise OptimizerManagerError(f"Failed to create GradScaler: {e}") from e

    def step(self, scale_loss: bool = True) -> None:
        """Perform an optimizer step with optional GradScaler handling."""
        if self.optimizer is None:
            raise OptimizerManagerError("Optimizer has not been initialized.")
        
        if scale_loss and self.scaler is not None:
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            self.optimizer.step()

    def scheduler_step(self) -> None:
        """Step the learning rate scheduler."""
        if self.scheduler is None:
            raise OptimizerManagerError("Scheduler has not been initialized.")
        self.scheduler.step()

    def zero_grad(self, set_to_none: bool = True) -> None:
        """Zero optimizer gradients."""
        if self.optimizer is None:
            raise OptimizerManagerError("Optimizer has not been initialized.")
        self.optimizer.zero_grad(set_to_none=set_to_none)

    def get_lr(self) -> float:
        """Get current learning rate from parameter groups."""
        if self.optimizer is None:
            return 0.0
        try:
            return float(self.optimizer.param_groups[0]["lr"])
        except (IndexError, KeyError, AttributeError):
            return 0.0

    def clip_grad_norm(self, max_norm: float) -> float:
        """Clip parameter gradients by norm."""
        if max_norm <= 0:
            return 0.0
        if self.scaler is not None:
            self.scaler.unscale_(self.optimizer)
        norm = torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm)
        if torch.isnan(norm) or torch.isinf(norm):
            raise GradientNaNError(f"Gradient norm calculated as NaN/Inf ({norm}).")
        return float(norm)


__all__ = ["OptimizerManager"]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.trainers."):
        sys.modules["trainers." + __name__[len("optimization_core.trainers."):]] = _mod
    elif __name__.startswith("trainers."):
        sys.modules["optimization_core.trainers." + __name__[len("trainers."):]] = _mod
