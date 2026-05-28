"""
Learning Module
"""
from optimization_core.utils.dependency_manager import resolve_lazy_import

_LAZY_IMPORTS = {
    'EvolutionaryOptimizer': '.evolutionary.optimizer',
    'CausalInferenceEngine': '.causal.system',
    'ActiveLearningStrategy': '.active.enums',
    'evolutionary_computing': '.evolutionary',
    'causal_inference': '.causal',
    'active_learning': '.active',
}

def __getattr__(name: str):
    return resolve_lazy_import(name, __package__ or 'learning', _LAZY_IMPORTS)

def __dir__():
    return list(_LAZY_IMPORTS.keys())

__all__ = list(_LAZY_IMPORTS.keys())
