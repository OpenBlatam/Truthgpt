"""Unified Optimizer Factory module for Optimization Core.

Provides centralized factory pattern for instantiating PyTorch, JAX, or C++ native optimizers.
"""

import logging
from typing import Any, Dict, Optional
import torch
import torch.nn as nn
import torch.optim as optim

logger = logging.getLogger(__name__)


class UnifiedOptimizerFactory:
    """Factory class to create and configure PyTorch, JAX, or custom optimizers."""

    @staticmethod
    def create_optimizer(
        model: nn.Module,
        optimizer_type: str = "adamw",
        lr: float = 1e-4,
        weight_decay: float = 0.01,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> optim.Optimizer:
        """Instantiate standard PyTorch optimizer for given model parameters."""
        kwargs = kwargs or {}
        optimizer_type = optimizer_type.lower()

        trainable_params = [p for p in model.parameters() if p.requires_grad]

        if optimizer_type in {"adamw", "adam_w"}:
            logger.info("UnifiedOptimizerFactory: Creating AdamW optimizer (lr=%f, weight_decay=%f)", lr, weight_decay)
            return optim.AdamW(trainable_params, lr=lr, weight_decay=weight_decay, **kwargs)
        elif optimizer_type == "adam":
            logger.info("UnifiedOptimizerFactory: Creating Adam optimizer (lr=%f)", lr)
            return optim.Adam(trainable_params, lr=lr, weight_decay=weight_decay, **kwargs)
        elif optimizer_type == "sgd":
            logger.info("UnifiedOptimizerFactory: Creating SGD optimizer (lr=%f)", lr)
            return optim.SGD(trainable_params, lr=lr, weight_decay=weight_decay, **kwargs)
        elif optimizer_type in {"adam8bit", "bitsandbytes"}:
            try:
                import bitsandbytes as bnb
                logger.info("UnifiedOptimizerFactory: Creating 8-bit AdamW optimizer via bitsandbytes")
                return bnb.optim.AdamW8bit(trainable_params, lr=lr, weight_decay=weight_decay, **kwargs)
            except ImportError:
                logger.warning("bitsandbytes not installed, falling back to PyTorch standard AdamW")
                return optim.AdamW(trainable_params, lr=lr, weight_decay=weight_decay, **kwargs)
        else:
            raise ValueError(f"Unsupported optimizer type: '{optimizer_type}'")


__all__ = ["UnifiedOptimizerFactory"]
