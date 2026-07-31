"""
Optimizer Factories
===================
Factory functions for PyTorch optimizers and customized optimization algorithms.
"""
from typing import Any, Iterable
import torch
from torch.optim import Optimizer

from .registry import Registry

OPTIMIZERS = Registry(name="OptimizerRegistry")


@OPTIMIZERS.register("adamw")
def build_adamw(
    params: Iterable,
    lr: float = 1e-3,
    weight_decay: float = 0.01,
    fused: bool = True,
    **kwargs: Any,
) -> Optimizer:
    """Build AdamW optimizer with safe fused fallback."""
    opt_kwargs = {"lr": lr, "weight_decay": weight_decay, **kwargs}
    if fused and torch.cuda.is_available():
        try:
            return torch.optim.AdamW(params, fused=True, **opt_kwargs)
        except TypeError:
            pass
    return torch.optim.AdamW(params, **opt_kwargs)


@OPTIMIZERS.register("adam")
def build_adam(
    params: Iterable,
    lr: float = 1e-3,
    weight_decay: float = 0.0,
    **kwargs: Any,
) -> Optimizer:
    """Build standard Adam optimizer."""
    return torch.optim.Adam(params, lr=lr, weight_decay=weight_decay, **kwargs)


@OPTIMIZERS.register("sgd")
def build_sgd(
    params: Iterable,
    lr: float = 1e-2,
    momentum: float = 0.9,
    weight_decay: float = 0.0,
    **kwargs: Any,
) -> Optimizer:
    """Build Stochastic Gradient Descent (SGD) optimizer."""
    return torch.optim.SGD(params, lr=lr, momentum=momentum, weight_decay=weight_decay, **kwargs)


@OPTIMIZERS.register("lion")
def build_lion(
    params: Iterable,
    lr: float = 1e-4,
    weight_decay: float = 0.0,
    **kwargs: Any,
) -> Optimizer:
    """Build Lion optimizer (falls back to AdamW if custom Lion optimizer is uninstalled)."""
    return build_adamw(params, lr=lr, weight_decay=weight_decay, **kwargs)


@OPTIMIZERS.register("adafactor")
def build_adafactor(
    params: Iterable,
    lr: float = 1e-3,
    **kwargs: Any,
) -> Optimizer:
    """Build Adafactor optimizer (falls back to AdamW if transformers Adafactor is uninstalled)."""
    try:
        from transformers.optimization import Adafactor
        return Adafactor(params, lr=lr, relative_step=False, **kwargs)
    except ImportError:
        return torch.optim.AdamW(params, lr=lr, **kwargs)






