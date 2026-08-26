"""
Common Runtime Module for TruthGPT Optimization Core.
Contains core configurations, interfaces, exceptions, utilities, and validation mechanisms.
"""

from .config import (
    ConfigManager,
    TruthGPTConfigManager,
    ConfigurationManager,
    TrainerConfig,
    TrainingConfig,
    ModelConfig,
    DataConfig,
    OptimizerConfig,
    OptimizationConfig,
    MonitoringConfig,
    PerformanceConfig,
    HardwareConfig,
    CheckpointConfig,
    EMAConfig,
    ResumeConfig,
    Environment,
    ConfigSource,
    create_config_manager,
    config_context,
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
    "TruthGPTConfigManager",
    "ConfigurationManager",
    "TrainerConfig",
    "TrainingConfig",
    "ModelConfig",
    "DataConfig",
    "OptimizerConfig",
    "OptimizationConfig",
    "MonitoringConfig",
    "PerformanceConfig",
    "HardwareConfig",
    "CheckpointConfig",
    "EMAConfig",
    "ResumeConfig",
    "Environment",
    "ConfigSource",
    "create_config_manager",
    "config_context",
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

