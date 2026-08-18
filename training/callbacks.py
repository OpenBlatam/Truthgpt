"""
Training Lifecycle Callbacks and Handlers
=========================================
Event-driven callback system providing hooks into all stages of the training lifecycle.
Includes early stopping, checkpointing, LR monitoring, metrics logging, gradient norm tracking,
and aggregate callback execution handlers.
"""

from __future__ import annotations

import logging
import math
import time
from typing import Any, Callable, Dict, List, Optional, Union
import torch

from .exceptions import EarlyStoppingTriggered
from .interfaces import BaseCallback
from .types import EarlyStoppingConfig

logger = logging.getLogger(__name__)


class Callback(BaseCallback):
    """Base concrete implementation of callback with no-op hooks."""
    pass


class EarlyStoppingCallback(Callback):
    """
    Early stopping callback that halts training when monitored metric ceases to improve.
    """

    def __init__(
        self,
        patience: int = 5,
        min_delta: float = 0.0,
        mode: str = "min",
        metric_name: str = "loss",
        restore_best_weights: bool = True,
    ) -> None:
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode.lower()
        self.metric_name = metric_name
        self.restore_best_weights = restore_best_weights

        self.best_metric: Optional[float] = None
        self.bad_epochs: int = 0
        self.best_weights: Optional[Dict[str, torch.Tensor]] = None
        self.stopped_epoch: Optional[int] = None

    def on_eval(self, eval_metrics: Dict[str, Any], state: Dict[str, Any]) -> None:
        """Inspect evaluation metric after validation phase."""
        if self.metric_name not in eval_metrics:
            return

        current_val = float(eval_metrics[self.metric_name])
        is_better = False

        if self.best_metric is None:
            is_better = True
        elif self.mode == "min":
            is_better = current_val < (self.best_metric - self.min_delta)
        elif self.mode == "max":
            is_better = current_val > (self.best_metric + self.min_delta)

        if is_better:
            self.best_metric = current_val
            self.bad_epochs = 0
            model = state.get("model")
            if self.restore_best_weights and model is not None:
                self.best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        else:
            self.bad_epochs += 1
            if self.bad_epochs >= self.patience:
                self.stopped_epoch = state.get("epoch", 0)
                logger.info(
                    f"Early stopping triggered at epoch {self.stopped_epoch}: "
                    f"metric '{self.metric_name}' did not improve for {self.bad_epochs} epochs "
                    f"(best: {self.best_metric:.6f}, current: {current_val:.6f})."
                )
                if self.restore_best_weights and self.best_weights is not None and "model" in state:
                    state["model"].load_state_dict(self.best_weights)
                    logger.info("Restored model weights from best checkpoint.")
                state["should_stop"] = True
                raise EarlyStoppingTriggered(
                    message=f"Early stopping triggered at epoch {self.stopped_epoch}",
                    patience=self.patience,
                    best_metric=self.best_metric,
                    current_metric=current_val,
                )


class ModelCheckpointCallback(Callback):
    """
    Automated checkpoint callback triggered on evaluation or epoch end.
    """

    def __init__(
        self,
        checkpoint_manager: Any,
        metric_name: str = "loss",
        mode: str = "min",
        save_best_only: bool = False,
        save_interval_epochs: int = 1,
    ) -> None:
        self.checkpoint_manager = checkpoint_manager
        self.metric_name = metric_name
        self.mode = mode.lower()
        self.save_best_only = save_best_only
        self.save_interval_epochs = save_interval_epochs
        self.best_metric: Optional[float] = None

    def on_eval(self, eval_metrics: Dict[str, Any], state: Dict[str, Any]) -> None:
        """Save best checkpoint if eval metrics improve."""
        epoch = state.get("epoch", 0)
        step = state.get("step", 0)
        if self.metric_name not in eval_metrics:
            return

        current_val = float(eval_metrics[self.metric_name])
        is_best = False

        if self.best_metric is None:
            is_best = True
        elif self.mode == "min" and current_val < self.best_metric:
            is_best = True
        elif self.mode == "max" and current_val > self.best_metric:
            is_best = True

        if is_best:
            self.best_metric = current_val
            saved_path = self.checkpoint_manager.save(
                epoch=epoch,
                step=step,
                metrics=eval_metrics,
                is_best=True,
                model=state.get("model"),
                optimizer=state.get("optimizer"),
                scheduler=state.get("scheduler"),
                scaler=state.get("scaler"),
            )
            logger.info(f"Saved new best checkpoint at {saved_path}")
        elif not self.save_best_only and epoch % self.save_interval_epochs == 0:
            self.checkpoint_manager.save(
                epoch=epoch,
                step=step,
                metrics=eval_metrics,
                is_best=False,
                model=state.get("model"),
                optimizer=state.get("optimizer"),
                scheduler=state.get("scheduler"),
                scaler=state.get("scaler"),
            )


class LRMonitorCallback(Callback):
    """
    Tracks and logs learning rate across optimizer parameter groups.
    """

    def __init__(self, log_every_steps: int = 1) -> None:
        self.log_every_steps = log_every_steps
        self.lr_history: List[Dict[str, Any]] = []

    def on_step_end(self, step: int, state: Dict[str, Any]) -> None:
        if step % self.log_every_steps != 0:
            return

        optimizer = state.get("optimizer")
        if optimizer is None:
            return

        lrs = [param_group.get("lr", 0.0) for param_group in optimizer.param_groups]
        record = {"step": step, "learning_rates": lrs, "lr": lrs[0] if lrs else 0.0}
        self.lr_history.append(record)
        state["current_lr"] = record["lr"]


class MetricsLoggerCallback(Callback):
    """
    Formats and logs training/eval metrics to standard logger or tracker.
    """

    def __init__(self, log_every_steps: int = 10, tracker: Optional[Any] = None) -> None:
        self.log_every_steps = log_every_steps
        self.tracker = tracker

    def on_step_end(self, step: int, state: Dict[str, Any]) -> None:
        if step % self.log_every_steps == 0:
            metrics = state.get("step_metrics", {})
            lr = state.get("current_lr")
            loss = metrics.get("loss")
            lr_str = f" | lr: {lr:.2e}" if lr is not None else ""
            loss_str = f" | loss: {loss:.4f}" if loss is not None else ""
            logger.info(f"[Step {step:06d}]{loss_str}{lr_str}")
            if self.tracker is not None:
                self.tracker.log_metrics(metrics, step=step)

    def on_eval(self, eval_metrics: Dict[str, Any], state: Dict[str, Any]) -> None:
        epoch = state.get("epoch", 0)
        formatted = ", ".join(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}" for k, v in eval_metrics.items())
        logger.info(f"[Validation Epoch {epoch:03d}] {formatted}")
        if self.tracker is not None:
            self.tracker.log_metrics({f"eval/{k}": v for k, v in eval_metrics.items()}, step=state.get("step", 0))


class GradientNormCallback(Callback):
    """
    Monitors and records gradient norms across model parameters.
    """

    def __init__(self, norm_type: float = 2.0) -> None:
        self.norm_type = norm_type
        self.grad_norms: List[float] = []

    def on_step_end(self, step: int, state: Dict[str, Any]) -> None:
        model = state.get("model")
        if model is None:
            return

        total_norm = 0.0
        for p in model.parameters():
            if p.grad is not None:
                param_norm = p.grad.detach().data.norm(self.norm_type)
                total_norm += param_norm.item() ** self.norm_type
        total_norm = total_norm ** (1.0 / self.norm_type)
        self.grad_norms.append(total_norm)
        state["grad_norm"] = total_norm


class ProgressCallback(Callback):
    """
    Tracks elapsed training time and estimated throughput.
    """

    def __init__(self) -> None:
        self.start_time: float = 0.0
        self.step_count: int = 0

    def on_train_begin(self, state: Dict[str, Any]) -> None:
        self.start_time = time.perf_counter()
        self.step_count = 0

    def on_step_end(self, step: int, state: Dict[str, Any]) -> None:
        self.step_count += 1

    def on_epoch_end(self, epoch: int, state: Dict[str, Any]) -> None:
        elapsed = time.perf_counter() - self.start_time
        steps_per_sec = self.step_count / max(1.0, elapsed)
        logger.info(f"[Epoch {epoch:03d} Completed] Elapsed: {elapsed:.2f}s | Steps/sec: {steps_per_sec:.2f}")


class CallbackHandler:
    """
    Manages and safely broadcasts lifecycle events to a collection of callbacks.
    """

    def __init__(self, callbacks: Optional[List[BaseCallback]] = None) -> None:
        self.callbacks: List[BaseCallback] = list(callbacks or [])

    def add_callback(self, callback: BaseCallback) -> None:
        """Add a callback to the execution chain."""
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def remove_callback(self, callback_type: type) -> None:
        """Remove callbacks of a specific type."""
        self.callbacks = [cb for cb in self.callbacks if not isinstance(cb, callback_type)]

    def on_train_begin(self, state: Dict[str, Any]) -> None:
        for cb in self.callbacks:
            cb.on_train_begin(state)

    def on_train_end(self, state: Dict[str, Any]) -> None:
        for cb in self.callbacks:
            cb.on_train_end(state)

    def on_epoch_begin(self, epoch: int, state: Dict[str, Any]) -> None:
        for cb in self.callbacks:
            cb.on_epoch_begin(epoch, state)

    def on_epoch_end(self, epoch: int, state: Dict[str, Any]) -> None:
        for cb in self.callbacks:
            cb.on_epoch_end(epoch, state)

    def on_step_begin(self, step: int, state: Dict[str, Any]) -> None:
        for cb in self.callbacks:
            cb.on_step_begin(step, state)

    def on_step_end(self, step: int, state: Dict[str, Any]) -> None:
        for cb in self.callbacks:
            cb.on_step_end(step, state)

    def on_log(self, metrics: Dict[str, Any], state: Dict[str, Any]) -> None:
        for cb in self.callbacks:
            cb.on_log(metrics, state)

    def on_eval(self, eval_metrics: Dict[str, Any], state: Dict[str, Any]) -> None:
        for cb in self.callbacks:
            cb.on_eval(eval_metrics, state)

    def on_save(self, checkpoint_path: str, state: Dict[str, Any]) -> None:
        for cb in self.callbacks:
            cb.on_save(checkpoint_path, state)

    def on_exception(self, exception: Exception, state: Dict[str, Any]) -> None:
        for cb in self.callbacks:
            cb.on_exception(exception, state)
