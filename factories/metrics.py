"""
Metric Factories
================
Factory functions, MetricsFactory manager, and registry for training, evaluation, throughput, latency, FLOPS,
VRAM utilization, and composite metric calculations.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from .base import BaseFactory
from .registry import Registry

METRICS = Registry(name="MetricsRegistry")


@dataclass
class MetricConfig:
    """Configuration specification for training and evaluation metric calculators."""

    name: str = "loss"
    target_key: str = "val_loss"
    extra_kwargs: Dict[str, Any] = field(default_factory=dict)


class MetricAggregator:
    """Helper container to compute running average across logged metrics."""

    def __init__(self) -> None:
        self.totals: Dict[str, float] = {}
        self.counts: Dict[str, int] = {}

    def update(self, metrics: Dict[str, Any]) -> None:
        """Accumulate numeric metric values."""
        for k, v in metrics.items():
            if isinstance(v, (int, float)):
                self.totals[k] = self.totals.get(k, 0.0) + float(v)
                self.counts[k] = self.counts.get(k, 0) + 1

    def compute(self) -> Dict[str, float]:
        """Compute current running average for all updated metrics."""
        return {k: self.totals[k] / max(1, self.counts[k]) for k in self.totals}

    def get_mean(self, key: str) -> float:
        """Get mean running average for a specific metric key."""
        if key not in self.totals or self.counts.get(key, 0) == 0:
            return 0.0
        return self.totals[key] / self.counts[key]

    get_avg = get_mean

    def get_count(self, key: str) -> int:
        """Get sample count for a specific metric key."""
        return self.counts.get(key, 0)

    def get_total(self, key: str) -> float:
        """Get total sum for a specific metric key."""
        return self.totals.get(key, 0.0)

    def reset(self) -> None:
        """Clear all stored totals and counts."""
        self.totals.clear()
        self.counts.clear()


@METRICS.register(
    "loss",
    priority=100,
    aliases=["val_loss", "train_loss"],
    description="Extract validation or training loss from context.",
    tags=["loss", "eval"],
)
def metric_loss(context: Dict[str, Any]) -> float:
    """Extract validation loss from evaluation context."""
    val_loss = context.get("val_loss", context.get("loss", float("inf")))
    return float(val_loss)


@METRICS.register(
    "ppl",
    priority=90,
    aliases=["perplexity"],
    description="Calculate perplexity exp(val_loss) with numerical bounds [-20, 20].",
    tags=["ppl", "perplexity"],
)
def metric_ppl(context: Dict[str, Any]) -> float:
    """Calculate perplexity exp(val_loss) with numerical bounds."""
    val_loss = context.get("val_loss", context.get("loss", float("inf")))
    try:
        val = float(val_loss)
        return math.exp(min(20.0, max(-20.0, val)))
    except Exception:
        return float("inf")


@METRICS.register(
    "accuracy",
    priority=80,
    aliases=["acc", "top1_acc"],
    description="Extract classification or token accuracy from context.",
    tags=["accuracy", "top1"],
)
def metric_accuracy(context: Dict[str, Any]) -> float:
    """Extract classification/token accuracy from context."""
    acc = context.get("accuracy", context.get("acc", 0.0))
    return float(acc)


@METRICS.register(
    "bpc",
    priority=70,
    aliases=["bits_per_character"],
    description="Calculate Bits Per Character (val_loss / ln(2)).",
    tags=["bpc", "bits"],
)
def metric_bpc(context: Dict[str, Any]) -> float:
    """Calculate Bits Per Character (val_loss / ln(2))."""
    val_loss = context.get("val_loss", context.get("loss", float("inf")))
    try:
        return float(val_loss) / math.log(2)
    except Exception:
        return float("inf")


@METRICS.register(
    "latency_p99",
    priority=60,
    aliases=["p99_latency", "latency_ms"],
    description="Extract p99 latency in milliseconds from evaluation context.",
    tags=["latency", "p99", "profiling"],
)
def metric_latency_p99(context: Dict[str, Any]) -> float:
    """Extract 99th percentile latency in milliseconds."""
    return float(context.get("latency_p99", context.get("p99_ms", 0.0)))


@METRICS.register(
    "throughput",
    priority=65,
    aliases=["tokens_per_sec", "tps"],
    description="Calculate token processing throughput per second.",
    tags=["throughput", "tps"],
)
def metric_throughput(context: Dict[str, Any]) -> float:
    """Calculate token throughput (tokens per second)."""
    if "throughput" in context:
        return float(context["throughput"])
    num_tokens = context.get("num_tokens", context.get("tokens", 0))
    elapsed_sec = context.get("elapsed_sec", context.get("time", context.get("elapsed", 1.0)))
    if elapsed_sec <= 0:
        return 0.0
    return float(num_tokens) / float(elapsed_sec)


@METRICS.register(
    "flops",
    priority=50,
    aliases=["tflops", "throughput_flops"],
    description="Calculate achieved FLOPS/TFLOPS token processing throughput.",
    tags=["flops", "tflops"],
)
def metric_flops(context: Dict[str, Any]) -> float:
    """Calculate TFLOPS processing efficiency."""
    return float(context.get("tflops", context.get("flops", 0.0)))


@METRICS.register(
    "vram_utilization",
    priority=40,
    aliases=["gpu_mem", "vram_mb", "gpu_memory"],
    description="Extract peak VRAM memory utilization in Megabytes.",
    hardware_requirements=["cuda"],
    tags=["vram", "gpu_memory"],
)
def metric_vram_utilization(context: Dict[str, Any]) -> float:
    """Extract GPU VRAM memory usage in MB."""
    return float(context.get("vram_mb", context.get("gpu_memory", 0.0)))


metric_gpu_memory = metric_vram_utilization


@METRICS.register(
    "composite",
    priority=30,
    description="Calculate weighted composite score over multiple evaluation metrics.",
    tags=["composite", "weighted"],
)
def metric_composite(context: Dict[str, Any], weights: Optional[Dict[str, float]] = None) -> float:
    """Calculate composite weighted metric score."""
    weights = weights or {"loss": 1.0, "ppl": 0.1, "accuracy": 1.0}
    total_score = 0.0
    for key, weight in weights.items():
        if key in METRICS:
            total_score += weight * METRICS.build(key, context)
        elif key in context:
            total_score += weight * float(context[key])
    return total_score


class MetricsFactory(BaseFactory[Callable[[Dict[str, Any]], float]]):
    """
    Manager class providing a unified factory interface for creating and executing
    metric calculators.
    """

    def __init__(self, registry: Registry = METRICS) -> None:
        self.registry = registry

    def build(self, name: str, *args: Any, **kwargs: Any) -> Callable[[Dict[str, Any]], float]:
        """Construct metric calculation function by metric name."""
        return self.registry.build(name, *args, **kwargs)

    def create(self, config: Union[str, MetricConfig], **kwargs: Any) -> Callable[[Dict[str, Any]], float]:
        """Create metric calculator from MetricConfig object or metric name string."""
        if isinstance(config, MetricConfig):
            name = config.name
            combined = {**config.extra_kwargs, **kwargs}
        else:
            name = str(config)
            combined = kwargs

        return self.build(name, **combined)

    def evaluate(self, name: str, context: Dict[str, Any], **kwargs: Any) -> float:
        """Directly calculate metric value for a given context dictionary."""
        metric_fn = self.build(name, **kwargs)
        return metric_fn(context)


__all__ = [
    "METRICS",
    "MetricConfig",
    "MetricsFactory",
    "MetricAggregator",
    "metric_loss",
    "metric_ppl",
    "metric_accuracy",
    "metric_bpc",
    "metric_latency_p99",
    "metric_flops",
    "metric_throughput",
    "metric_vram_utilization",
    "metric_gpu_memory",
    "metric_composite",
]
