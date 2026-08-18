"""
System Utilities Module

System-level utilities, quantum deep learning, multiverse optimization,
distributed systems, and integration frameworks.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .._lazy_loader import create_lazy_module

__all__ = [
    'QuantumDeepLearningSystem',
    'QuantumHybridAISystem',
    'FederatedLearningSystem',
    'SyntheticMultiverseOptimizationSystem',
    'TensorFlowIntegrationSystem',
    'RevolutionaryQuantumDeepLearningSystem',
    'list_available_systems',
    'get_system_info',
]

_LAZY_IMPORTS: Dict[str, str] = {
    'QuantumDeepLearningSystem': '..quantum.quantum_deep_learning_system',
    'QuantumHybridAISystem': '..quantum.quantum_hybrid_ai_system',
    'FederatedLearningSystem': '..modules.federated_learning',
    'SyntheticMultiverseOptimizationSystem': '..synthetic_multiverse_optimization_system',
    'TensorFlowIntegrationSystem': '..tensorflow_integration_system',
    'RevolutionaryQuantumDeepLearningSystem': '..quantum.revolutionary_quantum_deep_learning_system',
}

_ALIASES: Dict[str, str] = {
    'FederatedLearningSystem': 'TruthGPTFederatedManager',
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


def list_available_systems() -> List[str]:
    """List all available system utilities."""
    return _loader.list_components()


def get_system_info(system_name: str) -> Dict[str, Any]:
    """Get information about a system utility."""
    return _loader.get_component_info(system_name)
