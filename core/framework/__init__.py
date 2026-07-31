"""
Core Framework Package.
Provides centralized component factories, state managers, and error handling.
"""

from .error_handler import ErrorHandler, StrategyErrorHandler
from .component_factory import ComponentFactory
from .state_manager import StateManager
from .config import OptimizationConfig

__all__ = [
    "ErrorHandler",
    "StrategyErrorHandler",
    "ComponentFactory",
    "StateManager",
    "OptimizationConfig",
]
