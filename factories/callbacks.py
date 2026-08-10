"""
Callback & Logging Factories
=============================
Factory functions and registry for training callbacks, experiment trackers (WandB, TensorBoard),
file loggers (CSV, JSONL), early stopping, checkpointing, and composite callback execution.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from .base import BaseFactory
from .registry import Registry

logger = logging.getLogger(__name__)

# Import existing trainer callbacks with high-resilience fallback handling
try:
    from optimization_core.trainers.callbacks import (
        PrintLogger,
        TensorBoardLogger,
        WandbLogger,
    )
except (ImportError, ModuleNotFoundError):
    try:
        from ..trainers.callbacks import (
            PrintLogger,
            TensorBoardLogger,
            WandbLogger,
        )
    except (ImportError, ModuleNotFoundError):
        try:
            from trainers.callbacks import (
                PrintLogger,
                TensorBoardLogger,
                WandbLogger,
            )
        except (ImportError, ModuleNotFoundError):

            class PrintLogger:  # type: ignore
                """Fallback stdout logger."""

                def log(self, metrics: Dict[str, Any], step: Optional[int] = None) -> None:
                    step_str = f"[Step {step}] " if step is not None else ""
                    m_str = ", ".join(
                        f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}"
                        for k, v in metrics.items()
                    )
                    print(f"{step_str}{m_str}")

            class WandbLogger:  # type: ignore
                def __init__(self, project: str = "truthgpt", run_name: Optional[str] = None, **kwargs: Any):
                    self.project = project
                    self.run_name = run_name

                def log(self, metrics: Dict[str, Any], step: Optional[int] = None) -> None:
                    pass

            class TensorBoardLogger:  # type: ignore
                def __init__(self, log_dir: str = "runs", **kwargs: Any):
                    self.log_dir = log_dir

                def log(self, metrics: Dict[str, Any], step: Optional[int] = None) -> None:
                    pass


CALLBACKS = Registry(name="CallbacksRegistry")


@dataclass
class CallbackConfig:
    """Configuration specification for callbacks and experiment logging."""

    name: str = "print"
    log_dir: Optional[str] = "logs"
    project: Optional[str] = "truthgpt"
    run_name: Optional[str] = None
    extra_kwargs: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate configuration properties."""
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "log_dir": self.log_dir,
            "project": self.project,
            "run_name": self.run_name,
            "extra_kwargs": self.extra_kwargs,
        }


class CompositeCallback:
    """Composite callback executor with exception isolation delegating events to sub-callbacks."""

    def __init__(self, callbacks: Optional[List[Any]] = None, loggers: Optional[List[Any]] = None) -> None:
        raw_list = callbacks or loggers or []
        self.callbacks = [c for c in raw_list if c is not None]

    def _safe_dispatch(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        for cb in self.callbacks:
            if hasattr(cb, event_name):
                try:
                    getattr(cb, event_name)(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error executing callback '{type(cb).__name__}.{event_name}': {e}", exc_info=True)

    def on_train_begin(self, logs: Optional[Dict[str, Any]] = None) -> None:
        self._safe_dispatch("on_train_begin", logs)

    def on_train_end(self, logs: Optional[Dict[str, Any]] = None) -> None:
        self._safe_dispatch("on_train_end", logs)

    def on_epoch_begin(self, epoch: int, logs: Optional[Dict[str, Any]] = None) -> None:
        self._safe_dispatch("on_epoch_begin", epoch, logs)

    def on_epoch_end(self, epoch: int, logs: Optional[Dict[str, Any]] = None) -> None:
        self._safe_dispatch("on_epoch_end", epoch, logs)

    def on_step_end(self, step: int, logs: Optional[Dict[str, Any]] = None) -> None:
        for cb in self.callbacks:
            if hasattr(cb, "on_step_end"):
                try:
                    cb.on_step_end(step, logs)
                except Exception as e:
                    logger.error(f"Error in on_step_end of {type(cb).__name__}: {e}")
            elif hasattr(cb, "log") and logs:
                try:
                    cb.log(logs, step=step)
                except Exception as e:
                    logger.error(f"Error in log of {type(cb).__name__}: {e}")

    def log(self, metrics: Dict[str, Any], step: Optional[int] = None) -> None:
        for cb in self.callbacks:
            if hasattr(cb, "log"):
                try:
                    cb.log(metrics, step=step)
                except Exception as e:
                    logger.error(f"Error in log of {type(cb).__name__}: {e}")


class CSVLoggerCallback:
    """Callback for logging metrics to CSV file."""

    def __init__(self, filename: str = "metrics.csv", filepath: Optional[str] = None):
        self.filename = filepath or filename
        self.initialized = False
        os.makedirs(os.path.dirname(self.filename) or ".", exist_ok=True)

    def log(self, metrics: Dict[str, Any], step: Optional[int] = None) -> None:
        import csv

        row = {"step": step, **metrics} if step is not None else metrics
        fieldnames = list(row.keys())

        file_exists = os.path.exists(self.filename)
        with open(self.filename, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists or not self.initialized:
                writer.writeheader()
                self.initialized = True
            writer.writerow(row)


class JSONLoggerCallback:
    """Callback for logging metrics to JSON Lines file."""

    def __init__(self, filename: str = "metrics.jsonl", filepath: Optional[str] = None):
        self.filename = filepath or filename
        os.makedirs(os.path.dirname(self.filename) or ".", exist_ok=True)

    def log(self, metrics: Dict[str, Any], step: Optional[int] = None) -> None:
        record = {"timestamp": time.time(), "step": step, "metrics": metrics}
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")


class EarlyStoppingCallback:
    """Early stopping callback on validation loss stagnation."""

    def __init__(self, monitor: str = "val_loss", patience: int = 5, min_delta: float = 1e-4):
        self.monitor = monitor
        self.patience = patience
        self.min_delta = min_delta
        self.best_score: Optional[float] = None
        self.counter = 0
        self.should_stop = False

    def on_epoch_end(self, epoch: int, logs: Optional[Dict[str, Any]] = None) -> None:
        if not logs or self.monitor not in logs:
            return
        score = logs[self.monitor]
        if self.best_score is None or score < self.best_score - self.min_delta:
            self.best_score = score
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.should_stop = True
                logger.info(f"Early stopping triggered at epoch {epoch}.")


# Convenient class aliases
CsvLogger = CSVLoggerCallback
JsonlLogger = JSONLoggerCallback
CompositeLogger = CompositeCallback


@CALLBACKS.register(
    "print",
    priority=100,
    aliases=["stdout", "console"],
    description="Build standard stdout logger.",
    tags=["print", "stdout", "console"],
)
def build_print(*args: Any, **kwargs: Any) -> PrintLogger:
    """Build standard stdout logger."""
    return PrintLogger()


@CALLBACKS.register(
    "wandb",
    priority=90,
    aliases=["weights_and_biases"],
    description="Build Weights & Biases logger.",
    tags=["wandb", "cloud", "experiment_tracking"],
)
def build_wandb(
    project: Optional[str] = None, run_name: Optional[str] = None, **kwargs: Any
) -> WandbLogger:
    """Build a Weights & Biases logger."""
    return WandbLogger(project=project or "truthgpt", run_name=run_name, **kwargs)


@CALLBACKS.register(
    "tensorboard",
    priority=80,
    aliases=["tb"],
    description="Build TensorBoard logger.",
    tags=["tensorboard", "plots"],
)
def build_tensorboard(log_dir: str = "runs", **kwargs: Any) -> TensorBoardLogger:
    """Build a TensorBoard logger."""
    return TensorBoardLogger(log_dir=log_dir, **kwargs)


@CALLBACKS.register(
    "csv",
    priority=70,
    aliases=["csv_logger"],
    description="Build CSV metrics file logger.",
    tags=["csv", "file", "logger"],
)
def build_csv(filename: str = "metrics.csv", filepath: Optional[str] = None, **kwargs: Any) -> CSVLoggerCallback:
    """Build CSV file logger."""
    return CSVLoggerCallback(filename=filename, filepath=filepath)


@CALLBACKS.register(
    "jsonl",
    priority=60,
    aliases=["json_logger"],
    description="Build JSON Lines metrics logger.",
    tags=["jsonl", "file", "logger"],
)
def build_jsonl(filename: str = "metrics.jsonl", filepath: Optional[str] = None, **kwargs: Any) -> JSONLoggerCallback:
    """Build JSON Lines file logger."""
    return JSONLoggerCallback(filename=filename, filepath=filepath)


@CALLBACKS.register(
    "early_stopping",
    priority=50,
    aliases=["early_stop"],
    description="Build EarlyStopping callback.",
    tags=["early_stopping", "control"],
)
def build_early_stopping(
    monitor: str = "val_loss", patience: int = 5, min_delta: float = 1e-4, **kwargs: Any
) -> EarlyStoppingCallback:
    """Build EarlyStopping callback."""
    return EarlyStoppingCallback(monitor=monitor, patience=patience, min_delta=min_delta)


@CALLBACKS.register(
    "composite",
    priority=40,
    aliases=["multi_callback"],
    description="Build CompositeLogger.",
    tags=["composite", "orchestration"],
)
def build_composite(
    *args: Any,
    callback_list: Optional[List[Union[str, Dict[str, Any], Any]]] = None,
    loggers: Optional[List[Any]] = None,
    callbacks: Optional[List[Any]] = None,
    **kwargs: Any,
) -> CompositeLogger:
    """Construct a CompositeLogger from a list of callback names, dicts, or objects."""
    raw_list = []
    if args:
        if len(args) == 1 and isinstance(args[0], (list, tuple)):
            raw_list = list(args[0])
        else:
            raw_list = list(args)
    elif callback_list is not None:
        raw_list = callback_list
    elif loggers is not None:
        raw_list = loggers
    elif callbacks is not None:
        raw_list = callbacks

    built_callbacks = []
    for cb in raw_list:
        if isinstance(cb, str):
            built_callbacks.append(CALLBACKS.build(cb))
        elif isinstance(cb, dict) and "name" in cb:
            cb_copy = dict(cb)
            cb_name = cb_copy.pop("name")
            built_callbacks.append(CALLBACKS.build(cb_name, **cb_copy))
        else:
            built_callbacks.append(cb)
    return CompositeLogger(built_callbacks)


build_composite_callback = build_composite


class CallbackFactory(BaseFactory[Any]):
    """Manager class providing a unified factory interface for callbacks and loggers."""

    def __init__(self, registry: Registry = CALLBACKS) -> None:
        super().__init__(name="CallbackFactory")
        self.registry = registry

    def build(self, name: str, *args: Any, **kwargs: Any) -> Any:
        return self.registry.build(name, *args, **kwargs)

    def create_callback(
        self, config: Union[str, CallbackConfig, Dict[str, Any]] = "print", **kwargs: Any
    ) -> Any:
        if isinstance(config, CallbackConfig):
            config.validate()
            cb_name = config.name
            cb_kwargs = {
                "log_dir": config.log_dir,
                "project": config.project,
                "run_name": config.run_name,
                **config.extra_kwargs,
                **kwargs,
            }
        elif isinstance(config, dict):
            cb_name = config.get("name", "print")
            cb_kwargs = {**config, **kwargs}
        else:
            cb_name = str(config)
            cb_kwargs = kwargs

        return self.build(cb_name, **cb_kwargs)


__all__ = [
    "CALLBACKS",
    "CallbackConfig",
    "CallbackFactory",
    "PrintLogger",
    "WandbLogger",
    "TensorBoardLogger",
    "CSVLoggerCallback",
    "JSONLoggerCallback",
    "EarlyStoppingCallback",
    "CsvLogger",
    "JsonlLogger",
    "CompositeLogger",
    "CompositeCallback",
    "build_print",
    "build_wandb",
    "build_tensorboard",
    "build_csv",
    "build_jsonl",
    "build_early_stopping",
    "build_composite",
    "build_composite_callback",
]
