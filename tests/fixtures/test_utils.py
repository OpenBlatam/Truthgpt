"""
High-Precision Test Utilities, Telemetry Profilers, and Memory Trackers for TruthGPT Optimization Core.
"""

from __future__ import annotations

import time
import os
import sys
import gc
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from contextlib import contextmanager
import psutil
import torch
import numpy as np

from ..interfaces import (
    BaseProfilerInterface,
    BaseMemoryTrackerInterface,
    BaseAssertionInterface,
)
from ..exceptions import (
    ProfilerError,
    MemoryTrackingError,
    AssertionErrorWrapper,
    TestTimeoutError,
)
from ..types import BenchmarkMetric, MemorySnapshot


class TestUtils:
    """Foundational test utility operations."""

    @staticmethod
    def assert_tensor_close(
        tensor1: torch.Tensor,
        tensor2: torch.Tensor,
        rtol: float = 1e-5,
        atol: float = 1e-8,
        msg: Optional[str] = None,
    ) -> bool:
        """Assert two tensors are elementwise close within tolerance."""
        if not torch.allclose(tensor1, tensor2, rtol=rtol, atol=atol):
            diff = (tensor1 - tensor2).abs().max().item()
            raise AssertionErrorWrapper(
                msg or f"Tensors not close. Max absolute diff: {diff:.6e} (rtol={rtol}, atol={atol})"
            )
        return True

    @staticmethod
    def assert_shape_equal(tensor: torch.Tensor, expected_shape: tuple) -> bool:
        """Assert tensor has expected shape."""
        if tuple(tensor.shape) != tuple(expected_shape):
            raise AssertionErrorWrapper(
                f"Shape mismatch: expected {expected_shape}, got {tuple(tensor.shape)}"
            )
        return True

    @staticmethod
    def assert_dtype_equal(tensor: torch.Tensor, expected_dtype: torch.dtype) -> bool:
        """Assert tensor has expected dtype."""
        if tensor.dtype != expected_dtype:
            raise AssertionErrorWrapper(
                f"Dtype mismatch: expected {expected_dtype}, got {tensor.dtype}"
            )
        return True

    @staticmethod
    def create_test_config(**kwargs: Any) -> Dict[str, Any]:
        """Create a default test configuration dictionary."""
        default_config = {
            'batch_size': 2,
            'seq_len': 128,
            'd_model': 512,
            'n_heads': 8,
            'n_layers': 6,
            'dropout': 0.1,
            'learning_rate': 0.001,
            'max_epochs': 10,
            'device': 'cpu',
        }
        default_config.update(kwargs)
        return default_config

    @staticmethod
    def measure_execution_time(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Measure execution latency and host memory usage for a function invocation."""
        process = psutil.Process()
        start_memory = process.memory_info().rss / (1024 * 1024)
        t0 = time.perf_counter()

        result = func(*args, **kwargs)

        elapsed_sec = time.perf_counter() - t0
        end_memory = process.memory_info().rss / (1024 * 1024)

        return {
            'result': result,
            'execution_time': elapsed_sec,
            'execution_time_ms': elapsed_sec * 1000.0,
            'memory_used_mb': end_memory - start_memory,
            'start_memory_mb': start_memory,
            'end_memory_mb': end_memory,
        }

    @staticmethod
    def compare_performance(
        baseline_func: Callable[..., Any],
        optimized_func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Compare execution throughput and speedup between baseline and optimized routines."""
        baseline_metrics = TestUtils.measure_execution_time(baseline_func, *args, **kwargs)
        optimized_metrics = TestUtils.measure_execution_time(optimized_func, *args, **kwargs)

        b_time = baseline_metrics['execution_time']
        o_time = optimized_metrics['execution_time']
        speedup = b_time / o_time if o_time > 0 else float('inf')

        return {
            'baseline': baseline_metrics,
            'optimized': optimized_metrics,
            'speedup': speedup,
            'is_faster': speedup > 1.0,
        }


class PerformanceProfiler(BaseProfilerInterface):
    """Performance profiler recording execution times and CPU utilization spans."""

    def __init__(self) -> None:
        self.profiles: List[Dict[str, Any]] = []
        self._active_spans: Dict[str, Dict[str, Any]] = {}
        self.process = psutil.Process()

    def start_profile(self, name: str) -> None:
        """Start profiling span."""
        self._active_spans[name] = {
            'name': name,
            'start_time': time.perf_counter(),
            'start_memory': self.process.memory_info().rss / (1024 * 1024),
            'start_cpu': self.process.cpu_percent(interval=None),
        }

    def end_profile(self, name: Optional[str] = None) -> Dict[str, Any]:
        """End profiling span and return computed span metrics."""
        if not self._active_spans:
            return {}

        target_name = name or next(reversed(self._active_spans.keys()))
        if target_name not in self._active_spans:
            raise ProfilerError(f"Span '{target_name}' was not started.")

        span_data = self._active_spans.pop(target_name)
        end_time = time.perf_counter()
        end_mem = self.process.memory_info().rss / (1024 * 1024)

        elapsed = end_time - span_data['start_time']
        profile = {
            'name': target_name,
            'execution_time': elapsed,
            'execution_time_ms': elapsed * 1000.0,
            'memory_used_mb': end_mem - span_data['start_memory'],
            'timestamp': time.time(),
        }
        self.profiles.append(profile)
        return profile

    def get_all_profiles(self) -> List[Dict[str, Any]]:
        return self.profiles.copy()

    def get_profile_summary(self) -> Dict[str, Any]:
        if not self.profiles:
            return {'total_profiles': 0, 'total_execution_time': 0.0}

        total_time = sum(p['execution_time'] for p in self.profiles)
        total_mem = sum(p['memory_used_mb'] for p in self.profiles)
        n = len(self.profiles)

        return {
            'total_profiles': n,
            'total_execution_time': total_time,
            'total_execution_time_ms': total_time * 1000.0,
            'average_execution_time_ms': (total_time / n) * 1000.0,
            'total_memory_used_mb': total_mem,
            'average_memory_used_mb': total_mem / n,
        }

    def reset(self) -> None:
        self.profiles.clear()
        self._active_spans.clear()


class MemoryTracker(BaseMemoryTrackerInterface):
    """Memory tracking utility for process host RAM and CUDA VRAM."""

    def __init__(self) -> None:
        self.memory_snapshots: List[MemorySnapshot] = []
        self.peak_memory: float = 0.0
        self.process = psutil.Process()

    def take_snapshot(self, label: str = "snapshot") -> Dict[str, float]:
        """Capture instantaneous memory snapshot."""
        mem_info = self.process.memory_info()
        rss_mb = mem_info.rss / (1024 * 1024)
        vms_mb = mem_info.vms / (1024 * 1024)

        gpu_alloc_mb = 0.0
        gpu_res_mb = 0.0
        if torch.cuda.is_available():
            gpu_alloc_mb = torch.cuda.memory_allocated() / (1024 * 1024)
            gpu_res_mb = torch.cuda.memory_reserved() / (1024 * 1024)

        self.peak_memory = max(self.peak_memory, rss_mb)

        snap = MemorySnapshot(
            timestamp=time.time(),
            label=label,
            rss_mb=rss_mb,
            vms_mb=vms_mb,
            gpu_allocated_mb=gpu_alloc_mb,
            gpu_reserved_mb=gpu_res_mb,
            peak_mb=self.peak_memory,
        )
        self.memory_snapshots.append(snap)
        return snap.to_dict()

    def detect_leak(self, threshold_mb: float = 10.0) -> bool:
        """Check if memory growth across snapshots exceeds a threshold."""
        if len(self.memory_snapshots) < 2:
            return False
        first_rss = self.memory_snapshots[0].rss_mb
        last_rss = self.memory_snapshots[-1].rss_mb
        return (last_rss - first_rss) > threshold_mb

    def get_memory_summary(self) -> Dict[str, Any]:
        if not self.memory_snapshots:
            return {'snapshots_taken': 0}

        rss_vals = [s.rss_mb for s in self.memory_snapshots]
        growth = []
        for i in range(1, len(self.memory_snapshots)):
            prev = self.memory_snapshots[i - 1]
            curr = self.memory_snapshots[i]
            growth.append({
                'from': prev.label,
                'to': curr.label,
                'growth_mb': curr.rss_mb - prev.rss_mb,
            })

        return {
            'snapshots_taken': len(self.memory_snapshots),
            'peak_memory_mb': self.peak_memory,
            'min_memory_mb': min(rss_vals),
            'max_memory_mb': max(rss_vals),
            'average_memory_mb': sum(rss_vals) / len(rss_vals),
            'growth_timeline': growth,
            'has_leak': self.detect_leak(),
        }

    def reset(self) -> None:
        self.memory_snapshots.clear()
        self.peak_memory = 0.0

    @contextmanager
    def track_memory(self, label: str = ""):
        """Context manager for automatic memory tracking."""
        self.take_snapshot(f"{label}_start")
        try:
            yield self
        finally:
            self.take_snapshot(f"{label}_end")


class TestAssertions(BaseAssertionInterface):
    """Custom assertion toolkit for numerical, memory, and performance properties."""

    def assert_tensor_close(
        self,
        actual: Any,
        expected: Any,
        rtol: float = 1e-4,
        atol: float = 1e-4,
        msg: Optional[str] = None,
    ) -> None:
        if isinstance(actual, torch.Tensor) and isinstance(expected, torch.Tensor):
            if not torch.allclose(actual, expected, rtol=rtol, atol=atol):
                diff = (actual - expected).abs().max().item()
                raise AssertionErrorWrapper(msg or f"Tensors mismatch: max diff = {diff:.6e}")
        elif isinstance(actual, np.ndarray) and isinstance(expected, np.ndarray):
            if not np.allclose(actual, expected, rtol=rtol, atol=atol):
                diff = np.abs(actual - expected).max()
                raise AssertionErrorWrapper(msg or f"Ndarrays mismatch: max diff = {diff:.6e}")

    def assert_performance_improvement(
        self,
        baseline_ms: float,
        improved_ms: float,
        min_improvement: float = 1.1,
        msg: Optional[str] = None,
    ) -> None:
        speedup = baseline_ms / improved_ms if improved_ms > 0 else float('inf')
        if speedup < min_improvement:
            raise AssertionErrorWrapper(
                msg or f"Expected at least {min_improvement:.2f}x speedup, got {speedup:.2f}x "
                       f"({baseline_ms:.2f}ms vs {improved_ms:.2f}ms)"
            )

    def assert_memory_bounded(
        self,
        current_mb: float,
        max_limit_mb: float,
        msg: Optional[str] = None,
    ) -> None:
        if current_mb > max_limit_mb:
            raise AssertionErrorWrapper(
                msg or f"Memory usage {current_mb:.2f}MB exceeded limit {max_limit_mb:.2f}MB"
            )

    @staticmethod
    def assert_numerical_stability(tensor: torch.Tensor, max_nan: int = 0, max_inf: int = 0) -> bool:
        nan_count = torch.isnan(tensor).sum().item()
        inf_count = torch.isinf(tensor).sum().item()
        if nan_count > max_nan or inf_count > max_inf:
            raise AssertionErrorWrapper(f"Numerical instability: NaNs={nan_count}, Infs={inf_count}")
        return True

    @staticmethod
    def assert_gradient_flow(gradients: List[Optional[torch.Tensor]], min_grad_norm: float = 1e-6) -> bool:
        total_grad_norm = sum(g.norm().item() ** 2 for g in gradients if g is not None) ** 0.5
        if total_grad_norm < min_grad_norm:
            raise AssertionErrorWrapper(
                f"Gradient vanishing: norm {total_grad_norm:.6e} < min {min_grad_norm:.6e}"
            )
        return True


class AdvancedTestDecorators:
    """Cross-platform decorators for test retry, timeout, and performance regressions."""

    @staticmethod
    def retry(max_attempts: int = 3, delay: float = 0.5) -> Callable[..., Any]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                last_exc = None
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exc = e
                        if attempt < max_attempts - 1:
                            time.sleep(delay)
                raise last_exc
            return wrapper
        return decorator

    @staticmethod
    def timeout(seconds: float) -> Callable[..., Any]:
        """Cross-platform thread-based timeout decorator (safe on Windows, Linux, and macOS)."""
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                res = [None]
                exc = [None]

                def target():
                    try:
                        res[0] = func(*args, **kwargs)
                    except Exception as e:
                        exc[0] = e

                thread = threading.Thread(target=target)
                thread.daemon = True
                thread.start()
                thread.join(timeout=seconds)

                if thread.is_alive():
                    raise TestTimeoutError(getattr(func, '__name__', 'anonymous_test'), seconds)
                if exc[0] is not None:
                    raise exc[0]
                return res[0]
            return wrapper
        return decorator

    @staticmethod
    def performance_test(baseline_time_ms: float, tolerance: float = 1.25) -> Callable[..., Any]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                t0 = time.perf_counter()
                result = func(*args, **kwargs)
                actual_ms = (time.perf_counter() - t0) * 1000.0
                if actual_ms > baseline_time_ms * tolerance:
                    raise AssertionErrorWrapper(
                        f"Performance regression: {actual_ms:.2f}ms vs baseline {baseline_time_ms:.2f}ms"
                    )
                return result
            return wrapper
        return decorator


class ParallelTestRunner:
    """Execute test callables across threads."""

    def __init__(self, max_workers: int = 4) -> None:
        self.max_workers = max_workers

    def run_tests_parallel(self, test_functions: List[Callable[[], Any]]) -> List[Any]:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(f) for f in test_functions]
            return [f.result() for f in futures]


class TestVisualizer:
    """Generate textual representations and visual summaries of test executions."""

    @staticmethod
    def create_results_summary(results: Dict[str, Any]) -> str:
        lines = [
            "=" * 70,
            "TruthGPT Optimization Core Test Summary",
            "=" * 70,
        ]
        if 'total_tests' in results:
            lines.append(f"Total Tests : {results['total_tests']}")
            lines.append(f"Passed      : {results.get('passed', 0)}")
            lines.append(f"Failed      : {results.get('failed', 0)}")
            lines.append(f"Skipped     : {results.get('skipped', 0)}")
            lines.append(f"Errors      : {results.get('errors', 0)}")
            lines.append(f"Pass Rate   : {results.get('pass_rate_pct', 0.0):.1f}%")
        lines.append("=" * 70)
        return "\n".join(lines)


__all__ = [
    "TestUtils",
    "PerformanceProfiler",
    "MemoryTracker",
    "TestAssertions",
    "AdvancedTestDecorators",
    "ParallelTestRunner",
    "TestVisualizer",
]
