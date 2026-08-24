"""
TruthGPT Optimization Core - Testing Framework Types & Enums
============================================================
Comprehensive typed schemas, value objects, enums, and dataclasses for the test subsystem.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Union


class TestType(str, Enum):
    """Classification of test execution scopes."""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    BENCHMARK = "benchmark"
    REGRESSION = "regression"
    SMOKE = "smoke"
    SYSTEM = "system"
    E2E = "e2e"
    STRESS = "stress"
    POLYGLOT = "polyglot"
    ASYNC = "async"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.value.lower() == other.lower()
        return super().__eq__(other)


class TestStatus(str, Enum):
    """Outcome status for individual tests and suites."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"
    XFAIL = "XFAIL"
    XPASS = "XPASS"
    TIMEOUT = "TIMEOUT"
    TIMED_OUT = "TIMED_OUT"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.value.lower() == other.lower()
        return super().__eq__(other)

    def is_success(self) -> bool:
        """Return True if the test outcome represents a successful execution."""
        return self.value.upper() in ("PASSED", "XFAIL", "XPASS")

    @property
    def is_failure(self) -> bool:
        """Return True if the test outcome represents a failure or error."""
        return self.value.upper() in ("FAILED", "ERROR", "TIMEOUT")


class TestSeverity(str, Enum):
    """Impact and priority level of test scenarios."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    TRIVIAL = "trivial"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.value.lower() == other.lower()
        return super().__eq__(other)


class TestCategory(str, Enum):
    """Functional categories within the Optimization Core."""
    CORE = "core"
    COMPILERS = "compilers"
    MODELS = "models"
    TRAINERS = "trainers"
    UTILS = "utils"
    INFERENCE = "inference"
    DATA = "data"
    POLYGLOT = "polyglot"
    MEMORY = "memory"
    AGENTS = "agents"
    HARDWARE = "hardware"
    SECURITY = "security"
    OPTIMIZERS = "optimizers"
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    BENCHMARK = "benchmark"
    SMOKE = "smoke"
    E2E = "e2e"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.value.lower() == other.lower()
        return super().__eq__(other)


class AssertionLevel(str, Enum):
    """Level of strictness for assertions."""
    STRICT = "strict"
    SOFT = "soft"
    WARNING = "warning"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


class ExecutionMode(str, Enum):
    """Execution orchestration modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PARALLEL_THREADS = "parallel_threads"
    PARALLEL_PROCESSES = "parallel_processes"
    ISOLATED = "isolated"
    ASYNC = "async"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


class ReportFormat(str, Enum):
    """Available serialization formats for test reports."""
    CONSOLE = "console"
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    JUNIT_XML = "junit_xml"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.value.lower() == other.lower()
        return super().__eq__(other)


class BackendType(str, Enum):
    """Polyglot backend target environments."""
    PYTHON = "python"
    RUST = "rust"
    CPP = "cpp"
    JULIA = "julia"
    GO = "go"
    SCALA = "scala"
    ELIXIR = "elixir"
    CUDA = "cuda"
    ROCM = "rocm"
    MPS = "mps"
    CPU = "cpu"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.value.lower() == other.lower()
        return super().__eq__(other)


@dataclass
class TestCaseResult:
    """Detailed telemetry and result of an individual test case execution."""
    test_id: str = "test"
    name: str = "test"
    category: Union[TestCategory, str] = field(default_factory=lambda: TestCategory.CORE)
    status: TestStatus = field(default_factory=lambda: TestStatus.PASSED)
    duration_sec: float = 0.0
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    stack_trace: Optional[str] = None
    stdout: str = ""
    stderr: str = ""
    memory_delta_mb: float = 0.0
    severity: Union[TestSeverity, str] = field(default_factory=lambda: TestSeverity.MAJOR)
    backend: Optional[Union[BackendType, str]] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def __init__(
        self,
        test_id_or_name: str = "test",
        name: Optional[str] = None,
        category: Union[TestCategory, str] = TestCategory.CORE,
        status: TestStatus = TestStatus.PASSED,
        duration_sec: float = 0.0,
        duration_ms: float = 0.0,
        error_message: Optional[str] = None,
        traceback: Optional[str] = None,
        stack_trace: Optional[str] = None,
        stdout: str = "",
        stderr: str = "",
        memory_delta_mb: float = 0.0,
        severity: Union[TestSeverity, str] = TestSeverity.MAJOR,
        backend: Optional[Union[BackendType, str]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        if name is not None:
            self.test_id = test_id_or_name
            self.name = name
        else:
            self.test_id = test_id_or_name
            self.name = test_id_or_name

        self.category = category
        self.status = TestStatus(status) if not isinstance(status, TestStatus) else status
        self.duration_sec = duration_sec
        self.duration_ms = duration_ms
        if self.duration_ms == 0.0 and self.duration_sec > 0.0:
            self.duration_ms = self.duration_sec * 1000.0
        elif self.duration_sec == 0.0 and self.duration_ms > 0.0:
            self.duration_sec = self.duration_ms / 1000.0

        self.error_message = error_message
        self.traceback = traceback or stack_trace
        self.stack_trace = stack_trace or traceback
        self.stdout = stdout
        self.stderr = stderr
        self.memory_delta_mb = memory_delta_mb
        self.severity = severity
        self.backend = backend
        self.metrics = metrics or {}
        self.metadata = metadata or {}
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to dictionary."""
        cat_val = self.category.value if isinstance(self.category, Enum) else str(self.category)
        stat_val = self.status.value if isinstance(self.status, Enum) else str(self.status)
        sev_val = self.severity.value if isinstance(self.severity, Enum) else str(self.severity)
        be_val = self.backend.value if isinstance(self.backend, Enum) else (str(self.backend) if self.backend else None)

        return {
            "name": self.name,
            "test_id": self.test_id,
            "status": stat_val,
            "category": cat_val,
            "severity": sev_val,
            "duration_sec": round(self.duration_sec, 4),
            "duration_ms": round(self.duration_ms, 3),
            "error_message": self.error_message,
            "traceback": self.traceback,
            "stack_trace": self.stack_trace,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "memory_delta_mb": round(self.memory_delta_mb, 2),
            "backend": be_val,
            "metrics": self.metrics,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


# Alias for backward compatibility
TestResult = TestCaseResult


@dataclass
class TestSuiteResult:
    """Aggregated execution results across an entire test suite run."""
    suite_name: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    duration_sec: float = 0.0
    total_time_ms: float = 0.0
    results: List[TestCaseResult] = field(default_factory=list)
    backend_status: Dict[str, bool] = field(default_factory=dict)
    system_info: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.total_time_ms == 0.0 and self.duration_sec > 0.0:
            self.total_time_ms = self.duration_sec * 1000.0
        elif self.duration_sec == 0.0 and self.total_time_ms > 0.0:
            self.duration_sec = self.total_time_ms / 1000.0

    @property
    def success(self) -> bool:
        """True if zero failures and zero errors."""
        return self.failed == 0 and self.errors == 0

    @property
    def is_successful(self) -> bool:
        """Alias for success property."""
        return self.success

    @property
    def success_rate(self) -> float:
        """Percentage of successfully passed tests."""
        if self.total_tests == 0:
            return 100.0 if self.success else 0.0
        return round((self.passed / self.total_tests) * 100.0, 2)

    @property
    def pass_rate(self) -> float:
        """Alias for success_rate."""
        return self.success_rate

    def add_result(self, result: TestCaseResult) -> None:
        """Incorporate a single test case result into suite aggregates."""
        self.results.append(result)
        self.total_tests += 1
        stat_upper = str(result.status.value if isinstance(result.status, Enum) else result.status).upper()

        if stat_upper == "PASSED":
            self.passed += 1
        elif stat_upper == "FAILED":
            self.failed += 1
        elif stat_upper in ("ERROR", "TIMEOUT"):
            self.errors += 1
        elif stat_upper == "SKIPPED":
            self.skipped += 1

    def to_dict(self) -> Dict[str, Any]:
        """Serialize suite result to dictionary."""
        return {
            "suite_name": self.suite_name,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "skipped": self.skipped,
            "duration_sec": round(self.duration_sec, 4),
            "total_time_ms": round(self.total_time_ms or (self.duration_sec * 1000.0), 2),
            "success": self.success,
            "is_successful": self.is_successful,
            "success_rate": self.success_rate,
            "pass_rate": self.pass_rate,
            "pass_rate_pct": self.pass_rate,
            "backend_status": self.backend_status,
            "system_info": self.system_info,
            "results": [r.to_dict() for r in self.results],
            "metadata": self.metadata,
        }


@dataclass
class TestSessionMetrics:
    """Comprehensive performance and resource metrics across an entire test session."""
    total_suites: int = 0
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    wall_clock_time: float = 0.0
    peak_memory_mb: float = 0.0
    average_memory_mb: float = 0.0
    cpu_percent: float = 0.0
    suite_summaries: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    suite_results: List[TestSuiteResult] = field(default_factory=list)
    environment_info: Dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Session-wide success rate percentage."""
        if self.total_tests == 0:
            return 100.0 if (self.failed == 0 and self.errors == 0) else 0.0
        return round(((self.total_tests - self.failed - self.errors) / self.total_tests) * 100.0, 2)

    @property
    def is_successful(self) -> bool:
        """Return True if session had zero failures and zero errors."""
        return self.failed == 0 and self.errors == 0

    def add_suite_result(self, suite: TestSuiteResult) -> None:
        """Add a completed suite result into session aggregates."""
        self.total_suites += 1
        self.total_tests += suite.total_tests
        self.passed += suite.passed
        self.failed += suite.failed
        self.errors += suite.errors
        self.skipped += suite.skipped
        self.suite_results.append(suite)
        self.suite_summaries[suite.suite_name] = suite.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session metrics to dictionary."""
        return {
            "total_suites": self.total_suites,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "skipped": self.skipped,
            "success_rate": self.success_rate,
            "is_successful": self.is_successful,
            "wall_clock_time": round(self.wall_clock_time, 4),
            "peak_memory_mb": round(self.peak_memory_mb, 2),
            "average_memory_mb": round(self.average_memory_mb, 2),
            "cpu_percent": round(self.cpu_percent, 2),
            "suite_summaries": self.suite_summaries,
            "environment_info": self.environment_info,
        }

    def to_json(self) -> str:
        """Serialize session metrics to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class TestFilterConfig:
    """Filtering criteria for selective test discovery and execution."""
    categories: List[Union[TestCategory, str]] = field(default_factory=list)
    types: List[Union[TestType, str]] = field(default_factory=list)
    severities: List[Union[TestSeverity, str]] = field(default_factory=list)
    pattern: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    exclude_tags: List[str] = field(default_factory=list)
    backends: List[Union[BackendType, str]] = field(default_factory=list)
    fail_fast: bool = False
    max_failures: int = 0

    def matches(self, path_or_name: str, category: Optional[str] = None) -> bool:
        """Check if test path/name and category match filter criteria."""
        if self.pattern and self.pattern.lower() not in path_or_name.lower():
            return False
        if category and self.categories:
            cat_strs = [c.value.upper() if isinstance(c, Enum) else str(c).upper() for c in self.categories]
            if category.upper() not in cat_strs:
                return False
        return True


@dataclass
class BenchmarkMetrics:
    """Statistical measurement container for benchmark test routines."""
    name: str = "benchmark"
    iterations: int = 10
    warmup: int = 3
    avg_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0
    std_ms: float = 0.0
    p50_ms: float = 0.0
    p90_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    throughput_per_sec: float = 0.0
    throughput: float = 0.0
    speedup_vs_baseline: float = 1.0
    speedup: float = 1.0
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.throughput == 0.0 and self.throughput_per_sec > 0.0:
            self.throughput = self.throughput_per_sec
        elif self.throughput_per_sec == 0.0 and self.throughput > 0.0:
            self.throughput_per_sec = self.throughput
        if self.speedup != 1.0 and self.speedup_vs_baseline == 1.0:
            self.speedup_vs_baseline = self.speedup
        elif self.speedup_vs_baseline != 1.0 and self.speedup == 1.0:
            self.speedup = self.speedup_vs_baseline

    def to_dict(self) -> Dict[str, Any]:
        """Serialize benchmark metrics to dictionary."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "warmup": self.warmup,
            "avg_ms": round(self.avg_ms, 4),
            "min_ms": round(self.min_ms, 4),
            "max_ms": round(self.max_ms, 4),
            "std_ms": round(self.std_ms, 4),
            "p50_ms": round(self.p50_ms, 4),
            "p90_ms": round(self.p90_ms, 4),
            "p95_ms": round(self.p95_ms, 4),
            "p99_ms": round(self.p99_ms, 4),
            "throughput": round(self.throughput, 2),
            "throughput_per_sec": round(self.throughput_per_sec, 2),
            "speedup": round(self.speedup or self.speedup_vs_baseline, 2),
            "speedup_vs_baseline": round(self.speedup_vs_baseline or self.speedup, 2),
            "extra_metadata": self.extra_metadata,
        }

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key) or key in self.extra_metadata

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        if key in self.extra_metadata:
            return self.extra_metadata[key]
        raise KeyError(key)


# Aliases for backward compatibility
BenchmarkMetric = BenchmarkMetrics


@dataclass
class MemorySnapshot:
    """Instantaneous recording of host and device memory."""
    timestamp: float = field(default_factory=time.time)
    label: str = "snapshot"
    rss_mb: float = 0.0
    vms_mb: float = 0.0
    gpu_allocated_mb: float = 0.0
    gpu_cached_mb: float = 0.0
    gpu_reserved_mb: float = 0.0
    peak_mb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "label": self.label,
            "rss_mb": round(self.rss_mb, 2),
            "vms_mb": round(self.vms_mb, 2),
            "gpu_allocated_mb": round(self.gpu_allocated_mb, 2),
            "gpu_cached_mb": round(self.gpu_cached_mb, 2),
            "gpu_reserved_mb": round(self.gpu_reserved_mb, 2),
            "peak_mb": round(self.peak_mb, 2),
        }


MemoryProfile = MemorySnapshot


@dataclass
class FlakyTestPolicy:
    """Configuration for automatic retry of intermittent or flaky tests."""
    max_retries: int = 3
    delay_sec: float = 0.5
    backoff_multiplier: float = 1.5
    backoff_factor: float = 1.5
    retry_exceptions: tuple = (Exception,)


@dataclass
class MockConfig:
    """Configuration for mock engine and synthetic data generation."""
    enabled: bool = True
    seed: int = 42
    latency_ms: float = 0.0
    mock_latency_ms: float = 0.0
    failure_rate: float = 0.0
    fail_rate: float = 0.0
    sample_size: int = 100
    tensor_dim: int = 512
    backend: str = "mock"
    mock_device: str = "cpu"


@dataclass
class TestRunnerConfig:
    """Master configuration for the TruthGPT test execution runner."""
    verbose: bool = True
    mode: ExecutionMode = field(default_factory=lambda: ExecutionMode.SEQUENTIAL)
    parallel: bool = False
    max_workers: int = 4
    coverage: bool = False
    enable_coverage: bool = False
    profile_performance: bool = True
    enable_profiling: bool = True
    profile_memory: bool = True
    enable_memory_tracking: bool = True
    timeout_sec: float = 300.0
    timeout_seconds: float = 300.0
    fail_fast: bool = False
    output_formats: List[ReportFormat] = field(default_factory=lambda: [ReportFormat.CONSOLE])
    report_dir: str = "test_reports"
    project_root: str = "."
    device_target: str = "cpu"
    flaky_policy: FlakyTestPolicy = field(default_factory=FlakyTestPolicy)
    filter_config: TestFilterConfig = field(default_factory=TestFilterConfig)


@dataclass
class TestCoverageSummary:
    """Code coverage aggregation metrics."""
    total_statements: int = 0
    covered_statements: int = 0
    coverage_percentage: float = 0.0
    missing_lines_by_file: Dict[str, List[int]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_statements": self.total_statements,
            "covered_statements": self.covered_statements,
            "coverage_percentage": round(self.coverage_percentage, 2),
            "missing_lines_by_file": self.missing_lines_by_file,
        }


@dataclass
class ExecutionMetrics:
    """Hardware and performance execution telemetry for a test run."""
    total_duration_sec: float = 0.0
    peak_rss_mb: float = 0.0
    peak_gpu_mb: float = 0.0
    cpu_percent: float = 0.0
    throughput_ops_sec: float = 0.0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


TestEnvironmentConfig = TestRunnerConfig


__all__ = [
    "TestType",
    "TestStatus",
    "TestSeverity",
    "TestCategory",
    "AssertionLevel",
    "ExecutionMode",
    "ReportFormat",
    "BackendType",
    "TestCaseResult",
    "TestResult",
    "TestSuiteResult",
    "TestSessionMetrics",
    "TestFilterConfig",
    "BenchmarkMetrics",
    "BenchmarkMetric",
    "MemorySnapshot",
    "MemoryProfile",
    "FlakyTestPolicy",
    "MockConfig",
    "TestRunnerConfig",
    "TestEnvironmentConfig",
    "TestCoverageSummary",
    "ExecutionMetrics",
]
