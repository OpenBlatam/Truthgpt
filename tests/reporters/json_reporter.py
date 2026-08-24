"""
TruthGPT Optimization Core - JSON Test Reporter
===============================================
Structured JSON test results serializer for automated CI/CD parsing and storage.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..types import ReportFormat, TestSessionMetrics
from .base_reporter import BaseTestReporter

# ---------------------------------------------------------------------------
# Module Aliasing across namespaces
# ---------------------------------------------------------------------------
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.tests.reporters.json_reporter":
        sys.modules["tests.reporters.json_reporter"] = _mod
    elif __name__ == "tests.reporters.json_reporter":
        sys.modules["optimization_core.tests.reporters.json_reporter"] = _mod


class JSONTestReporter(BaseTestReporter):
    """Serializes test session outcomes and hardware metrics to structured JSON."""

    def __init__(self, indent: int = 2, output_dir: Optional[Union[str, Path]] = None) -> None:
        super().__init__(output_dir=output_dir)
        self.indent = indent

    @property
    def format(self) -> ReportFormat:
        return ReportFormat.JSON

    def generate_report(
        self,
        session: TestSessionMetrics,
        output_path: Optional[Union[str, Path]] = None,
    ) -> str:
        """Serialize test session metrics to JSON string and optionally save to disk."""
        data: Dict[str, Any] = session.to_dict()
        data["summary"] = self.format_summary_stats(session)

        json_str = json.dumps(data, indent=self.indent, default=str)

        if output_path:
            self._save_to_file(json_str, output_path)
        else:
            self._save_to_file(json_str, "test_results.json")

        return json_str


__all__ = ["JSONTestReporter"]
