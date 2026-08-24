"""
TruthGPT Optimization Core - Test Reporters Subpackage
======================================================
Exporting console, JSON, Markdown, and HTML test execution reporters.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional, Union

from ..types import ReportFormat
from .base_reporter import BaseTestReporter
from .console_reporter import ConsoleTestReporter
from .json_reporter import JSONTestReporter
from .markdown_reporter import MarkdownTestReporter
from .html_reporter import HTMLTestReporter

# ---------------------------------------------------------------------------
# Module Aliasing across namespaces
# ---------------------------------------------------------------------------
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.tests.reporters":
        sys.modules["tests.reporters"] = _mod
    elif __name__ == "tests.reporters":
        sys.modules["optimization_core.tests.reporters"] = _mod


def create_reporter(
    report_format: Union[ReportFormat, str] = ReportFormat.CONSOLE,
    output_dir: Optional[Union[str, Path]] = None,
    **kwargs: Any,
) -> BaseTestReporter:
    """Factory helper to instantiate a test reporter by format."""
    if isinstance(report_format, str):
        report_format = ReportFormat(report_format.lower())

    if report_format == ReportFormat.CONSOLE:
        return ConsoleTestReporter(output_dir=output_dir, **kwargs)
    elif report_format == ReportFormat.JSON:
        return JSONTestReporter(output_dir=output_dir, **kwargs)
    elif report_format == ReportFormat.MARKDOWN:
        return MarkdownTestReporter(output_dir=output_dir)
    elif report_format == ReportFormat.HTML:
        return HTMLTestReporter(output_dir=output_dir)
    else:
        raise ValueError(f"Unsupported report format: {report_format}")


create_test_reporter = create_reporter

__all__ = [
    "BaseTestReporter",
    "ConsoleTestReporter",
    "JSONTestReporter",
    "MarkdownTestReporter",
    "HTMLTestReporter",
    "create_reporter",
    "create_test_reporter",
]
