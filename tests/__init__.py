"""
TruthGPT Optimization Core - Test Framework Subsystem
=====================================================
Comprehensive, enterprise-grade testing architecture for optimization algorithms,
polyglot native backends, inference engines, memory caches, and agent frameworks.

Provides:
- Strongly typed schemas, enums, dataclasses, and execution configs (types.py)
- Formal abstract lifecycle interfaces and protocols (interfaces.py)
- Granular typed exception hierarchy (exceptions.py)
- Thread-safe dynamic component and fixture registry (registry.py)
- Fluent declarative test suite and execution pipeline builders (builder.py)
- Multi-format test reporters (Console, JSON, Markdown, HTML) (reporters/)
- Standardized, robust base test cases for unit, polyglot, benchmark, and async testing (base.py)
- High-throughput test runner with telemetry, memory tracking, and flakiness isolation (runner.py)
"""

from __future__ import annotations

__version__ = "2.0.0"
__author__ = "TruthGPT Optimization Core Architecture Team"

# Test directories
TEST_DIRS = ["unit", "integration", "performance", "benchmark", "fixtures", "utils"]

# ---------------------------------------------------------------------------
# 1. Types & Schemas
# ---------------------------------------------------------------------------
from .types import (
    AssertionLevel,
    BackendType,
    BenchmarkMetric,
    BenchmarkMetrics,
    ExecutionMetrics,
    ExecutionMode,
    FlakyTestPolicy,
    MemoryProfile,
    MemorySnapshot,
    MockConfig,
    ReportFormat,
    TestCaseResult,
    TestCategory,
    TestCoverageSummary,
    TestEnvironmentConfig,
    TestFilterConfig,
    TestResult,
    TestRunnerConfig,
    TestSessionMetrics,
    TestSeverity,
    TestStatus,
    TestSuiteResult,
    TestType,
)

# ---------------------------------------------------------------------------
# 2. Interfaces & Protocols
# ---------------------------------------------------------------------------
from .interfaces import (
    BaseAssertionInterface,
    BaseFixtureFactoryInterface,
    BaseMemoryTrackerInterface,
    BaseMockFactoryInterface,
    BaseProfilerInterface,
    BaseReporterInterface,
    BaseTestCaseInterface,
    BaseTestDataManagerInterface,
    BaseTestDiscoveryInterface,
    BaseTestHookInterface,
    BaseTestRunnerInterface,
    IMockComponent,
    ITestAssertion,
    ITestCase,
    ITestDataManager,
    ITestDiscovery,
    ITestFixture,
    ITestHook,
    ITestMemoryTracker,
    ITestProfiler,
    ITestReporter,
    ITestRunner,
)

# ---------------------------------------------------------------------------
# 3. Typed Exceptions
# ---------------------------------------------------------------------------
from .exceptions import (
    AssertionErrorWrapper,
    BackendUnavailableError,
    BenchmarkFailureError,
    EnvironmentSetupError,
    FixtureError,
    FlakyTestError,
    MemoryTrackingError,
    MockComponentError,
    ProfilerError,
    RegistryError,
    TestAssertionError,
    TestConfigurationError,
    TestDiscoveryError,
    TestExecutionError,
    TestFixtureError,
    TestFrameworkError,
    TestReportError,
    TestTimeoutError,
)

# ---------------------------------------------------------------------------
# 4. Registry & Discovery Catalog
# ---------------------------------------------------------------------------
from .registry import (
    TEST_REGISTRY,
    TestRegistry,
    create_fixture,
    create_mock,
    create_reporter,
    get_test_registry,
    get_test_registry_info,
    is_test_component_registered,
    list_available_assertions,
    list_available_benchmarks,
    list_available_fixtures,
    list_available_mocks,
    list_available_reporters,
    list_available_test_suites,
    register_assertion,
    register_benchmark,
    register_fixture,
    register_mock,
    register_reporter,
    register_test_suite,
)

# ---------------------------------------------------------------------------
# 5. Declarative Builders
# ---------------------------------------------------------------------------
from .builder import (
    BenchmarkBuilder,
    BenchmarkRunnerBuilder,
    TestExecutionPipeline,
    TestPipeline,
    TestSessionBuilder,
    TestSuiteBuilder,
    create_benchmark_builder,
    create_test_session_builder,
    create_test_suite_builder,
)

# ---------------------------------------------------------------------------
# 6. Standard Base Test Classes
# ---------------------------------------------------------------------------
from .base import (
    BaseAsyncTestCase,
    BaseBenchmarkTest,
    BaseBenchmarkTestCase,
    BaseIntegrationTest,
    BaseIntegrationTestCase,
    BaseOptimizationCoreTestCase,
    BasePerformanceTest,
    BasePolyglotTest,
)

BaseTestCase = BaseOptimizationCoreTestCase
BasePerformanceTestCase = BasePerformanceTest

# ---------------------------------------------------------------------------
# 7. Reporters
# ---------------------------------------------------------------------------
from .reporters import (
    BaseTestReporter,
    ConsoleTestReporter,
    HTMLTestReporter,
    JSONTestReporter,
    MarkdownTestReporter,
    create_reporter as create_test_reporter,
)

# ---------------------------------------------------------------------------
# 8. Test Runner Engine
# ---------------------------------------------------------------------------
from .runner import (
    MemoryTracker,
    PerformanceProfiler,
    TruthGPTTestRunner,
    discover_tests,
    run_tests,
)

__all__ = [
    # Metadata
    "__version__",
    "__author__",
    "TEST_DIRS",
    "discover_tests",
    "run_tests",
    # Types
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
    # Interfaces
    "BaseTestCaseInterface",
    "ITestCase",
    "BaseProfilerInterface",
    "ITestProfiler",
    "BaseMemoryTrackerInterface",
    "ITestMemoryTracker",
    "BaseAssertionInterface",
    "ITestAssertion",
    "BaseReporterInterface",
    "ITestReporter",
    "BaseFixtureFactoryInterface",
    "BaseMockFactoryInterface",
    "ITestFixture",
    "BaseTestDiscoveryInterface",
    "ITestDiscovery",
    "BaseTestHookInterface",
    "ITestHook",
    "BaseTestDataManagerInterface",
    "ITestDataManager",
    "IMockComponent",
    "BaseTestRunnerInterface",
    "ITestRunner",
    # Exceptions
    "TestFrameworkError",
    "TestDiscoveryError",
    "TestExecutionError",
    "BackendUnavailableError",
    "TestAssertionError",
    "AssertionErrorWrapper",
    "TestFixtureError",
    "FixtureError",
    "BenchmarkFailureError",
    "ProfilerError",
    "MemoryTrackingError",
    "EnvironmentSetupError",
    "RegistryError",
    "TestConfigurationError",
    "TestReportError",
    "MockComponentError",
    "FlakyTestError",
    "TestTimeoutError",
    # Registry
    "TestRegistry",
    "TEST_REGISTRY",
    "get_test_registry",
    "register_test_suite",
    "register_benchmark",
    "register_fixture",
    "register_mock",
    "register_reporter",
    "register_assertion",
    "create_fixture",
    "create_mock",
    "create_reporter",
    "list_available_fixtures",
    "list_available_test_suites",
    "list_available_benchmarks",
    "list_available_reporters",
    "list_available_mocks",
    "list_available_assertions",
    "get_test_registry_info",
    "is_test_component_registered",
    # Builders
    "TestSuiteBuilder",
    "TestSessionBuilder",
    "TestExecutionPipeline",
    "TestPipeline",
    "BenchmarkBuilder",
    "BenchmarkRunnerBuilder",
    "create_test_suite_builder",
    "create_test_session_builder",
    "create_benchmark_builder",
    # Base Classes
    "BaseOptimizationCoreTestCase",
    "BaseTestCase",
    "BasePolyglotTest",
    "BaseBenchmarkTestCase",
    "BaseBenchmarkTest",
    "BaseIntegrationTestCase",
    "BaseIntegrationTest",
    "BasePerformanceTestCase",
    "BasePerformanceTest",
    "BaseAsyncTestCase",
    # Reporters
    "BaseTestReporter",
    "ConsoleTestReporter",
    "JSONTestReporter",
    "MarkdownTestReporter",
    "HTMLTestReporter",
    "create_test_reporter",
    # Runner
    "TruthGPTTestRunner",
    "PerformanceProfiler",
    "MemoryTracker",
]