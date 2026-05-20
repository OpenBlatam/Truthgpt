"""
Evaluator - Handles model evaluation.

Separated from trainer for better modularity.
"""
import math
import logging
from typing import Dict, Optional
import torch
from torch.utils.data import DataLoader
from torch.cuda.amp import autocast

from trainers.config import TrainingConfig

logger = logging.getLogger(__name__)


class Evaluator:
    """
    Handles model evaluation.
    
    Responsibilities:
    - Evaluate model on validation set
    - Calculate metrics (loss, perplexity)
    - Support EMA weights during evaluation
    """
    
    def __init__(
        self,
        training_config: TrainingConfig,
        model: torch.nn.Module,
        val_loader: DataLoader,
        device: torch.device,
        use_amp: bool,
        ema_manager: Optional[object] = None,
    ):
        """
        Initialize Evaluator.
        
        Args:
            training_config: Training configuration
            model: Model to evaluate
            val_loader: Validation DataLoader
            device: Device for evaluation
            use_amp: Whether to use mixed precision
            ema_manager: Optional EMA manager for using EMA weights
        """
        self.training_config = training_config
        self.model = model
        self.val_loader = val_loader
        self.device = device
        self.use_amp = use_amp
        self.ema_manager = ema_manager
    
    def _get_amp_dtype(self):
        """Get AMP dtype."""
        if self.training_config.mixed_precision == "bf16":
            return torch.bfloat16
        if self.training_config.mixed_precision == "fp16":
            return torch.float16
        return None
    
    @torch.no_grad()
    def evaluate(self) -> Dict[str, float]:
        """
        Evaluate model on validation set.
        
        Returns:
            Dictionary with evaluation metrics (loss, perplexity)
        """
        # Apply EMA weights if available
        if self.ema_manager and self.ema_manager.ema_config.enabled:
            self.ema_manager.apply_ema()
        
        self.model.eval()
        total_loss = 0.0
        count = 0
        
        try:
            for batch in self.val_loader:
                try:
                    # Move batch to device
                    batch = {k: v.to(self.device, non_blocking=True) for k, v in batch.items()}
                    
                    # Forward pass
                    with autocast(enabled=self.use_amp, dtype=self._get_amp_dtype()):
                        outputs = self.model(**batch)
                        loss = outputs.loss
                        
                        # Handle DataParallel
                        if isinstance(loss, dict):
                            loss = loss.get("loss", list(loss.values())[0])
                        elif hasattr(loss, "mean"):
                            loss = loss.mean()
                    
                    # Accumulate if finite
                    if torch.isfinite(loss):
                        total_loss += float(loss.detach().item())
                        count += 1
                    else:
                        logger.warning(f"Non-finite loss encountered: {loss.item()}")
                        
                except Exception as e:
                    logger.error(f"Error in evaluation batch: {e}", exc_info=True)
                    continue
        finally:
            self.model.train()
            # Restore from EMA if used
            if self.ema_manager and self.ema_manager.ema_config.enabled:
                self.ema_manager.restore_from_ema()
        
        if count == 0:
            logger.warning("No valid evaluation samples processed")
            return {"loss": float("inf"), "perplexity": float("inf")}
        
        avg_loss = total_loss / count
        perplexity = math.exp(min(20.0, max(-20.0, avg_loss))) if avg_loss == avg_loss else float("inf")
        
        logger.debug(f"Evaluation: loss={avg_loss:.4f}, ppl={perplexity:.2f}, samples={count}")
        
        return {
            "loss": avg_loss,
            "perplexity": perplexity,
        }
    
    def select_best_metric(self, metrics: Dict[str, float]) -> float:
        """
        Select best metric based on configuration.
        
        Args:
            metrics: Dictionary of metrics
            
        Returns:
            Value of best metric
        """
        if self.training_config.select_best_by == "ppl":
            return metrics.get("perplexity", float("inf"))
        return metrics.get("loss", float("inf"))



