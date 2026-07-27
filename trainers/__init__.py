"""
Trainers module - Modular training components for PyTorch & Transformers LLMs.

This module provides:
- TrainerConfig: Configuration system with composition, property delegation, and validation
- ModelManager: Model loading, LoRA integration, compile, and device placement
- OptimizerManager: Optimizer creation, 2D/1D decay parameter grouping, and LR scheduling
- DataManager: Data loading, collation, and dynamic sequence length bucketing
- EMAManager: Exponential Moving Average weight tracking and state swapping
- Evaluator: Model evaluation, validation loss, and perplexity calculation
- CheckpointManager: Saving, loading, pruning checkpoints with safe tensors and RNG states
- GenericTrainer: Main modular training orchestrator
- TrainingProfiler & ProfilerManager: Performance, token throughput, and CUDA memory profiler
- MetricTracker & MetricsTracker: Sliding-window statistics accumulator
- DistributedManager: DDP rank resolution and barrier synchronization
- ExperimentTrackerRegistry: Dynamic plugin registry for experiment trackers
- Interfaces & Exception Hierarchy for enterprise extensibility
- Callbacks, Datasets, and ExperimentTrackers for modular extension
"""

__version__ = "2.5.0"

try:
    from .config import (
        TrainerConfig,
        ModelConfig,
        TrainingConfig,
        HardwareConfig,
        CheckpointConfig,
        EMAConfig,
    )
    from .model_manager import ModelManager
    from .optimizer_manager import OptimizerManager
    from .data_manager import DataManager
    from .ema_manager import EMAManager
    from .evaluator import Evaluator
    from .checkpoint_manager import CheckpointManager
    from .trainer import GenericTrainer, set_seed
    from .callbacks import Callback, CallbackHandler, PrintLogger, WandbLogger, TensorBoardLogger
    from .dataset import HFTextDataset, TextDataset, IterableTextDataset, PackedDataset, BucketBatchSampler
    from .experiment_tracker import (
        ExperimentTracker, ConsoleTracker, TensorBoardTracker, WandbTracker,
        MultiExperimentTracker, ExperimentTrackerRegistry,
    )
    from .profiler import TrainingProfiler, ProfilerManager
    from .metrics_tracker import MetricTracker, MetricsTracker
    from .dist_manager import DistributedManager
    from .interfaces import (
        BaseCallback, BaseExperimentTracker, BaseModelManager, BaseOptimizerManager,
        BaseDataManager, BaseCheckpointManager, BaseEMAManager, BaseEvaluator, BaseTrainer,
        ICallback, IExperimentTracker, IModelManager, IOptimizerManager,
        IDataManager, ICheckpointManager, IEMAManager, IEvaluator, ITrainer,
    )
    from .exceptions import (
        TrainerError, ConfigurationError, ModelManagerError, ModelInitializationError,
        OptimizerManagerError, OptimizerError, DataManagerError, DataLoadingError,
        CheckpointError, EvaluationError, EMAError, CallbackError, HardwareError, StateMismatchError,
        DistributedError, EarlyStoppingException,
    )
    from .types import (
        StepState, EvalMetrics, TrainerState, CheckpointMetadata, ProfilingSummary,
        DeviceType, PrecisionType, OptimizerType, SchedulerType, BatchType, LossType, MetricsDict, StateDict,
    )
except ImportError:
    from trainers.config import (
        TrainerConfig,
        ModelConfig,
        TrainingConfig,
        HardwareConfig,
        CheckpointConfig,
        EMAConfig,
    )
    from trainers.model_manager import ModelManager
    from trainers.optimizer_manager import OptimizerManager
    from trainers.data_manager import DataManager
    from trainers.ema_manager import EMAManager
    from trainers.evaluator import Evaluator
    from trainers.checkpoint_manager import CheckpointManager
    from trainers.trainer import GenericTrainer, set_seed
    from trainers.callbacks import Callback, CallbackHandler, PrintLogger, WandbLogger, TensorBoardLogger
    from trainers.dataset import HFTextDataset, TextDataset, IterableTextDataset, PackedDataset, BucketBatchSampler
    from trainers.experiment_tracker import (
        ExperimentTracker, ConsoleTracker, TensorBoardTracker, WandbTracker,
        MultiExperimentTracker, ExperimentTrackerRegistry,
    )
    from trainers.profiler import TrainingProfiler, ProfilerManager
    from trainers.metrics_tracker import MetricTracker, MetricsTracker
    from trainers.dist_manager import DistributedManager
    from trainers.interfaces import (
        BaseCallback, BaseExperimentTracker, BaseModelManager, BaseOptimizerManager,
        BaseDataManager, BaseCheckpointManager, BaseEMAManager, BaseEvaluator, BaseTrainer,
        ICallback, IExperimentTracker, IModelManager, IOptimizerManager,
        IDataManager, ICheckpointManager, IEMAManager, IEvaluator, ITrainer,
    )
    from trainers.exceptions import (
        TrainerError, ConfigurationError, ModelManagerError, ModelInitializationError,
        OptimizerManagerError, OptimizerError, DataManagerError, DataLoadingError,
        CheckpointError, EvaluationError, EMAError, CallbackError, HardwareError, StateMismatchError,
        DistributedError, EarlyStoppingException,
    )
    from trainers.types import (
        StepState, EvalMetrics, TrainerState, CheckpointMetadata, ProfilingSummary,
        DeviceType, PrecisionType, OptimizerType, SchedulerType, BatchType, LossType, MetricsDict, StateDict,
    )


__all__ = [
    # Metadata
    "__version__",
    # Configurations
    "TrainerConfig",
    "ModelConfig",
    "TrainingConfig",
    "HardwareConfig",
    "CheckpointConfig",
    "EMAConfig",
    # Managers & Orchestrator
    "ModelManager",
    "OptimizerManager",
    "DataManager",
    "EMAManager",
    "Evaluator",
    "CheckpointManager",
    "GenericTrainer",
    "set_seed",
    # Subsystems
    "TrainingProfiler",
    "ProfilerManager",
    "MetricTracker",
    "MetricsTracker",
    "DistributedManager",
    # Callbacks & Trackers
    "Callback",
    "CallbackHandler",
    "PrintLogger",
    "WandbLogger",
    "TensorBoardLogger",
    "ExperimentTracker",
    "ConsoleTracker",
    "TensorBoardTracker",
    "WandbTracker",
    "MultiExperimentTracker",
    "ExperimentTrackerRegistry",
    # Datasets
    "HFTextDataset",
    "TextDataset",
    "IterableTextDataset",
    "PackedDataset",
    "BucketBatchSampler",
    # Interfaces
    "BaseCallback",
    "BaseExperimentTracker",
    "BaseModelManager",
    "BaseOptimizerManager",
    "BaseDataManager",
    "BaseCheckpointManager",
    "BaseEMAManager",
    "BaseEvaluator",
    "BaseTrainer",
    "ICallback",
    "IExperimentTracker",
    "IModelManager",
    "IOptimizerManager",
    "IDataManager",
    "ICheckpointManager",
    "IEMAManager",
    "IEvaluator",
    "ITrainer",
    # Exceptions
    "TrainerError",
    "ConfigurationError",
    "ModelManagerError",
    "ModelInitializationError",
    "OptimizerManagerError",
    "OptimizerError",
    "DataManagerError",
    "DataLoadingError",
    "CheckpointError",
    "EvaluationError",
    "EMAError",
    "CallbackError",
    "HardwareError",
    "StateMismatchError",
    "DistributedError",
    "EarlyStoppingException",
    # Types
    "StepState",
    "EvalMetrics",
    "TrainerState",
    "CheckpointMetadata",
    "ProfilingSummary",
    "DeviceType",
    "PrecisionType",
    "OptimizerType",
    "SchedulerType",
    "BatchType",
    "LossType",
    "MetricsDict",
    "StateDict",
]
