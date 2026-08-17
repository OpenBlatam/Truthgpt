"""
Experiment Tracker Module
=========================
Professional experiment tracking with WandB, TensorBoard, and Console logging backends.
Supports resource lifecycle management, metrics logging, artifact tracking, and context managers.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import torch

try:
    from ..trainers.interfaces import BaseExperimentTracker
except ImportError:
    try:
        from optimization_core.trainers.interfaces import BaseExperimentTracker
    except ImportError:
        from abc import ABC, abstractmethod

        class BaseExperimentTracker(ABC):  # type: ignore
            """Fallback abstract base class for ExperimentTracker."""
            pass

logger = logging.getLogger(__name__)

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


class ExperimentTrackerError(RuntimeError):
    """Exception raised when experiment logging operations fail."""

    pass


class ExperimentTracker(BaseExperimentTracker):
    """
    Professional experiment tracking with multiple backends (WandB, TensorBoard, Console).
    Implements BaseExperimentTracker interface.
    """

    def __init__(
        self,
        trackers: Optional[Union[List[str], Dict[str, Any]]] = None,
        project: Optional[str] = None,
        run_name: Optional[str] = None,
        log_dir: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize experiment tracker.

        Args:
            trackers: List of trackers ("wandb", "tensorboard", "console", "logger") or dict config.
            project: Project name (for WandB).
            run_name: Run name.
            log_dir: Log directory (for TensorBoard).
            **kwargs: Additional tracker arguments.
        """
        if isinstance(trackers, dict):
            cfg = trackers
            self.trackers_enabled: List[str] = cfg.get("trackers", ["console"])
            project = project or cfg.get("project")
            run_name = run_name or cfg.get("run_name")
            log_dir = log_dir or cfg.get("log_dir")
        elif isinstance(trackers, list):
            self.trackers_enabled = trackers
        else:
            self.trackers_enabled = ["console"]

        self.run_name: Optional[str] = run_name
        self.wandb_run: Any = None
        self.tensorboard_writer: Any = None
        self.console_enabled: bool = "console" in self.trackers_enabled or "logger" in self.trackers_enabled

        # Initialize WandB backend if requested
        if "wandb" in self.trackers_enabled:
            if not _WANDB_AVAILABLE:
                logger.warning("WandB package not installed; skipping WandB initialization.")
            else:
                try:
                    self.wandb_run = wandb.init(
                        project=project or "truthgpt",
                        name=run_name,
                        **kwargs
                    )
                    logger.info("WandB initialized successfully.")
                except Exception as e:
                    logger.error(f"Failed to initialize WandB: {e}")

        # Initialize TensorBoard backend if requested
        if "tensorboard" in self.trackers_enabled:
            if not _TENSORBOARD_AVAILABLE:
                logger.warning("TensorBoard package not installed; skipping TensorBoard initialization.")
            else:
                try:
                    tb_log_dir = Path(log_dir) if log_dir else Path("runs") / (run_name or "default")
                    self.tensorboard_writer = SummaryWriter(log_dir=str(tb_log_dir))
                    logger.info(f"TensorBoard initialized at: {tb_log_dir}")
                except Exception as e:
                    logger.error(f"Failed to initialize TensorBoard: {e}")

    def __enter__(self) -> "ExperimentTracker":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and cleanup resources cleanly."""
        self.finish()

    def log(self, metrics: Dict[str, Any], step: Optional[int] = None) -> None:
        """
        Log metrics to all enabled trackers.

        Args:
            metrics: Dictionary of metric names to values.
            step: Optional step number.
        """
        if self.wandb_run:
            try:
                wandb.log(metrics, step=step)
            except Exception as e:
                logger.debug(f"Error logging to WandB: {e}")

        if self.tensorboard_writer:
            try:
                for key, value in metrics.items():
                    if isinstance(value, (int, float)):
                        self.tensorboard_writer.add_scalar(key, value, step or 0)
                    elif isinstance(value, torch.Tensor) and value.numel() == 1:
                        self.tensorboard_writer.add_scalar(key, value.item(), step or 0)
            except Exception as e:
                logger.debug(f"Error logging to TensorBoard: {e}")

        if self.console_enabled:
            step_str = f" [Step {step}]" if step is not None else ""
            metrics_str = ", ".join(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}" for k, v in metrics.items())
            logger.info(f"Metrics{step_str}: {metrics_str}")

    def log_metrics(self, metrics: Dict[str, Any], step: int) -> None:
        """Interface compliance wrapper for log."""
        self.log(metrics, step=step)

    def log_hyperparams(self, params: Dict[str, Any]) -> None:
        """
        Log hyperparameter configuration.

        Args:
            params: Dictionary of hyperparameters.
        """
        if self.wandb_run:
            try:
                wandb.config.update(params, allow_val_change=True)
            except Exception as e:
                logger.debug(f"Error updating WandB hyperparams: {e}")

        if self.tensorboard_writer and hasattr(self.tensorboard_writer, "add_hparams"):
            try:
                clean_params = {
                    k: (v if isinstance(v, (int, float, str, bool)) else str(v))
                    for k, v in params.items()
                }
                self.tensorboard_writer.add_hparams(clean_params, {})
            except Exception as e:
                logger.debug(f"Error logging hyperparams to TensorBoard: {e}")

        if self.console_enabled:
            logger.info(f"Hyperparameters: {params}")

    def log_histogram(self, name: str, values: torch.Tensor, step: Optional[int] = None) -> None:
        """
        Log histogram of values.

        Args:
            name: Histogram name.
            values: Values tensor to histogram.
            step: Optional step number.
        """
        if self.wandb_run:
            try:
                wandb.log({name: wandb.Histogram(values.cpu().numpy())}, step=step)
            except Exception as e:
                logger.debug(f"Error logging histogram to WandB: {e}")

        if self.tensorboard_writer:
            try:
                self.tensorboard_writer.add_histogram(name, values, step or 0)
            except Exception as e:
                logger.debug(f"Error logging histogram to TensorBoard: {e}")

    def log_model(self, model: torch.nn.Module, input_shape: Tuple[int, ...]) -> None:
        """
        Log model architecture.

        Args:
            model: Model to log.
            input_shape: Input shape tuple for visualization graph.
        """
        if self.wandb_run:
            try:
                wandb.watch(model, log="all", log_freq=100)
            except Exception as e:
                logger.debug(f"Error logging model to WandB: {e}")

        if self.tensorboard_writer:
            try:
                dummy_input = torch.zeros(input_shape)
                self.tensorboard_writer.add_graph(model, dummy_input)
            except Exception as e:
                logger.debug(f"Error logging model graph to TensorBoard: {e}")

    def log_artifact(self, artifact_path: str, name: Optional[str] = None, type_name: str = "model") -> None:
        """
        Log file artifact to tracker backends.

        Args:
            artifact_path: File system path to artifact file.
            name: Optional name for artifact.
            type_name: Type tag (default: "model").
        """
        if self.wandb_run:
            try:
                art = wandb.Artifact(name or Path(artifact_path).stem, type=type_name)
                art.add_file(artifact_path)
                wandb.log_artifact(art)
            except Exception as e:
                logger.debug(f"Error logging artifact to WandB: {e}")

    def finish(self) -> None:
        """Finish tracking session and release resources cleanly."""
        if self.wandb_run:
            try:
                wandb.finish()
            except Exception as e:
                logger.debug(f"Error finishing WandB session: {e}")
            finally:
                self.wandb_run = None

        if self.tensorboard_writer:
            try:
                self.tensorboard_writer.close()
            except Exception as e:
                logger.debug(f"Error closing TensorBoard writer: {e}")
            finally:
                self.tensorboard_writer = None


__all__ = ["ExperimentTracker", "ExperimentTrackerError"]
