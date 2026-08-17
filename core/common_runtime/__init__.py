"""
Common Runtime Module for TruthGPT Optimization Core.
Contains core configurations, interfaces, exceptions, utilities, and validation mechanisms.
"""

from .config import (
    ConfigManager,
    TrainerConfig,
    TrainingConfig,
    ModelConfig,
    DataConfig,
    OptimizerConfig,
    OptimizationConfig,
    Environment,
    ConfigSource,
)

from .exceptions import (
    TruthGPTCoreError,
    PluginError,
    ServiceRegistryError,
    OptimizerExecutionError,
    MicroserviceCommunicationError,
    ConfigValidationError,
    OptimizationCoreError,
)

from .interfaces import (
    BaseTrainer,
    BaseEvaluator,
    BaseModelManager,
    BaseDataLoader,
    BaseCheckpointManager,
)

from .metrics_base import BaseMetricsCalculator, MetricCollector
from .monitoring import PerformanceMonitor
from .paper_base import PaperImplementationBase
from .performance_utils import measure_latency, measure_model_memory

__all__ = [
    # Config
    "ConfigManager",
    "TrainerConfig",
    "TrainingConfig",
    "ModelConfig",
    "DataConfig",
    "OptimizerConfig",
    "OptimizationConfig",
    "Environment",
    "ConfigSource",
    # Exceptions
    "TruthGPTCoreError",
    "PluginError",
    "ServiceRegistryError",
    "OptimizerExecutionError",
    "MicroserviceCommunicationError",
    "ConfigValidationError",
    "OptimizationCoreError",
    # Interfaces
    "BaseTrainer",
    "BaseEvaluator",
    "BaseModelManager",
    "BaseDataLoader",
    "BaseCheckpointManager",
    # Runtime Utilities
    "BaseMetricsCalculator",
    "MetricCollector",
    "PerformanceMonitor",
    "PaperImplementationBase",
    "measure_latency",
    "measure_model_memory",
]

