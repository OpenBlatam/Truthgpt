"""
Experiment Tracker - Unified metrics, hyperparameters, and artifacts logging interface.

Supports multiplexing across Console, TensorBoard, WandB, MLflow, and custom dynamic trackers.
"""
import logging
from typing import Dict, Any, Optional, List, Type, ClassVar

from .interfaces import BaseExperimentTracker

logger = logging.getLogger(__name__)


class ExperimentTrackerRegistry:
    """Dynamic registry for experiment tracking backends."""
    
    _registry: ClassVar[Dict[str, Type[BaseExperimentTracker]]] = {}

    @classmethod
    def register(cls, name: str, tracker_cls: Type[BaseExperimentTracker]) -> None:
        """Register a new experiment tracker class under a key."""
        cls._registry[name.lower()] = tracker_cls

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> BaseExperimentTracker:
        """Factory method to instantiate a registered tracker."""
        key = name.lower()
        if key not in cls._registry:
            raise KeyError(f"Tracker '{name}' not found in ExperimentTrackerRegistry. Available: {list(cls._registry.keys())}")
        return cls._registry[key](**kwargs)


class ExperimentTracker(BaseExperimentTracker):
    """Base experiment tracker implementation logging to standard output."""

    def __init__(self, run_name: str = "run", log_dir: Optional[str] = None):
        self.run_name = run_name
        self.log_dir = log_dir

    def log_metrics(self, metrics: Dict[str, Any], step: int) -> None:
        formatted = ", ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in metrics.items())
        logger.info(f"[Step {step}] {formatted}")

    def log_hyperparams(self, params: Dict[str, Any]) -> None:
        logger.info(f"Hyperparameters: {params}")

    def finish(self) -> None:
        pass


class ConsoleTracker(ExperimentTracker):
    """Console-formatted metrics logger."""

    def log_metrics(self, metrics: Dict[str, Any], step: int) -> None:
        formatted = " | ".join(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}" for k, v in metrics.items())
        print(f"[Tracker step {step}] {formatted}")


class TensorBoardTracker(ExperimentTracker):
    """TensorBoard experiment tracking integration."""

    def __init__(self, run_name: str = "run", log_dir: Optional[str] = "runs"):
        super().__init__(run_name, log_dir)
        try:
            from torch.utils.tensorboard import SummaryWriter
            self.writer = SummaryWriter(log_dir=f"{log_dir}/{run_name}")
            self.enabled = True
        except ImportError:
            logger.warning("TensorBoard not available. Install with `pip install tensorboard`.")
            self.writer = None
            self.enabled = False

    def log_metrics(self, metrics: Dict[str, Any], step: int) -> None:
        super().log_metrics(metrics, step)
        if self.enabled and self.writer:
            for k, v in metrics.items():
                if isinstance(v, (int, float)):
                    self.writer.add_scalar(k, v, step)

    def finish(self) -> None:
        if self.enabled and self.writer:
            self.writer.close()


class WandbTracker(ExperimentTracker):
    """Weights & Biases experiment tracking integration."""

    def __init__(self, run_name: str = "run", project: str = "truthgpt"):
        super().__init__(run_name)
        try:
            import wandb
            self.wandb = wandb
            if not wandb.run:
                wandb.init(project=project, name=run_name)
            self.enabled = True
        except ImportError:
            logger.warning("W&B not available. Install with `pip install wandb`.")
            self.enabled = False

    def log_metrics(self, metrics: Dict[str, Any], step: int) -> None:
        super().log_metrics(metrics, step)
        if self.enabled:
            self.wandb.log(metrics, step=step)

    def finish(self) -> None:
        if self.enabled:
            self.wandb.finish()


class MultiExperimentTracker(ExperimentTracker):
    """Multiplexes experiment logging across multiple tracker backends."""

    def __init__(self, trackers: List[BaseExperimentTracker]):
        super().__init__()
        self.trackers = trackers

    def log_metrics(self, metrics: Dict[str, Any], step: int) -> None:
        for tracker in self.trackers:
            try:
                tracker.log_metrics(metrics, step)
            except Exception as e:
                logger.debug(f"MultiExperimentTracker error in {type(tracker).__name__}: {e}")

    def log_hyperparams(self, params: Dict[str, Any]) -> None:
        for tracker in self.trackers:
            try:
                tracker.log_hyperparams(params)
            except Exception as e:
                logger.debug(f"MultiExperimentTracker error in {type(tracker).__name__}: {e}")

    def finish(self) -> None:
        for tracker in self.trackers:
            try:
                tracker.finish()
            except Exception as e:
                logger.debug(f"MultiExperimentTracker finish error in {type(tracker).__name__}: {e}")


# Register standard trackers in registry
ExperimentTrackerRegistry.register("base", ExperimentTracker)
ExperimentTrackerRegistry.register("console", ConsoleTracker)
ExperimentTrackerRegistry.register("tensorboard", TensorBoardTracker)
ExperimentTrackerRegistry.register("wandb", WandbTracker)


__all__ = [
    "ExperimentTrackerRegistry",
    "ExperimentTracker",
    "ConsoleTracker",
    "TensorBoardTracker",
    "WandbTracker",
    "MultiExperimentTracker",
]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.trainers."):
        sys.modules["trainers." + __name__[len("optimization_core.trainers."):]] = _mod
    elif __name__.startswith("trainers."):
        sys.modules["optimization_core.trainers." + __name__[len("trainers."):]] = _mod
