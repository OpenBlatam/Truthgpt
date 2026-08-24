"""
Shared Base Test Classes for TruthGPT Optimization Core.
"""

from __future__ import annotations

import unittest
import time
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..interfaces import BaseTestCaseInterface
from ..types import BackendType
from .benchmark_helpers import run_benchmark, BenchmarkResult

logger = logging.getLogger(__name__)


class BasePolyglotTest(unittest.TestCase, BaseTestCaseInterface):
    """Base test class for polyglot native and cross-language tests."""
    __test__ = False

    def setUp(self) -> None:
        """Setup test fixtures and verify backend availability."""
        super().setUp()
        self.backend_availability = self._check_backends()
        self.test_results: List[Dict[str, Any]] = []

    def tearDown(self) -> None:
        """Tear down test state."""
        super().tearDown()

    def _check_backends(self) -> Dict[str, bool]:
        """Inspect which native polyglot backends are currently loaded."""
        availability = {
            "rust": False,
            "cpp": False,
            "julia": False,
            "python": True,
            "cuda": False,
            "mps": False,
        }

        try:
            import torch
            availability["cuda"] = torch.cuda.is_available()
            availability["mps"] = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        except ImportError:
            pass

        try:
            from truthgpt_rust import PyKVCache  # type: ignore
            availability["rust"] = True
        except (ImportError, ModuleNotFoundError):
            pass

        try:
            import _cpp_core  # type: ignore
            availability["cpp"] = True
        except (ImportError, ModuleNotFoundError):
            pass

        try:
            from julia import TruthGPTCore  # type: ignore
            availability["julia"] = True
        except (ImportError, ModuleNotFoundError):
            pass

        return availability

    def skip_if_backend_unavailable(self, backend: str) -> None:
        """Skip test execution if the requested backend is not available."""
        backend_lower = backend.lower()
        if not self.backend_availability.get(backend_lower, False):
            self.skipTest(f"Polyglot native backend '{backend}' is not available in current environment.")

    def measure_time(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Tuple[Any, float]:
        """Measure function execution time returning (result, elapsed_ms)."""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return result, elapsed_ms

    def assert_performance_improvement(
        self,
        baseline_ms: float,
        improved_ms: float,
        min_improvement: float = 1.1,
    ) -> None:
        """Assert that optimized execution is faster than baseline by a minimum factor."""
        improvement = baseline_ms / improved_ms if improved_ms > 0 else float('inf')
        self.assertGreaterEqual(
            improvement,
            min_improvement,
            f"Expected {min_improvement}x improvement, got {improvement:.2f}x "
            f"({baseline_ms:.2f}ms vs {improved_ms:.2f}ms)",
        )

    def run_benchmark(
        self,
        func: Callable[..., Any],
        *args: Any,
        num_runs: Optional[int] = None,
        warmup_runs: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, float]:
        """Execute a micro-benchmark returning a summary dictionary."""
        runs = num_runs or 10
        warmup = warmup_runs or 3
        res = run_benchmark(func, *args, num_runs=runs, warmup_runs=warmup, **kwargs)
        return {
            "avg_ms": res.avg_ms,
            "min_ms": res.min_ms,
            "max_ms": res.max_ms,
            "std_ms": res.std_ms,
            "p50_ms": res.p50_ms,
            "p95_ms": res.p95_ms,
            "p99_ms": res.p99_ms,
            "throughput": res.throughput,
        }


class BaseBenchmarkTest(BasePolyglotTest):
    """Base class for benchmark suites."""
    __test__ = False

    def setUp(self) -> None:
        super().setUp()
        self.benchmark_results: List[Dict[str, Any]] = []
        self.num_runs = 10
        self.warmup_runs = 3

    def compare_backends(
        self,
        func: Callable[..., Any],
        backends: List[str],
        *args: Any,
        **kwargs: Any,
    ) -> Dict[str, Dict[str, float]]:
        """Compare performance across native backends."""
        results = {}
        for backend in backends:
            self.skip_if_backend_unavailable(backend)
            stats = self.run_benchmark(func, *args, backend=backend, **kwargs)
            results[backend] = stats
        return results


class BaseIntegrationTest(BasePolyglotTest):
    """Base class for end-to-end and multi-component integration tests."""
    __test__ = False

    def setUp(self) -> None:
        super().setUp()
        self.integration_results: List[Dict[str, Any]] = []

    def test_end_to_end_flow(self) -> None:
        """Subclasses can override to define full integration flows."""
        pass


class BasePerformanceTest(BasePolyglotTest):
    """Base class for performance regression tests with target thresholds."""
    __test__ = False

    def setUp(self) -> None:
        super().setUp()
        self.performance_metrics: Dict[str, float] = {}

    def assert_meets_performance_target(
        self,
        metric_name: str,
        actual_value: float,
        target_value: float,
        tolerance: float = 0.1,
    ) -> None:
        """Assert that performance meets a target value within an allowable tolerance."""
        if actual_value < target_value * (1.0 - tolerance):
            self.fail(
                f"{metric_name}: {actual_value:.2f} < target {target_value:.2f} "
                f"(tolerance: {tolerance:.1%})"
            )


__all__ = [
    "BasePolyglotTest",
    "BaseBenchmarkTest",
    "BaseIntegrationTest",
    "BasePerformanceTest",
]
