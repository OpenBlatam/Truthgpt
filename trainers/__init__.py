"""
Trainers module - Modular training components.

This module provides:
- TrainerConfig: Configuration system with composition
- ModelManager: Model loading and configuration
- OptimizerManager: Optimizer and scheduler management
- DataManager: Data loading and preprocessing
- EMAManager: Exponential Moving Average
- Evaluator: Model evaluation
- CheckpointManager: Checkpoint management
- GenericTrainer: Main training orchestrator
"""

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

# Import trainer last to avoid circular dependencies
try:
    from trainers.trainer import GenericTrainer
except ImportError:
    # GenericTrainer might not be updated yet
    GenericTrainer = None

__all__ = [
    "TrainerConfig",
    "ModelConfig",
    "TrainingConfig",
    "HardwareConfig",
    "CheckpointConfig",
    "EMAConfig",
    "ModelManager",
    "OptimizerManager",
    "DataManager",
    "EMAManager",
    "Evaluator",
    "CheckpointManager",
    "GenericTrainer",
]



