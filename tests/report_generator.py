"""
Multi-Format Test Report Generator (HTML, Markdown, JSON) for TruthGPT Optimization Core.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .interfaces import BaseReporterInterface
from .types import TestSuiteResult


class HTMLReportGenerator(BaseReporterInterface):
    """Generate interactive HTML, Markdown, and JSON reports for test execution suites."""

    def __init__(self) -> None:
        self.template = self._load_template()

    def _to_dict(self, results: Any) -> Dict[str, Any]:
        if hasattr(results, "to_dict") and callable(results.to_dict):
            return results.to_dict()
        elif isinstance(results, dict):
            return results
        return getattr(results, "__dict__", {})

    def generate_report(self, results: Union[Dict[str, Any], Any], output_path: Union[str, Path]) -> str:
        """Generate and save HTML report file."""
        res_dict = self._to_dict(results)
        html_content = self.generate_html(res_dict)

        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(out_p)

    def generate_markdown_report(self, results: Union[Dict[str, Any], Any], output_path: Optional[Union[str, Path]] = None) -> str:
        """Generate a GitHub-flavored Markdown summary report."""
        res = self._to_dict(results)

        total = res.get('total_tests', 0)
        passed = res.get('passed', 0)
        failed = res.get('failed', 0)
        skipped = res.get('skipped', 0)
        errors = res.get('errors', 0)
        pass_rate = res.get('pass_rate_pct', (passed / total * 100) if total > 0 else 0.0)
        total_time_ms = res.get('total_time_ms', 0.0)
        suite_name = res.get('suite_name', 'Test Suite')

        lines = [
            f"# 🧪 Test Execution Report — {suite_name}",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Total Duration**: {total_time_ms:.2f} ms  ",
            f"**Overall Status**: {'✅ PASSED' if failed == 0 and errors == 0 else '❌ FAILED'}",
            "",
            "## 📊 Summary Metrics",
            "",
            "| Metric | Value |",
            "| :--- | :--- |",
            f"| **Total Tests** | {total} |",
            f"| **Passed** | {passed} |",
            f"| **Failed** | {failed} |",
            f"| **Skipped** | {skipped} |",
            f"| **Errors** | {errors} |",
            f"| **Pass Rate** | **{pass_rate:.1f}%** |",
            "",
        ]

        if "backend_status" in res and res["backend_status"]:
            lines.extend([
                "## 🌐 Native Polyglot Backends",
                "",
                "| Backend | Status |",
                "| :--- | :--- |",
            ])
            for b_name, b_avail in res["backend_status"].items():
                lines.append(f"| `{b_name}` | {'✅ Available' if b_avail else '❌ Unavailable'} |")
            lines.append("")

        if "results" in res and res["results"]:
            lines.extend([
                "## 📋 Detailed Test Case Breakdown",
                "",
                "| Test ID | Category | Status | Duration (ms) |",
                "| :--- | :--- | :--- | :--- |",
            ])
            for t in res["results"]:
                t_id = t.get('name', t.get('test_id', 'unknown'))
                cat = t.get('category', 'UNIT')
                st = t.get('status', 'PASSED')
                dur = t.get('duration_ms', 0.0)
                icon = "✅" if str(st).upper() in ("PASSED", "XFAIL") else "❌" if str(st).upper() in ("FAILED", "ERROR") else "⚠️"
                lines.append(f"| `{t_id}` | {cat} | {icon} {st} | {dur:.2f} |")
            lines.append("")

        md_content = "\n".join(lines)

        if output_path:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, 'w', encoding='utf-8') as f:
                f.write(md_content)

        return md_content

    def generate_json_report(self, results: Union[Dict[str, Any], Any], output_path: Union[str, Path]) -> str:
        """Export test results to structured JSON."""
        res = self._to_dict(results)
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, 'w', encoding='utf-8') as f:
            json.dump(res, f, indent=2)
        return str(out_p)

    def format_summary(self, results: Union[Dict[str, Any], Any]) -> str:
        """Format an inline terminal summary."""
        res = self._to_dict(results)
        total = res.get('total_tests', 0)
        passed = res.get('passed', 0)
        failed = res.get('failed', 0)
        skipped = res.get('skipped', 0)
        pass_rate = (passed / total * 100.0) if total > 0 else 0.0

        return (
            f"Tests: {total} total | Passed: {passed} | Failed: {failed} | "
            f"Skipped: {skipped} | Pass Rate: {pass_rate:.1f}%"
        )

    def generate_html(self, results: Union[Dict[str, Any], Any]) -> str:
        res = self._to_dict(results)
        total = res.get('total_tests', 0)
        passed = res.get('passed', total - res.get('total_failures', 0) - res.get('total_errors', 0))
        failed = res.get('failed', res.get('total_failures', 0))
        errors = res.get('errors', res.get('total_errors', 0))
        skipped = res.get('skipped', 0)
        pass_rate = (passed / total * 100) if total > 0 else 0.0
        suite_name = res.get('suite_name', 'TruthGPT Optimization Core')

        stats_html = f"""
        <div class="stat-card">
            <h3>{total}</h3>
            <p>Total Tests</p>
        </div>
        <div class="stat-card">
            <h3 style="color: #48bb78;">{passed}</h3>
            <p>Passed</p>
        </div>
        <div class="stat-card">
            <h3 style="color: #f56565;">{failed}</h3>
            <p>Failed</p>
        </div>
        <div class="stat-card">
            <h3 style="color: #ed8936;">{errors}</h3>
            <p>Errors</p>
        </div>
        <div class="stat-card">
            <h3 style="color: #a0aec0;">{skipped}</h3>
            <p>Skipped</p>
        </div>
        <div class="stat-card">
            <h3 style="color: #4299e1;">{pass_rate:.1f}%</h3>
            <p>Success Rate</p>
        </div>
        """

        tests_html = ""
        results_list = res.get('results', [])
        for r in results_list:
            st = str(r.get('status', 'PASSED')).upper()
            color = "#48bb78" if st in ("PASSED", "XFAIL") else "#f56565" if st in ("FAILED", "ERROR", "TIMED_OUT") else "#a0aec0"
            tests_html += f"""
            <div class="test-item">
                <div>
                    <span class="test-name">{r.get('name', r.get('test_id', 'Test'))}</span>
                    <span style="color: #718096; font-size: 0.9em; margin-left: 10px;">{r.get('duration_ms', 0.0):.2f}ms</span>
                </div>
                <span class="test-status" style="background: {color}; color: white;">{st}</span>
            </div>
            """

        html = self.template.replace("{{SUITE_NAME}}", suite_name)
        html = html.replace("{{STATS}}", stats_html)
        html = html.replace("{{PROGRESS_WIDTH}}", f"{pass_rate:.1f}%")
        html = html.replace("{{PROGRESS_TEXT}}", f"{pass_rate:.1f}% Pass Rate")
        html = html.replace("{{TIMESTAMP}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        html = html.replace("{{TESTS}}", tests_html or "<p>No individual test items recorded.</p>")

        return html

    def _load_template(self) -> str:
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TruthGPT Test Report — {{SUITE_NAME}}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #f7fafc;
            color: #2d3748;
            padding: 30px;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #4c51bf 0%, #6b46c1 100%);
            color: white;
            padding: 35px;
            text-align: center;
        }
        .header h1 { font-size: 2.2em; margin-bottom: 8px; }
        .header p { opacity: 0.85; font-size: 1.05em; }
        .content { padding: 35px; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        .stat-card {
            background: #edf2f7;
            padding: 18px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-card h3 { font-size: 1.8em; margin-bottom: 4px; }
        .stat-card p { color: #718096; font-size: 0.9em; text-transform: uppercase; letter-spacing: 0.5px; }
        .progress-bar {
            background: #edf2f7;
            height: 26px;
            border-radius: 13px;
            overflow: hidden;
            margin: 20px 0 30px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #48bb78, #38a169);
            width: {{PROGRESS_WIDTH}};
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.85em;
        }
        .test-item {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            padding: 12px 18px;
            margin-bottom: 8px;
            border-radius: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .test-name { font-weight: 600; font-family: monospace; font-size: 0.95em; }
        .test-status {
            padding: 3px 12px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{SUITE_NAME}}</h1>
            <p>Automated Test & Benchmark Report | {{TIMESTAMP}}</p>
        </div>
        <div class="content">
            <div class="stats-grid">
                {{STATS}}
            </div>
            <div class="progress-bar">
                <div class="progress-fill">{{PROGRESS_TEXT}}</div>
            </div>
            <h2 style="margin-bottom: 15px; font-size: 1.3em;">Test Execution Breakdown</h2>
            <div class="test-results">
                {{TESTS}}
            </div>
        </div>
    </div>
</body>
</html>"""


# Alias
ReportGenerator = HTMLReportGenerator

__all__ = [
    "HTMLReportGenerator",
    "ReportGenerator",
]
