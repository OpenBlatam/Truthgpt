"""
Base Metrics Classes for Common Runtime.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseMetricsCalculator(ABC):
    """Abstract base class for metrics calculation."""

    @abstractmethod
    def calculate(self, *args: Any, **kwargs: Any) -> Dict[str, float]:
        """Calculate metrics dictionary."""
        pass


class MetricCollector:
    """Collector for accumulating metrics over optimization steps."""

    def __init__(self):
        self.history: List[Dict[str, float]] = []

    def record(self, metrics: Dict[str, float]) -> None:
        """Record step metrics."""
        self.history.append(metrics)

    def get_summary(self) -> Dict[str, float]:
        """Compute average summary over recorded history."""
        if not self.history:
            return {}
        summary = {}
        keys = self.history[0].keys()
        for k in keys:
            vals = [h[k] for h in self.history if k in h]
            summary[f"avg_{k}"] = sum(vals) / len(vals) if vals else 0.0
        return summary

