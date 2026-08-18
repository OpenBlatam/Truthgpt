"""
Training Loop Module
====================
Separated from trainer for modularity and clean execution.
Handles forward pass, backward pass, gradient accumulation, gradient clipping,
mixed-precision training (AMP), learning rate extraction, callback execution,
and early stopping evaluation.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

try:
    from torch.amp import GradScaler, autocast
except ImportError:
    from torch.cuda.amp import GradScaler, autocast  # type: ignore

from .callbacks import CallbackHandler
from .exceptions import EarlyStoppingTriggered, TrainingConfigurationError, TrainingError
from .interfaces import BaseCallback, BaseTrainingLoop
from .types import EarlyStoppingConfig, PrecisionType, StepResult, TrainingLoopConfig

logger = logging.getLogger(__name__)


class TrainingLoop(BaseTrainingLoop):
    """
    Modular, high-performance PyTorch training loop implementation.
    Handles forward pass, backward pass, gradient accumulation, gradient norm/val clipping,
    automatic mixed-precision (AMP), learning rate extraction, and callback events.
    """

    def __init__(
        self,
        use_amp: bool = False,
        amp_dtype: Optional[Union[str, torch.dtype]] = None,
        max_grad_norm: float = 1.0,
        max_grad_val: Optional[float] = None,
        grad_accum_steps: int = 1,
        callbacks: Optional[List[BaseCallback]] = None,
        config: Optional[Union[Dict[str, Any], TrainingLoopConfig]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize TrainingLoop.

        Args:
            use_amp: Enable automatic mixed precision (AMP).
            amp_dtype: AMP torch.dtype or string ("fp16", "bf16").
            max_grad_norm: Maximum gradient norm for clipping (> 0).
            max_grad_val: Optional maximum absolute value for clipping.
            grad_accum_steps: Number of steps to accumulate gradients over (>= 1).
            callbacks: Optional list of lifecycle callbacks.
            config: Optional TrainingLoopConfig instance or dictionary.
        """
        if config is not None:
            if isinstance(config, TrainingLoopConfig):
                use_amp = config.use_amp
                amp_dtype = config.amp_dtype
                max_grad_norm = config.max_grad_norm
                max_grad_val = config.max_grad_val
                grad_accum_steps = config.grad_accum_steps
            elif isinstance(config, dict):
                use_amp = config.get("use_amp", use_amp)
                amp_dtype = config.get("amp_dtype", amp_dtype)
                max_grad_norm = config.get("max_grad_norm", max_grad_norm)
                max_grad_val = config.get("max_grad_val", max_grad_val)
                grad_accum_steps = config.get("grad_accum_steps", grad_accum_steps)

        if grad_accum_steps < 1:
            raise ValueError(f"grad_accum_steps must be at least 1, got {grad_accum_steps}")
        if max_grad_norm <= 0:
            raise ValueError(f"max_grad_norm must be positive, got {max_grad_norm}")

        self.use_amp: bool = use_amp
        if isinstance(amp_dtype, str):
            self.amp_dtype: Optional[torch.dtype] = PrecisionType.to_torch_dtype(amp_dtype)
        else:
            self.amp_dtype = amp_dtype

        self.max_grad_norm: float = max_grad_norm
        self.max_grad_val: Optional[float] = max_grad_val
        self.grad_accum_steps: int = grad_accum_steps

        # Callbacks
        self.callback_handler = CallbackHandler(callbacks or [])

        # Internal state tracking for early stopping
        self.best_metric: Optional[float] = None
        self.bad_epochs: int = 0
        self.total_steps: int = 0

    def add_callback(self, callback: BaseCallback) -> None:
        """Register an additional lifecycle callback."""
        self.callback_handler.add_callback(callback)

    def _get_autocast_context(self, model: Optional[nn.Module] = None) -> Any:
        """
        Obtain device-appropriate autocast context manager.
        """
        if not self.use_amp:
            return autocast("cpu", enabled=False)

        device_type = "cpu"
        if model is not None and list(model.parameters()):
            dev = next(model.parameters()).device
            if dev.type in ("cuda", "cpu", "xpu", "mps"):
                device_type = dev.type
        elif torch.cuda.is_available():
            device_type = "cuda"

        try:
            return autocast(device_type=device_type, dtype=self.amp_dtype, enabled=True)
        except TypeError:
            return autocast(enabled=True, dtype=self.amp_dtype)

    def _extract_loss(self, outputs: Any) -> torch.Tensor:
        """
        Extract scalar loss tensor cleanly from various model output types.
        """
        if hasattr(outputs, "loss") and getattr(outputs, "loss") is not None:
            raw_loss = getattr(outputs, "loss")
        elif isinstance(outputs, dict) and "loss" in outputs:
            raw_loss = outputs["loss"]
        elif isinstance(outputs, (tuple, list)) and len(outputs) > 0 and isinstance(outputs[0], torch.Tensor):
            raw_loss = outputs[0]
        elif isinstance(outputs, torch.Tensor):
            raw_loss = outputs
        else:
            raise TrainingError(f"Could not extract loss from model output of type {type(outputs)}")

        if isinstance(raw_loss, dict):
            raw_loss = raw_loss.get("loss", list(raw_loss.values())[0])

        if hasattr(raw_loss, "mean") and getattr(raw_loss, "dim", lambda: 0)() > 0:
            raw_loss = raw_loss.mean()

        return raw_loss

    def _clip_gradients(self, model: nn.Module) -> float:
        """
        Apply gradient norm and gradient value clipping to model parameters.
        Returns total gradient norm before clipping.
        """
        model_for_clipping = (
            model.module if isinstance(model, (nn.DataParallel, nn.parallel.DistributedDataParallel))
            else model
        )

        total_norm = 0.0
        if hasattr(model_for_clipping, "parameters"):
            params: List[nn.Parameter] = [p for p in model_for_clipping.parameters() if p.grad is not None]
            if not params:
                return 0.0

            if self.max_grad_norm > 0:
                total_norm = float(nn.utils.clip_grad_norm_(params, self.max_grad_norm))
            if self.max_grad_val is not None and self.max_grad_val > 0:
                nn.utils.clip_grad_value_(params, self.max_grad_val)

        return total_norm

    def train_step(
        self,
        model: nn.Module,
        batch: Union[Dict[str, torch.Tensor], torch.Tensor, Any],
        optimizer: torch.optim.Optimizer,
        scaler: GradScaler,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Perform a single training step including forward, backward, accumulation, and optimizer update.

        Args:
            model: PyTorch module.
            batch: Input batch.
            optimizer: Optimizer instance.
            scaler: GradScaler for mixed precision.
            **kwargs: Extra arguments (e.g. step index).

        Returns:
            Dictionary with step metrics ('loss', 'skipped', 'grad_norm').
        """
        step_start_time = time.perf_counter()
        try:
            with self._get_autocast_context(model):
                if isinstance(batch, dict):
                    outputs = model(**batch)
                elif isinstance(batch, (tuple, list)):
                    outputs = model(*batch)
                else:
                    outputs = model(batch)

                raw_loss = self._extract_loss(outputs)
                loss = raw_loss / self.grad_accum_steps

            # Check for non-finite loss
            if not torch.isfinite(loss):
                logger.warning(f"Non-finite loss encountered during training step: {loss.item()}")
                optimizer.zero_grad(set_to_none=True)
                return {"loss": float("inf"), "skipped": True, "grad_norm": 0.0}

            # Backward pass with gradient scaling
            scaler.scale(loss).backward()

            # Perform optimizer step on accumulation boundaries
            step = kwargs.get("step", 1)
            grad_norm = 0.0
            if step % self.grad_accum_steps == 0:
                scaler.unscale_(optimizer)
                grad_norm = self._clip_gradients(model)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)

            step_time = (time.perf_counter() - step_start_time) * 1000.0
            unscaled_loss_val = float((loss * self.grad_accum_steps).item())

            return {
                "loss": unscaled_loss_val,
                "skipped": False,
                "grad_norm": grad_norm,
                "step_time_ms": step_time,
            }
        except Exception as e:
            if isinstance(e, TrainingError):
                raise
            logger.error(f"Error during training step: {e}", exc_info=True)
            raise TrainingError(f"Training step failed: {e}") from e

    def train_epoch(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        optimizer: torch.optim.Optimizer,
        scheduler: Optional[Any] = None,
        scaler: Optional[GradScaler] = None,
        step_callback: Optional[Callable[..., Any]] = None,
        epoch_callback: Optional[Callable[..., Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Train model for one full epoch over train_loader dataset.
        """
        if scaler is None:
            try:
                scaler = GradScaler("cuda", enabled=self.use_amp)
            except Exception:
                scaler = GradScaler(enabled=self.use_amp)

        epoch_idx = kwargs.get("epoch", 1)
        state: Dict[str, Any] = {
            "model": model,
            "optimizer": optimizer,
            "scheduler": scheduler,
            "scaler": scaler,
            "epoch": epoch_idx,
            "should_stop": False,
        }

        self.callback_handler.on_epoch_begin(epoch_idx, state)

        model.train()
        total_loss = 0.0
        num_steps = 0
        start_time = time.perf_counter()

        for step, batch in enumerate(train_loader, start=1):
            self.total_steps += 1
            state["step"] = self.total_steps
            state["epoch_step"] = step

            self.callback_handler.on_step_begin(self.total_steps, state)

            try:
                step_metrics = self.train_step(
                    model=model,
                    batch=batch,
                    optimizer=optimizer,
                    scaler=scaler,
                    step=step,
                    **kwargs,
                )

                if step_metrics.get("skipped", False):
                    continue

                total_loss += step_metrics["loss"]
                num_steps += 1

                # Step learning rate scheduler if provided
                if scheduler is not None and step % self.grad_accum_steps == 0:
                    scheduler.step()

                # Determine active learning rate safely
                current_lr = None
                if scheduler is not None and hasattr(scheduler, "get_last_lr"):
                    try:
                        current_lr = scheduler.get_last_lr()[0]
                    except Exception:
                        current_lr = None
                elif optimizer is not None and len(optimizer.param_groups) > 0:
                    current_lr = optimizer.param_groups[0].get("lr")

                step_metrics["lr"] = current_lr
                state["step_metrics"] = step_metrics
                state["current_lr"] = current_lr

                self.callback_handler.on_step_end(self.total_steps, state)

                if step_callback:
                    step_callback(
                        step=step,
                        metrics=step_metrics,
                        learning_rate=current_lr,
                    )

            except Exception as e:
                self.callback_handler.on_exception(e, state)
                if isinstance(e, EarlyStoppingTriggered):
                    raise
                logger.error(f"Error in training step {step}: {e}", exc_info=True)
                optimizer.zero_grad(set_to_none=True)
                continue

        elapsed = time.perf_counter() - start_time
        avg_loss = total_loss / max(1, num_steps)

        epoch_result = {
            "epoch": epoch_idx,
            "loss": avg_loss,
            "num_steps": num_steps,
            "elapsed_time": elapsed,
            "steps_per_sec": num_steps / max(0.001, elapsed),
        }

        state["epoch_metrics"] = epoch_result
        self.callback_handler.on_epoch_end(epoch_idx, state)

        if epoch_callback:
            epoch_callback(metrics=epoch_result)

        return epoch_result

    def train(self, *args: Any, **kwargs: Any) -> Any:
        """Standard train execution for BaseTrainingLoop / BaseTrainer compliance."""
        model = kwargs.get("model")
        train_loader = kwargs.get("train_loader")
        optimizer = kwargs.get("optimizer")
        scheduler = kwargs.get("scheduler")
        scaler = kwargs.get("scaler")
        if model is not None and train_loader is not None and optimizer is not None:
            return self.train_epoch(
                model=model,
                train_loader=train_loader,
                optimizer=optimizer,
                scheduler=scheduler,
                scaler=scaler,
                **kwargs,
            )
        logger.warning("train() called without required arguments (model, train_loader, optimizer).")
        return None

    def evaluate(self, *args: Any, **kwargs: Any) -> Dict[str, float]:
        """Evaluate model performance for BaseTrainingLoop compliance."""
        model = kwargs.get("model")
        data_loader = kwargs.get("data_loader") or kwargs.get("val_loader")
        device = kwargs.get("device")
        if model is not None and data_loader is not None:
            from .evaluator import Evaluator
            evaluator = Evaluator(use_amp=self.use_amp, amp_dtype=self.amp_dtype, device=device)
            return evaluator.evaluate(model=model, data_loader=data_loader, device=device, **kwargs)
        return {}

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text stub for compatibility."""
        return prompt

    def reset_early_stopping(self) -> None:
        """Reset internal early stopping tracking state."""
        self.best_metric = None
        self.bad_epochs = 0

    def should_stop_early(
        self,
        current_metric: float,
        best_metric: float,
        patience: int,
        mode: str = "min",
        min_delta: float = 0.0,
        bad_epochs: int = 0,
        **kwargs: Any,
    ) -> bool:
        """
        Determine if training should stop early based on metric performance.
        """
        mode = mode.lower()
        if mode == "min":
            is_improved = current_metric < (best_metric - min_delta)
        elif mode == "max":
            is_improved = current_metric > (best_metric + min_delta)
        else:
            is_improved = False

        if is_improved:
            return False

        return bad_epochs >= patience
