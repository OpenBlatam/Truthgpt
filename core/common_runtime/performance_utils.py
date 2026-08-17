"""
Performance Utilities for Common Runtime.
"""

import time
import torch
import torch.nn as nn
from typing import Dict, Any, Callable


def measure_latency(func: Callable, *args: Any, num_runs: int = 10, **kwargs: Any) -> Dict[str, float]:
    """Measure function latency over multiple runs."""
    latencies = []
    for _ in range(num_runs):
        start = time.perf_counter()
        func(*args, **kwargs)
        latencies.append(time.perf_counter() - start)
    avg_sec = sum(latencies) / len(latencies)
    return {
        "avg_latency_ms": avg_sec * 1000.0,
        "min_latency_ms": min(latencies) * 1000.0,
        "max_latency_ms": max(latencies) * 1000.0,
    }


def measure_model_memory(model: nn.Module) -> float:
    """Estimate model parameters memory size in Megabytes."""
    param_size = sum(p.numel() * p.element_size() for p in model.parameters())
    buffer_size = sum(b.numel() * b.element_size() for b in model.buffers())
    return (param_size + buffer_size) / (1024 ** 2)

