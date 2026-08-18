"""
Unified Checkpoint Manager Module
==================================
Handles PyTorch model checkpointing, random number generator (RNG) state capture/restoration,
cross-platform atomic file operations, manifest queries, safe loading, and automated pruning.
"""

from __future__ import annotations

import hashlib
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

from .exceptions import CheckpointCorruptedError, CheckpointError, CheckpointNotFoundError
from .interfaces import BaseCheckpointManager
from .types import CheckpointConfig, CheckpointMetadata, CheckpointStrategy

logger = logging.getLogger(__name__)


class CheckpointManager(BaseCheckpointManager):
    """
    Manages PyTorch model checkpointing, RNG state preservation, manifest metadata,
    safe state-dict loading, atomic file writes, and automated pruning.
    """

    def __init__(
        self,
        output_dir: Union[str, Path] = "./checkpoints",
        checkpoint_config: Optional[Union[Dict[str, Any], CheckpointConfig, Any]] = None,
        model: Optional[nn.Module] = None,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[Any] = None,
        scaler: Optional[Any] = None,
        tokenizer: Optional[Any] = None,
        max_to_keep: Optional[int] = None,
        save_best: bool = True,
        metric_name: str = "loss",
        mode: str = "min",
        **kwargs: Any,
    ) -> None:
        """
        Initialize CheckpointManager.
        """
        self.output_path: Path = Path(output_dir)
        self.output_dir: str = str(self.output_path)
        self.checkpoint_config = checkpoint_config
        self.model: Optional[nn.Module] = model
        self.optimizer: Optional[torch.optim.Optimizer] = optimizer
        self.scheduler: Optional[Any] = scheduler
        self.scaler: Optional[Any] = scaler
        self.tokenizer: Optional[Any] = tokenizer

        # Extract config values
        if isinstance(checkpoint_config, CheckpointConfig):
            self.max_to_keep: int = checkpoint_config.max_to_keep
            self.save_best: bool = checkpoint_config.save_best
            self.metric_name: str = checkpoint_config.metric_name
            self.mode: str = checkpoint_config.mode.lower()
            self.strategy: CheckpointStrategy = checkpoint_config.strategy
        elif isinstance(checkpoint_config, dict):
            self.max_to_keep = checkpoint_config.get("max_to_keep", max_to_keep or 3)
            self.save_best = checkpoint_config.get("save_best", save_best)
            self.metric_name = checkpoint_config.get("metric_name", metric_name)
            self.mode = checkpoint_config.get("mode", mode).lower()
            self.strategy = CheckpointStrategy(checkpoint_config.get("strategy", CheckpointStrategy.KEEP_TOP_K))
        elif checkpoint_config is not None and hasattr(checkpoint_config, "keep_last"):
            self.max_to_keep = getattr(checkpoint_config, "keep_last", 3)
            self.save_best = getattr(checkpoint_config, "save_best", save_best)
            self.metric_name = getattr(checkpoint_config, "metric_name", metric_name)
            self.mode = getattr(checkpoint_config, "mode", mode).lower()
            self.strategy = CheckpointStrategy.KEEP_LAST_N
        else:
            self.max_to_keep = max_to_keep if max_to_keep is not None else 3
            self.save_best = save_best
            self.metric_name = metric_name
            self.mode = mode.lower()
            self.strategy = CheckpointStrategy.KEEP_TOP_K

        self.manifest_file = self.output_path / "manifest.json"
        self.best_metric: Optional[float] = None
        self.best_checkpoint_path: Optional[str] = None

        try:
            self.output_path.mkdir(parents=True, exist_ok=True)
            self._load_or_init_manifest()
        except Exception as e:
            logger.error(f"Failed to create checkpoint directory '{self.output_path}': {e}")
            raise CheckpointError(f"Cannot initialize directory '{self.output_path}': {e}") from e

    def _load_or_init_manifest(self) -> Dict[str, Any]:
        """Load manifest from disk or initialize a new empty one."""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.best_checkpoint_path = data.get("best_checkpoint")
                    self.best_metric = data.get("best_metric")
                    return data
            except Exception as e:
                logger.warning(f"Could not parse manifest {self.manifest_file}: {e}")
        return {"checkpoints": [], "best_checkpoint": None, "best_metric": None}

    def _save_manifest(self, manifest_data: Dict[str, Any]) -> None:
        """Atomically persist manifest data to disk."""
        tmp_file = self.output_path / f"manifest_{int(time.time()*1000)}.tmp"
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2)
            shutil.move(str(tmp_file), str(self.manifest_file))
        except Exception as e:
            if tmp_file.exists():
                tmp_file.unlink(missing_ok=True)
            logger.error(f"Failed to save manifest file: {e}")

    def _get_base_model(self, model: Optional[nn.Module] = None) -> nn.Module:
        """
        Unwrap parallel or distributed model containers to access the underlying PyTorch module.
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
        """
        try:
            if "python" in rng_state:
                random.setstate(rng_state["python"])
            if "torch" in rng_state:
                torch.set_rng_state(rng_state["torch"])
            if "torch_cuda" in rng_state and torch.cuda.is_available():
                torch.cuda.set_rng_state_all(rng_state["torch_cuda"])
            if "numpy" in rng_state:
                try:
                    import numpy as np
                    np.random.set_state(rng_state["numpy"])
                except ImportError:
                    pass
        except Exception as e:
            logger.warning(f"Error restoring RNG state: {e}")

    def _clean_state_dict_keys(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Strip wrapping prefixes (_orig_mod., module.) from state dict keys."""
        cleaned: Dict[str, Any] = {}
        for k, v in state_dict.items():
            new_key = k
            for prefix in ("_orig_mod.", "module."):
                if new_key.startswith(prefix):
                    new_key = new_key[len(prefix):]
            cleaned[new_key] = v
        return cleaned

    def save(
        self,
        epoch: int = 0,
        step: int = 0,
        metrics: Optional[Dict[str, float]] = None,
        checkpoint_name: Optional[str] = None,
        filename: Optional[str] = None,
        is_best: bool = False,
        model: Optional[nn.Module] = None,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[Any] = None,
        scaler: Optional[Any] = None,
        **kwargs: Any,
    ) -> str:
        """
        Atomically save a checkpoint to disk with model weights, optimizer state, manifest, and RNG states.

        Returns:
            Absolute directory or file path of the saved checkpoint.
        """
        target_model = self._get_base_model(model)
        target_opt = optimizer or self.optimizer
        target_sched = scheduler or self.scheduler
        target_scaler = scaler or self.scaler

        metrics = metrics or {}
        metric_val = metrics.get(self.metric_name)

        # Determine best status
        if metric_val is not None and not is_best:
            if self.best_metric is None:
                is_best = True
            elif self.mode == "min" and metric_val < self.best_metric:
                is_best = True
            elif self.mode == "max" and metric_val > self.best_metric:
                is_best = True

        if is_best and metric_val is not None:
            self.best_metric = metric_val

        folder_name = filename or checkpoint_name or f"checkpoint_epoch_{epoch:04d}_step_{step:06d}"
        if folder_name.endswith(".pt"):
            folder_name = folder_name[:-3]
        elif folder_name.endswith(".pth"):
            folder_name = folder_name[:-4]

        save_dir = self.output_path / folder_name
        save_dir.mkdir(parents=True, exist_ok=True)

        # Build payload
        state: Dict[str, Any] = {
            "epoch": epoch,
            "step": step,
            "model_state_dict": target_model.state_dict(),
            "metrics": metrics,
            "metric_value": metric_val,
            "metric_name": self.metric_name,
            "is_best": is_best,
            "timestamp": time.time(),
            "rng_state": self._capture_rng_state(),
        }

        if target_opt is not None and hasattr(target_opt, "state_dict"):
            state["optimizer_state_dict"] = target_opt.state_dict()
        if target_sched is not None and hasattr(target_sched, "state_dict"):
            state["scheduler_state_dict"] = target_sched.state_dict()
        if target_scaler is not None and hasattr(target_scaler, "state_dict"):
            state["scaler_state_dict"] = target_scaler.state_dict()

        # Write training_state.pt atomically inside save_dir
        dest_state_file = save_dir / "training_state.pt"
        tmp_fd, tmp_file_str = tempfile.mkstemp(dir=str(save_dir), suffix=".tmp")
        os.close(tmp_fd)
        try:
            torch.save(state, tmp_file_str)
            shutil.move(tmp_file_str, str(dest_state_file))
        except Exception as e:
            if os.path.exists(tmp_file_str):
                os.remove(tmp_file_str)
            raise CheckpointError(f"Failed to write checkpoint to {dest_state_file}: {e}") from e

        # Write checkpoint_manifest.json inside save_dir
        manifest_path = save_dir / "checkpoint_manifest.json"
        manifest_meta = {
            "path": str(save_dir),
            "filename": folder_name,
            "epoch": epoch,
            "step": step,
            "metrics": metrics,
            "metric_value": metric_val,
            "is_best": is_best,
            "timestamp": state["timestamp"],
        }
        with open(manifest_path, "w", encoding="utf-8") as mf:
            json.dump(manifest_meta, mf, indent=2)

        # Update root manifest
        manifest = self._load_or_init_manifest()
        manifest["checkpoints"].append(manifest_meta)
        if is_best:
            manifest["best_checkpoint"] = str(save_dir)
            manifest["best_metric"] = metric_val
            best_dir = self.output_path / "best_model"
            try:
                if best_dir.exists():
                    shutil.rmtree(str(best_dir))
                shutil.copytree(str(save_dir), str(best_dir))
                self.best_checkpoint_path = str(save_dir)
            except Exception as e:
                logger.warning(f"Could not update best_model folder: {e}")

        self._save_manifest(manifest)

        # Prune if needed
        self.prune()

        return str(save_dir)

    def load(
        self,
        checkpoint_path: Optional[str] = None,
        load_best: bool = False,
        map_location: Optional[Union[str, torch.device]] = None,
        strict: bool = True,
        model: Optional[nn.Module] = None,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[Any] = None,
        scaler: Optional[Any] = None,
        restore_rng: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Load checkpoint from disk and restore model, optimizer, scheduler, and RNG state.
        """
        target_path = checkpoint_path
        if load_best:
            target_path = self.find_best_checkpoint(self.metric_name, self.mode)
        elif target_path is None:
            target_path = self.get_latest_checkpoint()

        if target_path is None:
            raise CheckpointNotFoundError(f"No checkpoint found to load in '{self.output_path}'")

        path_obj = Path(target_path)
        if not path_obj.exists():
            raise CheckpointNotFoundError(f"Checkpoint path not found: '{target_path}'")

        if path_obj.is_dir():
            state_file = path_obj / "training_state.pt"
            if not state_file.exists():
                # Search for any .pt file inside
                pt_files = list(path_obj.glob("*.pt"))
                if pt_files:
                    state_file = pt_files[0]
                else:
                    raise CheckpointNotFoundError(f"No state file found inside directory '{target_path}'")
        else:
            state_file = path_obj

        try:
            loc = map_location or ("cuda" if torch.cuda.is_available() else "cpu")
            checkpoint = torch.load(str(state_file), map_location=loc, weights_only=False)
        except Exception as e:
            raise CheckpointCorruptedError(f"Failed to load checkpoint file '{state_file}': {e}") from e

        # Restore model
        target_model = model or self.model
        if target_model is not None and "model_state_dict" in checkpoint:
            base_model = self._get_base_model(target_model)
            cleaned_sd = self._clean_state_dict_keys(checkpoint["model_state_dict"])
            base_model.load_state_dict(cleaned_sd, strict=strict)
            logger.info(f"Model parameters successfully restored from {state_file}")

        # Restore optimizer
        target_opt = optimizer or self.optimizer
        if target_opt is not None and "optimizer_state_dict" in checkpoint:
            try:
                target_opt.load_state_dict(checkpoint["optimizer_state_dict"])
            except Exception as e:
                logger.warning(f"Could not restore optimizer state: {e}")

        # Restore scheduler
        target_sched = scheduler or self.scheduler
        if target_sched is not None and "scheduler_state_dict" in checkpoint:
            try:
                target_sched.load_state_dict(checkpoint["scheduler_state_dict"])
            except Exception as e:
                logger.warning(f"Could not restore scheduler state: {e}")

        # Restore scaler
        target_scaler = scaler or self.scaler
        if target_scaler is not None and "scaler_state_dict" in checkpoint:
            try:
                target_scaler.load_state_dict(checkpoint["scaler_state_dict"])
            except Exception as e:
                logger.warning(f"Could not restore scaler state: {e}")

        # Restore RNG
        if restore_rng and "rng_state" in checkpoint:
            self._restore_rng_state(checkpoint["rng_state"])

        return checkpoint

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """Return list of all recorded checkpoints from manifest or filesystem scan."""
        manifest = self._load_or_init_manifest()
        ckpts = manifest.get("checkpoints", [])
        if ckpts:
            return ckpts

        # Scan filesystem for folders containing training_state.pt
        found = []
        for d in sorted(self.output_path.iterdir(), key=os.path.getmtime):
            if d.is_dir() and (d / "training_state.pt").exists():
                found.append({"path": str(d), "filename": d.name, "timestamp": os.path.getmtime(d)})
        return found

    def get_latest_checkpoint(self) -> Optional[str]:
        """Get path to the latest checkpoint directory."""
        ckpts = self.list_checkpoints()
        if ckpts:
            return ckpts[-1]["path"]
        dirs = [d for d in self.output_path.iterdir() if d.is_dir() and (d / "training_state.pt").exists()]
        if dirs:
            dirs.sort(key=os.path.getmtime)
            return str(dirs[-1])
        return None

    def get_latest_checkpoint_path(self) -> Optional[str]:
        """Alias for get_latest_checkpoint."""
        return self.get_latest_checkpoint()

    def find_best_checkpoint(self, metric_name: str = "loss", mode: str = "min") -> Optional[str]:
        """Find the checkpoint path with the best metric value."""
        manifest = self._load_or_init_manifest()
        ckpts = manifest.get("checkpoints", [])
        if not ckpts:
            best_dir = self.output_path / "best_model"
            if best_dir.exists():
                return str(best_dir)
            return self.get_latest_checkpoint()

        scored = [c for c in ckpts if c.get("metrics", {}).get(metric_name) is not None or c.get("metric_value") is not None]
        if not scored:
            return ckpts[-1]["path"]

        reverse = (mode.lower() == "max")
        def get_val(c):
            if metric_name in c.get("metrics", {}):
                return c["metrics"][metric_name]
            return c.get("metric_value", float("inf") if not reverse else float("-inf"))

        scored.sort(key=get_val, reverse=reverse)
        return scored[0]["path"]

    def get_best_checkpoint_path(self) -> Optional[str]:
        """Get best checkpoint path."""
        return self.find_best_checkpoint(self.metric_name, self.mode)

    def prune_checkpoints(self, keep_last: Optional[int] = None) -> List[str]:
        """Prune older checkpoints keeping the specified number of most recent."""
        limit = keep_last
        if limit is None and self.checkpoint_config is not None:
            limit = getattr(self.checkpoint_config, "keep_last", None)
        if limit is None:
            limit = self.max_to_keep

        return self.prune(max_to_keep=limit)

    def prune(self, max_to_keep: Optional[int] = None) -> List[str]:
        """
        Prune checkpoints according to retention limit.
        """
        limit = max_to_keep if max_to_keep is not None else self.max_to_keep
        if limit is None or limit <= 0:
            return []

        ckpts = self.list_checkpoints()
        if len(ckpts) <= limit:
            return []

        # Keep last `limit`
        to_keep_paths = set(c["path"] for c in ckpts[-limit:])
        best_path = self.get_best_checkpoint_path()
        if best_path:
            to_keep_paths.add(best_path)

        pruned_paths: List[str] = []
        remaining_ckpts: List[Dict[str, Any]] = []

        for c in ckpts:
            path_str = c["path"]
            if path_str not in to_keep_paths:
                p = Path(path_str)
                if p.exists():
                    try:
                        if p.is_dir():
                            shutil.rmtree(str(p))
                        else:
                            p.unlink(missing_ok=True)
                        pruned_paths.append(path_str)
                    except Exception as e:
                        logger.warning(f"Failed to delete pruned checkpoint {path_str}: {e}")
            else:
                remaining_ckpts.append(c)

        manifest = self._load_or_init_manifest()
        manifest["checkpoints"] = remaining_ckpts
        self._save_manifest(manifest)
        return pruned_paths

    def delete_checkpoint(self, checkpoint_path: str) -> bool:
        """Explicitly delete a specific checkpoint."""
        p = Path(checkpoint_path)
        if p.exists():
            if p.is_dir():
                shutil.rmtree(str(p))
            else:
                p.unlink(missing_ok=True)
        manifest = self._load_or_init_manifest()
        manifest["checkpoints"] = [c for c in manifest.get("checkpoints", []) if c["path"] != checkpoint_path]
        if manifest.get("best_checkpoint") == checkpoint_path:
            manifest["best_checkpoint"] = None
        self._save_manifest(manifest)
        return True
