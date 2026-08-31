"""
Export & File Generation Manager for TruthGPT Interface.
=========================================================
Handles structured code extraction, markdown artifact saving, and natural language
path parsing.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from interface.export_utils import (
    LANGUAGE_EXTENSION_MAP,
    export_mission_result,
    extract_and_save_code_blocks,
    extract_target_directory,
    save_mission_output,
)
from interface.interfaces import BaseExportManager


class ExportManager(BaseExportManager):
    """Concrete implementation of BaseExportManager contract."""

    def export_mission_result(
        self,
        content: str,
        mission_name: str = "Mission_Result",
    ) -> Path:
        return export_mission_result(content, mission_name=mission_name)

    def extract_target_directory(self, query: Optional[str]) -> Optional[Path]:
        return extract_target_directory(query)


__all__ = [
    "ExportManager",
    "LANGUAGE_EXTENSION_MAP",
    "export_mission_result",
    "save_mission_output",
    "extract_target_directory",
    "extract_and_save_code_blocks",
]
