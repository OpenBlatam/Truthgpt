"""
Core Framework Package.

Contains the AI optimization framework components:
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

from .error_handler import ErrorHandler, StrategyErrorHandler
from .component_factory import ComponentFactory
from .state_manager import StateManager
from ..common_runtime.config import OptimizationConfig

from .optimization_pipeline import OptimizationPipeline
from .result_builder import ResultBuilder
from .statistics_calculator import StatisticsCalculator
from .strategy_selector import StrategySelector
from .metrics_calculator import MetricsCalculator, AIOptimizationLevel
from .models import AIOptimizationResult
from .neural_network import NeuralOptimizationNetwork
from .learning_mechanism import LearningMechanism
from .learning_analyzer import LearningAnalyzer
from .insights_generator import InsightsGenerator
from .state_persistence import StatePersistence
from .model_features import ModelFeatureExtractor
from .ai_extreme_optimizer import AIExtremeOptimizer


try:
    from .training_pipeline import TrainingPipeline
except ImportError:
    TrainingPipeline = None

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
