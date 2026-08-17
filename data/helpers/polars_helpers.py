"""
Polars Processor Helpers
========================

Helper functions for Polars data processing operations.
"""

import logging
from typing import List, Union, Optional, Any
from pathlib import Path

try:
    from ..utils.validators import validate_file_path, validate_non_empty_string
    from ..utils.file_utils import validate_file_format
except (ImportError, ValueError):
    try:
        from optimization_core.data.utils.validators import validate_file_path, validate_non_empty_string
        from optimization_core.data.utils.file_utils import validate_file_format
    except ImportError:
        def validate_file_path(path, must_exist=True, allowed_extensions=None):
            p = Path(path)
            if must_exist and not p.exists():
                raise FileNotFoundError(f"Path does not exist: {path}")
            if allowed_extensions and p.suffix.lower() not in allowed_extensions:
                raise ValueError(f"Invalid extension {p.suffix}")
            return p
        def validate_non_empty_string(val, name):
            if not val or not str(val).strip():
                raise ValueError(f"{name} cannot be empty")
        def validate_file_format(path, allowed_formats=None):
            return Path(path).suffix.lower().lstrip(".")

def validate_path(path: Union[str, Path]) -> Path:
    """Validate path object."""
    if not path:
        raise ValueError("path cannot be empty")
    return Path(path)

try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False
    pl = None

logger = logging.getLogger(__name__)


def validate_polars_available():
    """Check if Polars is available."""
    if not POLARS_AVAILABLE:
        raise ImportError(
            "Polars is not installed. Install with: pip install polars"
        )


def normalize_paths(paths: Union[str, Path, List[str], List[Path]]) -> List[Path]:
    """
    Normalize file paths to list of Path objects.
    
    Args:
        paths: Single path or list of paths
    
    Returns:
        List of Path objects
    
    Raises:
        ValueError: If paths is empty
    """
    if isinstance(paths, (str, Path)):
        paths = [paths]
    
    if not paths:
        raise ValueError("paths cannot be empty")
    
    return [validate_path(p) for p in paths]


def validate_file_exists(path: Path, extension: Optional[str] = None):
    """
    Validate that file exists and optionally has correct extension.
    
    Args:
        path: Path to validate
        extension: Expected file extension (e.g., '.parquet')
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If extension doesn't match
    """
    validate_file_path(
        path,
        must_exist=True,
        allowed_extensions=[extension] if extension else None
    )


def detect_dataframe_type(df: Any) -> str:
    """
    Detect if DataFrame is eager or lazy.
    
    Args:
        df: DataFrame or LazyFrame
    
    Returns:
        "eager" or "lazy"
    """
    if pl is not None and isinstance(df, pl.LazyFrame):
        return "lazy"
    return "eager"


def ensure_lazy(df: Any) -> Any:
    """
    Convert DataFrame to LazyFrame if needed.
    
    Args:
        df: DataFrame or LazyFrame
    
    Returns:
        LazyFrame or original object if Polars unavailable
    """
    if pl is not None:
        if isinstance(df, pl.LazyFrame):
            return df
        if isinstance(df, pl.DataFrame):
            return df.lazy()
    return df


def ensure_eager(df: Any) -> Any:
    """
    Convert LazyFrame to DataFrame if needed.
    
    Args:
        df: DataFrame or LazyFrame
    
    Returns:
        DataFrame or original object if Polars unavailable
    """
    if pl is not None:
        if isinstance(df, pl.DataFrame):
            return df
        if isinstance(df, pl.LazyFrame):
            return df.collect()
    return df


def get_numeric_columns(df: Any) -> List[str]:
    """
    Get list of numeric column names.
    
    Args:
        df: DataFrame or LazyFrame
    
    Returns:
        List of numeric column names
    """
    if pl is None:
        return []
    
    schema = df.schema
    numeric_types = (
        pl.Int8, pl.Int16, pl.Int32, pl.Int64,
        pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
        pl.Float32, pl.Float64
    )
    
    result = []
    for col, dtype in schema.items():
        if hasattr(dtype, "is_numeric") and callable(getattr(dtype, "is_numeric")):
            if dtype.is_numeric():
                result.append(col)
        elif isinstance(dtype, numeric_types) or dtype in numeric_types or type(dtype) in numeric_types:
            result.append(col)
    return result


def log_dataframe_info(
    df: Any,
    operation: str,
    logger_instance: Optional[logging.Logger] = None
):
    """
    Log DataFrame information.
    
    Args:
        df: DataFrame or LazyFrame
        operation: Operation name
        logger_instance: Logger instance (optional)
    """
    log = logger_instance or logger
    
    if pl is not None and isinstance(df, pl.LazyFrame):
        log.debug(f"{operation}: LazyFrame with {len(df.schema)} columns")
    elif pl is not None and isinstance(df, pl.DataFrame):
        log.debug(
            f"{operation}: DataFrame shape={df.shape}, "
            f"columns={len(df.columns)}, memory={df.estimated_size()}"
        )
    else:
        log.debug(f"{operation}: Data object type={type(df).__name__}")
