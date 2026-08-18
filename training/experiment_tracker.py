"""
Experiment Tracker Module
=========================
Professional experiment tracking with WandB, TensorBoard, MLflow, and Console logging backends.
Supports resource lifecycle management, metrics logging, artifact tracking, and context managers.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import torch

from .exceptions import ExperimentTrackerError
from .interfaces import BaseExperimentTracker
from .types import TrackerBackend, TrackerConfig

logger = logging.getLogger(__name__)

# Optional backend imports
try:
    import wandb
    _WANDB_AVAILABLE = True
except ImportError:
    _WANDB_AVAILABLE = False

try:
    from torch.utils.tensorboard import SummaryWriter
    _TENSORBOARD_AVAILABLE = True
except ImportError:
    _TENSORBOARD_AVAILABLE = False

try:
    import mlflow
    _MLFLOW_AVAILABLE = True
except ImportError:
    _MLFLOW_AVAILABLE = False


class ExperimentTracker(BaseExperimentTracker):
    """
    Unified experiment tracking system dispatching across multiple backends
    (WandB, TensorBoard, MLflow, Console, Logger, In-Memory).
    """

    def __init__(
        self,
        trackers: Optional[Union[List[str], Dict[str, Any]]] = None,
        project: Optional[str] = None,
        run_name: Optional[str] = None,
        log_dir: Optional[str] = None,
        config: Optional[Union[Dict[str, Any], TrackerConfig]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize ExperimentTracker.
        """
        if config is not None:
            if isinstance(config, TrackerConfig):
                self.trackers_enabled = [t.lower() for t in config.trackers]
                project = project or config.project
                run_name = run_name or config.run_name
                log_dir = log_dir or config.log_dir
            elif isinstance(config, dict):
                self.trackers_enabled = [t.lower() for t in config.get("trackers", ["console"])]
                project = project or config.get("project")
                run_name = run_name or config.get("run_name")
                log_dir = log_dir or config.get("log_dir")
        elif isinstance(trackers, dict):
            self.trackers_enabled = [t.lower() for t in trackers.get("trackers", ["console"])]
            project = project or trackers.get("project")
            run_name = run_name or trackers.get("run_name")
            log_dir = log_dir or trackers.get("log_dir")
        elif isinstance(trackers, list):
            self.trackers_enabled = [t.lower() for t in trackers]
        else:
            self.trackers_enabled = ["console"]

        self.project = project or "truthgpt"
        self.run_name = run_name
        self.log_dir = log_dir or "./logs"

        self.wandb_run: Any = None
        self.tensorboard_writer: Any = None
        self.mlflow_run: Any = None
        self.console_enabled: bool = any(t in self.trackers_enabled for t in ("console", "logger"))
        self.in_memory_metrics: List[Dict[str, Any]] = []

        # Initialize backends
        self._init_backends(**kwargs)

    def _init_backends(self, **kwargs: Any) -> None:
        """Initialize requested external tracking backends safely."""
        # 1. WandB
        if "wandb" in self.trackers_enabled:
            if not _WANDB_AVAILABLE:
                logger.warning("WandB package not installed; skipping WandB initialization.")
            else:
                try:
                    self.wandb_run = wandb.init(
                        project=self.project,
                        name=self.run_name,
                        **kwargs,
                    )
                    logger.info("WandB initialized successfully.")
                except Exception as e:
                    logger.error(f"Failed to initialize WandB: {e}")

        # 2. TensorBoard
        if "tensorboard" in self.trackers_enabled:
            if not _TENSORBOARD_AVAILABLE:
                logger.warning("TensorBoard (torch.utils.tensorboard) not installed; skipping TensorBoard.")
            else:
                try:
                    tb_path = Path(self.log_dir) / (self.run_name or "run")
                    tb_path.mkdir(parents=True, exist_ok=True)
                    self.tensorboard_writer = SummaryWriter(log_dir=str(tb_path))
                    logger.info(f"TensorBoard SummaryWriter initialized at '{tb_path}'.")
                except Exception as e:
                    logger.error(f"Failed to initialize TensorBoard: {e}")

        # 3. MLflow
        if "mlflow" in self.trackers_enabled:
            if not _MLFLOW_AVAILABLE:
                logger.warning("MLflow package not installed; skipping MLflow initialization.")
            else:
                try:
                    mlflow.set_experiment(self.project)
                    self.mlflow_run = mlflow.start_run(run_name=self.run_name)
                    logger.info("MLflow run started successfully.")
                except Exception as e:
                    logger.error(f"Failed to initialize MLflow: {e}")

    def log(self, metrics: Dict[str, Any], step: Optional[int] = None) -> None:
        """Alias for log_metrics for backward compatibility."""
        self.log_metrics(metrics, step=step)

    def log_metrics(self, metrics: Dict[str, Any], step: Optional[int] = None) -> None:
        """
        Log scalar metrics to all enabled backends.
        """
        clean_metrics = {}
        for k, v in metrics.items():
            if isinstance(v, (int, float)):
                clean_metrics[k] = float(v)
            elif isinstance(v, torch.Tensor) and v.numel() == 1:
                clean_metrics[k] = float(v.item())

        if not clean_metrics:
            return

        # Record in memory
        self.in_memory_metrics.append({"step": step, "metrics": clean_metrics})

        # WandB
        if self.wandb_run is not None:
            try:
                self.wandb_run.log(clean_metrics, step=step)
            except Exception as e:
                logger.warning(f"Error logging to WandB: {e}")

        # TensorBoard
        if self.tensorboard_writer is not None:
            try:
                for k, v in clean_metrics.items():
                    self.tensorboard_writer.add_scalar(k, v, global_step=step)
            except Exception as e:
                logger.warning(f"Error logging to TensorBoard: {e}")

        # MLflow
        if self.mlflow_run is not None:
            try:
                mlflow.log_metrics(clean_metrics, step=step)
            except Exception as e:
                logger.warning(f"Error logging to MLflow: {e}")

        # Console
        if self.console_enabled:
            step_str = f"[Step {step}] " if step is not None else ""
            metrics_str = ", ".join(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}" for k, v in clean_metrics.items())
            logger.debug(f"{step_str}{metrics_str}")

    def log_hyperparams(self, params: Dict[str, Any]) -> None:
        """
        Log hyperparameter configuration to all backends.
        """
        if self.wandb_run is not None:
            try:
                self.wandb_run.config.update(params)
            except Exception as e:
                logger.warning(f"Error logging hyperparameters to WandB: {e}")

        if self.tensorboard_writer is not None:
            try:
                self.tensorboard_writer.add_hparams(params, {})
            except Exception as e:
                logger.debug(f"Could not log hparams to TensorBoard: {e}")

        if self.mlflow_run is not None:
            try:
                mlflow.log_params(params)
            except Exception as e:
                logger.warning(f"Error logging parameters to MLflow: {e}")

    def log_artifact(self, artifact_path: str, artifact_type: Optional[str] = None) -> None:
        """
        Log file or directory artifact to backends.
        """
        p = Path(artifact_path)
        if not p.exists():
            logger.debug(f"Artifact path does not exist on disk: {artifact_path}")
            return

        if self.wandb_run is not None:
            try:
                artifact = wandb.Artifact(name=p.stem, type=artifact_type or "model")
                if p.is_dir():
                    artifact.add_dir(str(p))
                else:
                    artifact.add_file(str(p))
                self.wandb_run.log_artifact(artifact)
            except Exception as e:
                logger.warning(f"Failed to log artifact to WandB: {e}")

        if self.mlflow_run is not None:
            try:
                if p.is_dir():
                    mlflow.log_artifacts(str(p))
                else:
                    mlflow.log_artifact(str(p))
            except Exception as e:
                logger.warning(f"Failed to log artifact to MLflow: {e}")

    def finish(self) -> None:
        """
        Finalize and close active tracking sessions.
        """
        if self.wandb_run is not None:
            try:
                self.wandb_run.finish()
            except Exception as e:
                logger.warning(f"Error closing WandB: {e}")
            self.wandb_run = None

        if self.tensorboard_writer is not None:
            try:
                self.tensorboard_writer.flush()
                self.tensorboard_writer.close()
            except Exception as e:
                logger.warning(f"Error closing TensorBoard: {e}")
            self.tensorboard_writer = None

        if self.mlflow_run is not None:
            try:
                mlflow.end_run()
            except Exception as e:
                logger.warning(f"Error closing MLflow: {e}")
            self.mlflow_run = None

    def get_logged_metrics(self) -> List[Dict[str, Any]]:
        """Return all metric records captured in memory."""
        return list(self.in_memory_metrics)

    def __enter__(self) -> "ExperimentTracker":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.finish()
