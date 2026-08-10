"""
File utilities for data processing.

Provides high-performance file format detection, directory management,
and file operations for the optimization_core data module.
"""
import os
import shutil
import tempfile
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = {
    ".parquet": "parquet",
    ".pq": "parquet",
    ".csv": "csv",
    ".tsv": "csv",
    ".jsonl": "jsonl",
    ".ndjson": "jsonl",
    ".json": "json",
    ".arrow": "arrow",
    ".feather": "arrow",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
}

try:
    from optimization_core.core.file_utils import (
        detect_file_format,
        validate_file_format,
        ensure_output_directory,
        get_file_size,
        get_file_size_mb,
        list_files,
        get_file_info,
        safe_remove,
        safe_rename,
        get_temp_path,
    )
except (ImportError, AttributeError):
    def detect_file_format(file_path: Union[str, Path]) -> str:
        """Detect file format from extension."""
        path_obj = Path(file_path)
        suffix = path_obj.suffix.lower()
        if suffix in SUPPORTED_FORMATS:
            return SUPPORTED_FORMATS[suffix]
        raise ValueError(
            f"Unsupported file format: '{suffix}'. "
            f"Supported extensions: {list(SUPPORTED_FORMATS.keys())}"
        )

    def validate_file_format(
        file_path: Union[str, Path],
        allowed_formats: Optional[Set[str]] = None
    ) -> str:
        """Validate and return file format."""
        format_name = detect_file_format(file_path)
        if allowed_formats and format_name not in allowed_formats:
            raise ValueError(
                f"File format '{format_name}' not allowed. "
                f"Allowed formats: {allowed_formats}"
            )
        return format_name

    def ensure_output_directory(output_path: Union[str, Path]) -> Path:
        """Ensure output directory exists, create if needed."""
        path_obj = Path(output_path)
        directory = path_obj.parent
        if directory and not directory.exists():
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created output directory: {directory}")
            except OSError as e:
                logger.error(f"Failed to create directory {directory}: {e}")
                raise
        return path_obj

    def get_file_size(file_path: Union[str, Path]) -> int:
        """Get file size in bytes."""
        return os.path.getsize(file_path)

    def get_file_size_mb(file_path: Union[str, Path]) -> float:
        """Get file size in Megabytes."""
        return get_file_size(file_path) / (1024 * 1024)

    def list_files(
        directory: Union[str, Path],
        extension: Optional[str] = None,
        recursive: bool = False
    ) -> List[Path]:
        """List files in directory matching optional extension."""
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            raise FileNotFoundError(f"Directory not found: {directory}")
        pattern = f"**/*{extension}" if recursive else f"*{extension}" if extension else "*"
        return [p for p in dir_path.glob(pattern) if p.is_file()]

    def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get file metadata information."""
        path_obj = Path(file_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        stat = path_obj.stat()
        return {
            "path": str(path_obj.absolute()),
            "name": path_obj.name,
            "extension": path_obj.suffix,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified_time": stat.st_mtime,
        }

    def safe_remove(file_path: Union[str, Path]) -> bool:
        """Safely remove file or directory if it exists."""
        try:
            p = Path(file_path)
            if p.is_file() or p.is_symlink():
                p.unlink()
                return True
            elif p.is_dir():
                shutil.rmtree(p)
                return True
        except Exception as e:
            logger.warning(f"Could not remove {file_path}: {e}")
        return False

    def safe_rename(src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """Safely rename or move file."""
        try:
            shutil.move(str(src), str(dst))
            return True
        except Exception as e:
            logger.error(f"Could not rename {src} to {dst}: {e}")
            return False

    def get_temp_path(prefix: str = "tmp_", suffix: str = ".tmp") -> Path:
        """Get temporary path for writing files."""
        fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
        os.close(fd)
        return Path(path)


__all__ = [
    "detect_file_format",
    "validate_file_format",
    "ensure_output_directory",
    "get_file_size",
    "get_file_size_mb",
    "list_files",
    "get_file_info",
    "safe_remove",
    "safe_rename",
    "get_temp_path",
    "SUPPORTED_FORMATS",
]
