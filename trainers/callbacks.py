"""
Enhanced callback system for training monitoring, logging, early stopping, and metric tracking.

Provides expandable lifecycle hooks, exception insulation, and pre-built loggers/monitors.
"""
import os
import csv
import logging
from typing import Any, Dict, Optional, List
import torch

from .interfaces import BaseCallback
from .exceptions import CallbackError, CallbackExecutionError

logger = logging.getLogger(__name__)


class Callback(BaseCallback):
    """Base class for all training event callbacks with default no-op lifecycle hooks."""

    def on_train_begin(self, state: Dict[str, Any]) -> None:
        pass

    def on_train_end(self, state: Dict[str, Any]) -> None:
        pass

    def on_epoch_begin(self, epoch: int, state: Dict[str, Any]) -> None:
        pass

    def on_epoch_end(self, epoch: int, state: Dict[str, Any]) -> None:
        pass

    def on_step_begin(self, step: int, state: Dict[str, Any]) -> None:
        pass

    def on_step_end(self, step: int, state: Dict[str, Any]) -> None:
        pass

    def on_before_optimizer_step(self, state: Dict[str, Any]) -> None:
        pass

    def on_log(self, state: Dict[str, Any]) -> None:
        pass

    def on_eval(self, state: Dict[str, Any]) -> None:
        pass

    def on_save(self, state: Dict[str, Any]) -> None:
        pass


class PrintLogger(Callback):
    """Console print logger for formatting step and evaluation statistics."""

    def on_log(self, state: Dict[str, Any]) -> None:
        step = state.get("step", state.get("global_step", 0))
        loss = state.get("loss")
        lr = state.get("learning_rate")
        tps = state.get("tokens_per_sec", 0)

        msg_parts = [f"step={step}"]
        if loss is not None:
            msg_parts.append(f"loss={loss:.4f}")
        if lr is not None:
            msg_parts.append(f"lr={lr:.2e}")
        if tps > 0:
            msg_parts.append(f"tokens/s={tps:.0f}")

        print(f"[train] {' '.join(msg_parts)}")

    def on_eval(self, state: Dict[str, Any]) -> None:
        step = state.get("step", state.get("global_step", 0))
        val_loss = state.get("val_loss")
        ppl = state.get("perplexity")
        improved = state.get("improved", False)

        msg_parts = [f"step={step}"]
        if val_loss is not None:
            msg_parts.append(f"val_loss={val_loss:.4f}")
        if ppl is not None:
            msg_parts.append(f"ppl={ppl:.2f}")
        if improved:
            msg_parts.append("✨ improved")

        print(f"[eval] {' '.join(msg_parts)}")

    def on_save(self, state: Dict[str, Any]) -> None:
        path = state.get("path", state.get("checkpoint_dir", "unknown"))
        print(f"[save] checkpoint saved -> {path}")


class EarlyStoppingCallback(Callback):
    """Monitors validation loss and signals early stopping when patience is exceeded."""

    def __init__(self, patience: int = 3, min_delta: float = 1e-4, monitor: str = "val_loss"):
        self.patience = patience
        self.min_delta = min_delta
        self.monitor = monitor
        self.best_score: Optional[float] = None
        self.counter: int = 0
        self.should_stop: bool = False

    def on_eval(self, state: Dict[str, Any]) -> None:
        current = state.get(self.monitor, state.get("val_loss"))
        if current is None:
            return

        if self.best_score is None:
            self.best_score = current
        elif current < self.best_score - self.min_delta:
            self.best_score = current
            self.counter = 0
        else:
            self.counter += 1
            logger.info(f"EarlyStopping counter: {self.counter}/{self.patience}")
            if self.counter >= self.patience:
                self.should_stop = True
                state["should_stop"] = True
                logger.info("Early stopping triggered by EarlyStoppingCallback.")


class LearningRateMonitor(Callback):
    """Logs learning rate changes across steps."""

    def __init__(self):
        self.lr_history: List[float] = []

    def on_log(self, state: Dict[str, Any]) -> None:
        lr = state.get("learning_rate")
        if lr is not None:
            self.lr_history.append(lr)


class GradNormLogger(Callback):
    """Logs parameter gradient norm metrics."""

    def on_before_optimizer_step(self, state: Dict[str, Any]) -> None:
        grad_norm = state.get("grad_norm")
        if grad_norm is not None:
            logger.debug(f"[GradNormLogger] step={state.get('global_step', 0)} norm={grad_norm:.4f}")


class MemoryTrackerCallback(Callback):
    """Tracks and logs CUDA memory utilization."""

    def on_step_end(self, step: int, state: Dict[str, Any]) -> None:
        if torch.cuda.is_available():
            mem_allocated = torch.cuda.memory_allocated() / (1024 ** 2)
            mem_reserved = torch.cuda.memory_reserved() / (1024 ** 2)
            state["cuda_mem_allocated_mb"] = mem_allocated
            state["cuda_mem_reserved_mb"] = mem_reserved


class CSVLogger(Callback):
    """Logs metrics directly into a structured CSV file."""

    def __init__(self, filename: str = "training_metrics.csv"):
        self.filename = filename
        self._file_initialized = False

    def _init_file(self, fieldnames: List[str]) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.filename)), exist_ok=True)
        with open(self.filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        self._file_initialized = True

    def on_log(self, state: Dict[str, Any]) -> None:
        try:
            row = {k: v for k, v in state.items() if isinstance(v, (int, float, str, bool))}
            if not self._file_initialized:
                self._init_file(list(row.keys()))
            with open(self.filename, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(row.keys()))
                writer.writerow(row)
        except Exception as e:
            logger.debug(f"CSVLogger error: {e}")


class WandbLogger(Callback):
    """Weights & Biases logging integration."""

    def __init__(
        self,
        project: Optional[str] = None,
        run_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[list] = None,
    ) -> None:
        self._wandb = None
        self._enabled = False

        try:
            import wandb
            self._wandb = wandb

            if not wandb.run:
                wandb.init(
                    project=project or "truthgpt",
                    name=run_name,
                    config=config or {},
                    tags=tags or [],
                    reinit=False,
                )
            elif config:
                wandb.config.update(config)

            self._enabled = True
            logger.info(f"W&B initialized: project={project}, run={run_name}")
        except ImportError:
            logger.warning("wandb not installed. Continuing without W&B logging.")
        except Exception as e:
            logger.error(f"Failed to initialize W&B: {e}", exc_info=True)

    def on_train_begin(self, state: Dict[str, Any]) -> None:
        if not self._enabled or self._wandb is None:
            return
        try:
            if torch.cuda.is_available():
                self._wandb.config.update({
                    "gpu_name": torch.cuda.get_device_name(0),
                    "gpu_count": torch.cuda.device_count(),
                })
            self._wandb.config.update({"pytorch_version": torch.__version__})
        except Exception as e:
            logger.debug(f"Error logging system info to W&B: {e}")

    def on_log(self, state: Dict[str, Any]) -> None:
        if not self._enabled or self._wandb is None:
            return
        try:
            metrics = {
                "train/loss": state.get("loss"),
                "train/learning_rate": state.get("learning_rate"),
                "train/tokens_per_sec": state.get("tokens_per_sec"),
            }
            metrics = {k: v for k, v in metrics.items() if v is not None}
            if metrics:
                step = state.get("step", state.get("global_step", 0))
                self._wandb.log(metrics, step=step)
        except Exception as e:
            logger.debug(f"Error logging to W&B: {e}")

    def on_eval(self, state: Dict[str, Any]) -> None:
        if not self._enabled or self._wandb is None:
            return
        try:
            metrics = {
                "eval/val_loss": state.get("val_loss"),
                "eval/perplexity": state.get("perplexity"),
            }
            metrics = {k: v for k, v in metrics.items() if v is not None}
            if metrics:
                step = state.get("step", state.get("global_step", 0))
                self._wandb.log(metrics, step=step)
        except Exception as e:
            logger.debug(f"Error logging eval to W&B: {e}")

    def on_train_end(self, state: Dict[str, Any]) -> None:
        if not self._enabled or self._wandb is None:
            return
        try:
            if state:
                self._wandb.log(state)
        except Exception as e:
            logger.debug(f"Error finishing W&B run: {e}")


class TensorBoardLogger(Callback):
    """TensorBoard SummaryWriter logging integration."""

    def __init__(self, log_dir: Optional[str] = None) -> None:
        self._writer = None
        self._enabled = False
        self._log_dir = log_dir or "runs"

        try:
            from torch.utils.tensorboard import SummaryWriter
            self._writer = SummaryWriter(log_dir=self._log_dir)
            self._enabled = True
            logger.info(f"TensorBoard initialized: log_dir={self._log_dir}")
        except ImportError:
            logger.warning("TensorBoard not installed. Continuing without TensorBoard logging.")
        except Exception as e:
            logger.error(f"Failed to initialize TensorBoard: {e}", exc_info=True)

    def on_log(self, state: Dict[str, Any]) -> None:
        if not self._enabled or self._writer is None:
            return
        try:
            step = state.get("step", state.get("global_step", 0))
            if "loss" in state and state["loss"] is not None:
                self._writer.add_scalar("train/loss", state["loss"], global_step=step)
            if "learning_rate" in state and state["learning_rate"] is not None:
                self._writer.add_scalar("train/learning_rate", state["learning_rate"], global_step=step)
            if "tokens_per_sec" in state and state["tokens_per_sec"] is not None:
                self._writer.add_scalar("train/tokens_per_sec", state["tokens_per_sec"], global_step=step)

            if step % 10 == 0:
                self._writer.flush()
        except Exception as e:
            logger.debug(f"Error logging to TensorBoard: {e}")

    def on_eval(self, state: Dict[str, Any]) -> None:
        if not self._enabled or self._writer is None:
            return
        try:
            step = state.get("step", state.get("global_step", 0))
            if "val_loss" in state and state["val_loss"] is not None:
                self._writer.add_scalar("eval/val_loss", state["val_loss"], global_step=step)
            if "perplexity" in state and state["perplexity"] is not None:
                self._writer.add_scalar("eval/perplexity", state["perplexity"], global_step=step)
            self._writer.flush()
        except Exception as e:
            logger.debug(f"Error logging eval to TensorBoard: {e}")

    def on_train_end(self, state: Dict[str, Any]) -> None:
        if not self._enabled or self._writer is None:
            return
        try:
            self._writer.flush()
            self._writer.close()
        except Exception as e:
            logger.debug(f"Error closing TensorBoard writer: {e}")


class CallbackHandler:
    """Manages callback dispatching across all lifecycle hooks with exception insulation."""

    def __init__(self, callbacks: Optional[list] = None) -> None:
        self.callbacks: List[Callback] = callbacks or []

    def add_callback(self, callback: Callback) -> None:
        self.callbacks.append(callback)

    def _dispatch(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        for cb in self.callbacks:
            try:
                method = getattr(cb, method_name, None)
                if method and callable(method):
                    try:
                        method(*args, **kwargs)
                    except TypeError:
                        # Fallback for signature mismatches (e.g. (step, state) vs (state,))
                        if len(args) == 2 and isinstance(args[0], int) and isinstance(args[1], dict):
                            try:
                                method(args[1])
                            except TypeError:
                                pass
                        elif len(args) == 1 and isinstance(args[0], dict):
                            s = args[0]
                            idx_key = "epoch" if "epoch" in method_name else "step"
                            idx = s.get(idx_key, s.get("global_step", 0))
                            try:
                                method(idx, s)
                            except TypeError:
                                pass
            except Exception as e:
                logger.debug(f"Callback dispatch error ({type(cb).__name__}.{method_name}): {e}")

    def on_train_begin(self, state: Dict[str, Any]) -> None:
        self._dispatch("on_train_begin", state)

    def on_train_end(self, state: Dict[str, Any]) -> None:
        self._dispatch("on_train_end", state)

    def on_epoch_begin(self, epoch: Union[int, Dict[str, Any]] = 0, state: Optional[Dict[str, Any]] = None) -> None:
        if isinstance(epoch, dict):
            state = epoch
            epoch = state.get("epoch", 0)
        state = state or {}
        self._dispatch("on_epoch_begin", epoch, state)

    def on_epoch_end(self, epoch: Union[int, Dict[str, Any]] = 0, state: Optional[Dict[str, Any]] = None) -> None:
        if isinstance(epoch, dict):
            state = epoch
            epoch = state.get("epoch", 0)
        state = state or {}
        self._dispatch("on_epoch_end", epoch, state)

    def on_step_begin(self, step: Union[int, Dict[str, Any]] = 0, state: Optional[Dict[str, Any]] = None) -> None:
        if isinstance(step, dict):
            state = step
            step = state.get("step", 0)
        state = state or {}
        self._dispatch("on_step_begin", step, state)

    def on_step_end(self, step: Union[int, Dict[str, Any]] = 0, state: Optional[Dict[str, Any]] = None) -> None:
        if isinstance(step, dict):
            state = step
            step = state.get("step", 0)
        state = state or {}
        self._dispatch("on_step_end", step, state)

    def on_before_optimizer_step(self, state: Dict[str, Any]) -> None:
        self._dispatch("on_before_optimizer_step", state)

    def on_log(self, state: Dict[str, Any]) -> None:
        self._dispatch("on_log", state)

    def on_eval(self, state: Dict[str, Any]) -> None:
        self._dispatch("on_eval", state)

    def on_save(self, state: Dict[str, Any]) -> None:
        self._dispatch("on_save", state)


__all__ = [
    "Callback",
    "PrintLogger",
    "EarlyStoppingCallback",
    "LearningRateMonitor",
    "GradNormLogger",
    "MemoryTrackerCallback",
    "CSVLogger",
    "WandbLogger",
    "TensorBoardLogger",
    "CallbackHandler",
]
