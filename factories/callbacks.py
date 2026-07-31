"""
Callback Factories
===================
Factory functions and registry for training callbacks and loggers.
"""
from typing import Optional

from .registry import Registry

try:
    from optimization_core.trainers.callbacks import (
        PrintLogger,
        WandbLogger,
        TensorBoardLogger,
    )
except (ImportError, ModuleNotFoundError):
    try:
        from ..trainers.callbacks import (
            PrintLogger,
            WandbLogger,
            TensorBoardLogger,
        )
    except (ImportError, ModuleNotFoundError):
        from trainers.callbacks import (
            PrintLogger,
            WandbLogger,
            TensorBoardLogger,
        )

CALLBACKS = Registry(name="CallbacksRegistry")


@CALLBACKS.register("print")
def build_print() -> PrintLogger:
    """Build a standard stdout logger."""
    return PrintLogger()


@CALLBACKS.register("wandb")
def build_wandb(
    project: Optional[str] = None, run_name: Optional[str] = None
) -> WandbLogger:
    """Build a Weights & Biases logger."""
    return WandbLogger(project=project or "truthgpt", run_name=run_name)


@CALLBACKS.register("tensorboard")
def build_tensorboard(log_dir: Optional[str] = None) -> TensorBoardLogger:
    """Build a TensorBoard event logger."""
    return TensorBoardLogger(log_dir=log_dir or "runs")



