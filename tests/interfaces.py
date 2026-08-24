"""
Core Test Interfaces and Abstract Contracts for TruthGPT Optimization Core.

Defines the formal abstract base classes (ABCs) and protocols governing test cases,
performance profilers, memory trackers, test assertion engines, test reporters,
fixture factories, hooks, and runner orchestrators.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
from pathlib import Path


class ITestCase(ABC):
    """Abstract lifecycle interface for all test cases."""

    @abstractmethod
    def setUp(self) -> None:
        """Initialize test environment, fixtures, and telemetry trackers."""
        pass

    @abstractmethod
    def tearDown(self) -> None:
        """Clean up allocated resources, temp directories, and device tensors."""
        pass


class BaseTestCaseInterface(ITestCase, ABC):
    """Abstract interface for Optimization Core base test cases with domain helpers."""

    @abstractmethod
    def run_benchmark(
        self,
        func: Callable[..., Any],
        *args: Any,
        num_runs: Optional[int] = None,
        warmup_runs: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        """Execute a micro-benchmark with statistical latency tracking."""
        pass

    @abstractmethod
    def skip_if_backend_unavailable(self, backend: str) -> None:
        """Conditionally skip a test if the specified native backend is not loaded."""
        pass


class ITestRunner(ABC):
    """Abstract contract for test discovery and test suite orchestrators."""

    @abstractmethod
    def discover_tests(self, *args: Any, **kwargs: Any) -> List[Any]:
        """Discover test files or test suites matching criteria."""
        pass

    @abstractmethod
    def run_all_tests(self) -> Any:
        """Execute all discovered tests and return structured metrics."""
        pass


class BaseTestRunnerInterface(ITestRunner, ABC):
    """Extended runner interface with specific file list execution."""

    @abstractmethod
    def run_tests(self, test_files: List[str]) -> Dict[str, Any]:
        """Execute discovered tests and return structured results."""
        pass


class ITestReporter(ABC):
    """Abstract contract for test result formatters and exporters."""

    @abstractmethod
    def generate_report(self, session: Any, output_path: Optional[Union[str, Path]] = None) -> str:
        """Generate and save formatted test report."""
        pass


class BaseReporterInterface(ITestReporter, ABC):
    """Extended reporter interface with inline summary formatting."""

    @abstractmethod
    def format_summary(self, results: Dict[str, Any]) -> str:
        """Format an inline text summary of test results."""
        pass


class ITestFixture(ABC):
    """Abstract contract for synthetic test fixtures and data providers."""

    @abstractmethod
    def create_fixture(self, name: str, **kwargs: Any) -> Any:
        """Instantiate a fixture by identifier."""
        pass


class BaseFixtureFactoryInterface(ITestFixture, ABC):
    """Contract for synthetic test data and mock component generation."""

    @abstractmethod
    def create_mock_model(self, **kwargs: Any) -> Any:
        """Create a mock neural network model for testing."""
        pass

    @abstractmethod
    def create_mock_optimizer(self, **kwargs: Any) -> Any:
        """Create a mock optimizer instance for testing."""
        pass

    @abstractmethod
    def create_sample_tensors(self, **kwargs: Any) -> Dict[str, Any]:
        """Generate synthetic tensors for testing."""
        pass


# Alias for mock factory interface
BaseMockFactoryInterface = BaseFixtureFactoryInterface


class ITestDiscovery(ABC):
    """Abstract contract for discovering test modules and test classes."""

    @abstractmethod
    def discover(self, path: Union[str, Path], pattern: Optional[str] = None) -> List[Path]:
        """Discover test paths matching pattern."""
        pass


BaseTestDiscoveryInterface = ITestDiscovery


class ITestAssertion(ABC):
    """Abstract contract for rich domain-specific assertion helpers."""

    @abstractmethod
    def assert_performance_improvement(
        self,
        baseline_ms: float,
        improved_ms: float,
        min_improvement: float = 1.05,
        msg: Optional[str] = None,
    ) -> None:
        """Assert that optimized execution is faster than baseline."""
        pass


class BaseAssertionInterface(ITestAssertion, ABC):
    """Extended assertion contract with tensor and memory bounding checks."""

    @abstractmethod
    def assert_tensor_close(
        self,
        actual: Any,
        expected: Any,
        rtol: float = 1e-4,
        atol: float = 1e-4,
        msg: Optional[str] = None,
    ) -> None:
        """Assert that two tensors or numeric arrays are elementwise close."""
        pass

    @abstractmethod
    def assert_memory_bounded(
        self,
        current_mb: float,
        max_limit_mb: float,
        msg: Optional[str] = None,
    ) -> None:
        """Assert that memory consumption does not breach an upper bound."""
        pass


class ITestHook(ABC):
    """Lifecycle hook for intercepting test session execution events."""

    def on_session_start(self, session: Any) -> None:
        """Called before test session execution begins."""
        pass

    def on_session_end(self, session: Any, metrics: Any) -> None:
        """Called after test session completes."""
        pass

    def on_test_start(self, test: Any) -> None:
        """Called before an individual test starts."""
        pass

    def on_test_end(self, test: Any, result: Any) -> None:
        """Called after an individual test completes."""
        pass


BaseTestHookInterface = ITestHook


class ITestDataManager(ABC):
    """Abstract contract for managing test data caches and artifacts."""

    @abstractmethod
    def load_data(self, key: str) -> Any:
        """Load test data by key."""
        pass

    @abstractmethod
    def store_data(self, key: str, value: Any) -> None:
        """Store test data by key."""
        pass


BaseTestDataManagerInterface = ITestDataManager


class IMockComponent(ABC):
    """Abstract contract for dynamic mock components."""

    @abstractmethod
    def reset(self) -> None:
        """Reset mock component internal state."""
        pass


class BaseProfilerInterface(ABC):
    """Abstract contract for performance and execution latency profiling."""

    @abstractmethod
    def start_profile(self, name: str) -> None:
        """Start recording metrics for a named profiling span."""
        pass

    @abstractmethod
    def end_profile(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Stop recording and return computed span metrics."""
        pass

    @abstractmethod
    def get_profile_summary(self) -> Dict[str, Any]:
        """Return aggregated profiling statistics across all recorded spans."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Clear all active and recorded profiling sessions."""
        pass


ITestProfiler = BaseProfilerInterface


class BaseMemoryTrackerInterface(ABC):
    """Abstract contract for host RAM and device (GPU/MPS) memory introspection."""

    @abstractmethod
    def take_snapshot(self, label: str) -> Dict[str, float]:
        """Capture an instantaneous memory snapshot."""
        pass

    @abstractmethod
    def get_memory_summary(self) -> Dict[str, Any]:
        """Return peak, baseline, and delta memory usage."""
        pass

    @abstractmethod
    def detect_leak(self, threshold_mb: float = 10.0) -> bool:
        """Check whether memory growth across snapshots exceeds a threshold."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset memory tracker state and baseline snapshots."""
        pass


ITestMemoryTracker = BaseMemoryTrackerInterface


__all__ = [
    "ITestCase",
    "BaseTestCaseInterface",
    "ITestRunner",
    "BaseTestRunnerInterface",
    "ITestReporter",
    "BaseReporterInterface",
    "ITestFixture",
    "BaseFixtureFactoryInterface",
    "BaseMockFactoryInterface",
    "ITestDiscovery",
    "BaseTestDiscoveryInterface",
    "ITestAssertion",
    "BaseAssertionInterface",
    "ITestHook",
    "BaseTestHookInterface",
    "ITestDataManager",
    "BaseTestDataManagerInterface",
    "IMockComponent",
    "BaseProfilerInterface",
    "ITestProfiler",
    "BaseMemoryTrackerInterface",
    "ITestMemoryTracker",
]
