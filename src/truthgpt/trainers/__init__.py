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

from truthgpt.trainers.config import (
    TrainerConfig,
    ModelConfig,
    TrainingConfig,
    HardwareConfig,
    CheckpointConfig,
    EMAConfig,
)
from truthgpt.trainers.model_manager import ModelManager
from truthgpt.trainers.optimizer_manager import OptimizerManager
from truthgpt.trainers.data_manager import DataManager
from truthgpt.trainers.ema_manager import EMAManager
from truthgpt.trainers.evaluator import Evaluator
from truthgpt.trainers.checkpoint_manager import CheckpointManager

# Import trainer last to avoid circular dependencies
try:
    from truthgpt.trainers.trainer import GenericTrainer
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



