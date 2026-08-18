"""
Quantum Utilities Module

Quantum computing utilities, quantum circuit simulation, VQE, QAOA,
and quantum-based deep learning optimization engines.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .._lazy_loader import create_lazy_module

__all__ = [
    'QuantumUtils',
    'QuantumOptimizationLevel',
    'QuantumDeepLearningSystem',
    'QuantumHybridAISystem',
    'QuantumNeuralOptimizationEngine',
    'UniversalQuantumOptimizer',
    'CuttingEdgeUniversalQuantumOptimizer',
    'NextGenQuantumNeuralOptimizationEngine',
    'RevolutionaryQuantumDeepLearningSystem',
    'UltraQuantumOptimization',
    'list_available_quantum_components',
    'get_quantum_component_info',
]

_LAZY_IMPORTS: Dict[str, str] = {
    'QuantumUtils': '.quantum_utils',
    'QuantumOptimizationLevel': '.quantum_utils',
    'QuantumDeepLearningSystem': '.quantum_deep_learning_system',
    'QuantumHybridAISystem': '.quantum_hybrid_ai_system',
    'QuantumNeuralOptimizationEngine': '.quantum_neural_optimization_engine',
    'UniversalQuantumOptimizer': '.universal_quantum_optimizer',
    'CuttingEdgeUniversalQuantumOptimizer': '.cutting_edge_universal_quantum_optimizer',
    'NextGenQuantumNeuralOptimizationEngine': '.next_gen_quantum_neural_optimization_engine',
    'RevolutionaryQuantumDeepLearningSystem': '.revolutionary_quantum_deep_learning_system',
    'UltraQuantumOptimization': '.ultra_quantum_optimization',
}

_loader = create_lazy_module(
    package_name=__name__,
    lazy_imports=_LAZY_IMPORTS,
    all_exports=__all__,
    globals_dict=globals(),
)


def __getattr__(name: str) -> Any:
    return _loader.__getattr__(name)


def __dir__() -> List[str]:
    return _loader.__dir__()


def list_available_quantum_components() -> List[str]:
    """List all available quantum utility components."""
    return _loader.list_components()


def get_quantum_component_info(component_name: str) -> Dict[str, Any]:
    """Get information about a quantum component."""
    return _loader.get_component_info(component_name)
