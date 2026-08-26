"""
Performance Utilities for Common Runtime.
"""

from __future__ import annotations

import time
from typing import Dict, Any, Callable


def measure_latency(func: Callable, *args: Any, num_runs: int = 10, **kwargs: Any) -> Dict[str, float]:
    """Measure function latency over multiple runs."""
    latencies = []
    for _ in range(num_runs):
        start = time.perf_counter()
        func(*args, **kwargs)
        latencies.append(time.perf_counter() - start)
    avg_sec = sum(latencies) / len(latencies) if latencies else 0.0
    return {
        "avg_latency_ms": avg_sec * 1000.0,
        "min_latency_ms": min(latencies) * 1000.0 if latencies else 0.0,
        "max_latency_ms": max(latencies) * 1000.0 if latencies else 0.0,
    }


def measure_model_memory(model: Any) -> float:
    """Estimate model parameters memory size in Megabytes."""
    if hasattr(model, "parameters") and hasattr(model, "buffers"):
        param_size = sum(p.numel() * (p.element_size() if hasattr(p, "element_size") else 4) for p in model.parameters())
        buffer_size = sum(b.numel() * (b.element_size() if hasattr(b, "element_size") else 4) for b in model.buffers())
        return (param_size + buffer_size) / (1024 ** 2)
    return 0.0


__all__ = [
    "measure_latency",
    "measure_model_memory",
]
