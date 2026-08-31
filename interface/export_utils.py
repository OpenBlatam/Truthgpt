"""
Export & File Output Utilities for TruthGPT Interface.
Handles markdown persistence and automated multi-language code block extraction.
"""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from interface.config import current_dir
from interface.console import console
from interface.input_utils import get_input

logger = logging.getLogger(__name__)

LANGUAGE_EXTENSION_MAP = {
    "python": ".py",
    "py": ".py",
    "javascript": ".js",
    "js": ".js",
    "typescript": ".ts",
    "ts": ".ts",
    "html": ".html",
    "htm": ".html",
    "css": ".css",
    "json": ".json",
    "rust": ".rs",
    "rs": ".rs",
    "go": ".go",
    "bash": ".sh",
    "sh": ".sh",
    "shell": ".sh",
    "powershell": ".ps1",
    "ps1": ".ps1",
    "c": ".c",
    "cpp": ".cpp",
    "c++": ".cpp",
    "java": ".java",
    "solidity": ".sol",
    "sol": ".sol",
    "yaml": ".yaml",
    "yml": ".yml",
    "toml": ".toml",
    "sql": ".sql",
}


def extract_target_directory(query: Optional[str]) -> Optional[Path]:
    """Extract a target directory path mentioned in user prompt, if any."""
    if not query:
        return None
    words = query.split()

    # Pass 1: Look for exact existing directories
    for length in range(len(words), 0, -1):
        for start in range(len(words) - length + 1):
            candidate = " ".join(words[start : start + length]).strip("\"'")
            if not candidate:
                continue
            try:
                path = Path(candidate)
                if path.exists() and path.is_dir():
                    return path.resolve()
            except Exception:
                pass

    # Pass 2: Look for potential path strings where parent directory exists
    for length in range(1, len(words) + 1):
        for start in range(len(words) - length + 1):
            candidate = " ".join(words[start : start + length]).strip("\"'")
            if not candidate:
                continue
            is_path_like = False
            if (
                re.match(r"^[a-zA-Z]:[/\\]", candidate)
                or candidate.startswith("/")
                or candidate.startswith(".\\")
                or candidate.startswith("./")
            ):
                is_path_like = True
            elif ("\\" in candidate or "/" in candidate) and not candidate.startswith("http"):
                is_path_like = True

            if is_path_like:
                try:
                    path = Path(candidate)
                    if path.parent.exists() and path.parent.is_dir():
                        return path.resolve()
                except Exception:
                    pass
    return None


def extract_and_save_code_blocks(
    content: str,
    target_dir: Path,
    timestamp: Optional[str] = None,
    prefix: str = "code_block",
) -> List[Path]:
    """Extract code blocks from markdown content and write each to individual source files."""
    if not content:
        return []

    target_dir.mkdir(parents=True, exist_ok=True)
    ts = timestamp or time.strftime("%Y%m%d_%H%M%S")

    code_blocks = re.findall(
        r"```([a-zA-Z0-9+#_ -]*)\n(.*?)\n```", content, re.DOTALL
    )
    saved_files: List[Path] = []

    if code_blocks:
        console.print(
            f"[cyan]📦 Extracting and writing {len(code_blocks)} code blocks to {target_dir}...[/cyan]"
        )
        for idx, (lang, code) in enumerate(code_blocks, 1):
            lang_clean = lang.strip().lower()
            code_ext = LANGUAGE_EXTENSION_MAP.get(
                lang_clean, ".py" if not lang_clean else f".{lang_clean}"
            )
            code_filename = f"{prefix}_{idx}_{ts}{code_ext}"
            code_filepath = target_dir / code_filename
            try:
                code_filepath.write_text(code, encoding="utf-8")
                saved_files.append(code_filepath)
                console.print(
                    f"  [green]● Saved code block {idx} ({lang_clean or 'python/unknown'}) to {code_filepath.name}[/green]"
                )
            except Exception as e:
                logger.error(f"Failed to write code block {code_filepath}: {e}")

    return saved_files


def export_mission_result(
    title_or_content: str,
    content: Optional[str] = None,
    export_code: bool = True,
    target_dir: Optional[Path] = None,
    format: str = "MD",
    mission_name: Optional[str] = None,
    **kwargs: Any,
) -> Path:
    """Prompt user or export mission markdown and extracted code blocks to target_dir or exports/."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if content is not None:
        actual_title = title_or_content
        actual_content = content
    else:
        actual_title = mission_name or "Mission_Result"
        actual_content = title_or_content

    clean_name = actual_title.replace(" ", "_")
    export_dir = target_dir or (current_dir / "truthgpt_collected" / "exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{clean_name}_{ts}"
    file_path = export_dir / f"{filename}.md"
    file_path.write_text(actual_content, encoding="utf-8")

    if export_code:
        extract_and_save_code_blocks(actual_content, export_dir, timestamp=ts)

    try:
        console.print(f"[bold green]✓ Exported to {file_path}[/bold green]")
    except Exception:
        pass
    return file_path


def save_mission_output(
    content: str, mission_name: str, query: Optional[str] = None
) -> None:
    """Save mission response to custom directory if specified in query, otherwise prompt."""
    target_dir = extract_target_directory(query)
    if target_dir:
        extract_and_save_code_blocks(
            content,
            target_dir,
            prefix=mission_name.lower().replace(" ", "_"),
        )
    else:
        export_mission_result(content, mission_name=mission_name)
