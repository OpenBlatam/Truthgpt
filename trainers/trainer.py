"""
Modular GenericTrainer for PyTorch & Transformers LLM training.

Refactored facade orchestrating specialized sub-managers with deconstructed step methods,
complete event lifecycle callbacks, PyTorch profiler integration, and robust exception safety.
"""
import math
import os
import random
import time
import logging
from typing import Dict, Optional, List, Any, Union, Tuple

import torch
import torch.nn as nn

try:
    from torch.cuda.amp import autocast
except ImportError:
    from torch.amp import autocast

from .config import (
    TrainerConfig,
    ModelConfig,
    TrainingConfig,
    HardwareConfig,
    CheckpointConfig,
    EMAConfig,
)
from .model_manager import ModelManager
from .optimizer_manager import OptimizerManager
from .data_manager import DataManager
from .ema_manager import EMAManager
from .evaluator import Evaluator, get_autocast_context
from .checkpoint_manager import CheckpointManager
from .callbacks import Callback, CallbackHandler
from .interfaces import BaseTrainer
from .types import StepState, EvalMetrics, TrainerState
from .exceptions import TrainerError
from .profiler import TrainingProfiler
from .metrics_tracker import MetricTracker

try:
    from utils.logging_utils import TrainingLogger
    _TRAINING_LOGGER_AVAILABLE = True
except Exception:
    _TRAINING_LOGGER_AVAILABLE = False
    class TrainingLogger:
        def __init__(self, logger_inst=None):
            self.logger = logger_inst or logging.getLogger(__name__)
        def log_step(self, step: int, epoch: int, loss: float, learning_rate: float, tokens_per_sec: float = 0.0):
            self.logger.info(f"Step {step} | Epoch {epoch} | Loss {loss:.4f} | LR {learning_rate:.2e} | TPS {tokens_per_sec:.1f}")
        def log_eval(self, step: int, val_loss: float, perplexity: float, improved: bool = False):
            flag = " (Improved)" if improved else ""
            self.logger.info(f"Eval Step {step} | Val Loss {val_loss:.4f} | PPL {perplexity:.2f}{flag}")
        def log_checkpoint(self, step: int, path: str, is_best: bool = False):
            self.logger.info(f"Checkpoint saved at step {step}: {path} best={is_best}")

logger = logging.getLogger(__name__)


def set_seed(seed: int) -> None:
    """
    Set random seeds across Python, NumPy, and PyTorch for reproducibility.

    Args:
        seed: Seed integer value.
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


class GenericTrainer(BaseTrainer):
    """
    Main training orchestrator for Transformer / LLM model optimization.
    
    Coordinates ModelManager, OptimizerManager, DataManager, EMAManager,
    Evaluator, and CheckpointManager through clean sub-step methods and lifecycle callbacks.
    """

    def __init__(
        self,
        cfg: TrainerConfig,
        train_texts: List[str],
        val_texts: List[str],
        text_field_max_len: int = 512,
        callbacks: Optional[List[Callback]] = None,
        data_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize GenericTrainer.

        Args:
            cfg: Master configuration (TrainerConfig)
            train_texts: List of training text strings
            val_texts: List of validation text strings
            text_field_max_len: Maximum token sequence length
            callbacks: Optional list of Callback handlers
            data_options: Optional dictionary of data loading customization options
        """
        if not isinstance(cfg, TrainerConfig):
            try:
                cfg = TrainerConfig.from_dict(cfg) if isinstance(cfg, dict) else cfg
            except Exception as e:
                raise TrainerError(f"Invalid TrainerConfig provided: {e}") from e

        self.cfg = cfg
        set_seed(cfg.seed)

        self.callback_handler = CallbackHandler(callbacks or [])
        self.callbacks = self.callback_handler.callbacks
        self.data_options = data_options or {}
        self.state = TrainerState()
        self.state.max_steps = getattr(cfg.training, "max_steps", None)
        self.profiler = TrainingProfiler(enabled=bool(getattr(cfg.hardware, "use_profiler", False)))
        self.metric_tracker = MetricTracker()

        # 1. Device resolution
        self.device = self._resolve_device(cfg.hardware.device)

        # 2. Model Manager initialization & model loading
        self.model_manager = ModelManager(
            model_config=cfg.model,
            hardware_config=cfg.hardware,
            training_config=cfg.training,
            device=self.device,
        )
        self.tokenizer = self.model_manager.load_tokenizer()
        self.model = self.model_manager.load_model()

        # 3. Data Manager initialization & DataLoader creation
        self.data_manager = DataManager(
            training_config=cfg.training,
            hardware_config=cfg.hardware,
            tokenizer=self.tokenizer,
            text_field_max_len=text_field_max_len,
            data_options=self.data_options,
        )
        self.train_loader, self.val_loader = self.data_manager.create_loaders(
            train_texts=train_texts,
            val_texts=val_texts,
        )

        # 4. Optimizer Manager initialization
        self.optimizer_manager = OptimizerManager(
            training_config=cfg.training,
            model=self.model,
            use_amp=self._use_amp(),
        )
        opt_type = getattr(cfg.training, "optimizer_type", cfg.metadata.get("optimizer_type", "adamw"))
        self.optimizer = self.optimizer_manager.create_optimizer(optimizer_type=opt_type)

        num_train_steps = max(
            1, (len(self.train_loader) * cfg.training.epochs) // max(1, cfg.training.grad_accum_steps)
        )
        self.lr_scheduler = self.optimizer_manager.create_scheduler(num_train_steps)
        self.scaler = self.optimizer_manager.create_scaler()

        # 5. EMA Manager initialization
        self.ema_manager = EMAManager(
            ema_config=cfg.ema,
            model=self.model,
        )

        # 6. Evaluator initialization
        self.evaluator = Evaluator(
            training_config=cfg.training,
            model=self.model,
            val_loader=self.val_loader,
            device=self.device,
            use_amp=self._use_amp(),
            ema_manager=self.ema_manager,
        )

        # 7. Checkpoint Manager initialization
        self.checkpoint_manager = CheckpointManager(
            checkpoint_config=cfg.checkpoint,
            output_dir=cfg.output_dir,
            model=self.model,
            optimizer=self.optimizer,
            scheduler=self.lr_scheduler,
            scaler=self.scaler,
            tokenizer=self.tokenizer,
        )

        # 8. Profiler and Metrics tracker
        self.profiler = TrainingProfiler(enabled=getattr(cfg.hardware, "use_profiler", False))
        self.metrics_tracker = MetricTracker()
        self.training_logger = TrainingLogger(logger)

    def _resolve_device(self, target: str) -> torch.device:
        """Resolve PyTorch target device specification."""
        if target == "auto":
            if torch.cuda.is_available():
                device = torch.device("cuda")
                logger.info(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
                return device
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                logger.info("Using Apple MPS device")
                return torch.device("mps")
            logger.info("Using CPU device")
            return torch.device("cpu")
        return torch.device(target)

    def _use_amp(self) -> bool:
        """Determine if Automatic Mixed Precision (AMP) is enabled."""
        if self.device.type == "cuda" and self.cfg.training.mixed_precision in ("fp16", "bf16"):
            return True
        return False

    def _amp_dtype(self) -> Optional[torch.dtype]:
        """Get target AMP floating point dtype."""
        if self.cfg.training.mixed_precision == "bf16":
            return torch.bfloat16
        if self.cfg.training.mixed_precision == "fp16":
            return torch.float16
        return None

    def _try_resume(self) -> int:
        """Attempt to resume training state from existing checkpoint."""
        checkpoint_path = self.cfg.checkpoint.resume_from_checkpoint
        if not checkpoint_path or not os.path.exists(checkpoint_path):
            return 0
        try:
            state = self.checkpoint_manager.load(checkpoint_path)
            step = state.get("step", state.get("global_step", 0))
            logger.info(f"Resumed training state from {checkpoint_path} at global step {step}")
            return step
        except Exception as e:
            logger.error(f"Error resuming from checkpoint '{checkpoint_path}': {e}", exc_info=True)
            return 0

    def _step_forward_and_backward(self, batch: Union[Dict[str, torch.Tensor], Any]) -> Optional[torch.Tensor]:
        """Perform forward pass under AMP and backward pass scaled by GradScaler."""
        if isinstance(batch, dict):
            batch = {k: v.to(self.device, non_blocking=True) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
        elif isinstance(batch, (list, tuple)):
            batch = [v.to(self.device, non_blocking=True) if isinstance(v, torch.Tensor) else v for v in batch]
        else:
            batch = batch.to(self.device, non_blocking=True)

        with get_autocast_context(self.device.type, enabled=self._use_amp(), dtype=self._amp_dtype()):
            if isinstance(batch, dict):
                outputs = self.model(**batch)
            elif isinstance(batch, (list, tuple)):
                outputs = self.model(*batch)
            else:
                outputs = self.model(batch)

            raw_loss = getattr(outputs, "loss", outputs)
            if isinstance(raw_loss, dict):
                raw_loss = raw_loss.get("loss", list(raw_loss.values())[0])
            elif hasattr(raw_loss, "mean"):
                raw_loss = raw_loss.mean()

            scaled_loss = raw_loss / max(1, self.cfg.training.grad_accum_steps)

        if not torch.isfinite(scaled_loss):
            logger.warning(f"Non-finite loss encountered ({scaled_loss.item()}). Skipping step.")
            self.optimizer_manager.zero_grad()
            return None

        if self._use_amp() and self.scaler is not None:
            self.scaler.scale(scaled_loss).backward()
        else:
            scaled_loss.backward()

        return scaled_loss

    def _step_optimizer_and_clip(self, global_step: int) -> Tuple[bool, Optional[float]]:
        """Perform unscaling, gradient clipping, optimizer step, EMA update, and scheduler step."""
        if self._use_amp() and self.scaler is not None:
            self.scaler.unscale_(self.optimizer)

        grad_norm = None
        try:
            total_norm = torch.nn.utils.clip_grad_norm_(
                self.model.parameters(),
                self.cfg.training.max_grad_norm,
                error_if_nonfinite=False,
            )
            grad_norm = float(total_norm.item()) if hasattr(total_norm, "item") else float(total_norm)

            if not math.isfinite(grad_norm):
                logger.warning(f"Non-finite grad norm detected ({grad_norm}). Updating scaler without step.")
                if self._use_amp() and self.scaler is not None:
                    self.scaler.update()
                self.optimizer_manager.zero_grad()
                return False, grad_norm
        except Exception as e:
            logger.error(f"Grad clip error: {e}", exc_info=True)
            if self._use_amp() and self.scaler is not None:
                self.scaler.update()
            self.optimizer_manager.zero_grad()
            return False, None

        # Dispatch pre-step callback
        self.callback_handler.on_before_optimizer_step({
            "global_step": global_step,
            "grad_norm": grad_norm,
        })

        if self._use_amp() and self.scaler is not None:
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            self.optimizer.step()

        self.ema_manager.update()
        self.optimizer_manager.zero_grad()
        self.lr_scheduler.step()

        return True, grad_norm

    def train(self) -> None:
        """Execute complete training loop with deconstructed steps and full event hooks."""
        self.state.mark_training()
        self.state.global_step = self._try_resume()
        self.profiler.start()

        self.callback_handler.on_train_begin({
            "config": self.cfg,
            "global_step": self.state.global_step,
            "model": self.model,
        })

        self.model.train()
        if self.cfg.hardware.detect_anomaly:
            torch.autograd.set_detect_anomaly(True)
            logger.warning("Autograd anomaly detection enabled")

        try:
            for epoch in range(self.cfg.training.epochs):
                if self.state.should_stop_by_max_steps:
                    break

                self.state.epoch = epoch + 1
                self.callback_handler.on_epoch_begin(self.state.epoch, {"global_step": self.state.global_step})

                running_loss = 0.0
                epoch_start = time.perf_counter()
                tokens_accum = 0
                step_count = 0

                logger.info(f"Starting epoch {self.state.epoch}/{self.cfg.training.epochs}")

                for step, batch in enumerate(self.train_loader, start=1):
                    if self.state.should_stop_by_max_steps:
                        logger.info(f"Max steps limit reached ({self.state.max_steps}). Stopping training.")
                        break

                    step_t0 = self.profiler.step_start()
                    self.callback_handler.on_step_begin(step, {
                        "global_step": self.state.global_step,
                        "epoch": self.state.epoch,
                    })

                    try:
                        scaled_loss = self._step_forward_and_backward(batch)
                        if scaled_loss is None:
                            continue

                        # Gradient accumulation threshold
                        if step % self.cfg.training.grad_accum_steps == 0:
                            success, grad_norm = self._step_optimizer_and_clip(self.state.global_step)
                            if not success:
                                continue

                            self.state.global_step += 1
                            step_count += 1

                        loss_val = scaled_loss.detach().item()
                        running_loss += loss_val
                        self.metric_tracker.update("loss", loss_val)

                        batch_tokens = 0
                        if isinstance(batch, dict):
                            if "attention_mask" in batch:
                                batch_tokens = int(batch["attention_mask"].sum().item())
                            elif "input_ids" in batch:
                                batch_tokens = int(batch["input_ids"].numel())
                        tokens_accum += batch_tokens

                        prof_metrics = self.profiler.step_end(step_t0, num_tokens=batch_tokens)

                        step_state = {
                            "global_step": self.state.global_step,
                            "step": step,
                            "epoch": self.state.epoch,
                            "loss": loss_val,
                        }
                        if prof_metrics:
                            step_state.update(prof_metrics)
                        self.callback_handler.on_step_end(step, step_state)

                        # Logging interval
                        if self.state.global_step and self.state.global_step % self.cfg.training.log_interval == 0:
                            avg_loss = running_loss / max(1, step_count)
                            elapsed = max(1e-6, time.perf_counter() - epoch_start)
                            tps = tokens_accum / elapsed if tokens_accum > 0 else 0.0
                            current_lr = self.optimizer_manager.get_lr()
                            self.metric_tracker.update("learning_rate", current_lr)
                            self.metric_tracker.update("tokens_per_sec", tps)

                            self.training_logger.log_step(
                                step=self.state.global_step,
                                epoch=self.state.epoch,
                                loss=avg_loss,
                                learning_rate=current_lr,
                                tokens_per_sec=tps,
                            )

                            log_state = {
                                "step": self.state.global_step,
                                "global_step": self.state.global_step,
                                "epoch": self.state.epoch,
                                "loss": avg_loss,
                                "learning_rate": current_lr,
                                "tokens_per_sec": tps,
                            }
                            self.callback_handler.on_log(log_state)

                            running_loss = 0.0
                            tokens_accum = 0
                            step_count = 0
                            epoch_start = time.perf_counter()

                        # Evaluation interval
                        if self.state.global_step and self.state.global_step % self.cfg.training.eval_interval == 0:
                            eval_metrics = self.evaluate()
                            val_loss = eval_metrics.get("loss", float("inf"))
                            ppl = eval_metrics.get("perplexity", float("inf"))
                            metric_val = self.evaluator.select_best_metric(eval_metrics)
                            self.metric_tracker.update("val_loss", val_loss)
                            self.metric_tracker.update("perplexity", ppl)

                            improved = metric_val < (self.state.best_val_loss if self.cfg.training.select_best_by in ("loss",) else self.state.best_metric)
                            self.training_logger.log_eval(
                                step=self.state.global_step,
                                val_loss=val_loss,
                                perplexity=ppl,
                                improved=improved,
                            )

                            if improved:
                                self.state.best_val_loss = val_loss
                                self.state.best_metric = metric_val
                                self.state.bad_epochs = 0
                                saved_dir = self.checkpoint_manager.save(
                                    "best.pt", step=self.state.global_step, is_best=True, metrics=eval_metrics
                                )
                                self.training_logger.log_checkpoint(self.state.global_step, saved_dir, is_best=True)
                            else:
                                self.state.bad_epochs += 1
                                if self.state.bad_epochs >= self.cfg.training.early_stopping_patience:
                                    logger.info("Early stopping threshold reached.")
                                    self.checkpoint_manager.save("last.pt", step=self.state.global_step, metrics=eval_metrics)
                                    return

                            eval_state = {
                                "step": self.state.global_step,
                                "global_step": self.state.global_step,
                                "val_loss": val_loss,
                                "perplexity": ppl,
                                "improved": improved,
                            }
                            self.callback_handler.on_eval(eval_state)

                        # Checkpoint interval
                        if self.state.global_step and (self.state.global_step % max(1, self.cfg.checkpoint.interval_steps) == 0):
                            saved_path = self.checkpoint_manager.save(f"step_{self.state.global_step}.pt", step=self.state.global_step)
                            self.checkpoint_manager.prune_checkpoints()
                            self.callback_handler.on_save({"path": saved_path, "step": self.state.global_step})

                    except Exception as step_err:
                        logger.error(f"Error in training step {step}: {step_err}", exc_info=True)
                        self.optimizer_manager.zero_grad()
                        continue

                self.callback_handler.on_epoch_end(self.state.epoch, {"global_step": self.state.global_step})

            # Final checkpoint
            final_saved = self.checkpoint_manager.save("last.pt", step=self.state.global_step)
            self.callback_handler.on_save({"path": final_saved, "step": self.state.global_step})
            logger.info("Training process completed successfully.")

            self.state.mark_completed()
            train_end_payload = {
                "global_step": self.state.global_step,
                "best_metric": self.state.best_metric,
                "elapsed_seconds": self.state.elapsed_seconds(),
                "metrics_summary": self.metric_tracker.summary(),
            }
            if self.profiler.enabled:
                train_end_payload["profiling"] = self.profiler.summary()
            self.callback_handler.on_train_end(train_end_payload)

        except KeyboardInterrupt:
            logger.warning("Training interrupted by user.")
            self.state.mark_failed("Interrupted by user")
            self.checkpoint_manager.save("last.pt", step=self.state.global_step)
            raise
        except Exception as e:
            logger.error(f"Unhandled error in training loop: {e}", exc_info=True)
            self.state.mark_failed(str(e))
            self.callback_handler.on_exception(e, {
                "global_step": self.state.global_step,
                "epoch": self.state.epoch,
            })
            self.checkpoint_manager.save("last.pt", step=self.state.global_step)
            raise TrainerError(f"Training loop failed: {e}") from e
        finally:
            self.state.is_training = False

    def evaluate(self) -> Dict[str, float]:
        """
        Evaluate model performance on validation set.

        Returns:
            Dictionary containing metrics ('loss', 'perplexity')
        """
        return self.evaluator.evaluate()

    @torch.no_grad()
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 64,
        temperature: float = 0.8,
        top_p: float = 0.95,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
    ) -> str:
        """
        Generate text from prompt.

        Args:
            prompt: Input prompt text.
            max_new_tokens: Maximum generated sequence length.
            temperature: Sampling temperature.
            top_p: Nucleus sampling parameter.
            top_k: Top-k sampling parameter.
            repetition_penalty: Repetition penalty factor.

        Returns:
            Generated text string.
        """
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt must be a non-empty string")
        if temperature <= 0:
            raise ValueError("Temperature must be positive")

        self.model.eval()
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with get_autocast_context(self.device.type, enabled=self._use_amp(), dtype=self._amp_dtype()):
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                pad_token_id=getattr(self.tokenizer, "eos_token_id", None),
            )

        text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        self.model.train()
        return text


__all__ = ["GenericTrainer", "TrainerConfig", "set_seed", "TrainingLogger"]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.trainers."):
        sys.modules["trainers." + __name__[len("optimization_core.trainers."):]] = _mod
    elif __name__.startswith("trainers."):
        sys.modules["optimization_core.trainers." + __name__[len("trainers."):]] = _mod
