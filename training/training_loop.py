"""
Training loop module - separated from trainer for modularity.
"""
import logging
import time
from typing import Dict, Any, Optional, Callable
import torch
from torch.utils.data import DataLoader
from torch.cuda.amp import autocast, GradScaler

from core.interfaces import BaseTrainer

logger = logging.getLogger(__name__)


class TrainingLoop(BaseTrainer):
    """
    Training loop implementation.
    Handles forward pass, backward pass, and optimization.
    """
    
    def __init__(
        self,
        use_amp: bool = False,
        amp_dtype: Optional[torch.dtype] = None,
        max_grad_norm: float = 1.0,
        grad_accum_steps: int = 1,
    ):
        """
        Initialize training loop.
        
        Args:
            use_amp: Use automatic mixed precision
            amp_dtype: AMP dtype
            max_grad_norm: Maximum gradient norm for clipping
            grad_accum_steps: Gradient accumulation steps
        """
        self.use_amp = use_amp
        self.amp_dtype = amp_dtype
        self.max_grad_norm = max_grad_norm
        self.grad_accum_steps = grad_accum_steps
    
    def train_step(
        self,
        model: torch.nn.Module,
        batch: Dict[str, torch.Tensor],
        optimizer: torch.optim.Optimizer,
        scaler: GradScaler,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform a single training step.
        
        Args:
            model: Model to train
            batch: Input batch
            optimizer: Optimizer
            scaler: GradScaler for mixed precision
            **kwargs: Additional arguments
        
        Returns:
            Dictionary with step metrics
        """
        # Forward pass with AMP
        with autocast(enabled=self.use_amp, dtype=self.amp_dtype):
            outputs = model(**batch)
            loss = outputs.loss / self.grad_accum_steps
            
            # Handle DataParallel
            if isinstance(loss, dict):
                loss = loss.get("loss", list(loss.values())[0]) / self.grad_accum_steps
            elif hasattr(loss, "mean"):
                loss = loss.mean() / self.grad_accum_steps
        
        # Check for finite loss
        if not torch.isfinite(loss):
            logger.warning(f"Non-finite loss encountered: {loss.item()}")
            optimizer.zero_grad(set_to_none=True)
            return {"loss": float("inf"), "skipped": True}
        
        # Backward pass
        scaler.scale(loss).backward()
        
        # Gradient accumulation check
        step = kwargs.get("step", 0)
        if step % self.grad_accum_steps == 0:
            # Unscale gradients
            scaler.unscale_(optimizer)
            
            # Gradient clipping
            model_for_clipping = (
                model.module if isinstance(model, torch.nn.DataParallel) else model
            )
            torch.nn.utils.clip_grad_norm_(
                model_for_clipping.parameters(),
                self.max_grad_norm
            )
            
            # Optimizer step
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)
        
        return {
            "loss": float(loss.item() * self.grad_accum_steps),
            "skipped": False,
        }
    
    def train_epoch(
        self,
        model: torch.nn.Module,
        train_loader: DataLoader,
        optimizer: torch.optim.Optimizer,
        scheduler: Any,
        scaler: GradScaler,
        step_callback: Optional[Callable] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Train for one epoch.
        
        Args:
            model: Model to train
            train_loader: Training data loader
            optimizer: Optimizer
            scheduler: Learning rate scheduler
            scaler: GradScaler
            step_callback: Optional callback after each step
            **kwargs: Additional arguments
        
        Returns:
            Dictionary with epoch metrics
        """
        model.train()
        total_loss = 0.0
        num_steps = 0
        start_time = time.perf_counter()
        
        for step, batch in enumerate(train_loader, start=1):
            try:
                # Training step
                step_metrics = self.train_step(
                    model=model,
                    batch=batch,
                    optimizer=optimizer,
                    scaler=scaler,
                    step=step,
                    **kwargs
                )
                
                if step_metrics.get("skipped", False):
                    continue
                
                total_loss += step_metrics["loss"]
                num_steps += 1
                
                # Scheduler step (after optimizer step)
                if step % self.grad_accum_steps == 0:
                    scheduler.step()
                
                # Step callback
                if step_callback:
                    step_callback(
                        step=step,
                        metrics=step_metrics,
                        learning_rate=scheduler.get_last_lr()[0] if scheduler else None,
                    )
                
            except Exception as e:
                logger.error(f"Error in training step {step}: {e}", exc_info=True)
                optimizer.zero_grad(set_to_none=True)
                continue
        
        elapsed = time.perf_counter() - start_time
        avg_loss = total_loss / max(1, num_steps)
        
        return {
            "loss": avg_loss,
            "num_steps": num_steps,
            "elapsed_time": elapsed,
        }
    
    def should_stop_early(
        self,
        current_metric: float,
        best_metric: float,
        patience: int,
        **kwargs
    ) -> bool:
        """
        Determine if training should stop early.
        
        Args:
            current_metric: Current metric value
            best_metric: Best metric value seen
            patience: Early stopping patience
            **kwargs: Additional arguments
        
        Returns:
            True if should stop early
        """
        # For metrics where lower is better (loss, perplexity)
        if current_metric >= best_metric:
            return False
        
        # Check patience
        bad_epochs = kwargs.get("bad_epochs", 0)
        return bad_epochs >= patience


