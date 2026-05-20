"""
Training Utilities Module

This module contains utilities for training, evaluation, and optimization.
"""

from __future__ import annotations

__all__ = [
    'TruthGPTTrainingUtils',
    'TruthGPTAdvancedTraining',
    'TruthGPTOptimizationUtils',
    'TruthGPTEvaluationUtils',
    'TruthGPTAdvancedEvaluation',
]

_LAZY_IMPORTS = {
    'TruthGPTTrainingUtils': '..truthgpt_training_utils',
    'TruthGPTAdvancedTraining': '..truthgpt_advanced_training',
    'TruthGPTOptimizationUtils': '..truthgpt_optimization_utils',
    'TruthGPTEvaluationUtils': '..truthgpt_evaluation_utils',
    'TruthGPTAdvancedEvaluation': '..truthgpt_advanced_evaluation',
}

_import_cache = {}


def __getattr__(name: str):
    """Lazy import system for training utility modules."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    if name in _import_cache:
        return _import_cache[name]
    
    module_path = _LAZY_IMPORTS[name]
    try:
        module = __import__(module_path, fromlist=[name], level=2)
        obj = getattr(module, name)
        _import_cache[name] = obj
        return obj
    except (ImportError, AttributeError) as e:
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'. "
            f"Failed to import: {e}"
        ) from e


