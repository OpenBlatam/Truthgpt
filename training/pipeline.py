"""
Training Pipeline Orchestrator and Fluent Builder
=================================================
End-to-end training pipeline orchestrator tying together models, datasets, optimizers,
schedulers, checkpoint managers, EMA trackers, evaluators, experiment trackers, and callbacks.
Includes the fluent TrainingPipelineBuilder for declarative assembly.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from .callbacks import (
    CallbackHandler,
    EarlyStoppingCallback,
    LRMonitorCallback,
    MetricsLoggerCallback,
    ModelCheckpointCallback,
    ProgressCallback,
)
from .checkpoint_manager import CheckpointManager
from .ema_manager import EMAManager
from .evaluator import Evaluator
from .exceptions import EarlyStoppingTriggered, PipelineError, TrainingConfigurationError
from .experiment_tracker import ExperimentTracker
from .interfaces import BaseCallback, BaseTrainingPipeline
from .training_loop import TrainingLoop
from .types import (
    CheckpointConfig,
    EMAConfig,
    EvaluatorConfig,
    TrackerConfig,
    TrainingLoopConfig,
    TrainingPipelineConfig,
)

logger = logging.getLogger(__name__)


class TrainingPipeline(BaseTrainingPipeline):
    """
    High-level training pipeline orchestrator.
    Manages multi-epoch execution, validation cycles, checkpoint persistence,
    EMA synchronization, metrics streaming, and callback dispatch.
    """

    def __init__(
        self,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        scheduler: Optional[Any] = None,
        training_loop: Optional[TrainingLoop] = None,
        checkpoint_manager: Optional[CheckpointManager] = None,
        ema_manager: Optional[EMAManager] = None,
        evaluator: Optional[Evaluator] = None,
        tracker: Optional[ExperimentTracker] = None,
        callbacks: Optional[List[BaseCallback]] = None,
        config: Optional[TrainingPipelineConfig] = None,
    ) -> None:
        self.model = model
        self.optimizer = optimizer
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.scheduler = scheduler

        self.config = config or TrainingPipelineConfig()
        self.training_loop = training_loop or TrainingLoop(config=self.config.training_loop)
        self.checkpoint_manager = checkpoint_manager
        self.ema_manager = ema_manager
        self.evaluator = evaluator or Evaluator()
        self.tracker = tracker
        self.callbacks = list(callbacks or [])

        # Build callback handler
        self.callback_handler = CallbackHandler(self.callbacks)

        # Connect automatic callbacks
        if self.checkpoint_manager is not None:
            self.callback_handler.add_callback(
                ModelCheckpointCallback(checkpoint_manager=self.checkpoint_manager)
            )

        self.callback_handler.add_callback(ProgressCallback())
        self.callback_handler.add_callback(LRMonitorCallback())
        if self.tracker is not None:
            self.callback_handler.add_callback(MetricsLoggerCallback(tracker=self.tracker))

    def fit(
        self,
        epochs: Optional[int] = None,
        eval_every_epochs: int = 1,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute full training workflow across specified number of epochs.

        Args:
            epochs: Total number of epochs to train.
            eval_every_epochs: Interval between validation evaluation runs.

        Returns:
            Dictionary containing overall training history and metrics.
        """
        total_epochs = epochs or self.config.epochs
        eval_interval = eval_every_epochs or self.config.eval_every_epochs

        history: Dict[str, List[Any]] = {
            "train_loss": [],
            "val_loss": [],
            "val_metrics": [],
            "epoch_times": [],
        }

        pipeline_state: Dict[str, Any] = {
            "model": self.model,
            "optimizer": self.optimizer,
            "scheduler": self.scheduler,
            "total_epochs": total_epochs,
            "should_stop": False,
        }

        self.callback_handler.on_train_begin(pipeline_state)
        training_start_time = time.perf_counter()

        try:
            for epoch in range(1, total_epochs + 1):
                pipeline_state["epoch"] = epoch
                logger.info(f"--- Starting Epoch {epoch}/{total_epochs} ---")

                # 1. Train epoch
                epoch_result = self.training_loop.train_epoch(
                    model=self.model,
                    train_loader=self.train_loader,
                    optimizer=self.optimizer,
                    scheduler=self.scheduler,
                    epoch=epoch,
                    **kwargs,
                )

                history["train_loss"].append(epoch_result["loss"])
                history["epoch_times"].append(epoch_result["elapsed_time"])

                # 2. Update EMA weights
                if self.ema_manager is not None:
                    self.ema_manager.update(self.model)

                # 3. Validation Phase
                if self.val_loader is not None and epoch % eval_interval == 0:
                    val_metrics = self._run_evaluation()
                    history["val_loss"].append(val_metrics.get("loss"))
                    history["val_metrics"].append(val_metrics)

                    # Trigger callbacks on eval
                    self.callback_handler.on_eval(val_metrics, pipeline_state)

                    if self.tracker is not None:
                        self.tracker.log_metrics(
                            {f"val/{k}": v for k, v in val_metrics.items()},
                            step=self.training_loop.total_steps,
                        )

                if pipeline_state.get("should_stop", False):
                    logger.info(f"Training stopped early at epoch {epoch}.")
                    break

        except EarlyStoppingTriggered as est:
            logger.info(f"Training completed via early stopping: {est}")
        except Exception as e:
            self.callback_handler.on_exception(e, pipeline_state)
            raise PipelineError(f"Training pipeline execution failed: {e}") from e
        finally:
            total_duration = time.perf_counter() - training_start_time
            pipeline_state["total_duration"] = total_duration
            self.callback_handler.on_train_end(pipeline_state)
            if self.tracker is not None:
                self.tracker.finish()

        return {
            "epochs_completed": len(history["train_loss"]),
            "history": history,
            "total_duration": total_duration,
            "final_train_loss": history["train_loss"][-1] if history["train_loss"] else None,
            "final_val_loss": history["val_loss"][-1] if history["val_loss"] else None,
        }

    def _run_evaluation(self) -> Dict[str, float]:
        """Internal helper to execute evaluation, utilizing EMA weights if configured."""
        if self.val_loader is None:
            return {}

        if self.ema_manager is not None and self.ema_manager.enabled:
            with self.ema_manager.swap_weights(self.model):
                return self.evaluator.evaluate(self.model, self.val_loader)
        else:
            return self.evaluator.evaluate(self.model, self.val_loader)

    def evaluate(self, data_loader: Optional[DataLoader] = None, **kwargs: Any) -> Dict[str, float]:
        """Evaluate model on given data loader or configured validation loader."""
        target_loader = data_loader or self.val_loader
        if target_loader is None:
            raise PipelineError("No data loader provided for evaluation.")

        if self.ema_manager is not None and self.ema_manager.enabled:
            with self.ema_manager.swap_weights(self.model):
                return self.evaluator.evaluate(self.model, target_loader, **kwargs)
        return self.evaluator.evaluate(self.model, target_loader, **kwargs)


class TrainingPipelineBuilder:
    """
    Fluent builder for configuring and assembling TrainingPipeline instances.
    """

    def __init__(self) -> None:
        self._model: Optional[nn.Module] = None
        self._optimizer: Optional[torch.optim.Optimizer] = None
        self._train_loader: Optional[DataLoader] = None
        self._val_loader: Optional[DataLoader] = None
        self._scheduler: Optional[Any] = None
        self._training_loop_config: Optional[TrainingLoopConfig] = None
        self._checkpoint_config: Optional[CheckpointConfig] = None
        self._ema_config: Optional[EMAConfig] = None
        self._evaluator_config: Optional[EvaluatorConfig] = None
        self._tracker_config: Optional[TrackerConfig] = None
        self._callbacks: List[BaseCallback] = []
        self._pipeline_config: TrainingPipelineConfig = TrainingPipelineConfig()

    def with_model(self, model: nn.Module) -> "TrainingPipelineBuilder":
        """Set model to train."""
        self._model = model
        return self

    def with_optimizer(
        self,
        optimizer: torch.optim.Optimizer,
        scheduler: Optional[Any] = None,
    ) -> "TrainingPipelineBuilder":
        """Set optimizer and optional learning rate scheduler."""
        self._optimizer = optimizer
        self._scheduler = scheduler
        return self

    def with_data(
        self,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
    ) -> "TrainingPipelineBuilder":
        """Set train and validation data loaders."""
        self._train_loader = train_loader
        self._val_loader = val_loader
        return self

    def with_training_config(
        self,
        config: Union[TrainingLoopConfig, Dict[str, Any]],
    ) -> "TrainingPipelineBuilder":
        """Configure training loop parameters."""
        if isinstance(config, dict):
            self._training_loop_config = TrainingLoopConfig(**config)
        else:
            self._training_loop_config = config
        return self

    def with_checkpointing(
        self,
        config: Union[CheckpointConfig, Dict[str, Any]],
    ) -> "TrainingPipelineBuilder":
        """Configure model checkpointing."""
        if isinstance(config, dict):
            self._checkpoint_config = CheckpointConfig(**config)
        else:
            self._checkpoint_config = config
        return self

    def with_ema(
        self,
        config: Union[EMAConfig, Dict[str, Any]],
    ) -> "TrainingPipelineBuilder":
        """Configure Exponential Moving Average tracking."""
        if isinstance(config, dict):
            self._ema_config = EMAConfig(**config)
        else:
            self._ema_config = config
        return self

    def with_evaluator(
        self,
        config: Union[EvaluatorConfig, Dict[str, Any]],
    ) -> "TrainingPipelineBuilder":
        """Configure evaluation engine."""
        if isinstance(config, dict):
            self._evaluator_config = EvaluatorConfig(**config)
        else:
            self._evaluator_config = config
        return self

    def with_tracker(
        self,
        config: Union[TrackerConfig, Dict[str, Any]],
    ) -> "TrainingPipelineBuilder":
        """Configure experiment tracker."""
        if isinstance(config, dict):
            self._tracker_config = TrackerConfig(**config)
        else:
            self._tracker_config = config
        return self

    def with_callbacks(self, callbacks: List[BaseCallback]) -> "TrainingPipelineBuilder":
        """Add custom lifecycle callbacks."""
        self._callbacks.extend(callbacks)
        return self

    def build(self) -> TrainingPipeline:
        """
        Assemble and return the fully initialized TrainingPipeline.

        Raises:
            TrainingConfigurationError: If required components (model, optimizer, train_loader) are missing.
        """
        if self._model is None:
            raise TrainingConfigurationError("Model must be set before building TrainingPipeline.")
        if self._optimizer is None:
            raise TrainingConfigurationError("Optimizer must be set before building TrainingPipeline.")
        if self._train_loader is None:
            raise TrainingConfigurationError("Train DataLoader must be set before building TrainingPipeline.")

        training_loop = TrainingLoop(
            config=self._training_loop_config or TrainingLoopConfig(),
            callbacks=self._callbacks,
        )

        checkpoint_mgr = None
        if self._checkpoint_config is not None:
            checkpoint_mgr = CheckpointManager(
                checkpoint_config=self._checkpoint_config,
                model=self._model,
                optimizer=self._optimizer,
                scheduler=self._scheduler,
            )

        ema_mgr = None
        if self._ema_config is not None and self._ema_config.enabled:
            ema_mgr = EMAManager(
                ema_config=self._ema_config,
                model=self._model,
            )

        evaluator = Evaluator(config=self._evaluator_config or EvaluatorConfig())

        tracker = None
        if self._tracker_config is not None:
            tracker = ExperimentTracker(config=self._tracker_config)

        return TrainingPipeline(
            model=self._model,
            optimizer=self._optimizer,
            train_loader=self._train_loader,
            val_loader=self._val_loader,
            scheduler=self._scheduler,
            training_loop=training_loop,
            checkpoint_manager=checkpoint_mgr,
            ema_manager=ema_mgr,
            evaluator=evaluator,
            tracker=tracker,
            callbacks=self._callbacks,
            config=self._pipeline_config,
        )
