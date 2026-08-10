"""
Validation utilities for data processing.

Provides validation functions for file paths, dataset schemas, string values,
and positive numbers with fallback mechanisms.
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path

class ValidationError(ValueError):
    """Custom exception for validation errors."""
    pass


def validate_non_empty_string(value: str, name: str) -> None:
    """Validate non-empty string."""
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be a string, got {type(value).__name__}")
    if not value.strip():
        raise ValidationError(f"{name} cannot be empty or whitespace")


def validate_file_path(
    file_path: Union[str, Path],
    must_exist: bool = True,
    allowed_extensions: Optional[List[str]] = None
) -> Path:
    """Validate file path."""
    if not file_path:
        raise ValidationError("file_path cannot be empty")
    p = Path(file_path)
    if must_exist and not p.exists():
        raise FileNotFoundError(f"file_path does not exist: {file_path}")
    if allowed_extensions:
        allowed_exts_lower = [ext.lower() for ext in allowed_extensions]
        if p.suffix.lower() not in allowed_exts_lower:
            raise ValidationError(
                f"Extension '{p.suffix}' is not allowed for path '{file_path}'. "
                f"Allowed extensions: {allowed_extensions}"
            )
    return p


def validate_positive_number(
    value: Union[int, float],
    name: str,
    min_value: Union[int, float] = 0,
    max_value: Optional[Union[int, float]] = None
) -> None:
    """Validate positive number within optional bounds."""
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be a number, got {type(value).__name__}")
    if value < min_value:
        raise ValidationError(f"{name} must be >= {min_value}, got {value}")
    if max_value is not None and value > max_value:
        raise ValidationError(f"{name} must be <= {max_value}, got {value}")


def validate_dataframe_schema(
    df_or_schema: Any,
    required_columns: List[str],
    dataset_name: str = "DataFrame"
) -> None:
    """
    Validate that a DataFrame, LazyFrame, Schema, or Schema dict contains required columns.
    
    Args:
        df_or_schema: DataFrame, LazyFrame, Polars Schema, or schema dictionary
        required_columns: List of column names that must be present
        dataset_name: Optional descriptive label for error reporting
    """
    if df_or_schema is None:
        raise ValidationError(f"{dataset_name} cannot be None")
    
    existing_cols = None
    if isinstance(df_or_schema, dict):
        existing_cols = list(df_or_schema.keys())
    elif hasattr(df_or_schema, "columns"):
        existing_cols = list(df_or_schema.columns)
    elif hasattr(df_or_schema, "names"):
        existing_cols = list(df_or_schema.names)
    elif isinstance(df_or_schema, (list, set, tuple)):
        existing_cols = list(df_or_schema)
    
    if existing_cols is None:
        raise ValidationError(
            f"Object of type {type(df_or_schema).__name__} does not expose schema or columns attribute"
        )
    
    missing = [col for col in required_columns if col not in existing_cols]
    if missing:
        raise ValidationError(
            f"Missing required columns in {dataset_name}: {missing}. "
            f"Available columns: {existing_cols}"
        )


def validate_column_exists(df: Any, column_name: str) -> None:
    """Validate that a column exists in DataFrame."""
    validate_dataframe_schema(df, [column_name])


__all__ = [
    "ValidationError",
    "validate_non_empty_string",
    "validate_file_path",
    "validate_dataframe_schema",
    "validate_column_exists",
    "validate_positive_number",
]
