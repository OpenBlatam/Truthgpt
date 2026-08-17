"""
Evaluation Module
=================
Model evaluation component supporting AMP autocast evaluation, device transfer,
multi-format loss extraction, custom metric evaluation, non-finite loss guardrails, and exception safety.
"""

import logging
import math
from typing import Any, Callable, Dict, Optional, Union
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

try:
    from torch.amp import autocast
except ImportError:
    from torch.cuda.amp import autocast  # type: ignore

try:
    from ..trainers.interfaces import BaseEvaluator
except ImportError:
    try:
        from optimization_core.trainers.interfaces import BaseEvaluator
    except ImportError:
        from abc import ABC, abstractmethod

        class BaseEvaluator(ABC):  # type: ignore
            """Fallback abstract base class for Evaluator."""
            pass

logger = logging.getLogger(__name__)


class EvaluationError(RuntimeError):
    """Exception raised when evaluation processing fails."""

    pass


class Evaluator(BaseEvaluator):
    """
    Evaluator for PyTorch model assessment.
    Implements BaseEvaluator interface.
    """

    def __init__(
        self,
        use_amp: bool = False,
        amp_dtype: Optional[torch.dtype] = None,
        device: Optional[Union[str, torch.device]] = None,
    ) -> None:
        """
        Initialize Evaluator.

        Args:
            use_amp: Use automatic mixed precision during evaluation.
            amp_dtype: AMP dtype (e.g. torch.bfloat16 or torch.float16).
            device: Target device for evaluation.
        """
        self.use_amp: bool = use_amp
        self.amp_dtype: Optional[torch.dtype] = amp_dtype
        self.device: Optional[torch.device] = torch.device(device) if device is not None else None

    def _get_autocast_context(self, eval_device: torch.device) -> Any:
        """
        Helper to obtain device-appropriate autocast context manager for evaluation.

        Args:
            eval_device: Target evaluation device.

        Returns:
            Autocast context manager.
        """
        if not self.use_amp:
            return autocast("cpu", enabled=False)
        device_type = eval_device.type if eval_device.type in ("cuda", "cpu", "xpu", "mps") else "cpu"
        try:
            return autocast(device_type=device_type, dtype=self.amp_dtype, enabled=True)
        except TypeError:
            return autocast(enabled=True, dtype=self.amp_dtype)

    def _to_device(self, batch: Any, device: torch.device) -> Any:
        """
        Recursively transfer Tensors in batch to target device, preserving non-tensor objects.

        Args:
            batch: Data batch (dict, list, tuple, set, or Tensor).
            device: Target torch device.

        Returns:
            Transformed batch on target device.
        """
        if isinstance(batch, torch.Tensor):
            return batch.to(device, non_blocking=True)
        elif isinstance(batch, dict):
            return {k: self._to_device(v, device) for k, v in batch.items()}
        elif isinstance(batch, list):
            return [self._to_device(v, device) for v in batch]
        elif isinstance(batch, tuple):
            return tuple(self._to_device(v, device) for v in batch)
        elif isinstance(batch, set):
            return {self._to_device(v, device) for v in batch}
        return batch

    def _extract_loss(self, outputs: Any) -> Any:
        """
        Extract loss tensor/value cleanly from model output.

        Args:
            outputs: Model forward pass output (Tensor, dict, or dataclass with loss attribute).

        Returns:
            Extracted loss tensor or scalar.
        """
        if hasattr(outputs, "loss") and getattr(outputs, "loss") is not None:
            loss = getattr(outputs, "loss")
        elif isinstance(outputs, dict) and "loss" in outputs:
            loss = outputs["loss"]
        elif isinstance(outputs, torch.Tensor):
            loss = outputs
        else:
            loss = outputs

        if isinstance(loss, dict):
            loss = loss.get("loss", list(loss.values())[0])
        if hasattr(loss, "mean") and getattr(loss, "dim", lambda: 0)() > 0:
            loss = loss.mean()

        return loss

    def evaluate(
        self,
        model: nn.Module,
        data_loader: DataLoader,
        device: Optional[Union[str, torch.device]] = None,
        custom_metric_fn: Optional[Callable[[Any, Any], Dict[str, float]]] = None,
        **kwargs: Any
    ) -> Dict[str, float]:
        """
        Evaluate model on data loader dataset.

        Args:
            model: Model to evaluate.
            data_loader: Data loader dataset.
            device: Optional evaluation device override.
            custom_metric_fn: Optional custom metric callback function taking (outputs, batch).
            **kwargs: Additional arguments.

        Returns:
            Dictionary of metric names to float values.

        Raises:
            EvaluationError: If model or data_loader is None.
        """
        if model is None:
            raise EvaluationError("Model cannot be None for evaluation.")
        if data_loader is None:
            raise EvaluationError("DataLoader cannot be None for evaluation.")

        eval_device = torch.device(device) if device is not None else self.device
        if eval_device is None:
            eval_device = next(model.parameters()).device if list(model.parameters()) else torch.device("cpu")

        model.eval()
        total_loss = 0.0
        count = 0
        custom_metrics_sum: Dict[str, float] = {}

        try:
            with torch.no_grad():
                for batch in data_loader:
                    try:
                        dev_batch = self._to_device(batch, eval_device)
                        with self._get_autocast_context(eval_device):
                            if isinstance(dev_batch, dict):
                                outputs = model(**dev_batch)
                            elif isinstance(dev_batch, (tuple, list)):
                                outputs = model(*dev_batch)
                            else:
                                outputs = model(dev_batch)

                            loss = self._extract_loss(outputs)

                        # Accumulate valid loss values
                        if torch.is_tensor(loss) and torch.isfinite(loss):
                            total_loss += float(loss.detach().item())
                            count += 1
                        elif isinstance(loss, (int, float)) and math.isfinite(loss):
                            total_loss += float(loss)
                            count += 1
                        else:
                            logger.warning(f"Non-finite loss encountered during evaluation: {loss}")

                        # Evaluate custom metrics callback if provided
                        if custom_metric_fn is not None:
                            extra_m = custom_metric_fn(outputs, batch)
                            if isinstance(extra_m, dict):
                                for mk, mv in extra_m.items():
                                    if isinstance(mv, (int, float)) and math.isfinite(mv):
                                        custom_metrics_sum[mk] = custom_metrics_sum.get(mk, 0.0) + float(mv)

                    except Exception as e:
                        logger.error(f"Error evaluating batch: {e}", exc_info=True)
                        continue

        finally:
            model.train()

        if count == 0:
            logger.warning("No valid evaluation samples processed.")
            return {"loss": float("inf"), "perplexity": float("inf")}

        avg_loss = total_loss / count
        perplexity = math.exp(min(20.0, max(-20.0, avg_loss))) if not math.isnan(avg_loss) else float("inf")

        metrics: Dict[str, float] = {
            "loss": avg_loss,
            "perplexity": perplexity,
        }

        for mk, msum in custom_metrics_sum.items():
            metrics[mk] = msum / count

        logger.debug(f"Evaluation completed: loss={avg_loss:.4f}, ppl={perplexity:.2f}")
        return metrics

    def compute_metrics(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor,
        **kwargs: Any
    ) -> Dict[str, float]:
        """
        Compute evaluation metrics directly from predictions and targets tensors.

        Args:
            predictions: Model predictions tensor.
            targets: Ground truth targets tensor.
            **kwargs: Additional arguments.

        Returns:
            Dictionary of metric names to float values.
        """
        loss_fn = nn.CrossEntropyLoss(ignore_index=-100)
        loss = loss_fn(predictions.view(-1, predictions.size(-1)), targets.view(-1))

        loss_val = float(loss.item())
        perplexity = math.exp(min(20.0, max(-20.0, loss_val))) if not math.isnan(loss_val) else float("inf")

        metrics = {
            "loss": loss_val,
            "perplexity": perplexity,
        }

        # Calculate Top-1 accuracy if predictions and targets allow
        try:
            with torch.no_grad():
                preds_flat = predictions.view(-1, predictions.size(-1))
                targets_flat = targets.view(-1)
                mask = targets_flat != -100
                if mask.sum() > 0:
                    correct = (preds_flat.argmax(dim=-1)[mask] == targets_flat[mask]).sum()
                    metrics["accuracy"] = float((correct / mask.sum()).item())
        except Exception:
            pass

        return metrics

    def select_best_metric(self, metrics: Dict[str, float], metric_name: str = "loss") -> float:
        """
        Select target metric value from evaluation metrics dict.

        Args:
            metrics: Metrics dictionary.
            metric_name: Name of metric to extract (default: "loss").

        Returns:
            Extracted metric float value.
        """
        if metric_name in metrics:
            return metrics[metric_name]
        if "loss" in metrics:
            return metrics["loss"]
        if metrics:
            return next(iter(metrics.values()))
        return float("inf")


__all__ = ["Evaluator", "EvaluationError"]
