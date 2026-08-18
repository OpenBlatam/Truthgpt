"""
AI Utilities Module

AI/ML optimization utilities, autonomous agents, neural architecture search,
and advanced AI reasoning tools.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .._lazy_loader import create_lazy_module

__all__ = [
    'AdvancedAIOptimizer',
    'UltraAIOptimizer',
    'AIUtils',
    'UltraAutonomousAgent',
    'UltraMachineLearningOptimizer',
    'UltraNeuralArchitectureSearch',
    'UltraNeuralNetworkOptimizer',
    'list_available_ai_components',
    'get_ai_component_info',
]

_LAZY_IMPORTS: Dict[str, str] = {
    'AdvancedAIOptimizer': '.ultra_ai_optimizer',
    'UltraAIOptimizer': '.ultra_ai_optimizer',
    'AIUtils': '.ai_utils',
    'UltraAutonomousAgent': '.ultra_autonomous_agent',
    'UltraMachineLearningOptimizer': '.ultra_ml_optimizer',
    'UltraNeuralArchitectureSearch': '.neural_architecture_search',
    'UltraNeuralNetworkOptimizer': '.ultra_nn_optimizer',
}

_ALIASES: Dict[str, str] = {
    'AdvancedAIOptimizer': 'UltraAIOptimizer',
}

_loader = create_lazy_module(
    package_name=__name__,
    lazy_imports=_LAZY_IMPORTS,
    aliases=_ALIASES,
    all_exports=__all__,
    globals_dict=globals(),
)


def __getattr__(name: str) -> Any:
    return _loader.__getattr__(name)


def __dir__() -> List[str]:
    return _loader.__dir__()


def list_available_ai_components() -> List[str]:
    """List all available AI utility components."""
    return _loader.list_components()


def get_ai_component_info(component_name: str) -> Dict[str, Any]:
    """Get information about an AI component."""
    return _loader.get_component_info(component_name)
