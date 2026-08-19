"""
Performance and GPU resource profiling module for trainers.

Provides step throughput calculation, CUDA memory tracking, latency timing,
PyTorch Profiler integration, and performance reporting.
"""
import time
import logging
from typing import Dict, Any, Optional
import torch

from .exceptions import TrainerError

logger = logging.getLogger(__name__)


class TrainingProfiler:
    """
    Tracks step timing, token processing throughput, and GPU memory utilization.
    """

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._start_time: Optional[float] = None
        self._last_step_time: Optional[float] = None
        self._total_tokens: int = 0
        self._step_count: int = 0

    def start(self) -> None:
        """Start total profiling timer."""
        if not self.enabled:
            return
        self._start_time = time.perf_counter()
        self._last_step_time = self._start_time

    def step_start(self) -> float:
        """Record step start timestamp."""
        return time.perf_counter()

    def step_end(self, step_start_time: float, num_tokens: int = 0) -> Dict[str, float]:
        """
        Record step completion metrics.

        Args:
            step_start_time: Timestamp from step_start()
            num_tokens: Number of tokens processed in step

        Returns:
            Dictionary of step latency and throughput metrics
        """
        if not self.enabled:
            return {}

        now = time.perf_counter()
        step_latency = max(1e-6, now - step_start_time)
        self._total_tokens += num_tokens
        self._step_count += 1

        tokens_per_sec = num_tokens / step_latency if step_latency > 0 else 0.0

        metrics: Dict[str, float] = {
            "step_latency_sec": step_latency,
            "tokens_per_sec": tokens_per_sec,
        }

        if torch.cuda.is_available():
            metrics["cuda_mem_allocated_mb"] = torch.cuda.memory_allocated() / (1024 ** 2)
            metrics["cuda_mem_reserved_mb"] = torch.cuda.memory_reserved() / (1024 ** 2)
            metrics["cuda_max_mem_allocated_mb"] = torch.cuda.max_memory_allocated() / (1024 ** 2)

        return metrics

    def summary(self) -> Dict[str, Any]:
        """Generate total profiling summary metrics."""
        if not self.enabled or self._start_time is None:
            return {}

        elapsed = max(1e-6, time.perf_counter() - self._start_time)
        avg_tps = self._total_tokens / elapsed if elapsed > 0 else 0.0
        avg_step_sec = elapsed / max(1, self._step_count)

        summary_data: Dict[str, Any] = {
            "total_elapsed_sec": elapsed,
            "total_steps": self._step_count,
            "total_tokens": self._total_tokens,
            "avg_tokens_per_sec": avg_tps,
            "avg_step_sec": avg_step_sec,
        }

        if torch.cuda.is_available():
            summary_data["max_cuda_mem_allocated_mb"] = torch.cuda.max_memory_allocated() / (1024 ** 2)

        return summary_data


# Alias for class name consistency across sub-managers
ProfilerManager = TrainingProfiler

__all__ = ["TrainingProfiler", "ProfilerManager"]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.trainers."):
        sys.modules["trainers." + __name__[len("optimization_core.trainers."):]] = _mod
    elif __name__.startswith("trainers."):
        sys.modules["optimization_core.trainers." + __name__[len("trainers."):]] = _mod
