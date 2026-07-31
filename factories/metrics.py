"""
Metric Factories
================
Factory functions and registry for training and evaluation metrics calculation.
"""
import math
from typing import Any, Dict, Optional

from .registry import Registry

METRICS = Registry(name="MetricsRegistry")


@METRICS.register("loss")
def metric_loss(context: Dict[str, Any]) -> float:
    """Extract validation loss from evaluation context."""
    val_loss = context.get("val_loss", context.get("loss", float("inf")))
    return float(val_loss)


@METRICS.register("ppl")
def metric_ppl(context: Dict[str, Any]) -> float:
    """Calculate perplexity exp(val_loss) with numerical bounds."""
    val_loss = context.get("val_loss", context.get("loss", float("inf")))
    try:
        val = float(val_loss)
        return math.exp(min(20.0, max(-20.0, val)))
    except Exception:
        return float("inf")


@METRICS.register("accuracy")
def metric_accuracy(context: Dict[str, Any]) -> float:
    """Extract classification/token accuracy from context."""
    acc = context.get("accuracy", context.get("acc", 0.0))
    return float(acc)


@METRICS.register("bpc")
def metric_bpc(context: Dict[str, Any]) -> float:
    """Calculate Bits Per Character (val_loss / ln(2))."""
    val_loss = context.get("val_loss", context.get("loss", float("inf")))
    try:
        return float(val_loss) / math.log(2)
    except Exception:
        return float("inf")




