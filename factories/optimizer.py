"""
Optimizer & Scheduler Factories
===============================
Factory functions for PyTorch optimizers, custom optimization algorithms, parameter group
partitioning (weight-decay exclusion), and learning rate scheduler construction.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import torch
from torch.optim import Optimizer
from torch.optim.lr_scheduler import (
    CosineAnnealingLR,
    ConstantLR,
    LinearLR,
    LRScheduler,
    OneCycleLR,
    PolynomialLR,
    ReduceLROnPlateau,
    SequentialLR,
)

from .registry import Registry

logger = logging.getLogger(__name__)

OPTIMIZERS = Registry(name="OptimizerRegistry")
SCHEDULERS = Registry(name="LRSchedulerRegistry")


@dataclass
class OptimizerConfig:
    """Configuration specification for optimizer construction."""

    name: str = "adamw"
    lr: float = 1e-3
    weight_decay: float = 0.01
    betas: Tuple[float, float] = (0.9, 0.999)
    eps: float = 1e-8
    fused: bool = True
    no_decay_bias_layernorm: bool = True
    extra_kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LRSchedulerConfig:
    """Configuration specification for learning rate schedulers."""

    name: str = "cosine"
    warmup_steps: int = 100
    total_steps: int = 1000
    min_lr: float = 1e-6
    extra_kwargs: Dict[str, Any] = field(default_factory=dict)


def create_param_groups(
    model_or_params: Union[
        torch.nn.Module, Iterable[torch.nn.Parameter], Iterable[Dict[str, Any]]
    ],
    weight_decay: float = 0.01,
    no_decay_keywords: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Separate parameters into decay and no-decay parameter groups.
    Excludes 1D tensors, biases, embeddings, and LayerNorm/RMSNorm parameters from weight decay.
    """
    if not isinstance(model_or_params, torch.nn.Module):
        if (
            isinstance(model_or_params, list)
            and len(model_or_params) > 0
            and isinstance(model_or_params[0], dict)
        ):
            return model_or_params
        return [{"params": list(model_or_params), "weight_decay": weight_decay}]

    keywords = no_decay_keywords or [
        "bias",
        "layernorm",
        "rmsnorm",
        "layer_norm",
        "embed",
        "ln_",
    ]
    decay_params: List[torch.nn.Parameter] = []
    no_decay_params: List[torch.nn.Parameter] = []

    for name, param in model_or_params.named_parameters():
        if not param.requires_grad:
            continue
        name_lower = name.lower()
        if param.ndim <= 1 or any(kw in name_lower for kw in keywords):
            no_decay_params.append(param)
        else:
            decay_params.append(param)

    return [
        {"params": decay_params, "weight_decay": weight_decay},
        {"params": no_decay_params, "weight_decay": 0.0},
    ]


@OPTIMIZERS.register(
    "adamw",
    priority=100,
    aliases=["adam_w"],
    description="AdamW optimizer with automatic fused kernel CUDA support.",
)
def build_adamw(
    params: Iterable,
    lr: float = 1e-3,
    weight_decay: float = 0.01,
    fused: bool = True,
    betas: Tuple[float, float] = (0.9, 0.999),
    eps: float = 1e-8,
    **kwargs: Any,
) -> Optimizer:
    """Build AdamW optimizer with safe fused fallback."""
    opt_kwargs = {
        "lr": lr,
        "weight_decay": weight_decay,
        "betas": betas,
        "eps": eps,
        **kwargs,
    }
    if fused and torch.cuda.is_available():
        try:
            return torch.optim.AdamW(params, fused=True, **opt_kwargs)
        except (TypeError, RuntimeError):
            pass
    return torch.optim.AdamW(params, **opt_kwargs)


@OPTIMIZERS.register(
    "adamw_8bit",
    priority=95,
    aliases=["adamw8bit", "bitsandbytes_adamw"],
    description="8-bit quantized AdamW optimizer (falls back to AdamW).",
)
def build_adamw_8bit(
    params: Iterable,
    lr: float = 1e-3,
    weight_decay: float = 0.01,
    **kwargs: Any,
) -> Optimizer:
    """Build 8-bit AdamW optimizer via bitsandbytes or AdamW fallback."""
    try:
        import bitsandbytes as bnb

        return bnb.optim.AdamW8bit(params, lr=lr, weight_decay=weight_decay, **kwargs)
    except ImportError:
        return build_adamw(params, lr=lr, weight_decay=weight_decay, **kwargs)


@OPTIMIZERS.register(
    "adam",
    priority=90,
    description="Standard PyTorch Adam optimizer.",
)
def build_adam(
    params: Iterable,
    lr: float = 1e-3,
    weight_decay: float = 0.0,
    betas: Tuple[float, float] = (0.9, 0.999),
    eps: float = 1e-8,
    **kwargs: Any,
) -> Optimizer:
    """Build standard Adam optimizer."""
    return torch.optim.Adam(
        params, lr=lr, weight_decay=weight_decay, betas=betas, eps=eps, **kwargs
    )


@OPTIMIZERS.register(
    "sgd",
    priority=80,
    description="Stochastic Gradient Descent (SGD) with momentum support.",
)
def build_sgd(
    params: Iterable,
    lr: float = 1e-2,
    momentum: float = 0.9,
    weight_decay: float = 0.0,
    nesterov: bool = False,
    **kwargs: Any,
) -> Optimizer:
    """Build SGD optimizer."""
    return torch.optim.SGD(
        params,
        lr=lr,
        momentum=momentum,
        weight_decay=weight_decay,
        nesterov=nesterov,
        **kwargs,
    )


@OPTIMIZERS.register(
    "rmsprop",
    priority=70,
    description="RMSprop optimizer.",
)
def build_rmsprop(
    params: Iterable,
    lr: float = 1e-2,
    alpha: float = 0.99,
    eps: float = 1e-8,
    weight_decay: float = 0.0,
    momentum: float = 0.0,
    **kwargs: Any,
) -> Optimizer:
    """Build RMSprop optimizer."""
    return torch.optim.RMSprop(
        params,
        lr=lr,
        alpha=alpha,
        eps=eps,
        weight_decay=weight_decay,
        momentum=momentum,
        **kwargs,
    )


@OPTIMIZERS.register(
    "lion",
    priority=60,
    aliases=["google_lion"],
    description="EvoLved Sign Momentum (Lion) memory-efficient optimizer.",
)
def build_lion(
    params: Iterable,
    lr: float = 1e-4,
    weight_decay: float = 0.1,
    betas: Tuple[float, float] = (0.9, 0.99),
    **kwargs: Any,
) -> Optimizer:
    """Build Lion optimizer (or fallback to AdamW if custom Lion is unimported)."""
    try:
        from lion_pytorch import Lion

        return Lion(params, lr=lr, weight_decay=weight_decay, betas=betas, **kwargs)
    except ImportError:
        logger.debug("lion_pytorch not found, falling back to AdamW.")
        return build_adamw(params, lr=lr, weight_decay=weight_decay, **kwargs)


@OPTIMIZERS.register(
    "adafactor",
    priority=50,
    description="Adafactor scale-invariant memory-efficient optimizer.",
)
def build_adafactor(
    params: Iterable,
    lr: Optional[float] = 1e-3,
    scale_parameter: bool = True,
    relative_step: bool = False,
    warmup_init: bool = False,
    **kwargs: Any,
) -> Optimizer:
    """Build Adafactor optimizer from transformers or PyTorch fallback."""
    try:
        from transformers.optimization import Adafactor

        return Adafactor(
            params,
            lr=lr,
            scale_parameter=scale_parameter,
            relative_step=relative_step,
            warmup_init=warmup_init,
            **kwargs,
        )
    except ImportError:
        return build_adamw(params, lr=lr or 1e-3, **kwargs)


# ==========================================
# Learning Rate Scheduler Registrations
# ==========================================


@SCHEDULERS.register("cosine", priority=100, aliases=["cosine_annealing"])
def build_cosine(
    optimizer: Optimizer,
    total_steps: int = 1000,
    min_lr: float = 1e-6,
    **kwargs: Any,
) -> LRScheduler:
    """Build Cosine Annealing learning rate scheduler."""
    t_max = kwargs.get("num_training_steps", total_steps)
    return CosineAnnealingLR(optimizer, T_max=t_max, eta_min=min_lr)


@SCHEDULERS.register("linear", priority=90, aliases=["linear_decay"])
def build_linear(
    optimizer: Optimizer,
    start_factor: float = 1.0,
    end_factor: float = 0.0,
    total_steps: int = 1000,
    **kwargs: Any,
) -> LRScheduler:
    """Build Linear decay learning rate scheduler."""
    t_max = kwargs.get("num_training_steps", total_steps)
    return LinearLR(
        optimizer, start_factor=start_factor, end_factor=end_factor, total_iters=t_max
    )


@SCHEDULERS.register("polynomial", priority=80, aliases=["poly"])
def build_polynomial(
    optimizer: Optimizer, total_steps: int = 1000, power: float = 1.0, **kwargs: Any
) -> LRScheduler:
    """Build Polynomial decay learning rate scheduler."""
    t_max = kwargs.get("num_training_steps", total_steps)
    return PolynomialLR(optimizer, total_iters=t_max, power=power)


@SCHEDULERS.register("one_cycle", priority=70, aliases=["onecycle"])
def build_one_cycle(
    optimizer: Optimizer, max_lr: float = 1e-3, total_steps: int = 1000, **kwargs: Any
) -> LRScheduler:
    """Build OneCycleLR scheduler."""
    t_max = kwargs.get("num_training_steps", total_steps)
    return OneCycleLR(optimizer, max_lr=max_lr, total_steps=t_max)


@SCHEDULERS.register("plateau", priority=60, aliases=["reduce_on_plateau"])
def build_plateau(
    optimizer: Optimizer,
    mode: str = "min",
    factor: float = 0.1,
    patience: int = 10,
    **kwargs: Any,
) -> ReduceLROnPlateau:
    """Build ReduceLROnPlateau scheduler."""
    return ReduceLROnPlateau(optimizer, mode=mode, factor=factor, patience=patience)


def build_scheduler(
    name_or_config: Union[str, Dict[str, Any], LRSchedulerConfig, Optimizer] = "cosine",
    optimizer: Optional[Optimizer] = None,
    total_steps: int = 1000,
    warmup_steps: int = 100,
    min_lr: float = 1e-6,
    **kwargs: Any,
) -> Any:
    """
    Unified learning rate scheduler factory function.
    Supports both:
      - build_scheduler("cosine", optimizer, total_steps=1000)
      - build_scheduler(optimizer, scheduler_type="cosine", num_training_steps=1000)
    """
    target_optimizer = optimizer
    target_name = "cosine"
    config_kwargs = dict(kwargs)

    if isinstance(name_or_config, Optimizer) or hasattr(name_or_config, "param_groups"):
        target_optimizer = name_or_config
        target_name = config_kwargs.pop("scheduler_type", config_kwargs.pop("name", "cosine"))
    elif isinstance(name_or_config, str):
        target_name = config_kwargs.pop("scheduler_type", name_or_config)
    elif isinstance(name_or_config, dict):
        target_name = name_or_config.get("name", name_or_config.get("scheduler_type", "cosine"))
        config_kwargs.update(name_or_config)
    elif isinstance(name_or_config, LRSchedulerConfig):
        target_name = name_or_config.name
        config_kwargs.update({
            "warmup_steps": name_or_config.warmup_steps,
            "total_steps": name_or_config.total_steps,
            "min_lr": name_or_config.min_lr,
            **name_or_config.extra_kwargs,
        })

    if target_optimizer is None and "optimizer" in config_kwargs:
        target_optimizer = config_kwargs.pop("optimizer")

    if target_optimizer is None:
        raise ValueError("An Optimizer instance must be provided to build_scheduler()")

    tot_steps = config_kwargs.get("num_training_steps", config_kwargs.get("total_steps", total_steps))
    w_steps = config_kwargs.get("num_warmup_steps", config_kwargs.get("warmup_steps", warmup_steps))
    minimum_lr = config_kwargs.get("min_lr", min_lr)

    sched_name = str(target_name).lower().strip()
    if sched_name in SCHEDULERS:
        return SCHEDULERS.build(
            sched_name,
            target_optimizer,
            total_steps=tot_steps,
            warmup_steps=w_steps,
            min_lr=minimum_lr,
            **config_kwargs,
        )

    return CosineAnnealingLR(target_optimizer, T_max=tot_steps, eta_min=minimum_lr)


__all__ = [
    "OPTIMIZERS",
    "SCHEDULERS",
    "OptimizerConfig",
    "LRSchedulerConfig",
    "create_param_groups",
    "build_adamw",
    "build_adamw_8bit",
    "build_adam",
    "build_sgd",
    "build_rmsprop",
    "build_lion",
    "build_adafactor",
    "build_cosine",
    "build_linear",
    "build_polynomial",
    "build_one_cycle",
    "build_plateau",
    "build_scheduler",
]
