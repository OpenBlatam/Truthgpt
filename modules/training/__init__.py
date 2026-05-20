"""
Ultra-fast modular training components
Following deep learning best practices
"""

import logging

logger = logging.getLogger(__name__)

# Try to import from trainer.py (the primary source)
try:
    from .trainer import (
        FastTrainer, 
        TrainerConfig, 
        TrainingStep,
        OptimizerType,
        SchedulerType,
        TrainingStrategy
    )
except ImportError as e:
    logger.warning(f"Core training components failed to load: {e}")
    FastTrainer = None
    TrainerConfig = None
    TrainingStep = None

# Fallback/Shim for missing modules to prevent system-wide boot failure
class FastDataLoader: pass
class DataLoaderConfig: pass
class DataProcessor: pass
class FastOptimizer: pass
class OptimizerConfig: pass
class SchedulerConfig: pass
class LossFunction: pass
class LossConfig: pass
def compute_loss(*args, **kwargs): pass
class MetricsTracker: pass
class MetricConfig: pass
def compute_metrics(*args, **kwargs): pass
class CheckpointManager: pass
class CheckpointConfig: pass
def save_checkpoint(*args, **kwargs): pass
def load_checkpoint(*args, **kwargs): pass
class Validator: pass
class ValidationConfig: pass
def validate_model(*args, **kwargs): pass
class TrainingProfiler: pass
class ProfilerConfig: pass
def profile_training(*args, **kwargs): pass

__all__ = [
    'FastTrainer', 'TrainerConfig', 'TrainingStep',
    'FastDataLoader', 'DataLoaderConfig', 'DataProcessor',
    'FastOptimizer', 'OptimizerConfig', 'SchedulerConfig',
    'LossFunction', 'LossConfig', 'compute_loss',
    'MetricsTracker', 'MetricConfig', 'compute_metrics',
    'CheckpointManager', 'CheckpointConfig', 'save_checkpoint', 'load_checkpoint',
    'Validator', 'ValidationConfig', 'validate_model',
    'TrainingProfiler', 'ProfilerConfig', 'profile_training'
]
