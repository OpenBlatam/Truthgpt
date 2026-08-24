"""
TruthGPT Optimization Core - Markdown Test Reporter
====================================================
GitHub-Flavored Markdown test execution summary generator.
"""

from __future__ import annotations

import datetime
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
    if __name__ == "optimization_core.tests.reporters.markdown_reporter":
        sys.modules["tests.reporters.markdown_reporter"] = _mod
    elif __name__ == "tests.reporters.markdown_reporter":
        sys.modules["optimization_core.tests.reporters.markdown_reporter"] = _mod


class MarkdownTestReporter(BaseTestReporter):
    """Generates clean GitHub Flavored Markdown test summaries."""

    def __init__(self, output_dir: Optional[Union[str, Path]] = None) -> None:
        super().__init__(output_dir=output_dir)

    @property
    def format(self) -> ReportFormat:
        return ReportFormat.MARKDOWN

    def generate_report(
        self,
        session: TestSessionMetrics,
        output_path: Optional[Union[str, Path]] = None,
    ) -> str:
        """Construct Markdown test report."""
        stats = self.format_summary_stats(session)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        status_badge = "![Passed](https://img.shields.io/badge/status-PASSED-brightgreen)" if stats["status"] == "PASSED" else "![Failed](https://img.shields.io/badge/status-FAILED-red)"

        lines = [
            f"# 🧪 TruthGPT Test Suite Execution Report",
            f"",
            f"**Generated:** `{now_str}` | **Status:** {status_badge}",
            f"",
            f"## 📊 Executive Summary",
            f"",
            f"| Metric | Value |",
            f"|:---|:---|",
            f"| **Total Suites** | `{stats['total_suites']}` |",
            f"| **Total Tests** | `{stats['total_tests']}` |",
            f"| **Passed** | `{stats['passed']}` |",
            f"| **Failed** | `{stats['failed']}` |",
            f"| **Errors** | `{stats['errors']}` |",
            f"| **Skipped** | `{stats['skipped']}` |",
            f"| **Success Rate** | `{stats['success_rate']:.2f}%` |",
            f"| **Wall Clock Time** | `{stats['wall_clock_time_sec']:.3f}s` |",
        ]

        if stats["peak_memory_mb"] > 0:
            lines.append(f"| **Peak Memory** | `{stats['peak_memory_mb']:.2f} MB` |")
        if stats["cpu_percent"] > 0:
            lines.append(f"| **CPU Usage** | `{stats['cpu_percent']:.2f}%` |")

        lines.extend([
            f"",
            f"## 📋 Test Suites Breakdown",
            f"",
            f"| Suite Name | Total | Pass | Fail | Error | Duration | Status |",
            f"|:---|:---:|:---:|:---:|:---:|:---:|:---:|",
        ])

        for suite_name, summary in session.suite_summaries.items():
            s_pass = summary.get("passed", 0)
            s_fail = summary.get("failed", 0)
            s_err = summary.get("errors", 0)
            s_tot = summary.get("total_tests", 0)
            s_dur = summary.get("duration_sec", 0.0)
            status_icon = "✅ Pass" if (s_fail == 0 and s_err == 0) else "❌ Fail"
            lines.append(
                f"| `{suite_name}` | {s_tot} | {s_pass} | {s_fail} | {s_err} | {s_dur:.3f}s | {status_icon} |"
            )

        lines.extend([
            f"",
            f"---",
            f"*Report generated automatically by TruthGPT Optimization Core Test Framework.*",
            f"",
        ])

        md_content = "\n".join(lines)

        if output_path:
            self._save_to_file(md_content, output_path)
        else:
            self._save_to_file(md_content, "test_report.md")

        return md_content


__all__ = ["MarkdownTestReporter"]
