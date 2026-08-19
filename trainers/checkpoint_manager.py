"""
Checkpoint Manager - Handles model checkpointing, RNG state tracking, and state pruning.

Provides robust serialization and deserialization for model weights, training state, and RNG.
"""
import os
import json
import random
import logging
import shutil
import tempfile
import time
from typing import Optional, Dict, Any, Union
import torch
import torch.nn as nn

from .config import CheckpointConfig
from .interfaces import BaseCheckpointManager
from .exceptions import CheckpointError

logger = logging.getLogger(__name__)


class CheckpointManager(BaseCheckpointManager):
    """
    Manages model checkpointing and state persistence.
    """
    
    def __init__(
        self,
        checkpoint_config: CheckpointConfig,
        output_dir: str,
        model: nn.Module,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[Any] = None,
        scaler: Optional[Any] = None,
        tokenizer: Optional[Any] = None,
    ) -> None:
        if model is None:
            raise CheckpointError("Model cannot be None for CheckpointManager.")
        if not output_dir:
            raise CheckpointError("output_dir must be specified for CheckpointManager.")
        self.checkpoint_config = checkpoint_config
        self.output_dir = output_dir
        self.model = model
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.scaler = scaler
        self.tokenizer = tokenizer
        
        os.makedirs(output_dir, exist_ok=True)
    
    def _get_base_model(self) -> nn.Module:
        """Unwrap parallel or distributed model wrappers."""
        model = self.model
        if isinstance(model, (nn.DataParallel, nn.parallel.DistributedDataParallel)):
            model = model.module
        if hasattr(model, "module"):
            model = model.module
        return model

    def _capture_rng_state(self) -> Dict[str, Any]:
        """Capture python, torch, and CUDA random number generator states."""
        rng_state: Dict[str, Any] = {
            "python": random.getstate(),
            "torch": torch.get_rng_state(),
        }
        if torch.cuda.is_available():
            rng_state["torch_cuda"] = torch.cuda.get_rng_state_all()
        try:
            import numpy as np
            rng_state["numpy"] = np.random.get_state()
        except ImportError:
            pass
        return rng_state

    def _restore_rng_state(self, rng_state: Dict[str, Any]) -> None:
        """Restore random number generator states."""
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
            logger.info("RNG states restored successfully")
        except Exception as e:
            logger.warning(f"Could not restore RNG state: {e}")

    def save(
        self,
        filename: str,
        step: int = 0,
        epoch: int = 0,
        is_best: bool = False,
        metrics: Optional[Dict[str, float]] = None,
        extra_state: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save complete training checkpoint atomically.
        """
        try:
            checkpoint_path = os.path.join(self.output_dir, filename)
            if filename.endswith(".pt"):
                checkpoint_dir = checkpoint_path.replace(".pt", "")
            else:
                checkpoint_dir = checkpoint_path
            
            os.makedirs(checkpoint_dir, exist_ok=True)
            base_model = self._get_base_model()
            
            # Try HF save_pretrained format if model supports it
            try:
                save_st = getattr(self.checkpoint_config, "save_safetensors", True)
                if hasattr(base_model, "save_pretrained"):
                    base_model.save_pretrained(
                        checkpoint_dir,
                        safe_serialization=save_st,
                    )
                if self.tokenizer is not None and hasattr(self.tokenizer, "save_pretrained"):
                    self.tokenizer.save_pretrained(checkpoint_dir)
            except Exception as e:
                logger.warning(f"Could not save pretrained HuggingFace format ({e}). Saving state dict only.")
            
            # Construct state dict
            state: Dict[str, Any] = {
                "step": step,
                "epoch": epoch,
                "model_state_dict": base_model.state_dict(),
                "rng_state": self._capture_rng_state(),
            }
            
            if self.optimizer is not None:
                state["optimizer_state_dict"] = self.optimizer.state_dict()
            if self.scheduler is not None and hasattr(self.scheduler, "state_dict"):
                state["scheduler_state_dict"] = self.scheduler.state_dict()
            if self.scaler is not None and hasattr(self.scaler, "state_dict"):
                state["scaler_state_dict"] = self.scaler.state_dict()
            if metrics:
                state["metrics"] = metrics
            if extra_state:
                state["extra_state"] = extra_state
            if is_best:
                state["is_best"] = True

            state_path = os.path.join(checkpoint_dir, "training_state.pt")
            
            # Write to atomic temp file then rename
            temp_fd, temp_path = tempfile.mkstemp(dir=checkpoint_dir, suffix=".tmp")
            os.close(temp_fd)
            try:
                torch.save(state, temp_path)
                os.replace(temp_path, state_path)
            except Exception:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise

            # Write manifest file
            manifest = {
                "step": step,
                "epoch": epoch,
                "is_best": is_best,
                "metrics": metrics or {},
                "timestamp": time.time(),
            }
            with open(os.path.join(checkpoint_dir, "checkpoint_manifest.json"), "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            
            logger.debug(f"Checkpoint saved successfully to {checkpoint_dir}")
            return checkpoint_dir
            
        except Exception as e:
            logger.error(f"Error saving checkpoint '{filename}': {e}", exc_info=True)
            raise CheckpointError(f"Failed to save checkpoint '{filename}': {e}") from e

    def load(self, checkpoint_path: str) -> Dict[str, Any]:
        """
        Load checkpoint and restore training states.
        """
        try:
            if os.path.isdir(checkpoint_path):
                state_path = os.path.join(checkpoint_path, "training_state.pt")
                if not os.path.exists(state_path):
                    state_path = checkpoint_path + ".pt" if not checkpoint_path.endswith(".pt") else checkpoint_path
            else:
                state_path = checkpoint_path
            
            if not os.path.exists(state_path):
                raise CheckpointError(f"Checkpoint state file not found: {state_path}")
            
            try:
                state = torch.load(state_path, map_location="cpu", weights_only=False)
            except TypeError:
                state = torch.load(state_path, map_location="cpu")
            base_model = self._get_base_model()
            
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

    def prune_checkpoints(self) -> None:
        """Prune old step checkpoints keeping only the most recent keep_last items."""
        keep_last = getattr(self.checkpoint_config, "keep_last", 3)
        if keep_last <= 0:
            return
            
        try:
            entries = os.listdir(self.output_dir)
            step_entries = []
            
            for entry in entries:
                if entry.startswith("step_"):
                    step_str = entry.replace("step_", "").replace(".pt", "")
                    if step_str.isdigit():
                        step_entries.append((int(step_str), entry))
            
            step_entries.sort(key=lambda x: x[0])
            excess_count = len(step_entries) - keep_last
            
            if excess_count > 0:
                for idx in range(excess_count):
                    step_num, entry_name = step_entries[idx]
                    full_path = os.path.join(self.output_dir, entry_name)
                    try:
                        if os.path.isdir(full_path):
                            shutil.rmtree(full_path)
                        else:
                            os.remove(full_path)
                        logger.debug(f"Pruned old checkpoint step {step_num}: {entry_name}")
                    except Exception as e:
                        logger.warning(f"Could not prune checkpoint {entry_name}: {e}")
                        
        except Exception as e:
            logger.warning(f"Error during checkpoint pruning: {e}")


__all__ = ["CheckpointManager"]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.trainers."):
        sys.modules["trainers." + __name__[len("optimization_core.trainers."):]] = _mod
    elif __name__.startswith("trainers."):
        sys.modules["optimization_core.trainers." + __name__[len("trainers."):]] = _mod
