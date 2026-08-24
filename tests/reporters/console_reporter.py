"""
TruthGPT Optimization Core - Console Test Reporter
==================================================
Colorized, Windows CP1252 / UTF-8 safe terminal test reporter.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Union

from ..types import ReportFormat, TestSessionMetrics
from .base_reporter import BaseTestReporter

# ---------------------------------------------------------------------------
# Module Aliasing across namespaces
# ---------------------------------------------------------------------------
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.tests.reporters.console_reporter":
        sys.modules["tests.reporters.console_reporter"] = _mod
    elif __name__ == "tests.reporters.console_reporter":
        sys.modules["optimization_core.tests.reporters.console_reporter"] = _mod


class ConsoleTestReporter(BaseTestReporter):
    """Rich console reporter with ANSI color highlights and fallback Unicode safety."""

    def __init__(self, color: bool = True, output_dir: Optional[Union[str, Path]] = None) -> None:
        super().__init__(output_dir=output_dir)
        self.color = color and hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    @property
    def format(self) -> ReportFormat:
        return ReportFormat.CONSOLE

    def _colorize(self, text: str, color_code: str) -> str:
        if not self.color:
            return text
        return f"\033[{color_code}m{text}\033[0m"

    def generate_report(
        self,
        session: TestSessionMetrics,
        output_path: Optional[Union[str, Path]] = None,
    ) -> str:
        """Generate and print formatted console test report."""
        stats = self.format_summary_stats(session)
        lines = []

        header_title = " TruthGPT Optimization Core - Test Execution Report "
        lines.append("=" * 65)
        lines.append(header_title.center(65, "="))
        lines.append("=" * 65)
        lines.append("")

        # Summary box
        status_str = "[ PASSED ]" if stats["status"] == "PASSED" else "[ FAILED ]"
        colored_status = (
            self._colorize(status_str, "92;1")
            if stats["status"] == "PASSED"
            else self._colorize(status_str, "91;1")
        )

        lines.append(f" Overall Status    : {colored_status}")
        lines.append(f" Total Suites      : {stats['total_suites']}")
        lines.append(f" Total Tests Run   : {stats['total_tests']}")
        lines.append(f" Passed            : {stats['passed']}")
        lines.append(f" Failed            : {stats['failed']}")
        lines.append(f" Errors            : {stats['errors']}")
        lines.append(f" Skipped           : {stats['skipped']}")
        lines.append(f" Success Rate      : {stats['success_rate']:.2f}%")
        lines.append(f" Wall Clock Time   : {stats['wall_clock_time_sec']:.4f}s")
        if stats["peak_memory_mb"] > 0:
            lines.append(f" Peak Memory (MB)  : {stats['peak_memory_mb']:.2f} MB")
        if stats["cpu_percent"] > 0:
            lines.append(f" CPU Utilization   : {stats['cpu_percent']:.2f}%")

        lines.append("")
        lines.append("-" * 65)
        lines.append(" Suite Breakdown:")
        lines.append("-" * 65)

        for suite_name, summary in session.suite_summaries.items():
            suite_status = "PASS" if summary.get("success", True) else "FAIL"
            marker = self._colorize(f"[{suite_status}]", "92" if suite_status == "PASS" else "91")
            t_count = summary.get("total_tests", 0)
            p_count = summary.get("passed", 0)
            f_count = summary.get("failed", 0)
            e_count = summary.get("errors", 0)
            dur = summary.get("duration_sec", 0.0)
            lines.append(
                f"  {marker} {suite_name:<30} {t_count} tests | {p_count} pass, {f_count} fail, {e_count} err ({dur:.3f}s)"
            )

        lines.append("-" * 65)
        report_text = "\n".join(lines) + "\n"

        # Print to stdout safely
        try:
            print(report_text)
        except UnicodeEncodeError:
            print(report_text.encode("ascii", errors="replace").decode("ascii"))

        if output_path:
            self._save_to_file(report_text, output_path)

        return report_text


__all__ = ["ConsoleTestReporter"]
