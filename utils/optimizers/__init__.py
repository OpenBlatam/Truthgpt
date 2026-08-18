"""
Optimizer Utilities Module

Various optimizer utilities, engines, and optimization systems including
hyper-speed, quantum, evolutionary, and neural optimization engines.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .._lazy_loader import create_lazy_module

__all__ = [
    'HyperSpeedOptimizer',
    'CuttingEdgeUniversalQuantumOptimizer',
    'UniversalQuantumOptimizer',
    'NeuralEvolutionaryOptimizer',
    'AdvancedAIOptimizer',
    'AutoPerformanceOptimizer',
    'UltraNeuralNetworkOptimizer',
    'UltraAIOptimizer',
    'UltraMachineLearningOptimizer',
    'NextGenOptimizationEngine',
    'NextGenQuantumNeuralOptimizationEngine',
    'RevolutionaryQuantumDeepLearningSystem',
    'UltraQuantumOptimization',
    'TruthGPTIntegratedOptimizer',
    'list_available_optimizers',
    'get_optimizer_info',
]

_LAZY_IMPORTS: Dict[str, str] = {
    'HyperSpeedOptimizer': '..hyper_speed_optimizer',
    'AutoPerformanceOptimizer': '..auto_performance_optimizer',
    'NeuralEvolutionaryOptimizer': '..neural_evolutionary_optimizer',
    'UltraAIOptimizer': '..ultra_ai_optimizer',
    'AdvancedAIOptimizer': '..ultra_ai_optimizer',
    'UltraMachineLearningOptimizer': '..ultra_machine_learning_optimizer',
    'UltraNeuralNetworkOptimizer': '..ultra_neural_network_optimizer',
    'NextGenOptimizationEngine': '..next_gen_optimization_engine',
    'CuttingEdgeUniversalQuantumOptimizer': '..quantum.cutting_edge_universal_quantum_optimizer',
    'UniversalQuantumOptimizer': '..quantum.universal_quantum_optimizer',
    'NextGenQuantumNeuralOptimizationEngine': '..quantum.next_gen_quantum_neural_optimization_engine',
    'RevolutionaryQuantumDeepLearningSystem': '..quantum.revolutionary_quantum_deep_learning_system',
    'UltraQuantumOptimization': '..quantum.ultra_quantum_optimization',
    'TruthGPTIntegratedOptimizer': '..truthgpt_core',
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


def list_available_optimizers() -> List[str]:
    """List all available optimizer utilities."""
    return _loader.list_components()


def get_optimizer_info(optimizer_name: str) -> Dict[str, Any]:
    """Get information about an optimizer utility."""
    return _loader.get_component_info(optimizer_name)
