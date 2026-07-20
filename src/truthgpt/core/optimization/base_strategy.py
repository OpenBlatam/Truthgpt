"""
Base Optimization Strategy
Provides the abstract base class for all optimization cores in the system.
"""

from abc import ABC, abstractmethod
import torch
import torch.nn as nn
from typing import Dict, Any, Tuple

class BaseOptimizationStrategy(ABC):
    """
    Abstract base class defining the standard interface for optimization strategies.
    Every optimization core must inherit from this class and implement its methods.
    """
    
    @abstractmethod
    def optimize_module(self, module: nn.Module, context: Dict[str, Any] = None) -> Tuple[nn.Module, Dict[str, Any]]:
        """
        Apply optimizations to the given module.
        
        Args:
            module: The neural network module to optimize.
            context: Additional context or data needed for the optimization.
            
        Returns:
            A tuple containing:
                - The optimized neural network module.
                - A dictionary containing optimization statistics and metadata.
        """
        pass
        
    @abstractmethod
    def get_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive report of the optimizations performed.
        
        Returns:
            A dictionary containing report metrics and details.
        """
        pass
