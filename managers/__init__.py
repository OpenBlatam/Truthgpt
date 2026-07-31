"""
Unified Manager System
======================
Centralized access to all manager classes in optimization_core.
"""

try:
    from config.config_manager import ConfigManager
    ConfigurationManager = ConfigManager
except Exception:
    try:
        from optimization_core.config.config_manager import ConfigManager
        ConfigurationManager = ConfigManager
    except Exception:
        ConfigManager = None
        ConfigurationManager = None

try:
    from training.checkpoint_manager import CheckpointManager
except Exception:
    try:
        from optimization_core.training.checkpoint_manager import CheckpointManager
    except Exception:
        CheckpointManager = None

TrainersCheckpointManager = CheckpointManager
TrainingCheckpointManager = CheckpointManager
CheckpointManagerAlias = CheckpointManager

try:
    from training.ema_manager import EMAManager
except Exception:
    try:
        from optimization_core.training.ema_manager import EMAManager
    except Exception:
        EMAManager = None

TrainersEMAManager = EMAManager
TrainingEMAManager = EMAManager
EMAManagerAlias = EMAManager

try:
    from data.dataset_manager import DatasetManager
except Exception:
    DatasetManager = None

try:
    from trainers.model_manager import ModelManager as TrainersModelManager
except Exception:
    TrainersModelManager = None

try:
    from trainers.data_manager import DataManager as TrainersDataManager
except Exception:
    TrainersDataManager = None

try:
    from trainers.optimizer_manager import OptimizerManager as TrainersOptimizerManager
except Exception:
    TrainersOptimizerManager = None

try:
    from inference.cache_manager import CacheManager as InferenceCacheManager
except Exception:
    InferenceCacheManager = None

try:
    from models.diffusion_manager import DiffusionManager
except Exception:
    DiffusionManager = None

try:
    from models.model_manager import ModelManager as ModelsModelManager
except Exception:
    ModelsModelManager = None

try:
    from modules.memory.advanced_memory_manager import (
        AdvancedMemoryManager,
        create_advanced_memory_manager,
    )
except Exception:
    AdvancedMemoryManager = None
    create_advanced_memory_manager = None

try:
    from modules.module_manager import ModuleManager
except Exception:
    ModuleManager = None


def create_manager(manager_type: str = "config", config: dict = None):
    """
    Unified factory function to create managers.
    """
    if config is None:
        config = {}

    manager_type = manager_type.lower()
    if manager_type in ("config", "configuration"):
        return ConfigManager(config) if ConfigManager else None
    elif manager_type == "checkpoint":
        out_dir = config.get("output_dir", "./checkpoints")
        return CheckpointManager(output_dir=out_dir) if CheckpointManager else None
    elif manager_type == "ema":
        decay = config.get("decay", 0.999)
        return EMAManager(decay=decay) if EMAManager else None
    elif manager_type == "dataset":
        return DatasetManager(config) if DatasetManager else None
    elif manager_type == "cache":
        return InferenceCacheManager(config) if InferenceCacheManager else None
    else:
        raise ValueError(f"Unknown manager_type: '{manager_type}'")


__all__ = [
    "ConfigurationManager",
    "ConfigManager",
    "CheckpointManager",
    "TrainersCheckpointManager",
    "TrainingCheckpointManager",
    "EMAManager",
    "TrainersEMAManager",
    "TrainingEMAManager",
    "DatasetManager",
    "create_manager",
]
