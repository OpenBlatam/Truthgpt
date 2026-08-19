"""
Metrics Accumulator & Tracking module for trainers.

Provides sliding-window statistics aggregation for training loss, validation metrics,
learning rates, gradient norms, throughput, and standard deviation.
"""
import math
import logging
from collections import deque
from typing import Dict, Any, List, Optional
import time

logger = logging.getLogger(__name__)


class MetricTracker:
    """
    Sliding window metric accumulator computing moving averages, exponential moving average, min, max, std, and current values.
    """

    def __init__(self, window_size: int = 100, ema_alpha: float = 0.1) -> None:
        self.window_size = window_size
        self.ema_alpha = ema_alpha
        self._history: Dict[str, deque] = {}
        self._global_history: Dict[str, List[float]] = {}
        self._ema_values: Dict[str, float] = {}
        self._start_time: float = time.time()

    def update(self, key: str, value: float) -> None:
        """
        Record a metric value.

        Args:
            key: Metric name string
            value: Metric numeric value
        """
        if not math.isfinite(value):
            return

        if key not in self._history:
            self._history[key] = deque(maxlen=self.window_size)
            self._global_history[key] = []
            self._ema_values[key] = value
        else:
            # Update exponential moving average
            self._ema_values[key] = (self.ema_alpha * value) + ((1.0 - self.ema_alpha) * self._ema_values[key])

        self._history[key].append(value)
        self._global_history[key].append(value)

    def update_dict(self, metrics: Dict[str, float]) -> None:
        """Record multiple key-value metrics."""
        for k, v in metrics.items():
            if isinstance(v, (int, float)):
                self.update(k, float(v))

    def get_avg(self, key: str) -> float:
        """Get moving average for key within window."""
        if key not in self._history or not self._history[key]:
            return 0.0
        return sum(self._history[key]) / len(self._history[key])

    def get_ema(self, key: str) -> float:
        """Get exponential moving average for key."""
        return self._ema_values.get(key, 0.0)

    def get_std(self, key: str) -> float:
        """Get standard deviation for key within window."""
        if key not in self._history or len(self._history[key]) < 2:
            return 0.0
        avg = self.get_avg(key)
        variance = sum((x - avg) ** 2 for x in self._history[key]) / (len(self._history[key]) - 1)
        return math.sqrt(variance)

    def get_latest(self, key: str, default: float = 0.0) -> float:
        """Get most recent metric value."""
        if key not in self._history or not self._history[key]:
            return default
        return self._history[key][-1]

    def get_min(self, key: str) -> Optional[float]:
        """Get global minimum for key."""
        if key not in self._global_history or not self._global_history[key]:
            return None
        return min(self._global_history[key])

    def get_max(self, key: str) -> Optional[float]:
        """Get global maximum for key."""
        if key not in self._global_history or not self._global_history[key]:
            return None
        return max(self._global_history[key])

    def reset(self) -> None:
        """Clear recorded metric histories."""
        self._history.clear()
        self._global_history.clear()
        self._ema_values.clear()
        self._start_time = time.time()

    def summary(self) -> Dict[str, Dict[str, float]]:
        """Generate full metrics summary report."""
        res: Dict[str, Dict[str, float]] = {}
        for key in self._global_history:
            vals = self._global_history[key]
            if not vals:
                continue
            res[key] = {
                "latest": vals[-1],
                "moving_avg": self.get_avg(key),
                "ema": self.get_ema(key),
                "std": self.get_std(key),
                "min": min(vals),
                "max": max(vals),
                "count": float(len(vals)),
            }
        return res


# Alias for backward compatibility
MetricsTracker = MetricTracker

__all__ = ["MetricTracker", "MetricsTracker"]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.trainers."):
        sys.modules["trainers." + __name__[len("optimization_core.trainers."):]] = _mod
    elif __name__.startswith("trainers."):
        sys.modules["optimization_core.trainers." + __name__[len("trainers."):]] = _mod

