"""
Checkpoint Manager - Handles model checkpointing.

Separated from trainer for better modularity.
"""
import os
import logging
from typing import Optional, Dict, Any
import torch
import torch.nn as nn

from trainers.config import CheckpointConfig

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Manages model checkpointing.
    
    Responsibilities:
    - Save checkpoints (best, last, periodic)
    - Load checkpoints for resuming
    - Prune old checkpoints
    - Manage checkpoint state
    """
    
    def __init__(
        self,
        checkpoint_config: CheckpointConfig,
        output_dir: str,
        model: nn.Module,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[object] = None,
        scaler: Optional[torch.cuda.amp.GradScaler] = None,
        tokenizer = None,
    ):
        """
        Initialize CheckpointManager.
        
        Args:
            checkpoint_config: Checkpoint configuration
            output_dir: Output directory for checkpoints
            model: Model to save
            optimizer: Optimizer state to save
            scheduler: Scheduler state to save
            scaler: GradScaler state to save
            tokenizer: Tokenizer to save
        """
        self.checkpoint_config = checkpoint_config
        self.output_dir = output_dir
        self.model = model
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.scaler = scaler
        self.tokenizer = tokenizer
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def _get_base_model(self) -> nn.Module:
        """Get base model (handles parallel wrappers)."""
        model = self.model
        if isinstance(model, (nn.DataParallel, nn.parallel.DistributedDataParallel)):
            model = model.module
        if hasattr(model, "module"):
            model = model.module
        return model
    
    def save(
        self,
        filename: str,
        step: int = 0,
        is_best: bool = False,
        metrics: Optional[Dict[str, float]] = None,
    ) -> str:
        """
        Save checkpoint.
        
        Args:
            filename: Checkpoint filename
            step: Current training step
            is_best: Whether this is the best checkpoint
            metrics: Optional metrics to save
            
        Returns:
            Path to saved checkpoint
        """
        try:
            # Create checkpoint directory
            checkpoint_path = os.path.join(self.output_dir, filename)
            if filename.endswith('.pt'):
                # For .pt files, create directory with same name
                checkpoint_dir = checkpoint_path.replace('.pt', '')
            else:
                checkpoint_dir = checkpoint_path
            
            os.makedirs(checkpoint_dir, exist_ok=True)
            
            # Get base model
            base_model = self._get_base_model()
            
            # Save model and tokenizer using HuggingFace format
            try:
                base_model.save_pretrained(
                    checkpoint_dir,
                    safe_serialization=self.checkpoint_config.save_safetensors,
                )
                if self.tokenizer is not None:
                    self.tokenizer.save_pretrained(checkpoint_dir)
            except Exception as e:
                logger.warning(f"Could not save pretrained format: {e}. Saving state dict only.")
            
            # Save training state
            state = {
                "step": step,
                "model_state_dict": base_model.state_dict(),
            }
            
            if self.optimizer is not None:
                state["optimizer_state_dict"] = self.optimizer.state_dict()
            if self.scheduler is not None:
                state["scheduler_state_dict"] = self.scheduler.state_dict()
            if self.scaler is not None:
                state["scaler_state_dict"] = self.scaler.state_dict()
            if metrics:
                state["metrics"] = metrics
            if is_best:
                state["is_best"] = True
            
            # Save state dict
            state_path = os.path.join(checkpoint_dir, "training_state.pt")
            if not filename.endswith('.pt'):
                state_path = os.path.join(self.output_dir, f"{filename}.pt")
            
            torch.save(state, state_path)
            
            logger.debug(f"Checkpoint saved: {checkpoint_dir}")
            return checkpoint_dir
            
        except Exception as e:
            logger.error(f"Error saving checkpoint {filename}: {e}", exc_info=True)
            raise
    
    def load(
        self,
        checkpoint_path: str,
    ) -> Dict[str, Any]:
        """
        Load checkpoint.
        
        Args:
            checkpoint_path: Path to checkpoint
            
        Returns:
            Dictionary with loaded state
        """
        try:
            # Try loading as directory first
            if os.path.isdir(checkpoint_path):
                state_path = os.path.join(checkpoint_path, "training_state.pt")
                if not os.path.exists(state_path):
                    # Try loading as .pt file
                    state_path = checkpoint_path + ".pt" if not checkpoint_path.endswith('.pt') else checkpoint_path
            else:
                state_path = checkpoint_path
            
            if not os.path.exists(state_path):
                raise FileNotFoundError(f"Checkpoint not found: {state_path}")
            
            state = torch.load(state_path, map_location="cpu")
            
            # Load model state
            base_model = self._get_base_model()
            if "model_state_dict" in state:
                base_model.load_state_dict(state["model_state_dict"])
            else:
                # Fallback: load entire state as model state
                base_model.load_state_dict(state)
            
            # Load optimizer if available
            if self.optimizer is not None and "optimizer_state_dict" in state:
                self.optimizer.load_state_dict(state["optimizer_state_dict"])
            
            # Load scheduler if available
            if self.scheduler is not None and "scheduler_state_dict" in state:
                self.scheduler.load_state_dict(state["scheduler_state_dict"])
            
            # Load scaler if available
            if self.scaler is not None and "scaler_state_dict" in state:
                self.scaler.load_state_dict(state["scaler_state_dict"])
            
            step = state.get("step", state.get("global_step", 0))
            logger.info(f"Loaded checkpoint from {checkpoint_path} at step {step}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error loading checkpoint {checkpoint_path}: {e}", exc_info=True)
            raise
    
    def prune_checkpoints(self) -> None:
        """Prune old checkpoints, keeping only the most recent ones."""
        try:
            files = [
                f for f in os.listdir(self.output_dir)
                if f.startswith("step_") and f.endswith(".pt")
            ]
            files.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))
            
            excess = max(0, len(files) - max(0, self.checkpoint_config.keep_last))
            for i in range(excess):
                try:
                    file_path = os.path.join(self.output_dir, files[i])
                    os.remove(file_path)
                    logger.debug(f"Pruned checkpoint: {files[i]}")
                except Exception as e:
                    logger.warning(f"Could not remove {files[i]}: {e}")
        except Exception as e:
            logger.warning(f"Error pruning checkpoints: {e}")



