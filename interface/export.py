"""
Export Engine & Artifact Reporting Tools for TruthGPT Interface.
================================================================
Extracts markdown reports, automatically extracts and saves enclosed multi-language
code blocks, and resolves path references from natural language mission queries.
"""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from interface.console import console
from interface.constants import CODE_EXTENSION_MAP
from interface.prompts import get_input
from interface.types import ExportFormat, ExportResult

logger = logging.getLogger(__name__)

CURRENT_DIR: Path = Path(__file__).resolve().parent.parent


def extract_target_directory(query: Optional[str]) -> Optional[Path]:
    """Scan query string for embedded file path or directory destinations."""
    if not query:
        return None

    words = query.split()
    for length in range(len(words), 0, -1):
        for start in range(len(words) - length + 1):
            candidate = " ".join(words[start : start + length]).strip("\"'")
            if not candidate:
                continue

            is_path_like = False
            if (
                re.match(r"^[a-zA-Z]:\\", candidate)
                or re.match(r"^[a-zA-Z]:/", candidate)
                or candidate.startswith("/")
                or candidate.startswith(".\\")
                or candidate.startswith("./")
            ):
                is_path_like = True
            elif "\\" in candidate or "/" in candidate:
                if not candidate.startswith("http"):
                    is_path_like = True

            if is_path_like:
                try:
                    path = Path(candidate)
                    if path.exists() and path.is_dir():
                        return path.resolve()
                    if not path.exists():
                        parent = path.parent
                        if parent and parent.exists():
                            return path.resolve()
                except Exception:
                    pass
    return None


def extract_and_save_code_blocks(
    content: str,
    destination_dir: Path,
    timestamp: Optional[str] = None,
) -> List[Path]:
    """Extract code blocks from markdown content and write individual source files to disk."""
    if timestamp is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")

    destination_dir.mkdir(parents=True, exist_ok=True)
    code_blocks = re.findall(r"```([a-zA-Z0-9+#_ -]*)\n(.*?)\n```", content, re.DOTALL)
    saved_files: List[Path] = []

    if code_blocks:
        console.print(f"[cyan]📦 Extracting and writing {len(code_blocks)} code blocks to {destination_dir}...[/cyan]")
        for idx, (lang, code) in enumerate(code_blocks, 1):
            lang_clean = lang.strip().lower()
            code_ext = CODE_EXTENSION_MAP.get(lang_clean, ".py" if not lang_clean else f".{lang_clean}")
            code_filename = f"code_block_{idx}_{timestamp}{code_ext}"
            code_filepath = destination_dir / code_filename
            try:
                code_filepath.write_text(code, encoding="utf-8")
                saved_files.append(code_filepath)
                console.print(f"  [green]● Saved code block {idx} ({lang_clean or 'python/unknown'}) to {code_filepath.name}[/green]")
            except Exception as e:
                console.print(f"  [red]Failed to write {code_filename}: {e}[/red]")

    return saved_files


def export_mission_result(
    content: str,
    mission_name: str = "Mission_Result",
    fmt: Optional[str] = None,
) -> ExportResult:
    """Exports structured mission output and extracted code blocks to `exports/`."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = mission_name.replace(" ", "_")
    console.print("\n[bold cyan]📤 Export & Reporting Engine[/bold cyan]")

    if fmt is None:
        fmt = get_input("Export format", choices=["MD", "PDF", "Word"], default="MD").upper()

    export_format = ExportFormat.from_str(fmt)
    filename = f"{clean_name}_{timestamp}"
    path = Path("exports") / f"{filename}.md"

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        console.print(f"[bold green]✓ Exported to {path}[/bold green]")

        extracted = extract_and_save_code_blocks(content, path.parent, timestamp=timestamp)
        return ExportResult(
            success=True,
            target_path=str(path),
            format=export_format,
            code_blocks_extracted=len(extracted),
            extracted_files=[str(p) for p in extracted],
        )
    except Exception as e:
        console.print(f"[red]Export Error: {e}[/red]")
        return ExportResult(
            success=False,
            target_path=str(path),
            format=export_format,
            error_message=str(e),
        )


def save_mission_output(
    content: str,
    mission_name: str = "Mission",
    query: Optional[str] = None,
) -> ExportResult:
    """Saves mission output markdown reports to user-specified target directory or `reports/`."""
    target_dir = extract_target_directory(query)
    if target_dir:
        report_dir = target_dir
    else:
        report_dir = CURRENT_DIR / "reports"

    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{mission_name}_{timestamp}.md"
    filepath = report_dir / filename

    try:
        filepath.write_text(content, encoding="utf-8")
        console.print(f"[bold green]✓ Output exported to {filepath}[/bold green]")

        extracted = extract_and_save_code_blocks(content, report_dir, timestamp=timestamp)
        return ExportResult(
            success=True,
            target_path=str(filepath),
            format=ExportFormat.MD,
            code_blocks_extracted=len(extracted),
            extracted_files=[str(p) for p in extracted],
        )
    except Exception as e:
        console.print(f"[red]Save Output Error: {e}[/red]")
        return ExportResult(
            success=False,
            target_path=str(filepath),
            format=ExportFormat.MD,
            error_message=str(e),
        )
