"""
Evaluator - Handles model evaluation.

Separated from trainer for better modularity, clean error handling, and testability.
"""
import math
import logging
from typing import Dict, Optional, Any
import torch
from torch.utils.data import DataLoader

from .config import TrainingConfig
from .interfaces import BaseEvaluator
from .exceptions import EvaluationError

logger = logging.getLogger(__name__)


def get_autocast_context(device_type: str, enabled: bool, dtype: Optional[torch.dtype] = None):
    """
    Get PyTorch 2.x unified torch.amp.autocast context with PyTorch 1.x fallback.
    """
    if not enabled:
        class DummyContextManager:
            def __enter__(self): return None
            def __exit__(self, exc_type, exc_val, exc_tb): pass
        return DummyContextManager()

    if hasattr(torch, "amp") and hasattr(torch.amp, "autocast"):
        dev = "cuda" if device_type == "cuda" else ("cpu" if device_type == "cpu" else "cuda")
        return torch.amp.autocast(device_type=dev, enabled=enabled, dtype=dtype)
    else:
        from torch.cuda.amp import autocast
        return autocast(enabled=enabled, dtype=dtype)


class Evaluator(BaseEvaluator):
    """
    Handles model evaluation loop and metric calculation.
    
    Responsibilities:
    - Evaluate model performance on validation DataLoader
    - Compute validation loss and perplexity
    - Manage EMA weight application and restoration
    - Robust error boundary per batch
    """
    
    def __init__(
        self,
        training_config: TrainingConfig,
        model: torch.nn.Module,
        val_loader: DataLoader,
        device: torch.device,
        use_amp: bool = False,
        ema_manager: Optional[Any] = None,
    ) -> None:
        """
        Initialize Evaluator.
        
        Args:
            training_config: Training configuration
            model: PyTorch model instance
            val_loader: Validation dataset DataLoader
            device: Computing device
            use_amp: Whether mixed precision is enabled
            ema_manager: Optional EMAManager for evaluating on EMA weights
        """
        if model is None:
            raise EvaluationError("Model cannot be None for Evaluator.")
        if val_loader is None:
            raise EvaluationError("val_loader cannot be None for Evaluator.")
        self.training_config = training_config
        self.model = model
        self.val_loader = val_loader
        self.device = device
        self.use_amp = use_amp
        self.ema_manager = ema_manager
    
    def _get_amp_dtype(self) -> Optional[torch.dtype]:
        """Get target float precision dtype."""
        mixed_prec = getattr(self.training_config, "mixed_precision", "none")
        if mixed_prec == "bf16":
            return torch.bfloat16
        if mixed_prec == "fp16":
            return torch.float16
        return None
    
    @torch.no_grad()
    def evaluate(self) -> Dict[str, float]:
        """
        Execute evaluation loop on validation dataset.
        
        Returns:
            Dictionary containing metrics ('loss', 'perplexity', 'samples')
        """
        # Apply EMA weights if enabled
        ema_enabled = self.ema_manager and getattr(getattr(self.ema_manager, "ema_config", None), "enabled", True)
        if ema_enabled:
            self.ema_manager.apply_ema()
        
        self.model.eval()
        total_loss = 0.0
        valid_batches = 0
        total_samples = 0
        
        try:
            for batch in self.val_loader:
                try:
                    if isinstance(batch, dict):
                        batch = {k: v.to(self.device, non_blocking=True) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
                        batch_len = next((len(v) for v in batch.values() if isinstance(v, torch.Tensor)), 1)
                    elif isinstance(batch, (list, tuple)):
                        batch = [v.to(self.device, non_blocking=True) if isinstance(v, torch.Tensor) else v for v in batch]
                        batch_len = len(batch[0]) if len(batch) > 0 and isinstance(batch[0], torch.Tensor) else 1
                    else:
                        batch = batch.to(self.device, non_blocking=True)
                        batch_len = len(batch)
                    
                    with get_autocast_context(self.device.type, self.use_amp, self._get_amp_dtype()):
                        if isinstance(batch, dict):
                            outputs = self.model(**batch)
                        elif isinstance(batch, (list, tuple)):
                            outputs = self.model(*batch)
                        else:
                            outputs = self.model(batch)
                            
                        loss = getattr(outputs, "loss", outputs)
                        if isinstance(loss, dict):
                            loss = loss.get("loss", list(loss.values())[0])
                        elif hasattr(loss, "mean"):
                            loss = loss.mean()
                    
                    if torch.isfinite(loss):
                        total_loss += float(loss.detach().item())
                        valid_batches += 1
                        total_samples += batch_len
                    else:
                        logger.warning(f"Non-finite loss encountered in validation: {loss.item()}")
                        
                except Exception as e:
                    logger.error(f"Error evaluating batch: {e}", exc_info=True)
                    continue
        finally:
            self.model.train()
            if ema_enabled:
                self.ema_manager.restore_from_ema()
        
        if valid_batches == 0:
            logger.warning("No valid evaluation samples processed")
            return {"loss": float("inf"), "perplexity": float("inf"), "samples": 0.0}
        
        avg_loss = total_loss / valid_batches
        try:
            perplexity = math.exp(min(20.0, max(-20.0, avg_loss)))
        except Exception:
            perplexity = float("inf")
            
        logger.debug(f"Evaluation complete: loss={avg_loss:.4f}, perplexity={perplexity:.2f}, batches={valid_batches}")
        
        return {
            "loss": avg_loss,
            "perplexity": perplexity,
            "samples": float(total_samples),
        }
    
    def select_best_metric(self, metrics: Dict[str, float]) -> float:
        """
        Select comparative metric based on configuration setting.
        
        Args:
            metrics: Dictionary of metric results
            
        Returns:
            Scalar metric value for best model comparison
        """
        select_by = getattr(self.training_config, "select_best_by", "loss")
        if select_by in ("ppl", "perplexity"):
            return metrics.get("perplexity", float("inf"))
        return metrics.get("loss", float("inf"))


__all__ = ["Evaluator", "get_autocast_context"]
