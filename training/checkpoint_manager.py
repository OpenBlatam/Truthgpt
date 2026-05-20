"""
Checkpoint management module for saving and loading training state.
"""
import os
import logging
import torch
import torch.nn as nn
from typing import Dict, Any, Optional
from pathlib import Path

from core.interfaces import BaseCheckpointManager

logger = logging.getLogger(__name__)


class CheckpointManager(BaseCheckpointManager):
    """
    Manages training checkpoints.
    Implements BaseCheckpointManager interface.
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize checkpoint manager.
        
        Args:
            output_dir: Output directory for checkpoints
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_checkpoint(
        self,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        scheduler: Any,
        step: int,
        path: str,
        tokenizer: Optional[Any] = None,
        scaler: Optional[Any] = None,
        ema_state: Optional[Dict[str, torch.Tensor]] = None,
        save_safetensors: bool = True,
        **kwargs
    ) -> None:
        """
        Save training checkpoint.
        
        Args:
            model: Model to save
            optimizer: Optimizer state
            scheduler: Scheduler state
            step: Training step
            path: Save path (directory)
            tokenizer: Optional tokenizer
            scaler: Optional GradScaler
            ema_state: Optional EMA state
            save_safetensors: Use SafeTensors format
            **kwargs: Additional save arguments
        """
        try:
            save_path = Path(path)
            save_path.mkdir(parents=True, exist_ok=True)
            
            # Get base model (handle DataParallel)
            model_to_save = model
            if isinstance(model, nn.DataParallel):
                model_to_save = model.module
            elif hasattr(model, "module"):
                model_to_save = model.module
            
            # Save model and tokenizer
            model_to_save.save_pretrained(save_path, safe_serialization=save_safetensors)
            if tokenizer:
                tokenizer.save_pretrained(save_path)
            
            # Save training state
            checkpoint_state = {
                "global_step": step,
                "model_state_dict": model_to_save.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
            }
            
            if scaler:
                checkpoint_state["scaler_state_dict"] = scaler.state_dict()
            
            if ema_state:
                checkpoint_state["ema_state_dict"] = ema_state
            
            # Save training state
            state_path = save_path / "training_state.pt"
            torch.save(checkpoint_state, state_path)
            
            logger.info(f"Checkpoint saved to {save_path} at step {step}")
            
        except Exception as e:
            logger.error(f"Error saving checkpoint to {path}: {e}", exc_info=True)
            raise
    
    def load_checkpoint(
        self,
        path: str,
        model: torch.nn.Module,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[Any] = None,
        scaler: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Load training checkpoint.
        
        Args:
            path: Checkpoint path (directory)
            model: Model to load state into
            optimizer: Optional optimizer
            scheduler: Optional scheduler
            scaler: Optional GradScaler
            **kwargs: Additional load arguments
        
        Returns:
            Dictionary with loaded state (step, epoch, etc.)
        """
        try:
            checkpoint_path = Path(path)
            
            # Load model (if using transformers)
            if (checkpoint_path / "config.json").exists():
                from transformers import AutoModelForCausalLM
                device = next(model.parameters()).device
                loaded_model = AutoModelForCausalLM.from_pretrained(
                    str(checkpoint_path),
                    torch_dtype=next(model.parameters()).dtype,
                ).to(device)
                
                # Copy state dict
                base_model = model.module if isinstance(model, nn.DataParallel) else model
                base_model.load_state_dict(loaded_model.state_dict())
                logger.debug("Model weights loaded from checkpoint")
            
            # Load training state
            state_path = checkpoint_path / "training_state.pt"
            if state_path.exists():
                checkpoint = torch.load(state_path, map_location=next(model.parameters()).device)
                
                if optimizer and "optimizer_state_dict" in checkpoint:
                    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
                
                if scheduler and "scheduler_state_dict" in checkpoint:
                    scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
                
                if scaler and "scaler_state_dict" in checkpoint:
                    scaler.load_state_dict(checkpoint["scaler_state_dict"])
                
                step = checkpoint.get("global_step", checkpoint.get("step", 0))
                logger.info(f"Loaded checkpoint from {path} at step {step}")
                
                return {
                    "step": step,
                    "ema_state": checkpoint.get("ema_state_dict"),
                }
            else:
                logger.warning(f"Training state not found at {state_path}")
                return {"step": 0}
                
        except Exception as e:
            logger.error(f"Error loading checkpoint from {path}: {e}", exc_info=True)
            raise
    
    def find_latest_checkpoint(self, checkpoint_dir: Optional[str] = None) -> Optional[str]:
        """
        Find latest checkpoint in directory.
        
        Args:
            checkpoint_dir: Directory to search (defaults to output_dir)
        
        Returns:
            Path to latest checkpoint or None
        """
        search_dir = Path(checkpoint_dir) if checkpoint_dir else self.output_dir
        
        if not search_dir.exists():
            return None
        
        # Look for step_*.pt directories or named checkpoints
        candidates = []
        
        for item in search_dir.iterdir():
            if not item.is_dir():
                continue
            
            # Check if it's a checkpoint directory
            if (item / "config.json").exists() or (item / "training_state.pt").exists():
                # Try to extract step number from name
                if item.name.startswith("step_"):
                    try:
                        step = int(item.name.split("_")[1].split(".")[0])
                        candidates.append((step, str(item)))
                    except Exception:
                        pass
                elif item.name in ("best.pt", "last.pt"):
                    candidates.append((999999, str(item)))  # Named checkpoints preferred
        
        if not candidates:
            return None
        
        # Return most recent
        candidates.sort(reverse=True)
        return candidates[0][1]
    
    def prune_checkpoints(self, keep_last: int = 3) -> None:
        """
        Prune old checkpoints, keeping only the most recent ones.
        
        Args:
            keep_last: Number of checkpoints to keep
        """
        try:
            checkpoints = []
            
            for item in self.output_dir.iterdir():
                if not item.is_dir():
                    continue
                
                if item.name.startswith("step_") and (item / "config.json").exists():
                    try:
                        step = int(item.name.split("_")[1].split(".")[0])
                        checkpoints.append((step, item))
                    except Exception:
                        continue
            
            # Sort by step
            checkpoints.sort()
            
            # Remove old checkpoints
            excess = max(0, len(checkpoints) - keep_last)
            for i in range(excess):
                try:
                    checkpoints[i][1].rmdir()
                    logger.debug(f"Removed old checkpoint: {checkpoints[i][1]}")
                except Exception as e:
                    logger.warning(f"Failed to remove checkpoint {checkpoints[i][1]}: {e}")
                    
        except Exception as e:
            logger.error(f"Error pruning checkpoints: {e}", exc_info=True)


