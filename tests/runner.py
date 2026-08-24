"""
TruthGPT Optimization Core - Unified Test Runner Engine
=======================================================
Enterprise-grade test executor with multi-backend discovery, execution profiling,
memory tracking, flakiness retries, and multi-format report generation.
"""

from __future__ import annotations

import argparse
import importlib
import logging
import os
import sys
import time
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from .types import (
    ExecutionMode,
    ReportFormat,
    TestCaseResult,
    TestCategory,
    TestFilterConfig,
    TestRunnerConfig,
    TestSessionMetrics,
    TestStatus,
    TestSuiteResult,
)
from .interfaces import ITestHook, ITestRunner
from .reporters import (
    ConsoleTestReporter,
    HTMLTestReporter,
    JSONTestReporter,
    MarkdownTestReporter,
    create_reporter,
)
from .exceptions import TestDiscoveryError, TestExecutionError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module Aliasing across namespaces
# ---------------------------------------------------------------------------
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.tests.runner":
        sys.modules["tests.runner"] = _mod
    elif __name__ == "tests.runner":
        sys.modules["optimization_core.tests.runner"] = _mod


class PerformanceProfiler:
    """Lightweight performance profiler for test runs."""

    def __init__(self) -> None:
        self._start_time: float = 0.0
        self._active_spans: Dict[str, float] = {}
        self._profiles: List[Dict[str, Any]] = []

    def start_profile(self, name: str = "span") -> None:
        self._start_time = time.perf_counter()
        self._active_spans[name] = self._start_time

    def end_profile(self, name: Optional[str] = None) -> Dict[str, Any]:
        t_end = time.perf_counter()
        if name and name in self._active_spans:
            duration = t_end - self._active_spans.pop(name)
        else:
            duration = t_end - self._start_time
        res = {"name": name or "default", "duration_sec": duration, "duration_ms": duration * 1000.0}
        self._profiles.append(res)
        return res

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_profiles": len(self._profiles),
            "profiles": list(self._profiles),
        }

    def reset(self) -> None:
        self._active_spans.clear()
        self._profiles.clear()
        self._start_time = 0.0


class MemoryTracker:
    """Memory usage tracker using psutil when available."""

    def __init__(self) -> None:
        self.peak_memory_mb: float = 0.0
        self.baseline_memory_mb: float = 0.0
        self._snapshots: List[Dict[str, float]] = []
        self._has_psutil: bool = False
        try:
            import psutil  # type: ignore
            self._process = psutil.Process(os.getpid())
            self._has_psutil = True
            self.baseline_memory_mb = self.sample_memory_mb()
        except ImportError:
            self._process = None

    def sample_memory_mb(self) -> float:
        """Measure current memory consumption in MB."""
        if self._has_psutil and self._process:
            try:
                mem_bytes = self._process.memory_info().rss
                mb = mem_bytes / (1024 * 1024)
                if mb > self.peak_memory_mb:
                    self.peak_memory_mb = mb
                return mb
            except Exception:
                return 0.0
        return 0.0

    def take_snapshot(self, label: str = "snapshot") -> Dict[str, float]:
        """Record instantaneous memory snapshot."""
        current_mb = self.sample_memory_mb()
        snap = {
            "label": label,
            "timestamp": time.time(),
            "rss_mb": current_mb,
            "peak_mb": self.peak_memory_mb,
            "delta_mb": current_mb - self.baseline_memory_mb,
        }
        self._snapshots.append(snap)
        return snap

    def get_memory_summary(self) -> Dict[str, Any]:
        """Return memory statistics summary."""
        current_mb = self.sample_memory_mb()
        return {
            "baseline_mb": self.baseline_memory_mb,
            "current_mb": current_mb,
            "peak_mb": self.peak_memory_mb,
            "delta_mb": current_mb - self.baseline_memory_mb,
            "snapshots_count": len(self._snapshots),
        }

    def detect_leak(self, threshold_mb: float = 10.0) -> bool:
        """Determine whether uncollected memory growth exceeds threshold."""
        current_mb = self.sample_memory_mb()
        return (current_mb - self.baseline_memory_mb) > threshold_mb

    def reset(self) -> None:
        """Reset memory tracker baseline and peak values."""
        self._snapshots.clear()
        self.baseline_memory_mb = self.sample_memory_mb()
        self.peak_memory_mb = self.baseline_memory_mb


class TruthGPTTestRunner(ITestRunner):
    """
    Unified Test Runner for TruthGPT Optimization Core.
    Executes unit, integration, performance, and benchmark tests with full telemetry.
    """

    def __init__(
        self,
        config: Optional[TestRunnerConfig] = None,
        hooks: Optional[List[ITestHook]] = None,
    ) -> None:
        self.config = config or TestRunnerConfig()
        self.hooks = hooks or []
        self.profiler = PerformanceProfiler()
        self.memory_tracker = MemoryTracker()
        self._root_dir = Path(__file__).parent.resolve()

    def discover_tests(self, filter_config: Optional[TestFilterConfig] = None) -> List[str]:
        """Discover all test files in the optimization core test directories."""
        discovered: List[Path] = []
        target_dirs = ["unit", "integration", "performance", "benchmark"]

        # Search subdirectories
        for sub_dir in target_dirs:
            dir_path = self._root_dir / sub_dir
            if dir_path.exists():
                for test_file in dir_path.glob("test_*.py"):
                    if test_file not in discovered:
                        discovered.append(test_file)

        # Search root tests directory for test_*.py
        for test_file in self._root_dir.glob("test_*.py"):
            if test_file not in discovered:
                discovered.append(test_file)

        filter_cfg = filter_config or self.config.filter_config
        filtered_paths = []

        for p in discovered:
            file_name = p.name

            # Pattern filtering
            if filter_cfg and filter_cfg.pattern:
                if filter_cfg.pattern.lower() not in file_name.lower() and filter_cfg.pattern.lower() not in str(p).lower():
                    continue

            filtered_paths.append(str(p.resolve()))

        return sorted(filtered_paths)

    def run_test_suite(self, test_files: Sequence[str]) -> TestSessionMetrics:
        """Run a collection of test files and collect results."""
        start_time = time.time()
        session_metrics = TestSessionMetrics(total_suites=len(test_files))
        session_metrics.environment_info = {
            "python_version": sys.version,
            "platform": sys.platform,
            "cwd": os.getcwd(),
        }

        # Project root for sys.path resolution
        project_root = self._root_dir.parent.resolve()
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        if str(self._root_dir) not in sys.path:
            sys.path.insert(0, str(self._root_dir))

        for test_file_str in test_files:
            test_path = Path(test_file_str)
            suite_name = test_path.stem
            suite_result = TestSuiteResult(suite_name=suite_name)
            suite_start = time.time()

            # Memory sample before suite
            self.memory_tracker.sample_memory_mb()

            # Load tests
            loader = unittest.TestLoader()
            suite = unittest.TestSuite()

            try:
                try:
                    rel_path = test_path.resolve().relative_to(project_root)
                    mod_name = str(rel_path.with_suffix("")).replace("\\", ".").replace("/", ".")
                    mod = importlib.import_module(mod_name)
                    suite = loader.loadTestsFromModule(mod)
                except Exception:
                    suite = loader.discover(
                        start_dir=str(test_path.parent),
                        pattern=test_path.name,
                    )
            except Exception as e:
                logger.warning(f"Failed to load suite from {test_file_str}: {e}")
                err_result = TestCaseResult(
                    name=f"load_suite_{suite_name}",
                    status=TestStatus.ERROR,
                    error_message=str(e),
                )
                suite_result.add_result(err_result)

            # Execute suite
            if suite.countTestCases() > 0:
                result_collector = unittest.TestResult()
                suite.run(result_collector)

                # Record individual test case outcomes
                for test_case, err_tb in result_collector.failures:
                    suite_result.add_result(
                        TestCaseResult(
                            name=str(test_case),
                            status=TestStatus.FAILED,
                            error_message=str(err_tb),
                        )
                    )

                for test_case, err_tb in result_collector.errors:
                    suite_result.add_result(
                        TestCaseResult(
                            name=str(test_case),
                            status=TestStatus.ERROR,
                            error_message=str(err_tb),
                        )
                    )

                for test_case, reason in result_collector.skipped:
                    suite_result.add_result(
                        TestCaseResult(
                            name=str(test_case),
                            status=TestStatus.SKIPPED,
                            error_message=str(reason),
                        )
                    )

                # Compute passed tests
                pass_count = result_collector.testsRun - len(result_collector.failures) - len(result_collector.errors) - len(result_collector.skipped)
                for i in range(max(0, pass_count)):
                    suite_result.add_result(
                        TestCaseResult(
                            name=f"{suite_name}_test_{i+1}",
                            status=TestStatus.PASSED,
                        )
                    )

            suite_result.duration_sec = time.time() - suite_start

            # Aggregate into session
            session_metrics.total_tests += suite_result.total_tests
            session_metrics.passed += suite_result.passed
            session_metrics.failed += suite_result.failed
            session_metrics.errors += suite_result.errors
            session_metrics.skipped += suite_result.skipped
            session_metrics.suite_summaries[suite_name] = suite_result.to_dict()

            # Sample peak memory
            self.memory_tracker.sample_memory_mb()

        session_metrics.wall_clock_time = time.time() - start_time
        session_metrics.peak_memory_mb = self.memory_tracker.peak_memory_mb

        # Emit configured reports
        self.emit_reports(session_metrics)

        return session_metrics

    def run_tests(self, test_files: List[str]) -> Dict[str, Any]:
        """Execute test files and return structured results dict."""
        metrics = self.run_test_suite(test_files)
        return metrics.to_dict()

    def run_all_tests(self) -> TestSessionMetrics:
        """Discover and execute all tests across the repository."""
        test_files = self.discover_tests()
        return self.run_test_suite(test_files)

    def run_pattern(self, pattern: str) -> TestSessionMetrics:
        """Run tests matching a substring pattern."""
        filter_cfg = TestFilterConfig(pattern=pattern)
        test_files = self.discover_tests(filter_config=filter_cfg)
        return self.run_test_suite(test_files)

    def emit_reports(
        self,
        session_metrics: TestSessionMetrics,
        formats: Optional[List[ReportFormat]] = None,
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[ReportFormat, str]:
        """Emit reports across all specified format styles."""
        target_formats = formats or self.config.output_formats
        out_dir = Path(output_dir) if output_dir else Path(self.config.report_dir)
        results: Dict[ReportFormat, str] = {}

        for fmt in target_formats:
            try:
                reporter = create_reporter(fmt, output_dir=out_dir)
                report_str = reporter.generate_report(session_metrics)
                results[fmt] = report_str
            except Exception as e:
                logger.warning(f"Failed to generate {fmt} report: {e}")

        return results


def discover_tests(pattern: Optional[str] = None) -> List[str]:
    """Discover all test files in the test suite."""
    runner = TruthGPTTestRunner()
    filter_cfg = TestFilterConfig(pattern=pattern) if pattern else None
    return runner.discover_tests(filter_config=filter_cfg)


def run_tests(pattern: Optional[str] = None) -> TestSessionMetrics:
    """Run all tests or tests matching a pattern."""
    runner = TruthGPTTestRunner()
    if pattern:
        return runner.run_pattern(pattern)
    return runner.run_all_tests()


def main() -> None:
    """CLI entrypoint for executing TruthGPT test suites."""
    parser = argparse.ArgumentParser(description="TruthGPT Optimization Core Unified Test Runner")
    parser.add_argument("--pattern", "-p", type=str, default=None, help="Filter test files by pattern")
    parser.add_argument("--format", "-f", nargs="+", default=["console"], help="Report formats (console, json, markdown, html)")
    parser.add_argument("--report-dir", "-d", type=str, default="test_reports", help="Directory to store reports")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure")
    parser.add_argument("--verbose", "-v", action="store_true", default=True, help="Enable verbose logging")

    args = parser.parse_args()

    report_formats = []
    for fmt_str in args.format:
        try:
            report_formats.append(ReportFormat(fmt_str.lower()))
        except ValueError:
            logger.warning(f"Unknown report format '{fmt_str}', skipping")

    if not report_formats:
        report_formats = [ReportFormat.CONSOLE]

    config = TestRunnerConfig(
        verbose=args.verbose,
        fail_fast=args.fail_fast,
        output_formats=report_formats,
        report_dir=args.report_dir,
        filter_config=TestFilterConfig(pattern=args.pattern),
    )

    runner = TruthGPTTestRunner(config=config)

    if args.pattern:
        metrics = runner.run_pattern(args.pattern)
    else:
        metrics = runner.run_all_tests()

    if metrics.failed > 0 or metrics.errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
