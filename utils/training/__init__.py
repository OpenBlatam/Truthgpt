"""
Training Utilities Module

Training, evaluation, optimization pipelines, and parallel training utilities.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .._lazy_loader import create_lazy_module

__all__ = [
    'TruthGPTTrainingUtils',
    'TruthGPTAdvancedTraining',
    'TruthGPTOptimizationUtils',
    'TruthGPTEvaluationUtils',
    'TruthGPTAdvancedEvaluation',
    'ParallelTraining',
    'list_available_training_components',
    'get_training_component_info',
]

_LAZY_IMPORTS: Dict[str, str] = {
    'TruthGPTTrainingUtils': '.training_utils',
    'TruthGPTAdvancedTraining': '.advanced_training',
    'TruthGPTOptimizationUtils': '.optimization_utils',
    'TruthGPTEvaluationUtils': '.evaluation_utils',
    'TruthGPTAdvancedEvaluation': '.advanced_evaluation',
    'ParallelTraining': '.parallel_training',
}

_ALIASES: Dict[str, str] = {
    'TruthGPTTrainingUtils': 'TruthGPTTrainer',
    'TruthGPTAdvancedTraining': 'TruthGPTAdvancedTrainer',
    'TruthGPTOptimizationUtils': 'TruthGPTIntegratedOptimizer',
    'TruthGPTEvaluationUtils': 'TruthGPTEvaluator',
    'TruthGPTAdvancedEvaluation': 'TruthGPTAdvancedEvaluator',
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


def list_available_training_components() -> List[str]:
    """List all available training utility components."""
    return _loader.list_components()


def get_training_component_info(component_name: str) -> Dict[str, Any]:
    """Get information about a training component."""
    return _loader.get_component_info(component_name)
