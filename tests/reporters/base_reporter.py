"""
TruthGPT Optimization Core - Base Test Reporter
===============================================
Foundational base class for all test report generators with file output and formatting helpers.
"""

from __future__ import annotations

import logging
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..types import ReportFormat, TestSessionMetrics
from ..interfaces import ITestReporter
from ..exceptions import TestReportError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module Aliasing across namespaces
# ---------------------------------------------------------------------------
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.tests.reporters.base_reporter":
        sys.modules["tests.reporters.base_reporter"] = _mod
    elif __name__ == "tests.reporters.base_reporter":
        sys.modules["optimization_core.tests.reporters.base_reporter"] = _mod


class BaseTestReporter(ITestReporter, ABC):
    """Base class for all test report generators."""

    def __init__(self, output_dir: Optional[Union[str, Path]] = None) -> None:
        self.output_dir = Path(output_dir) if output_dir else Path("test_reports")

    def _ensure_output_dir(self) -> None:
        """Create target output directory if it does not exist."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise TestReportError(
                f"Failed to create report output directory '{self.output_dir}': {e}",
                details={"output_dir": str(self.output_dir)},
            ) from e

    def _save_to_file(self, content: str, filename_or_path: Union[str, Path]) -> Path:
        """Save report string content to output file safely."""
        p = Path(filename_or_path)
        if p.is_absolute() or len(p.parts) > 1:
            file_path = p
        else:
            self._ensure_output_dir()
            file_path = self.output_dir / p

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(content)
            logger.info(f"Report saved to {file_path}")
            return file_path
        except Exception as e:
            raise TestReportError(
                f"Failed to write report to '{file_path}': {e}",
                details={"file_path": str(file_path), "error": str(e)},
            ) from e

    def format_summary_stats(self, session: TestSessionMetrics) -> Dict[str, Any]:
        """Compute standard summary statistics dictionary."""
        passed = session.passed
        failed = session.failed
        errors = session.errors
        skipped = session.skipped
        total = session.total_tests
        success_rate = session.success_rate
        wall_time = session.wall_clock_time

        return {
            "total_suites": session.total_suites,
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "success_rate": success_rate,
            "wall_clock_time_sec": round(wall_time, 4),
            "peak_memory_mb": round(session.peak_memory_mb, 2),
            "cpu_percent": round(session.cpu_percent, 2),
            "status": "PASSED" if (failed == 0 and errors == 0) else "FAILED",
        }

    def format_summary(self, results: Any) -> str:
        """Format an inline text summary of test results."""
        if isinstance(results, TestSessionMetrics):
            stats = self.format_summary_stats(results)
            return f"Suites: {stats['total_suites']} | Tests: {stats['total_tests']} | Passed: {stats['passed']} | Failed: {stats['failed']} | Success Rate: {stats['success_rate']:.2f}%"
        return str(results)


__all__ = ["BaseTestReporter"]
