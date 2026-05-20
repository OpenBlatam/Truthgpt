"""
Evaluation module for model assessment.
"""
import math
import logging
import torch
from typing import Dict, Any, Optional
from torch.utils.data import DataLoader
from torch.cuda.amp import autocast

from core.interfaces import BaseEvaluator

logger = logging.getLogger(__name__)


class Evaluator(BaseEvaluator):
    """
    Evaluator for model assessment.
    Implements BaseEvaluator interface.
    """
    
    def __init__(
        self,
        use_amp: bool = False,
        amp_dtype: Optional[torch.dtype] = None,
        device: Optional[torch.device] = None,
    ):
        """
        Initialize evaluator.
        
        Args:
            use_amp: Use automatic mixed precision
            amp_dtype: AMP dtype (bf16/fp16)
            device: Device for evaluation
        """
        self.use_amp = use_amp
        self.amp_dtype = amp_dtype
        self.device = device
    
    def evaluate(
        self,
        model: torch.nn.Module,
        data_loader: DataLoader,
        device: torch.device,
        **kwargs
    ) -> Dict[str, float]:
        """
        Evaluate model on data.
        
        Args:
            model: Model to evaluate
            data_loader: Data loader
            device: Device for evaluation
        
        Returns:
            Dictionary of metric names to values
        """
        model.eval()
        total_loss = 0.0
        count = 0
        
        try:
            with torch.no_grad():
                for batch in data_loader:
                    try:
                        # Move batch to device
                        batch = {k: v.to(device, non_blocking=True) for k, v in batch.items()}
                        
                        # Forward pass with AMP if enabled
                        with autocast(enabled=self.use_amp, dtype=self.amp_dtype):
                            outputs = model(**batch)
                            loss = outputs.loss
                            
                            # Handle DataParallel
                            if isinstance(loss, dict):
                                loss = loss.get("loss", list(loss.values())[0])
                            elif hasattr(loss, "mean"):
                                loss = loss.mean()
                        
                        # Check for finite loss
                        if torch.isfinite(loss):
                            total_loss += float(loss.detach().item())
                            count += 1
                        else:
                            logger.warning(f"Non-finite loss encountered: {loss.item()}")
                            
                    except Exception as e:
                        logger.error(f"Error in evaluation batch: {e}", exc_info=True)
                        continue
        
        finally:
            model.train()
        
        if count == 0:
            logger.warning("No valid evaluation samples processed")
            return {"loss": float("inf"), "perplexity": float("inf")}
        
        avg_loss = total_loss / count
        perplexity = math.exp(min(20.0, max(-20.0, avg_loss))) if avg_loss == avg_loss else float("inf")
        
        metrics = {
            "loss": avg_loss,
            "perplexity": perplexity,
        }
        
        logger.debug(f"Evaluation completed: loss={avg_loss:.4f}, ppl={perplexity:.2f}")
        return metrics
    
    def compute_metrics(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor,
        **kwargs
    ) -> Dict[str, float]:
        """
        Compute evaluation metrics.
        
        Args:
            predictions: Model predictions
            targets: Ground truth targets
            **kwargs: Additional arguments
        
        Returns:
            Dictionary of metric names to values
        """
        # Compute cross-entropy loss
        loss_fn = torch.nn.CrossEntropyLoss(ignore_index=-100)
        loss = loss_fn(predictions.view(-1, predictions.size(-1)), targets.view(-1))
        
        perplexity = math.exp(min(20.0, max(-20.0, loss.item()))) if loss.item() == loss.item() else float("inf")
        
        return {
            "loss": float(loss.item()),
            "perplexity": perplexity,
        }


