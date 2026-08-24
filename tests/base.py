"""
TruthGPT Optimization Core - Standardized Base Test Classes
===========================================================
Reusable, robust test case base classes for unit, integration, benchmark, polyglot,
and asynchronous testing.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import statistics
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple, TypeVar, Union

from .types import BenchmarkMetrics, MockConfig
from .exceptions import BackendUnavailableError, TestAssertionError

logger = logging.getLogger(__name__)

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Module Aliasing across namespaces
# ---------------------------------------------------------------------------
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.tests.base":
        sys.modules["tests.base"] = _mod
    elif __name__ == "tests.base":
        sys.modules["optimization_core.tests.base"] = _mod


class BaseOptimizationCoreTestCase(unittest.TestCase):
    """
    Standard Base TestCase for Optimization Core components.
    Provides isolated temporary directories, mock generators, and domain assertions.
    """
    __test__ = False

    def setUp(self) -> None:
        super().setUp()
        self.start_time = time.time()
        self._temp_dir = tempfile.mkdtemp(prefix="truthgpt_test_")
        self.temp_dir = Path(self._temp_dir)

    def tearDown(self) -> None:
        if hasattr(self, "_temp_dir") and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp dir {self._temp_dir}: {e}")
        super().tearDown()

    def create_temp_file(self, filename: str, content: str = "") -> Path:
        """Create a temporary file within the isolated test directory."""
        file_path = self.temp_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path

    def create_temp_directory(self, dirname: str = "temp_dir") -> Path:
        """Create a temporary subdirectory within the isolated test directory."""
        dir_path = self.temp_dir / dirname
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def create_mock_engine(self, **kwargs: Any) -> Any:
        """Instantiate mock inference engine."""
        try:
            from .utils.test_fixtures import MockInferenceEngine
            return MockInferenceEngine(**kwargs)
        except (ImportError, ModuleNotFoundError):
            class DummyEngine:
                def __init__(self, **kw: Any): self.kw = kw
                def generate(self, prompt: Any, **kw: Any) -> str: return f"Generated: {prompt}"
                def __call__(self, prompt: Any, **kw: Any) -> str: return self.generate(prompt, **kw)
            return DummyEngine(**kwargs)

    def create_mock_processor(self, **kwargs: Any) -> Any:
        """Instantiate mock data processor."""
        try:
            from .utils.test_fixtures import MockDataProcessor
            return MockDataProcessor(**kwargs)
        except (ImportError, ModuleNotFoundError):
            class DummyProcessor:
                def __init__(self, **kw: Any): self.kw = kw
                def read_parquet(self, path: Any, **kw: Any) -> List[Dict[str, int]]: return [{"dummy": 1}]
            return DummyProcessor(**kwargs)

    def create_mock_model(self, **kwargs: Any) -> Any:
        """Instantiate synthetic neural network model."""
        try:
            from .fixtures.mock_components import MockModel
            return MockModel(**kwargs)
        except (ImportError, ModuleNotFoundError):
            try:
                import torch.nn as nn
                return nn.Linear(kwargs.get("input_size", 32), kwargs.get("output_size", 32))
            except ImportError:
                class DummyModel:
                    def __init__(self, **kw: Any): self.kw = kw
                    def __call__(self, x: Any) -> Any: return x
                return DummyModel(**kwargs)

    def create_mock_optimizer(self, **kwargs: Any) -> Any:
        """Instantiate synthetic optimizer."""
        try:
            from .fixtures.mock_components import MockOptimizer
            return MockOptimizer(**kwargs)
        except (ImportError, ModuleNotFoundError):
            class DummyOptimizer:
                def __init__(self, **kw: Any): self.kw = kw
                def step(self, *args: Any) -> Dict[str, Any]: return {"status": "ok"}
                def zero_grad(self) -> None: pass
            return DummyOptimizer(**kwargs)

    def assert_dict_contains(self, actual: Dict[str, Any], expected: Dict[str, Any], path: str = "") -> None:
        """Verify that dictionary contains expected nested key-value pairs."""
        for key, exp_val in expected.items():
            current_path = f"{path}.{key}" if path else key
            self.assertIn(key, actual, f"Key '{current_path}' missing from dictionary")
            if isinstance(exp_val, dict):
                self.assertIsInstance(actual[key], dict, f"'{current_path}' is not a dict")
                self.assert_dict_contains(actual[key], exp_val, current_path)
            else:
                self.assertEqual(actual[key], exp_val, f"'{current_path}': expected {exp_val}, got {actual[key]}")

    def assert_performance_improvement(
        self,
        baseline_ms: float,
        improved_ms: float,
        min_improvement: float = 1.05,
        msg: Optional[str] = None,
    ) -> None:
        """Verify that improved execution time demonstrates sufficient speedup."""
        if baseline_ms <= 0 or improved_ms <= 0:
            raise ValueError("Execution times must be positive numbers")
        speedup = baseline_ms / improved_ms
        self.assertGreaterEqual(
            speedup,
            min_improvement,
            msg or f"Performance improvement factor {speedup:.2f}x does not meet target {min_improvement:.2f}x "
            f"({baseline_ms:.2f}ms baseline vs {improved_ms:.2f}ms improved)",
        )

    def assert_tensor_close(
        self,
        actual: Any,
        expected: Any,
        rtol: float = 1e-4,
        atol: float = 1e-4,
        msg: Optional[str] = None,
    ) -> None:
        """Verify that two PyTorch tensors, numpy ndarrays, or numeric sequences are numerically close."""
        try:
            import torch
            if isinstance(actual, torch.Tensor) and isinstance(expected, torch.Tensor):
                self.assertTrue(
                    torch.allclose(actual, expected, rtol=rtol, atol=atol),
                    msg or f"Tensors not close within rtol={rtol}, atol={atol}",
                )
                return
        except ImportError:
            pass

        try:
            import numpy as np
            if isinstance(actual, (np.ndarray, list, tuple)) and isinstance(expected, (np.ndarray, list, tuple)):
                a_arr = np.asarray(actual)
                e_arr = np.asarray(expected)
                self.assertTrue(
                    np.allclose(a_arr, e_arr, rtol=rtol, atol=atol),
                    msg or f"Arrays not close within rtol={rtol}, atol={atol}",
                )
                return
        except ImportError:
            pass

        self.assertEqual(actual, expected, msg)

    def assert_memory_bounded(
        self,
        current_mb: float,
        max_limit_mb: float,
        msg: Optional[str] = None,
    ) -> None:
        """Assert that memory consumption does not breach an upper bound."""
        self.assertLessEqual(
            current_mb,
            max_limit_mb,
            msg or f"Memory usage ({current_mb:.2f} MB) exceeded upper bound ({max_limit_mb:.2f} MB)",
        )

    def skip_if_backend_unavailable(self, backend: str) -> None:
        """Skip test execution if native polyglot backend is not loaded."""
        b = backend.lower()
        if b == "rust":
            try:
                import truthgpt_rust  # type: ignore # noqa: F401
            except ImportError:
                self.skipTest("Rust native backend (truthgpt_rust) not installed.")
        elif b == "cpp":
            try:
                import _cpp_core  # type: ignore # noqa: F401
            except ImportError:
                self.skipTest("C++ native backend (_cpp_core) not installed.")
        elif b == "julia":
            try:
                from julia import TruthGPTCore  # type: ignore # noqa: F401
            except ImportError:
                self.skipTest("Julia native bridge (TruthGPTCore) not installed.")
        elif b == "cuda":
            try:
                import torch
                if not torch.cuda.is_available():
                    self.skipTest("CUDA GPU hardware not available.")
            except ImportError:
                self.skipTest("PyTorch not installed.")
        elif b == "mps":
            try:
                import torch
                if not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
                    self.skipTest("Apple Silicon MPS hardware not available.")
            except ImportError:
                self.skipTest("PyTorch not installed.")

    def measure_time(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Tuple[Any, float]:
        """Execute callable and return (result, elapsed_ms)."""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return result, elapsed_ms

    def run_benchmark(
        self,
        func: Callable[..., Any],
        *args: Any,
        iterations: int = 10,
        warmup: int = 2,
        name: str = "benchmark",
        num_runs: Optional[int] = None,
        warmup_runs: Optional[int] = None,
        **kwargs: Any,
    ) -> BenchmarkMetrics:
        """Execute a statistical micro-benchmark returning BenchmarkMetrics."""
        runs = num_runs if num_runs is not None else iterations
        warm = warmup_runs if warmup_runs is not None else warmup

        for _ in range(warm):
            func(*args, **kwargs)

        timings: List[float] = []
        for _ in range(runs):
            start = time.perf_counter()
            func(*args, **kwargs)
            timings.append((time.perf_counter() - start) * 1000.0)

        avg_ms = statistics.mean(timings) if timings else 0.0
        min_ms = min(timings) if timings else 0.0
        max_ms = max(timings) if timings else 0.0
        std_ms = statistics.stdev(timings) if len(timings) > 1 else 0.0
        throughput = (1000.0 / avg_ms) if avg_ms > 0 else 0.0

        sorted_timings = sorted(timings)
        n = len(sorted_timings)
        p50 = sorted_timings[int(n * 0.50)] if n > 0 else 0.0
        p90 = sorted_timings[min(n - 1, int(n * 0.90))] if n > 0 else 0.0
        p95 = sorted_timings[min(n - 1, int(n * 0.95))] if n > 0 else 0.0
        p99 = sorted_timings[min(n - 1, int(n * 0.99))] if n > 0 else 0.0

        return BenchmarkMetrics(
            name=name,
            iterations=runs,
            warmup=warm,
            avg_ms=avg_ms,
            min_ms=min_ms,
            max_ms=max_ms,
            std_ms=std_ms,
            p50_ms=p50,
            p90_ms=p90,
            p95_ms=p95,
            p99_ms=p99,
            throughput_per_sec=throughput,
            throughput=throughput,
        )


class BasePolyglotTest(BaseOptimizationCoreTestCase):
    """Specialized base class for polyglot native extension testing."""
    __test__ = False

    def setUp(self) -> None:
        super().setUp()
        self.backend_availability = self._check_backends()

    def _check_backends(self) -> Dict[str, bool]:
        """Inspect available native backend modules."""
        availability = {
            "python": True,
            "rust": False,
            "cpp": False,
            "julia": False,
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
            import truthgpt_rust  # type: ignore # noqa: F401
            availability["rust"] = True
        except ImportError:
            pass

        try:
            import _cpp_core  # type: ignore # noqa: F401
            availability["cpp"] = True
        except ImportError:
            pass

        try:
            from julia import TruthGPTCore  # type: ignore # noqa: F401
            availability["julia"] = True
        except ImportError:
            pass

        return availability


class BaseBenchmarkTestCase(BaseOptimizationCoreTestCase):
    """Specialized base class for statistical benchmark test suites."""
    __test__ = False
    pass


# Backward compatibility alias
BaseBenchmarkTest = BaseBenchmarkTestCase


class BaseIntegrationTestCase(BaseOptimizationCoreTestCase):
    """Specialized base class for end-to-end integration test suites."""
    __test__ = False
    pass


# Backward compatibility alias
BaseIntegrationTest = BaseIntegrationTestCase


class BasePerformanceTest(BaseOptimizationCoreTestCase):
    """Specialized base class for performance regressions and latency validation."""
    __test__ = False
    pass


class BaseAsyncTestCase(BaseOptimizationCoreTestCase):
    """Specialized base class for testing asyncio coroutines cleanly."""
    __test__ = False

    def run_async(self, coro: Coroutine[Any, Any, T], timeout: float = 30.0) -> T:
        """Run coroutine to completion using a clean asyncio event loop."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            try:
                import nest_asyncio  # type: ignore
                nest_asyncio.apply()
            except ImportError:
                pass
        return loop.run_until_complete(asyncio.wait_for(coro, timeout=timeout))


__all__ = [
    "BaseOptimizationCoreTestCase",
    "BasePolyglotTest",
    "BaseBenchmarkTestCase",
    "BaseBenchmarkTest",
    "BaseIntegrationTestCase",
    "BaseIntegrationTest",
    "BasePerformanceTest",
    "BaseAsyncTestCase",
]
