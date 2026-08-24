"""
TruthGPT Optimization Core - Test Suite & Session Builders
==========================================================
Declarative builder patterns for composing test suites, test sessions, and execution pipelines.
"""

from __future__ import annotations

import logging
import sys
import time
import unittest
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from .types import (
    BenchmarkMetrics,
    ExecutionMode,
    FlakyTestPolicy,
    ReportFormat,
    TestCaseResult,
    TestCategory,
    TestFilterConfig,
    TestRunnerConfig,
    TestSessionMetrics,
    TestSeverity,
    TestStatus,
    TestSuiteResult,
    TestType,
)
from .exceptions import TestConfigurationError, TestExecutionError
from .interfaces import ITestHook, ITestReporter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module Aliasing across namespaces
# ---------------------------------------------------------------------------
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.tests.builder":
        sys.modules["tests.builder"] = _mod
    elif __name__ == "tests.builder":
        sys.modules["optimization_core.tests.builder"] = _mod


class TruthGPTTestSuite(unittest.TestSuite):
    """
    Subclass of unittest.TestSuite supporting dictionary-style access
    and rich metadata for fluent builder integration.
    """
    __test__ = False

    def __init__(self, name: str = "custom_suite", **kwargs: Any) -> None:
        super().__init__()
        self.name = name
        self.metadata = kwargs

    def __getitem__(self, key: str) -> Any:
        if key == "name":
            return self.name
        return self.metadata.get(key)

    def get(self, key: str, default: Any = None) -> Any:
        if key == "name":
            return self.name
        return self.metadata.get(key, default)

    def __contains__(self, key: str) -> bool:
        return key == "name" or key in self.metadata


class TestSuiteBuilder:
    """Fluent builder for constructing customized Test Suites."""
    __test__ = False

    def __init__(self, name: str = "custom_suite") -> None:
        self.name = name
        self._test_cases: List[Any] = []
        self._test_files: List[Path] = []
        self._category: TestCategory = TestCategory.CORE
        self._test_type: TestType = TestType.UNIT
        self._severity: TestSeverity = TestSeverity.MAJOR
        self._tags: List[str] = []
        self._timeout_sec: float = 60.0
        self._flaky_policy: Optional[FlakyTestPolicy] = None
        self._fixtures: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}

    def add_test(self, test_case: Any, name: Optional[str] = None) -> TestSuiteBuilder:
        """Add a test function or TestCase class."""
        if name and callable(test_case):
            try:
                test_case.__name__ = name
            except Exception:
                pass
        self._test_cases.append(test_case)
        return self

    def add_test_case(self, test_case: Any, name: Optional[str] = None) -> TestSuiteBuilder:
        """Alias for add_test."""
        return self.add_test(test_case, name=name)

    def add_test_file(self, file_path: Union[str, Path]) -> TestSuiteBuilder:
        """Add a test file path."""
        self._test_files.append(Path(file_path))
        return self

    def with_category(self, category: Union[TestCategory, str]) -> TestSuiteBuilder:
        """Set functional domain category."""
        if isinstance(category, str):
            try:
                category = TestCategory(category.lower())
            except ValueError:
                category = TestCategory[category.upper()]
        self._category = category
        return self

    def with_type(self, test_type: Union[TestType, str]) -> TestSuiteBuilder:
        """Set test type classification."""
        if isinstance(test_type, str):
            try:
                test_type = TestType(test_type.lower())
            except ValueError:
                test_type = TestType[test_type.upper()]
        self._test_type = test_type
        return self

    def with_test_type(self, test_type: Union[TestType, str]) -> TestSuiteBuilder:
        """Alias for with_type."""
        return self.with_type(test_type)

    def with_severity(self, severity: Union[TestSeverity, str]) -> TestSuiteBuilder:
        """Set severity priority."""
        if isinstance(severity, str):
            try:
                severity = TestSeverity(severity.lower())
            except ValueError:
                severity = TestSeverity[severity.upper()]
        self._severity = severity
        return self

    def with_tag(self, tag: str) -> TestSuiteBuilder:
        """Add metadata tag for filtering."""
        if tag not in self._tags:
            self._tags.append(tag)
        return self

    def with_timeout(self, timeout_sec: float) -> TestSuiteBuilder:
        """Set maximum allowable duration per test."""
        self._timeout_sec = timeout_sec
        return self

    def with_flaky_policy(self, max_retries: int = 3, delay_sec: float = 0.5) -> TestSuiteBuilder:
        """Configure flakiness retry policy."""
        self._flaky_policy = FlakyTestPolicy(max_retries=max_retries, delay_sec=delay_sec)
        return self

    def with_fixture(self, name: str, fixture_value_or_factory: Any) -> TestSuiteBuilder:
        """Attach a shared fixture."""
        self._fixtures[name] = fixture_value_or_factory
        return self

    def with_metadata(self, key: str, value: Any) -> TestSuiteBuilder:
        """Attach custom metadata."""
        self._metadata[key] = value
        return self

    def build(self) -> TruthGPTTestSuite:
        """Construct the test suite specification."""
        cat_val = self._category.value.lower() if hasattr(self._category, "value") else str(self._category).lower()
        type_val = self._test_type.value.lower() if hasattr(self._test_type, "value") else str(self._test_type).lower()
        sev_val = self._severity.value.lower() if hasattr(self._severity, "value") else str(self._severity).lower()

        suite = TruthGPTTestSuite(
            name=self.name,
            category=cat_val,
            type=type_val,
            severity=sev_val,
            tags=list(self._tags),
            timeout_sec=self._timeout_sec,
            flaky_policy=self._flaky_policy,
            fixtures=dict(self._fixtures),
            test_cases=list(self._test_cases),
            test_files=list(self._test_files),
            metadata=dict(self._metadata),
        )

        loader = unittest.TestLoader()
        for tc in self._test_cases:
            if isinstance(tc, type) and issubclass(tc, unittest.TestCase):
                loaded = loader.loadTestsFromTestCase(tc)
                suite.addTests(loaded)
            elif isinstance(tc, unittest.TestCase):
                suite.addTest(tc)
            elif callable(tc):
                class FunctionTestCaseWrapper(unittest.TestCase):
                    def __init__(self, fn=tc, *args, **kwargs):
                        super().__init__(*args, **kwargs)
                        self._fn = fn
                    def runTest(self):
                        self._fn()
                    def __str__(self):
                        return getattr(self._fn, "__name__", str(self._fn))
                suite.addTest(FunctionTestCaseWrapper())

        return suite

    def run(self) -> TestSuiteResult:
        """Execute built test suite and return TestSuiteResult."""
        suite = self.build()
        result = unittest.TestResult()
        t0 = time.time()
        suite.run(result)
        dur = time.time() - t0

        res = TestSuiteResult(
            suite_name=self.name,
            total_tests=result.testsRun,
            passed=result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
            failed=len(result.failures),
            skipped=len(result.skipped),
            errors=len(result.errors),
            duration_sec=dur,
            total_time_ms=dur * 1000.0,
        )
        return res


class BenchmarkRunnerBuilder:
    """Fluent builder for composing and executing micro-benchmarks."""
    __test__ = False

    def __init__(self, name: str = "benchmark") -> None:
        self.name = name
        self._target: Optional[Callable[..., Any]] = None
        self._baseline: Optional[Callable[..., Any]] = None
        self._warmup: int = 2
        self._iterations: int = 10
        self._target_args: tuple = ()
        self._target_kwargs: dict = {}
        self._baseline_args: tuple = ()
        self._baseline_kwargs: dict = {}

    def with_target(self, target: Callable[..., Any], *args: Any, **kwargs: Any) -> BenchmarkRunnerBuilder:
        """Set benchmark callable target."""
        self._target = target
        self._target_args = args
        self._target_kwargs = kwargs
        return self

    def with_baseline(self, baseline: Callable[..., Any], *args: Any, **kwargs: Any) -> BenchmarkRunnerBuilder:
        """Set baseline comparison callable."""
        self._baseline = baseline
        self._baseline_args = args
        self._baseline_kwargs = kwargs
        return self

    def warmup(self, n: int) -> BenchmarkRunnerBuilder:
        """Set number of warmup iterations."""
        self._warmup = n
        return self

    def with_warmup(self, n: int) -> BenchmarkRunnerBuilder:
        return self.warmup(n)

    def iterations(self, n: int) -> BenchmarkRunnerBuilder:
        """Set number of timed iterations."""
        self._iterations = n
        return self

    def with_iterations(self, n: int) -> BenchmarkRunnerBuilder:
        return self.iterations(n)

    def execute(self) -> BenchmarkMetrics:
        """Run benchmark and compute statistics."""
        if not self._target:
            raise ValueError("Target function not set")

        for _ in range(self._warmup):
            self._target(*self._target_args, **self._target_kwargs)

        timings: List[float] = []
        for _ in range(self._iterations):
            t0 = time.perf_counter()
            self._target(*self._target_args, **self._target_kwargs)
            timings.append((time.perf_counter() - t0) * 1000.0)

        import statistics
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

        speedup = 1.0
        if self._baseline:
            for _ in range(self._warmup):
                self._baseline(*self._baseline_args, **self._baseline_kwargs)
            base_timings: List[float] = []
            for _ in range(self._iterations):
                tb0 = time.perf_counter()
                self._baseline(*self._baseline_args, **self._baseline_kwargs)
                base_timings.append((time.perf_counter() - tb0) * 1000.0)
            base_avg = statistics.mean(base_timings) if base_timings else 0.0
            if avg_ms > 0:
                speedup = base_avg / avg_ms

        return BenchmarkMetrics(
            name=self.name,
            iterations=self._iterations,
            warmup=self._warmup,
            avg_ms=avg_ms,
            min_ms=min_ms,
            max_ms=max_ms,
            std_ms=std_ms,
            p50_ms=p50,
            p90_ms=p90,
            p95_ms=p95,
            p99_ms=p99,
            throughput=throughput,
            throughput_per_sec=throughput,
            speedup=speedup,
            speedup_vs_baseline=speedup,
        )

    def run(self) -> BenchmarkMetrics:
        """Alias for execute."""
        return self.execute()


BenchmarkBuilder = BenchmarkRunnerBuilder


class TestExecutionPipeline:
    """Execution engine for running composed multi-suite test pipelines."""
    __test__ = False

    def __init__(
        self,
        name: str,
        suites: List[Any],
        config: Optional[TestRunnerConfig] = None,
        reporters: Optional[List[Any]] = None,
        hooks: Optional[List[ITestHook]] = None,
    ) -> None:
        self.name = name
        self.suites = suites
        self.config = config or TestRunnerConfig()
        self.reporters = reporters or []
        self.hooks = hooks or []

    def execute(self) -> TestSessionMetrics:
        """Run all test suites in pipeline and aggregate metrics."""
        t_start = time.time()
        session_metrics = TestSessionMetrics(total_suites=len(self.suites))

        # Notify hooks
        for hook in self.hooks:
            try:
                hook.on_session_start(self.name)
            except Exception as e:
                logger.warning(f"Error in hook on_session_start: {e}")

        for suite_spec in self.suites:
            suite_name = suite_spec.get("name", getattr(suite_spec, "name", "unknown_suite"))
            suite_result = TestSuiteResult(suite_name=suite_name)
            suite_start = time.time()

            for hook in self.hooks:
                try:
                    hook.on_suite_start(suite_name)
                except Exception as e:
                    logger.warning(f"Error in hook on_suite_start: {e}")

            # Run test cases
            test_cases = suite_spec.get("test_cases", getattr(suite_spec, "test_cases", []))
            for test_case in test_cases:
                case_result = self._execute_single_test(test_case, suite_spec)
                suite_result.add_result(case_result)

            suite_result.duration_sec = time.time() - suite_start
            session_metrics.total_tests += suite_result.total_tests
            session_metrics.passed += suite_result.passed
            session_metrics.failed += suite_result.failed
            session_metrics.errors += suite_result.errors
            session_metrics.skipped += suite_result.skipped
            session_metrics.suite_summaries[suite_name] = suite_result.to_dict()

            for hook in self.hooks:
                try:
                    hook.on_suite_end(suite_name, suite_result)
                except Exception as e:
                    logger.warning(f"Error in hook on_suite_end: {e}")

        session_metrics.wall_clock_time = time.time() - t_start

        for hook in self.hooks:
            try:
                hook.on_session_end(session_metrics)
            except Exception as e:
                logger.warning(f"Error in hook on_session_end: {e}")

        # Trigger reporters
        for reporter in self.reporters:
            try:
                if hasattr(reporter, "generate_report"):
                    reporter.generate_report(session_metrics)
            except Exception as e:
                logger.warning(f"Error generating report with {reporter}: {e}")

        return session_metrics

    def _execute_single_test(self, test_case: Any, suite_spec: Any) -> TestCaseResult:
        """Run single test with error isolation, timing, and retry logic."""
        test_name = getattr(test_case, "__name__", str(test_case))
        t_start = time.time()

        for hook in self.hooks:
            try:
                hook.on_test_start(test_name)
            except Exception as e:
                logger.warning(f"Error in hook on_test_start: {e}")

        flaky_policy = getattr(suite_spec, "flaky_policy", None) or (suite_spec.get("flaky_policy") if isinstance(suite_spec, dict) or hasattr(suite_spec, "get") else None) or FlakyTestPolicy(max_retries=1)
        max_attempts = flaky_policy.max_retries
        last_error = None
        result = TestCaseResult(name=test_name, status=TestStatus.PASSED)

        for attempt in range(max_attempts):
            try:
                if callable(test_case):
                    test_case()
                elif isinstance(test_case, unittest.TestCase):
                    res = unittest.TestResult()
                    test_case.run(res)
                    if res.failures:
                        raise AssertionError(str(res.failures[0][1]))
                    if res.errors:
                        raise RuntimeError(str(res.errors[0][1]))

                # Success
                result = TestCaseResult(
                    name=test_name,
                    status=TestStatus.PASSED,
                    duration_sec=time.time() - t_start,
                )
                break
            except AssertionError as e:
                last_error = e
                result = TestCaseResult(
                    name=test_name,
                    status=TestStatus.FAILED,
                    duration_sec=time.time() - t_start,
                    error_message=str(e),
                )
            except Exception as e:
                last_error = e
                result = TestCaseResult(
                    name=test_name,
                    status=TestStatus.ERROR,
                    duration_sec=time.time() - t_start,
                    error_message=str(e),
                )

            if attempt < max_attempts - 1 and last_error is not None:
                time.sleep(flaky_policy.delay_sec)

        for hook in self.hooks:
            try:
                hook.on_test_end(result)
            except Exception as e:
                logger.warning(f"Error in hook on_test_end: {e}")

        return result


TestPipeline = TestExecutionPipeline


class TestSessionBuilder:
    """Fluent builder for composing multi-suite Test Sessions & Execution Pipelines."""
    __test__ = False

    def __init__(self, session_name: str = "truthgpt_test_session") -> None:
        self.session_name = session_name
        self._suites: List[Any] = []
        self._reporters: List[Any] = []
        self._hooks: List[ITestHook] = []
        self._config = TestRunnerConfig()

    def add_suite(self, suite_or_builder: Union[TestSuiteBuilder, Dict[str, Any], TruthGPTTestSuite]) -> TestSessionBuilder:
        """Add a test suite configuration."""
        if isinstance(suite_or_builder, TestSuiteBuilder):
            self._suites.append(suite_or_builder.build())
        else:
            self._suites.append(suite_or_builder)
        return self

    def with_execution_mode(self, mode: Union[ExecutionMode, str]) -> TestSessionBuilder:
        """Set execution concurrency mode."""
        if isinstance(mode, str):
            mode = ExecutionMode(mode.upper())
        self._config.mode = mode
        return self

    def with_reporter(self, reporter: Any) -> TestSessionBuilder:
        """Attach a result reporter."""
        self._reporters.append(reporter)
        return self

    def with_hook(self, hook: ITestHook) -> TestSessionBuilder:
        """Attach a lifecycle hook."""
        self._hooks.append(hook)
        return self

    def with_runner_config(self, config: TestRunnerConfig) -> TestSessionBuilder:
        """Provide custom runner configuration."""
        self._config = config
        return self

    def with_profiler(self, enabled: bool = True) -> TestSessionBuilder:
        """Enable or disable performance profiling."""
        self._config.profile_performance = enabled
        return self

    def with_memory_tracking(self, enabled: bool = True) -> TestSessionBuilder:
        """Enable or disable peak memory tracking."""
        self._config.profile_memory = enabled
        return self

    def build(self) -> TestExecutionPipeline:
        """Construct the configured TestExecutionPipeline."""
        return TestExecutionPipeline(
            name=self.session_name,
            suites=list(self._suites),
            config=self._config,
            reporters=list(self._reporters),
            hooks=list(self._hooks),
        )


def create_test_suite_builder(name: str = "custom_suite") -> TestSuiteBuilder:
    """Helper factory for TestSuiteBuilder."""
    return TestSuiteBuilder(name=name)


def create_test_session_builder(name: str = "truthgpt_session") -> TestSessionBuilder:
    """Helper factory for TestSessionBuilder."""
    return TestSessionBuilder(session_name=name)


def create_benchmark_builder(name: str = "benchmark") -> BenchmarkRunnerBuilder:
    """Helper factory for BenchmarkRunnerBuilder."""
    return BenchmarkRunnerBuilder(name=name)


__all__ = [
    "TruthGPTTestSuite",
    "TestSuiteBuilder",
    "TestSessionBuilder",
    "BenchmarkBuilder",
    "BenchmarkRunnerBuilder",
    "TestExecutionPipeline",
    "TestPipeline",
    "create_test_suite_builder",
    "create_test_session_builder",
    "create_benchmark_builder",
]
