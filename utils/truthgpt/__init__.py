"""
TruthGPT Utilities Module

TruthGPT-specific optimizers, configuration, integrated adapters,
enhanced utilities, integration, and monitoring components.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .._lazy_loader import create_lazy_module

__all__ = [
    'OptimizationLevel',
    'DeviceType',
    'PrecisionType',
    'TruthGPTConfig',
    'BaseTruthGPTOptimizer',
    'TruthGPTDeviceManager',
    'TruthGPTPrecisionManager',
    'TruthGPTMemoryManager',
    'TruthGPTPerformanceManager',
    'TruthGPTAttentionOptimizer',
    'TruthGPTQuantizationOptimizer',
    'TruthGPTPruningOptimizer',
    'TruthGPTIntegratedOptimizer',
    'create_truthgpt_config',
    'create_truthgpt_optimizer',
    'quick_truthgpt_optimization',
    'truthgpt_optimization_context',
    'TruthGPTEnhancedUtils',
    'TruthGPTIntegration',
    'TruthGPTMonitoring',
    'TruthGPTTrainingUtils',
    'TruthGPTEvaluationUtils',
    'list_available_truthgpt_components',
    'get_truthgpt_component_info',
]

_LAZY_IMPORTS: Dict[str, str] = {
    # Core — now local
    'OptimizationLevel': '.core',
    'DeviceType': '.core',
    'PrecisionType': '.core',
    'TruthGPTConfig': '.core',
    'BaseTruthGPTOptimizer': '.core',
    'TruthGPTDeviceManager': '.core',
    'TruthGPTPrecisionManager': '.core',
    'TruthGPTMemoryManager': '.core',
    'TruthGPTPerformanceManager': '.core',
    'TruthGPTAttentionOptimizer': '.core',
    'TruthGPTQuantizationOptimizer': '.core',
    'TruthGPTPruningOptimizer': '.core',
    'TruthGPTIntegratedOptimizer': '.core',
    'create_truthgpt_config': '.core',
    'create_truthgpt_optimizer': '.core',
    'quick_truthgpt_optimization': '.core',
    'truthgpt_optimization_context': '.core',
    # Enhanced utils — now local
    'TruthGPTEnhancedUtils': '.enhanced_utils',
    # Integration — now local
    'TruthGPTIntegration': '.integration',
    # Monitoring — now local
    'TruthGPTMonitoring': '.monitoring',
    # Training/Eval — reference training subpackage
    'TruthGPTTrainingUtils': '..training.training_utils',
    'TruthGPTEvaluationUtils': '..training.evaluation_utils',
}

_ALIASES: Dict[str, str] = {
    'TruthGPTTrainingUtils': 'TruthGPTTrainer',
    'TruthGPTEvaluationUtils': 'TruthGPTEvaluator',
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


def list_available_truthgpt_components() -> List[str]:
    """List all available TruthGPT components."""
    return _loader.list_components()


def get_truthgpt_component_info(component_name: str) -> Dict[str, Any]:
    """Get information about a TruthGPT component."""
    return _loader.get_component_info(component_name)
