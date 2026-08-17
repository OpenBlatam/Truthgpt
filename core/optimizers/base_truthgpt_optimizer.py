"""
Base TruthGPT Optimizer Module.
Provides the base class for TruthGPT model optimization.
"""

from typing import Dict, Any, Optional
import torch.nn as nn
from .pytorch_optimizer_base import PyTorchOptimizerBase, OptimizationConfig


class BaseTruthGPTOptimizer(PyTorchOptimizerBase):
    """
    Base class for TruthGPT optimizer instances.
    Provides optimization hooks, lifecycle management, and strategy dispatches.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            config = {}
        if isinstance(config, dict):
            opt_config = OptimizationConfig(
                model_name=config.get("model_name", "truthgpt"),
                learning_rate=config.get("learning_rate", 1e-4),
                batch_size=config.get("batch_size", 32),
                device=config.get("device", "auto"),
            )
        else:
            opt_config = config
        super().__init__(opt_config)
        self.user_config = config if isinstance(config, dict) else {}
        self.techniques_applied = []

    def optimize(self, model: nn.Module) -> nn.Module:
        """
        Base optimization method to be overridden by subclasses.
        """
        self.logger.info("Executing BaseTruthGPTOptimizer pipeline...")
        return model

    def get_applied_techniques(self) -> list:
        """Return list of applied optimization techniques."""
        return list(self.techniques_applied)

