"""
Core Framework Package.

Contains AI optimization framework components with thread-safe lazy loading:
- Pipeline: OptimizationPipeline, TrainingPipeline
- Builders: ResultBuilder, ComponentFactory
- Calculators: StatisticsCalculator, MetricsCalculator
- Strategy: StrategySelector
- State: StateManager, StatePersistence
- Error handling: ErrorHandler, StrategyErrorHandler
- AI components: AIExtremeOptimizer, NeuralOptimizationNetwork,
  LearningMechanism, LearningAnalyzer, InsightsGenerator,
  ModelFeatureExtractor
- Models: AIOptimizationResult, AIOptimizationLevel
"""

from __future__ import annotations

import importlib
import threading
from typing import Dict, Any, List

_LAZY_FRAMEWORK_MAP: Dict[str, tuple[str, str]] = {
    "ErrorHandler": (".error_handler", "ErrorHandler"),
    "StrategyErrorHandler": (".error_handler", "StrategyErrorHandler"),
    "ComponentFactory": (".component_factory", "ComponentFactory"),
    "StateManager": (".state_manager", "StateManager"),
    "OptimizationConfig": ("..common_runtime.config", "OptimizationConfig"),
    "TrainingPipeline": (".training_pipeline", "TrainingPipeline"),
    "OptimizationPipeline": (".optimization_pipeline", "OptimizationPipeline"),
    "ResultBuilder": (".result_builder", "ResultBuilder"),
    "StatisticsCalculator": (".statistics_calculator", "StatisticsCalculator"),
    "StrategySelector": (".strategy_selector", "StrategySelector"),
    "MetricsCalculator": (".metrics_calculator", "MetricsCalculator"),
    "AIOptimizationLevel": (".metrics_calculator", "AIOptimizationLevel"),
    "AIOptimizationResult": (".models", "AIOptimizationResult"),
    "NeuralOptimizationNetwork": (".neural_network", "NeuralOptimizationNetwork"),
    "LearningMechanism": (".learning_mechanism", "LearningMechanism"),
    "LearningAnalyzer": (".learning_analyzer", "LearningAnalyzer"),
    "InsightsGenerator": (".insights_generator", "InsightsGenerator"),
    "StatePersistence": (".state_persistence", "StatePersistence"),
    "ModelFeatureExtractor": (".model_features", "ModelFeatureExtractor"),
    "AIExtremeOptimizer": (".ai_extreme_optimizer", "AIExtremeOptimizer"),
}

_import_cache: Dict[str, Any] = {}
_cache_lock = threading.RLock()


def __getattr__(name: str) -> Any:
    """Lazy import framework symbols on first access."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    with _cache_lock:
        if name in _import_cache:
            return _import_cache[name]

        if name in _LAZY_FRAMEWORK_MAP:
            mod_rel_path, symbol_name = _LAZY_FRAMEWORK_MAP[name]
            try:
                mod = importlib.import_module(mod_rel_path, package=__name__)
                obj = getattr(mod, symbol_name)
                _import_cache[name] = obj
                globals()[name] = obj
                return obj
            except Exception as e:
                raise AttributeError(f"Failed to lazy load '{name}' from '{mod_rel_path}': {e}") from e

        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> List[str]:
    """Return available framework symbols."""
    return sorted(list(set(globals().keys()) | set(_LAZY_FRAMEWORK_MAP.keys()) | set(__all__)))


__all__ = [
    "ErrorHandler",
    "StrategyErrorHandler",
    "ComponentFactory",
    "StateManager",
    "OptimizationConfig",
    "TrainingPipeline",
    "OptimizationPipeline",
    "ResultBuilder",
    "StatisticsCalculator",
    "StrategySelector",
    "MetricsCalculator",
    "AIOptimizationLevel",
    "AIOptimizationResult",
    "NeuralOptimizationNetwork",
    "LearningMechanism",
    "LearningAnalyzer",
    "InsightsGenerator",
    "StatePersistence",
    "ModelFeatureExtractor",
    "AIExtremeOptimizer",
]
