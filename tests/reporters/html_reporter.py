"""
TruthGPT Optimization Core - HTML Test Reporter
===============================================
Modern, responsive HTML test report generator with visual charts and stats cards.
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
    if __name__ == "optimization_core.tests.reporters.html_reporter":
        sys.modules["tests.reporters.html_reporter"] = _mod
    elif __name__ == "tests.reporters.html_reporter":
        sys.modules["optimization_core.tests.reporters.html_reporter"] = _mod


class HTMLTestReporter(BaseTestReporter):
    """Generates responsive, standalone HTML test reports."""

    def __init__(self, output_dir: Optional[Union[str, Path]] = None) -> None:
        super().__init__(output_dir=output_dir)

    @property
    def format(self) -> ReportFormat:
        return ReportFormat.HTML

    def generate_report(
        self,
        session: TestSessionMetrics,
        output_path: Optional[Union[str, Path]] = None,
    ) -> str:
        """Construct interactive HTML report string."""
        stats = self.format_summary_stats(session)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        status_color = "#10b981" if stats["status"] == "PASSED" else "#ef4444"
        success_rate = stats["success_rate"]

        suite_rows = []
        for suite_name, summary in session.suite_summaries.items():
            s_pass = summary.get("passed", 0)
            s_fail = summary.get("failed", 0)
            s_err = summary.get("errors", 0)
            s_tot = summary.get("total_tests", 0)
            s_dur = summary.get("duration_sec", 0.0)
            is_ok = s_fail == 0 and s_err == 0
            badge_cls = "badge-pass" if is_ok else "badge-fail"
            badge_text = "PASSED" if is_ok else "FAILED"

            suite_rows.append(f"""
            <tr>
                <td style="font-weight: 600; font-family: monospace;">{suite_name}</td>
                <td>{s_tot}</td>
                <td style="color: #10b981; font-weight: 600;">{s_pass}</td>
                <td style="color: #ef4444; font-weight: 600;">{s_fail}</td>
                <td style="color: #f59e0b; font-weight: 600;">{s_err}</td>
                <td>{s_dur:.3f}s</td>
                <td><span class="badge {badge_cls}">{badge_text}</span></td>
            </tr>
            """)

        suite_rows_html = "".join(suite_rows)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TruthGPT Test Execution Report</title>
    <style>
        :root {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --pass: #10b981;
            --fail: #ef4444;
            --warn: #f59e0b;
        }}
        body {{
            background-color: var(--bg);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 30px;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .title {{
            font-size: 24px;
            font-weight: 700;
        }}
        .status-badge {{
            padding: 6px 14px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 14px;
            background-color: {status_color};
            color: #fff;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
        }}
        .card-val {{
            font-size: 28px;
            font-weight: 700;
            margin-top: 5px;
        }}
        .card-label {{
            color: var(--text-muted);
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }}
        th, td {{
            padding: 14px 18px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            background-color: #1a2333;
            color: var(--text-muted);
            font-size: 12px;
            text-transform: uppercase;
        }}
        .badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        .badge-pass {{
            background-color: rgba(16, 185, 129, 0.2);
            color: var(--pass);
        }}
        .badge-fail {{
            background-color: rgba(239, 68, 68, 0.2);
            color: var(--fail);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <div class="title">🧪 TruthGPT Test Execution Report</div>
                <div style="color: var(--text-muted); margin-top: 5px;">Generated: {now_str}</div>
            </div>
            <div class="status-badge">{stats["status"]}</div>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-label">Success Rate</div>
                <div class="card-val" style="color: {status_color};">{success_rate:.1f}%</div>
            </div>
            <div class="card">
                <div class="card-label">Total Tests</div>
                <div class="card-val">{stats["total_tests"]}</div>
            </div>
            <div class="card">
                <div class="card-label">Passed</div>
                <div class="card-val" style="color: var(--pass);">{stats["passed"]}</div>
            </div>
            <div class="card">
                <div class="card-label">Failed / Errors</div>
                <div class="card-val" style="color: var(--fail);">{stats["failed"] + stats["errors"]}</div>
            </div>
            <div class="card">
                <div class="card-label">Execution Time</div>
                <div class="card-val">{stats["wall_clock_time_sec"]:.2f}s</div>
            </div>
        </div>

        <h2 style="font-size: 18px; margin-bottom: 15px;">Suite Breakdown</h2>
        <table>
            <thead>
                <tr>
                    <th>Suite</th>
                    <th>Total</th>
                    <th>Pass</th>
                    <th>Fail</th>
                    <th>Error</th>
                    <th>Duration</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {suite_rows_html}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

        if output_path:
            self._save_to_file(html_content, output_path)
        else:
            self._save_to_file(html_content, "test_report.html")

        return html_content


__all__ = ["HTMLTestReporter"]
