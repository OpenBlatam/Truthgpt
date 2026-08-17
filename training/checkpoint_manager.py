"""
Unified Checkpoint Manager Module
==================================
Handles PyTorch model checkpointing, random number generator (RNG) state capture/restoration,
cross-platform atomic file operations, manifest queries, safe loading, and automated pruning.
"""

import json
import logging
import os
import random
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn

try:
    from ..trainers.interfaces import BaseCheckpointManager
except ImportError:
    try:
        from optimization_core.trainers.interfaces import BaseCheckpointManager
    except ImportError:
        from abc import ABC, abstractmethod

        class BaseCheckpointManager(ABC):  # type: ignore
            """Fallback abstract base class for CheckpointManager."""
            pass

logger = logging.getLogger(__name__)


class CheckpointError(RuntimeError):
    """Exception raised when a checkpoint save, load, prune, or delete operation fails."""

    pass


class CheckpointManager(BaseCheckpointManager):
    """
    Manages PyTorch model checkpointing, RNG state preservation, manifest metadata,
    safe state-dict loading, and automated pruning.

    Implements the BaseCheckpointManager interface with support for instance state
    and static/dynamic parameter save/load operations.
    """

    def __init__(
        self,
        output_dir: Union[str, Path] = "./checkpoints",
        checkpoint_config: Optional[Any] = None,
        model: Optional[nn.Module] = None,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[Any] = None,
        scaler: Optional[Any] = None,
        tokenizer: Optional[Any] = None,
    ) -> None:
        """
        Initialize CheckpointManager.

        Args:
            output_dir: Path string or Path object pointing to checkpoint directory.
            checkpoint_config: Optional CheckpointConfig configuration object.
            model: Optional PyTorch module instance.
            optimizer: Optional PyTorch optimizer instance.
            scheduler: Optional learning rate scheduler instance.
            scaler: Optional PyTorch GradScaler instance.
            tokenizer: Optional tokenizer instance.

        Raises:
            CheckpointError: If output directory creation fails.
        """
        self.output_path: Path = Path(output_dir)
        self.output_dir: str = str(self.output_path)
        self.checkpoint_config: Optional[Any] = checkpoint_config
        self.model: Optional[nn.Module] = model
        self.optimizer: Optional[torch.optim.Optimizer] = optimizer
        self.scheduler: Optional[Any] = scheduler
        self.scaler: Optional[Any] = scaler
        self.tokenizer: Optional[Any] = tokenizer

        try:
            self.output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create checkpoint directory '{self.output_path}': {e}")
            raise CheckpointError(f"Cannot initialize directory '{self.output_path}': {e}") from e

    def _get_base_model(self, model: Optional[nn.Module] = None) -> nn.Module:
        """
        Unwrap parallel or distributed model containers to access the underlying PyTorch module.

        Args:
            model: Optional model module override.

        Returns:
            Unwrapped base nn.Module instance.

        Raises:
            CheckpointError: If no model instance is available.
        """
        target_model = model if model is not None else self.model
        if target_model is None:
            raise CheckpointError("Model cannot be None for CheckpointManager operations.")

        while isinstance(target_model, (nn.DataParallel, nn.parallel.DistributedDataParallel)):
            target_model = target_model.module
        if hasattr(target_model, "module") and isinstance(getattr(target_model, "module"), nn.Module):
            target_model = target_model.module

        return target_model

    def _capture_rng_state(self) -> Dict[str, Any]:
        """
        Capture random number generator states across Python, PyTorch, CUDA, and NumPy.

        Returns:
            Dictionary containing random generator state representations.
        """
        rng_state: Dict[str, Any] = {
            "python": random.getstate(),
            "torch": torch.get_rng_state(),
        }
        if torch.cuda.is_available():
            try:
                rng_state["torch_cuda"] = torch.cuda.get_rng_state_all()
            except Exception as e:
                logger.warning(f"Could not capture CUDA RNG state: {e}")
        try:
            import numpy as np

            rng_state["numpy"] = np.random.get_state()
        except ImportError:
            pass
        return rng_state

    def _restore_rng_state(self, rng_state: Dict[str, Any]) -> None:
        """
        Restore Python, PyTorch, CUDA, and NumPy random number generator states safely.

        Args:
            rng_state: State dictionary previously produced by _capture_rng_state().
        """
        try:
            if "python" in rng_state:
                random.setstate(rng_state["python"])
            if "torch" in rng_state:
                torch.set_rng_state(rng_state["torch"])
            if "torch_cuda" in rng_state and torch.cuda.is_available():
                torch.cuda.set_rng_state_all(rng_state["torch_cuda"])
            if "numpy" in rng_state:
                import numpy as np

                np.random.set_state(rng_state["numpy"])
            logger.info("RNG states restored successfully.")
        except Exception as e:
            logger.warning(f"Could not restore RNG state cleanly: {e}")

    def save(
        self,
        filename: str = "checkpoint.pt",
        step: int = 0,
        epoch: int = 0,
        is_best: bool = False,
        metrics: Optional[Dict[str, float]] = None,
        extra_state: Optional[Dict[str, Any]] = None,
        model: Optional[nn.Module] = None,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[Any] = None,
        scaler: Optional[Any] = None,
        tokenizer: Optional[Any] = None,
    ) -> str:
        """
        Save a complete training checkpoint atomically.

        Args:
            filename: Checkpoint filename or subfolder name (e.g. 'step_10.pt').
            step: Current training step count.
            epoch: Current training epoch count.
            is_best: Whether this checkpoint represents the best model state so far.
            metrics: Optional dictionary of evaluation metrics.
            extra_state: Optional extra state dictionary (e.g. EMA weights).
            model: Optional model instance override.
            optimizer: Optional optimizer instance override.
            scheduler: Optional scheduler instance override.
            scaler: Optional scaler instance override.
            tokenizer: Optional tokenizer instance override.

        Returns:
            Absolute string path to saved checkpoint directory.

        Raises:
            CheckpointError: If saving process encounters filesystem or serialization errors.
        """
        try:
            checkpoint_path = self.output_path / filename
            if filename.endswith(".pt"):
                checkpoint_dir = checkpoint_path.with_suffix("")
            else:
                checkpoint_dir = checkpoint_path

            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            base_model = self._get_base_model(model)
            active_tokenizer = tokenizer if tokenizer is not None else self.tokenizer
            active_optimizer = optimizer if optimizer is not None else self.optimizer
            active_scheduler = scheduler if scheduler is not None else self.scheduler
            active_scaler = scaler if scaler is not None else self.scaler

            # Attempt HuggingFace pretrained serialization if model/tokenizer support it
            try:
                save_st = (
                    getattr(self.checkpoint_config, "save_safetensors", True)
                    if self.checkpoint_config
                    else True
                )
                if hasattr(base_model, "save_pretrained"):
                    base_model.save_pretrained(str(checkpoint_dir), safe_serialization=save_st)
                if active_tokenizer is not None and hasattr(active_tokenizer, "save_pretrained"):
                    active_tokenizer.save_pretrained(str(checkpoint_dir))
            except Exception as e:
                logger.warning(f"Could not save pretrained model format ({e}); defaulting to PyTorch state dict.")

            state: Dict[str, Any] = {
                "step": step,
                "epoch": epoch,
                "model_state_dict": base_model.state_dict(),
                "rng_state": self._capture_rng_state(),
            }

            if active_optimizer is not None:
                state["optimizer_state_dict"] = active_optimizer.state_dict()
            if active_scheduler is not None and hasattr(active_scheduler, "state_dict"):
                state["scheduler_state_dict"] = active_scheduler.state_dict()
            if active_scaler is not None and hasattr(active_scaler, "state_dict"):
                state["scaler_state_dict"] = active_scaler.state_dict()
            if metrics is not None:
                state["metrics"] = metrics
            if extra_state is not None:
                state["extra_state"] = extra_state
            if is_best:
                state["is_best"] = True

            state_path = checkpoint_dir / "training_state.pt"

            # Execute atomic write via temporary file replace
            temp_fd, temp_path_str = tempfile.mkstemp(dir=str(checkpoint_dir), suffix=".tmp")
            os.close(temp_fd)
            temp_path = Path(temp_path_str)
            try:
                torch.save(state, temp_path)
                os.replace(temp_path, state_path)
            except Exception as save_err:
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass
                raise CheckpointError(f"Failed writing PyTorch state dict atomically: {save_err}") from save_err

            manifest = {
                "step": step,
                "epoch": epoch,
                "is_best": is_best,
                "metrics": metrics or {},
                "timestamp": time.time(),
                "has_optimizer": active_optimizer is not None,
                "has_scheduler": active_scheduler is not None,
                "has_scaler": active_scaler is not None,
            }
            manifest_path = checkpoint_dir / "checkpoint_manifest.json"
            manifest_temp = checkpoint_dir / "manifest.tmp"
            with open(manifest_temp, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            os.replace(manifest_temp, manifest_path)

            logger.debug(f"Checkpoint saved successfully to {checkpoint_dir}")
            return str(checkpoint_dir)

        except Exception as e:
            if isinstance(e, CheckpointError):
                raise
            logger.error(f"Error saving checkpoint '{filename}': {e}", exc_info=True)
            raise CheckpointError(f"Failed to save checkpoint '{filename}': {e}") from e

    def save_checkpoint(
        self,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
        scheduler: Any,
        step: int,
        path: str,
        tokenizer: Optional[Any] = None,
        scaler: Optional[Any] = None,
        ema_state: Optional[Dict[str, torch.Tensor]] = None,
        save_safetensors: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Compatibility wrapper method for saving checkpoints directly from arguments.
        """
        filename = os.path.basename(path) or f"step_{step}"
        extra_state = kwargs.pop("extra_state", {})
        if ema_state:
            extra_state["ema_state_dict"] = ema_state
        self.save(
            filename=filename,
            step=step,
            model=model,
            optimizer=optimizer,
            scheduler=scheduler,
            scaler=scaler,
            tokenizer=tokenizer,
            extra_state=extra_state,
            **kwargs,
        )

    def load(
        self,
        checkpoint_path: Union[str, Path],
        model: Optional[nn.Module] = None,
        device: Optional[Union[str, torch.device]] = None,
    ) -> Dict[str, Any]:
        """
        Load checkpoint state and restore model, optimizer, scheduler, and RNG state.

        Args:
            checkpoint_path: Path to checkpoint directory or state file.
            model: Optional model instance to restore parameters into.
            device: Optional target torch device.

        Returns:
            Dictionary containing loaded checkpoint state.

        Raises:
            CheckpointError: If checkpoint folder or state file cannot be read.
        """
        try:
            path_obj = Path(checkpoint_path)
            if path_obj.is_dir():
                state_path = path_obj / "training_state.pt"
                if not state_path.exists():
                    state_path = Path(str(path_obj) + ".pt") if not str(path_obj).endswith(".pt") else path_obj
            else:
                state_path = path_obj

            if not state_path.exists():
                raise CheckpointError(f"Checkpoint state file not found: {state_path}")

            map_loc = device or "cpu"
            try:
                state = torch.load(state_path, map_location=map_loc, weights_only=False)
            except TypeError:
                state = torch.load(state_path, map_location=map_loc)

            base_model = self._get_base_model(model)

            if "model_state_dict" in state:
                base_model.load_state_dict(state["model_state_dict"])
            else:
                base_model.load_state_dict(state)

            if self.optimizer is not None and "optimizer_state_dict" in state:
                self.optimizer.load_state_dict(state["optimizer_state_dict"])
            if self.scheduler is not None and "scheduler_state_dict" in state:
                self.scheduler.load_state_dict(state["scheduler_state_dict"])
            if self.scaler is not None and "scaler_state_dict" in state:
                self.scaler.load_state_dict(state["scaler_state_dict"])

            if "rng_state" in state:
                self._restore_rng_state(state["rng_state"])

            step = state.get("step", 0)
            logger.info(f"Successfully loaded checkpoint from {checkpoint_path} at step {step}")
            return state

        except Exception as e:
            if isinstance(e, CheckpointError):
                raise
            logger.error(f"Error loading checkpoint '{checkpoint_path}': {e}", exc_info=True)
            raise CheckpointError(f"Failed to load checkpoint '{checkpoint_path}': {e}") from e

    def load_checkpoint(
        self,
        path: str,
        model: nn.Module,
        optimizer: Optional[torch.optim.Optimizer] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Compatibility wrapper method for loading checkpoints.
        """
        old_opt = self.optimizer
        if optimizer is not None:
            self.optimizer = optimizer
        res = self.load(path, model=model)
        self.optimizer = old_opt
        return res

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """
        List all valid checkpoints in output directory with step metadata sorted by step.

        Returns:
            List of metadata dictionaries containing checkpoint details and paths.
        """
        if not self.output_path.exists():
            return []

        checkpoints = []
        for entry in self.output_path.iterdir():
            manifest_path = entry / "checkpoint_manifest.json"
            if entry.is_dir() and manifest_path.exists():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    meta["path"] = str(entry)
                    checkpoints.append(meta)
                except Exception as e:
                    logger.warning(f"Could not read checkpoint manifest at {manifest_path}: {e}")

        checkpoints.sort(key=lambda x: x.get("step", 0))
        return checkpoints

    def get_latest_checkpoint(self) -> Optional[str]:
        """
        Get the file system path string to the most recent checkpoint by step count.

        Returns:
            Path string or None if no valid checkpoints exist.
        """
        checkpoints = self.list_checkpoints()
        if not checkpoints:
            return None
        return checkpoints[-1]["path"]

    def find_best_checkpoint(self, metric_name: str = "loss", mode: str = "min") -> Optional[str]:
        """
        Find checkpoint path corresponding to the optimal metric value.

        Args:
            metric_name: Name of metric to evaluate (e.g. 'loss', 'accuracy').
            mode: Comparison mode ('min' or 'max').

        Returns:
            Path string to best checkpoint, or None if no checkpoints match.

        Raises:
            ValueError: If mode is not 'min' or 'max'.
        """
        if mode not in ("min", "max"):
            raise ValueError(f"Mode must be 'min' or 'max', got '{mode}'")

        checkpoints = self.list_checkpoints()
        if not checkpoints:
            return None

        best_path: Optional[str] = None
        best_val: float = float("inf") if mode == "min" else float("-inf")

        for ckpt in checkpoints:
            metrics = ckpt.get("metrics", {})
            if metric_name in metrics:
                val = metrics[metric_name]
                if (mode == "min" and val < best_val) or (mode == "max" and val > best_val):
                    best_val = val
                    best_path = ckpt["path"]

        return best_path

    def delete_checkpoint(self, checkpoint_path: Union[str, Path]) -> bool:
        """
        Delete a checkpoint directory or file safely.

        Args:
            checkpoint_path: Path string or Path object pointing to checkpoint directory.

        Returns:
            True if deletion succeeded, False otherwise.
        """
        path_obj = Path(checkpoint_path)
        if not path_obj.exists():
            logger.warning(f"Checkpoint path does not exist for deletion: {checkpoint_path}")
            return False

        try:
            if path_obj.is_dir():
                shutil.rmtree(path_obj)
            else:
                path_obj.unlink()
            logger.info(f"Successfully deleted checkpoint at {checkpoint_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete checkpoint at {checkpoint_path}: {e}")
            return False

    def prune_checkpoints(self) -> None:
        """
        Prune older step checkpoints according to keep_last configuration setting.
        """
        keep_last = getattr(self.checkpoint_config, "keep_last", 3) if self.checkpoint_config else 3
        if keep_last <= 0:
            return

        try:
            if not self.output_path.exists():
                return
            step_entries: List[Tuple[int, Path]] = []
            for entry in self.output_path.iterdir():
                name = entry.name
                if name.startswith("step_"):
                    step_str = name.replace("step_", "").removesuffix(".pt")
                    if step_str.isdigit():
                        step_entries.append((int(step_str), entry))

            step_entries.sort(key=lambda x: x[0])
            excess_count = len(step_entries) - keep_last

            if excess_count > 0:
                for idx in range(excess_count):
                    step_num, entry_path = step_entries[idx]
                    self.delete_checkpoint(entry_path)
        except Exception as e:
            logger.warning(f"Error during checkpoint pruning execution: {e}")


__all__ = ["CheckpointManager", "CheckpointError"]
