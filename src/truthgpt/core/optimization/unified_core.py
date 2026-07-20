"""
Unified Optimization Core
Provides the Context for the optimization strategy pattern.
"""

import torch.nn as nn
from typing import Dict, Any, Tuple
from .base_strategy import BaseOptimizationStrategy

class UnifiedOptimizationCore:
    """
    The Context class for the optimization strategy pattern.
    It takes an optimization strategy and applies it to models.
    """
    
    def __init__(self, strategy: BaseOptimizationStrategy):
        """
        Initialize with a specific optimization strategy.
        
        Args:
            strategy: The optimization strategy to use.
        """
        self._strategy = strategy
        
    def set_strategy(self, strategy: BaseOptimizationStrategy):
        """
        Change the strategy dynamically at runtime.
        
        Args:
            strategy: The new optimization strategy to use.
        """
        self._strategy = strategy
        
    def optimize_module(self, module: nn.Module, context: Dict[str, Any] = None) -> Tuple[nn.Module, Dict[str, Any]]:
        """
        Optimize the module using the current strategy.
        
        Args:
            module: The neural network module to optimize.
            context: Additional context or data needed for the optimization.
            
        Returns:
            A tuple containing the optimized module and optimization statistics.
        """
        if context is None:
            context = {}
        return self._strategy.optimize_module(module, context)
        
    def get_report(self) -> Dict[str, Any]:
        """
        Get the optimization report from the current strategy.
        
        Returns:
            A dictionary containing report metrics and details.
        """
        return self._strategy.get_report()
