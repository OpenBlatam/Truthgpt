"""
High-Performance CLI Test Runner for TruthGPT Optimization Core.
"""

from __future__ import annotations

import unittest
import sys
import time
import os
import argparse
import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project and test roots are in sys.path
_test_dir = Path(__file__).parent
_proj_dir = _test_dir.parent
if str(_proj_dir) not in sys.path:
    sys.path.insert(0, str(_proj_dir))
if str(_test_dir) not in sys.path:
    sys.path.insert(0, str(_test_dir))

# Force UTF-8 stdout on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from tests.types import TestCategory, TestStatus, TestResult, TestSuiteResult, TestEnvironmentConfig
from tests.fixtures.test_utils import PerformanceProfiler, MemoryTracker
from tests.report_generator import HTMLReportGenerator


class TruthGPTTestRunner:
    """Comprehensive test runner for TruthGPT optimization core."""

    def __init__(
        self,
        verbose: bool = True,
        parallel: bool = False,
        coverage: bool = False,
        performance: bool = False,
        integration_only: bool = False,
    ) -> None:
        self.verbose = verbose
        self.parallel = parallel
        self.coverage = coverage
        self.performance = performance
        self.integration_only = integration_only
        self.profiler = PerformanceProfiler()
        self.memory_tracker = MemoryTracker()
        self.report_generator = HTMLReportGenerator()

    def discover_tests(self, pattern: Optional[str] = None) -> List[Path]:
        """Discover test files matching criteria."""
        test_dir = Path(__file__).parent
        test_files: List[Path] = []

        dirs_to_scan = []
        if self.integration_only:
            dirs_to_scan.append(test_dir / "integration")
        elif self.performance:
            dirs_to_scan.append(test_dir / "performance")
        else:
            dirs_to_scan.extend([
                test_dir / "unit",
                test_dir / "integration",
                test_dir / "performance",
            ])

        # Also search root tests directory for test_*.py
        for root_test in test_dir.glob("test_*.py"):
            test_files.append(root_test)

        for d in dirs_to_scan:
            if d.exists():
                for f in d.glob("test_*.py"):
                    if f not in test_files:
                        test_files.append(f)

        if pattern:
            test_files = [f for f in test_files if pattern.lower() in f.name.lower()]

        return sorted(test_files)

    def run_file(self, file_path: Path) -> TestSuiteResult:
        """Run all unittest TestCases inside a single file."""
        mod_name = f"tests_run_{file_path.stem}"
        spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
        if not spec or not spec.loader:
            return TestSuiteResult(suite_name=file_path.name, errors=1)

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            res = TestSuiteResult(suite_name=file_path.name, total_tests=1, errors=1)
            res.results.append(
                TestResult(
                    test_id=file_path.name,
                    name=file_path.name,
                    status=TestStatus.ERROR,
                    error_message=f"Module import failed: {e}",
                )
            )
            return res

        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        runner = unittest.TextTestRunner(verbosity=2 if self.verbose else 0)

        t0 = time.perf_counter()
        test_result = runner.run(suite)
        total_time_ms = (time.perf_counter() - t0) * 1000.0

        suite_res = TestSuiteResult(
            suite_name=file_path.name,
            total_tests=test_result.testsRun,
            passed=test_result.testsRun - len(test_result.failures) - len(test_result.errors) - len(test_result.skipped),
            failed=len(test_result.failures),
            skipped=len(test_result.skipped),
            errors=len(test_result.errors),
            total_time_ms=total_time_ms,
        )

        for tc, fail in test_result.failures:
            suite_res.results.append(
                TestResult(
                    test_id=tc.id(),
                    name=str(tc),
                    status=TestStatus.FAILED,
                    error_message=str(fail),
                )
            )

        for tc, err in test_result.errors:
            suite_res.results.append(
                TestResult(
                    test_id=tc.id(),
                    name=str(tc),
                    status=TestStatus.ERROR,
                    error_message=str(err),
                )
            )

        for tc, reason in test_result.skipped:
            suite_res.results.append(
                TestResult(
                    test_id=tc.id(),
                    name=str(tc),
                    status=TestStatus.SKIPPED,
                    error_message=str(reason),
                )
            )

        return suite_res

    def run_all(self, pattern: Optional[str] = None, save_report: bool = False) -> int:
        """Run all discovered test suites and print summary."""
        test_files = self.discover_tests(pattern)
        print("=" * 70)
        print(f"🧪 TruthGPT Optimization Core Test Runner — Discovered {len(test_files)} file(s)")
        print("=" * 70)

        overall = TestSuiteResult(suite_name="TruthGPT Complete Test Suite")
        start_all = time.perf_counter()

        for f in test_files:
            print(f"\n📂 Running: {f.name}")
            f_res = self.run_file(f)
            overall.total_tests += f_res.total_tests
            overall.passed += f_res.passed
            overall.failed += f_res.failed
            overall.skipped += f_res.skipped
            overall.errors += f_res.errors
            overall.results.extend(f_res.results)

        overall.total_time_ms = (time.perf_counter() - start_all) * 1000.0

        print("\n" + "=" * 70)
        print(self.report_generator.format_summary(overall.to_dict()))
        print(f"Total Run Time : {overall.total_time_ms:.2f} ms")
        print("=" * 70)

        if save_report:
            report_dir = _test_dir / "reports"
            report_dir.mkdir(exist_ok=True)
            html_p = self.report_generator.generate_report(overall, report_dir / "test_report.html")
            md_p = self.report_generator.generate_markdown_report(overall, report_dir / "test_report.md")
            json_p = self.report_generator.generate_json_report(overall, report_dir / "test_report.json")
            print(f"Reports saved to:\n - {html_p}\n - {md_p}\n - {json_p}")

        return 0 if overall.is_successful else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="TruthGPT Optimization Core Test Runner")
    parser.add_argument("--verbose", "-v", action="store_true", default=True, help="Verbose output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")
    parser.add_argument("--pattern", "-p", type=str, default=None, help="Filter tests by name pattern")
    parser.add_argument("--performance", "-perf", action="store_true", help="Run performance tests only")
    parser.add_argument("--integration", "-int", action="store_true", help="Run integration tests only")
    parser.add_argument("--save-results", "-s", action="store_true", help="Save HTML/Markdown/JSON reports")

    args = parser.parse_args()
    runner = TruthGPTTestRunner(
        verbose=not args.quiet,
        performance=args.performance,
        integration_only=args.integration,
    )
    exit_code = runner.run_all(pattern=args.pattern, save_report=args.save_results)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
