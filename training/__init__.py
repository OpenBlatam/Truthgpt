"""
Training Package
================
Modular PyTorch model training, evaluation, tracking, Exponential Moving Average (EMA),
checkpointing, lifecycle callbacks, and pipeline orchestration components.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

# 1. Exceptions
from .exceptions import (
    CheckpointCorruptedError,
    CheckpointError,
    CheckpointNotFoundError,
    DeviceTransferError,
    EarlyStoppingTriggered,
    EMAError,
    EvaluationError,
    ExperimentTrackerError,
    GradientOverflowError,
    PipelineError,
    TrainingBaseException,
    TrainingConfigurationError,
    TrainingError,
)

# 2. Interfaces
from .interfaces import (
    BaseCallback,
    BaseCheckpointManager,
    BaseEMAManager,
    BaseEvaluator,
    BaseExperimentTracker,
    BaseTrainingLoop,
    BaseTrainingPipeline,
)

# 3. Types and Enums
from .types import (
    CheckpointConfig,
    CheckpointMetadata,
    CheckpointStrategy,
    EarlyStoppingConfig,
    EMAConfig,
    EMADecaySchedule,
    EpochResult,
    EvaluationMetrics,
    EvaluatorConfig,
    PrecisionType,
    StepResult,
    TrackerBackend,
    TrackerConfig,
    TrainingComponentInfo,
    TrainingLoopConfig,
    TrainingMode,
    TrainingPipelineConfig,
)

# 4. Callbacks
from .callbacks import (
    Callback,
    CallbackHandler,
    EarlyStoppingCallback,
    GradientNormCallback,
    LRMonitorCallback,
    MetricsLoggerCallback,
    ModelCheckpointCallback,
    ProgressCallback,
)

# 5. Core Components
from .checkpoint_manager import CheckpointManager
from .ema_manager import EMAManager
from .evaluator import Evaluator
from .experiment_tracker import ExperimentTracker
from .pipeline import TrainingPipeline, TrainingPipelineBuilder
from .training_loop import TrainingLoop

# 6. Registry & Factory System
from .registry import (
    TRAINING_REGISTRY,
    TrainingRegistry,
    create_training_component,
    get_training_component_info,
    list_available_training_components,
    register_training_component,
)

__version__ = "2.0.0"


# Direct convenience factories
def create_training_loop(
    config: Optional[Union[Dict[str, Any], TrainingLoopConfig]] = None,
    **kwargs: Any,
) -> TrainingLoop:
    """Create a configured TrainingLoop instance."""
    return create_training_component("training_loop", config=config, **kwargs)


def create_checkpoint_manager(
    output_dir: str = "./checkpoints",
    config: Optional[Union[Dict[str, Any], CheckpointConfig]] = None,
    **kwargs: Any,
) -> CheckpointManager:
    """Create a configured CheckpointManager instance."""
    return create_training_component("checkpoint_manager", output_dir=output_dir, config=config, **kwargs)


def create_ema_manager(
    decay: float = 0.999,
    config: Optional[Union[Dict[str, Any], EMAConfig]] = None,
    **kwargs: Any,
) -> EMAManager:
    """Create a configured EMAManager instance."""
    return create_training_component("ema_manager", decay=decay, config=config, **kwargs)


def create_evaluator(
    config: Optional[Union[Dict[str, Any], EvaluatorConfig]] = None,
    **kwargs: Any,
) -> Evaluator:
    """Create a configured Evaluator instance."""
    return create_training_component("evaluator", config=config, **kwargs)


def create_experiment_tracker(
    trackers: Optional[Union[List[str], Dict[str, Any]]] = None,
    config: Optional[Union[Dict[str, Any], TrackerConfig]] = None,
    **kwargs: Any,
) -> ExperimentTracker:
    """Create a configured ExperimentTracker instance."""
    return create_training_component("experiment_tracker", trackers=trackers, config=config, **kwargs)


def create_training_pipeline(
    config: Optional[Union[Dict[str, Any], TrainingPipelineConfig]] = None,
    **kwargs: Any,
) -> TrainingPipeline:
    """Create a configured TrainingPipeline instance."""
    return create_training_component("training_pipeline", config=config, **kwargs)


def create_pipeline_builder() -> TrainingPipelineBuilder:
    """Create a fresh TrainingPipelineBuilder instance."""
    return TrainingPipelineBuilder()


__all__ = [
    # Version
    "__version__",
    # Core Components
    "TrainingLoop",
    "CheckpointManager",
    "EMAManager",
    "Evaluator",
    "ExperimentTracker",
    "TrainingPipeline",
    "TrainingPipelineBuilder",
    # Callbacks
    "Callback",
    "BaseCallback",
    "EarlyStoppingCallback",
    "ModelCheckpointCallback",
    "LRMonitorCallback",
    "MetricsLoggerCallback",
    "GradientNormCallback",
    "ProgressCallback",
    "CallbackHandler",
    # Interfaces
    "BaseTrainingLoop",
    "BaseCheckpointManager",
    "BaseEMAManager",
    "BaseEvaluator",
    "BaseExperimentTracker",
    "BaseTrainingPipeline",
    # Exceptions
    "TrainingBaseException",
    "TrainingError",
    "TrainingConfigurationError",
    "CheckpointError",
    "CheckpointNotFoundError",
    "CheckpointCorruptedError",
    "EMAError",
    "EvaluationError",
    "ExperimentTrackerError",
    "EarlyStoppingTriggered",
    "GradientOverflowError",
    "DeviceTransferError",
    "PipelineError",
    # Types & Enums
    "TrainingMode",
    "PrecisionType",
    "CheckpointStrategy",
    "EMADecaySchedule",
    "TrackerBackend",
    "StepResult",
    "EpochResult",
    "EvaluationMetrics",
    "CheckpointMetadata",
    "EarlyStoppingConfig",
    "TrainingLoopConfig",
    "CheckpointConfig",
    "EMAConfig",
    "EvaluatorConfig",
    "TrackerConfig",
    "TrainingPipelineConfig",
    "TrainingComponentInfo",
    # Registry & Factories
    "TRAINING_REGISTRY",
    "TrainingRegistry",
    "register_training_component",
    "create_training_component",
    "list_available_training_components",
    "get_training_component_info",
    "create_training_loop",
    "create_checkpoint_manager",
    "create_ema_manager",
    "create_evaluator",
    "create_experiment_tracker",
    "create_training_pipeline",
    "create_pipeline_builder",
]
