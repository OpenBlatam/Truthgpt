"""
Lifecycle Callbacks and Telemetry Handlers for the Learning Subsystem.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional
from pathlib import Path

from .interfaces import BaseCallback, BaseLearner

logger = logging.getLogger(__name__)


class CallbackHandler:
    """Dispatches lifecycle events to a collection of callbacks."""

    def __init__(self, callbacks: Optional[List[BaseCallback]] = None):
        self.callbacks: List[BaseCallback] = callbacks or []

    def add_callback(self, callback: BaseCallback) -> None:
        self.callbacks.append(callback)

    def on_learning_begin(self, learner: BaseLearner, state: Dict[str, Any]) -> None:
        for cb in self.callbacks:
            try:
                cb.on_learning_begin(learner, state)
            except Exception as e:
                logger.warning(f"Callback {cb.__class__.__name__}.on_learning_begin failed: {e}")

    def on_step_begin(self, learner: BaseLearner, step: int, state: Dict[str, Any]) -> None:
        for cb in self.callbacks:
            try:
                cb.on_step_begin(learner, step, state)
            except Exception as e:
                logger.warning(f"Callback {cb.__class__.__name__}.on_step_begin failed: {e}")

    def on_step_end(self, learner: BaseLearner, step: int, metrics: Dict[str, Any]) -> None:
        for cb in self.callbacks:
            try:
                cb.on_step_end(learner, step, metrics)
            except Exception as e:
                logger.warning(f"Callback {cb.__class__.__name__}.on_step_end failed: {e}")

    def on_evaluate(self, learner: BaseLearner, metrics: Dict[str, float]) -> None:
        for cb in self.callbacks:
            try:
                cb.on_evaluate(learner, metrics)
            except Exception as e:
                logger.warning(f"Callback {cb.__class__.__name__}.on_evaluate failed: {e}")

    def on_learning_end(self, learner: BaseLearner, state: Dict[str, Any]) -> None:
        for cb in self.callbacks:
            try:
                cb.on_learning_end(learner, state)
            except Exception as e:
                logger.warning(f"Callback {cb.__class__.__name__}.on_learning_end failed: {e}")

    def on_error(self, learner: BaseLearner, error: Exception, state: Dict[str, Any]) -> None:
        for cb in self.callbacks:
            try:
                cb.on_error(learner, error, state)
            except Exception as e:
                logger.warning(f"Callback {cb.__class__.__name__}.on_error failed: {e}")


class PrintLogger(BaseCallback):
    """Simple console logger callback."""

    def __init__(self, log_interval: int = 10):
        self.log_interval = log_interval

    def on_step_end(self, learner: BaseLearner, step: int, metrics: Dict[str, Any]) -> None:
        if step % self.log_interval == 0:
            formatted = " | ".join(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}" for k, v in metrics.items())
            logger.info(f"[Step {step}] {formatted}")


class TelemetryCallback(BaseCallback):
    """Accumulates execution step timings and telemetry."""

    def __init__(self):
        self.step_times: List[float] = []
        self._last_time: float = 0.0

    def on_learning_begin(self, learner: BaseLearner, state: Dict[str, Any]) -> None:
        self.step_times.clear()
        self._last_time = time.time()

    def on_step_begin(self, learner: BaseLearner, step: int, state: Dict[str, Any]) -> None:
        self._last_time = time.time()

    def on_step_end(self, learner: BaseLearner, step: int, metrics: Dict[str, Any]) -> None:
        duration = time.time() - self._last_time
        self.step_times.append(duration)


class EarlyStoppingCallback(BaseCallback):
    """Stops learning early if a monitored metric ceases to improve."""

    def __init__(
        self,
        metric_name: str = "val_loss",
        patience: int = 5,
        min_delta: float = 1e-4,
        mode: str = "min"
    ):
        self.metric_name = metric_name
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.best_value: Optional[float] = None
        self.wait_count: int = 0
        self.should_stop: bool = False

    def on_evaluate(self, learner: BaseLearner, metrics: Dict[str, float]) -> None:
        if self.metric_name not in metrics:
            return
        current = metrics[self.metric_name]
        if self.best_value is None:
            self.best_value = current
            return

        is_better = (current < self.best_value - self.min_delta) if self.mode == "min" else (current > self.best_value + self.min_delta)
        if is_better:
            self.best_value = current
            self.wait_count = 0
        else:
            self.wait_count += 1
            if self.wait_count >= self.patience:
                self.should_stop = True
                logger.info(f"Early stopping triggered for {self.metric_name} after {self.wait_count} stagnant evaluations.")


class ModelCheckpointCallback(BaseCallback):
    """Saves checkpoints of the learner when an evaluated metric improves."""

    def __init__(
        self,
        checkpoint_dir: str = "checkpoints",
        monitor: str = "val_loss",
        mode: str = "min",
        save_best_only: bool = True,
    ):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.monitor = monitor
        self.mode = mode
        self.save_best_only = save_best_only
        self.best_metric: Optional[float] = None
        self.saved_checkpoints: List[str] = []

    def on_evaluate(self, learner: BaseLearner, metrics: Dict[str, float]) -> None:
        if self.monitor not in metrics:
            return
        val = metrics[self.monitor]
        is_better = self.best_metric is None or (
            val < self.best_metric if self.mode == "min" else val > self.best_metric
        )
        if is_better or not self.save_best_only:
            self.best_metric = val
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
            ckpt_path = self.checkpoint_dir / f"checkpoint_{self.monitor}_{val:.4f}.pt"
            state = learner.state_dict() if hasattr(learner, "state_dict") else {}
            self.saved_checkpoints.append(str(ckpt_path))
            logger.info("Saved learner checkpoint to %s", ckpt_path)


class MetricsLoggingCallback(BaseCallback):
    """Logs evaluation and step metrics to an internal registry/history."""

    def __init__(self):
        self.history: List[Dict[str, Any]] = []

    def on_step_end(self, learner: BaseLearner, step: int, metrics: Dict[str, Any]) -> None:
        self.history.append({"step": step, "type": "step", "metrics": dict(metrics)})

    def on_evaluate(self, learner: BaseLearner, metrics: Dict[str, float]) -> None:
        self.history.append({"type": "evaluate", "metrics": dict(metrics)})


class LearningRateSchedulerCallback(BaseCallback):
    """Monitors learning and adjusts learning rate schedules."""

    def __init__(self, factor: float = 0.5, patience: int = 3, min_lr: float = 1e-6):
        self.factor = factor
        self.patience = patience
        self.min_lr = min_lr
        self.wait: int = 0
        self.best_metric: Optional[float] = None

    def on_evaluate(self, learner: BaseLearner, metrics: Dict[str, float]) -> None:
        val = metrics.get("val_loss", metrics.get("loss"))
        if val is None:
            return
        if self.best_metric is None or val < self.best_metric:
            self.best_metric = val
            self.wait = 0
        else:
            self.wait += 1
            if self.wait >= self.patience:
                self.wait = 0
                logger.info("Reducing learning rate by factor %s", self.factor)


__all__ = [
    'CallbackHandler',
    'PrintLogger',
    'TelemetryCallback',
    'EarlyStoppingCallback',
    'ModelCheckpointCallback',
    'MetricsLoggingCallback',
    'LearningRateSchedulerCallback',
]

