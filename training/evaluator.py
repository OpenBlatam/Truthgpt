"""
Evaluation Module
=================
Model evaluation component supporting AMP autocast evaluation, device transfer,
multi-format loss extraction, custom metric evaluation, non-finite loss guardrails, and exception safety.
"""

from __future__ import annotations

import logging
import math
import time
from typing import Any, Callable, Dict, Optional, Union
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

try:
    from torch.amp import autocast
except ImportError:
    from torch.cuda.amp import autocast  # type: ignore

from .exceptions import DeviceTransferError, EvaluationError
from .interfaces import BaseEvaluator
from .types import EvaluationMetrics, EvaluatorConfig, PrecisionType

logger = logging.getLogger(__name__)


class Evaluator(BaseEvaluator):
    """
    Evaluator for PyTorch model validation and metric assessment.
    Supports AMP mixed precision, device transfers, loss extraction, and custom metric hooks.
    """

    def __init__(
        self,
        use_amp: bool = False,
        amp_dtype: Optional[Union[str, torch.dtype]] = None,
        device: Optional[Union[str, torch.device]] = None,
        config: Optional[Union[Dict[str, Any], EvaluatorConfig]] = None,
        compute_perplexity: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Initialize Evaluator.
        """
        if config is not None:
            if isinstance(config, EvaluatorConfig):
                use_amp = config.use_amp
                amp_dtype = config.amp_dtype
                device = config.device
                compute_perplexity = config.compute_perplexity
            elif isinstance(config, dict):
                use_amp = config.get("use_amp", use_amp)
                amp_dtype = config.get("amp_dtype", amp_dtype)
                device = config.get("device", device)
                compute_perplexity = config.get("compute_perplexity", compute_perplexity)

        self.use_amp: bool = use_amp
        if isinstance(amp_dtype, str):
            self.amp_dtype: Optional[torch.dtype] = PrecisionType.to_torch_dtype(amp_dtype)
        else:
            self.amp_dtype = amp_dtype

        self.device: Optional[torch.device] = torch.device(device) if device is not None else None
        self.compute_perplexity: bool = compute_perplexity
        self.custom_metrics: Dict[str, Callable[[Any, Any], float]] = {}

    def add_metric(self, name: str, metric_fn: Callable[[Any, Any], float]) -> None:
        """
        Register a custom metric calculation callable.
        """
        self.custom_metrics[name] = metric_fn
        logger.debug(f"Registered custom evaluation metric '{name}'.")

    def _get_autocast_context(self, eval_device: torch.device) -> Any:
        """
        Helper to obtain device-appropriate autocast context manager for evaluation.
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
        """
        try:
            if isinstance(batch, torch.Tensor):
                return batch.to(device, non_blocking=True)
            elif isinstance(batch, dict):
                return {k: self._to_device(v, device) for k, v in batch.items()}
            elif isinstance(batch, list):
                return [self._to_device(v, device) for v in batch]
            elif isinstance(batch, tuple):
                return tuple(self._to_device(v, device) for v in batch)
            return batch
        except Exception as e:
            raise DeviceTransferError(f"Failed to move batch element of type {type(batch)} to {device}: {e}") from e

    def _extract_loss(self, outputs: Any) -> torch.Tensor:
        """
        Extract loss tensor cleanly from outputs.
        """
        if hasattr(outputs, "loss") and getattr(outputs, "loss") is not None:
            raw_loss = getattr(outputs, "loss")
        elif isinstance(outputs, dict) and "loss" in outputs:
            raw_loss = outputs["loss"]
        elif isinstance(outputs, (tuple, list)) and len(outputs) > 0 and isinstance(outputs[0], torch.Tensor):
            raw_loss = outputs[0]
        elif isinstance(outputs, torch.Tensor):
            raw_loss = outputs
        else:
            raise EvaluationError(f"Could not extract loss from model evaluation output of type {type(outputs)}")

        if isinstance(raw_loss, dict):
            raw_loss = raw_loss.get("loss", list(raw_loss.values())[0])

        if hasattr(raw_loss, "mean") and getattr(raw_loss, "dim", lambda: 0)() > 0:
            raw_loss = raw_loss.mean()

        return raw_loss

    def compute_metrics(self, predictions: torch.Tensor, targets: torch.Tensor) -> Dict[str, float]:
        """
        Compute standard metric values given model prediction logits and target labels.
        """
        preds = predictions.argmax(dim=-1) if predictions.dim() > 1 else predictions
        acc = (preds == targets).float().mean().item() if preds.shape == targets.shape else 0.0
        return {"accuracy": float(acc)}

    def select_best_metric(self, metrics: Dict[str, Any], metric_name: str = "loss") -> float:
        """Select target metric value from metrics dictionary."""
        return float(metrics.get(metric_name, float("inf")))

    def evaluate(
        self,
        model: Optional[nn.Module],
        data_loader: DataLoader,
        device: Optional[Union[str, torch.device]] = None,
        max_batches: Optional[int] = None,
        custom_metric_fn: Optional[Callable[[Any, Any], Union[Dict[str, float], float]]] = None,
        **kwargs: Any,
    ) -> Dict[str, float]:
        """
        Evaluate model performance on given data_loader.
        """
        if model is None:
            raise EvaluationError("Model cannot be None for evaluation.")

        eval_device = torch.device(device) if device is not None else (
            self.device or (next(model.parameters()).device if list(model.parameters()) else torch.device("cpu"))
        )

        model.eval()
        total_loss = 0.0
        num_batches = 0
        total_samples = 0
        custom_metric_accum: Dict[str, float] = {k: 0.0 for k in self.custom_metrics}
        custom_fn_accum: Dict[str, float] = {}
        start_time = time.perf_counter()

        try:
            with torch.no_grad():
                for i, batch in enumerate(data_loader):
                    if max_batches is not None and i >= max_batches:
                        break

                    batch_on_device = self._to_device(batch, eval_device)

                    with self._get_autocast_context(eval_device):
                        if isinstance(batch_on_device, dict):
                            # Filter non-tensor args if model doesn't accept arbitrary kwargs
                            clean_kwargs = {k: v for k, v in batch_on_device.items() if isinstance(v, torch.Tensor) or k in ("input_ids", "labels", "attention_mask", "x")}
                            outputs = model(**clean_kwargs)
                        elif isinstance(batch_on_device, (tuple, list)):
                            outputs = model(*batch_on_device)
                        else:
                            outputs = model(batch_on_device)

                        loss = self._extract_loss(outputs)

                    if torch.isfinite(loss):
                        total_loss += float(loss.item())
                        num_batches += 1
                    else:
                        logger.warning("Encountered non-finite loss during evaluation batch; skipping accumulation.")

                    # Compute registered custom metrics
                    for metric_name, metric_fn in self.custom_metrics.items():
                        try:
                            m_val = float(metric_fn(outputs, batch_on_device))
                            custom_metric_accum[metric_name] += m_val
                        except Exception as me:
                            logger.debug(f"Custom metric '{metric_name}' failed on batch: {me}")

                    # Compute custom_metric_fn passed as arg
                    if custom_metric_fn is not None:
                        try:
                            fn_res = custom_metric_fn(outputs, batch_on_device)
                            if isinstance(fn_res, dict):
                                for k, v in fn_res.items():
                                    custom_fn_accum[k] = custom_fn_accum.get(k, 0.0) + float(v)
                            elif isinstance(fn_res, (int, float)):
                                custom_fn_accum["custom_metric"] = custom_fn_accum.get("custom_metric", 0.0) + float(fn_res)
                        except Exception as cme:
                            logger.debug(f"custom_metric_fn failed on batch: {cme}")

                    # Count samples
                    if isinstance(batch, dict) and "input_ids" in batch:
                        total_samples += batch["input_ids"].size(0)
                    elif isinstance(batch, torch.Tensor):
                        total_samples += batch.size(0)

            elapsed_time = time.perf_counter() - start_time
            avg_loss = total_loss / max(1, num_batches)

            results: Dict[str, float] = {
                "loss": avg_loss,
                "eval_time": elapsed_time,
                "num_batches": float(num_batches),
            }

            if self.compute_perplexity and avg_loss < 100.0:
                try:
                    results["perplexity"] = math.exp(avg_loss)
                except OverflowError:
                    results["perplexity"] = float("inf")

            for k, total_val in custom_metric_accum.items():
                results[k] = total_val / max(1, num_batches)

            for k, total_val in custom_fn_accum.items():
                results[k] = total_val / max(1, num_batches)

            return results

        except Exception as e:
            if isinstance(e, EvaluationError):
                raise
            logger.error(f"Error during model evaluation: {e}", exc_info=True)
            raise EvaluationError(f"Evaluation process failed: {e}") from e
