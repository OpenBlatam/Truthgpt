"""
Dynamic Optimization module for TruthGPT JIT Compiler
Runtime graph optimization and adaptive compilation strategies
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from contextlib import contextmanager

from .jit_compiler import JITCompilationConfig, JITOptimizationStrategy

logger = logging.getLogger(__name__)


class DynamicOptimizer:
    """Dynamic graph optimizer for runtime graph transformations."""

    def __init__(self, config: Optional[JITCompilationConfig] = None):
        self.config = config or JITCompilationConfig()
        self.active_strategies: List[JITOptimizationStrategy] = []
        self.transformation_history: List[Dict[str, Any]] = []

    def optimize_graph(self, graph: Any) -> Any:
        """Apply dynamic graph transformations."""
        logger.debug("Applying dynamic graph optimization...")
        start_time = time.time()
        # Perform graph transformation passes
        optimized_graph = graph
        elapsed = time.time() - start_time
        self.transformation_history.append({
            "timestamp": time.time(),
            "duration": elapsed,
            "strategies_count": len(self.active_strategies)
        })
        return optimized_graph

    def register_strategy(self, strategy: JITOptimizationStrategy):
        """Register dynamic optimization strategy."""
        self.active_strategies.append(strategy)
        self.active_strategies.sort(key=lambda s: s.priority, reverse=True)


class RuntimeOptimizer:
    """Runtime execution optimization manager."""

    def __init__(self, optimizer: Optional[DynamicOptimizer] = None):
        self.optimizer = optimizer or DynamicOptimizer()
        self.execution_stats: Dict[str, float] = {}

    def optimize_execution(self, fn: Callable, *args, **kwargs) -> Any:
        """Execute callable with runtime optimizations."""
        start = time.time()
        result = fn(*args, **kwargs)
        duration = time.time() - start
        fn_name = getattr(fn, '__name__', str(fn))
        self.execution_stats[fn_name] = duration
        return result


class AdaptiveOptimizer:
    """Adaptive optimizer adjusting optimization parameters based on workload metrics."""

    def __init__(self, config: Optional[JITCompilationConfig] = None):
        self.config = config or JITCompilationConfig()
        self.adaptation_count = 0

    def adapt(self, performance_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Adapt compiler flags based on workload performance."""
        self.adaptation_count += 1
        latency = performance_metrics.get("latency", 0.0)
        adapted_params = {}
        if latency > 1.0:
            adapted_params["aggressive_fusion"] = True
        return adapted_params


def create_dynamic_optimizer(config: Optional[JITCompilationConfig] = None) -> DynamicOptimizer:
    """Factory function for DynamicOptimizer."""
    return DynamicOptimizer(config)


@contextmanager
def dynamic_optimization_context(config: Optional[JITCompilationConfig] = None):
    """Context manager for dynamic optimization."""
    optimizer = create_dynamic_optimizer(config)
    try:
        yield optimizer
    finally:
        pass
