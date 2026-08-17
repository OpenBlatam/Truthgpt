"""
Training Package
================
Modular PyTorch model training, evaluation, tracking, Exponential Moving Average (EMA),
and checkpointing components.
"""

from .checkpoint_manager import CheckpointError, CheckpointManager
from .ema_manager import EMAError, EMAManager
from .evaluator import EvaluationError, Evaluator
from .experiment_tracker import ExperimentTracker, ExperimentTrackerError
from .training_loop import TrainingError, TrainingLoop

__version__ = "1.0.0"

__all__ = [
    "Evaluator",
    "EvaluationError",
    "CheckpointManager",
    "CheckpointError",
    "EMAManager",
    "EMAError",
    "TrainingLoop",
    "TrainingError",
    "ExperimentTracker",
    "ExperimentTrackerError",
]
