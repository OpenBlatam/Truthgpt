"""
Base Data Processor Interface.
==============================

Defines abstract base class for all data processors in optimization_core.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pathlib import Path


class BaseDataProcessor(ABC):
    """Abstract base class for all data processors."""

    @abstractmethod
    def read_parquet(self, path: Union[str, List[str], Path], **kwargs: Any) -> Any:
        """Read Parquet file(s)."""
        pass

    @abstractmethod
    def read_csv(self, path: Union[str, List[str], Path], **kwargs: Any) -> Any:
        """Read CSV file(s)."""
        pass

    @abstractmethod
    def read_jsonl(self, path: Union[str, List[str], Path], **kwargs: Any) -> Any:
        """Read JSONL file(s)."""
        pass

    @abstractmethod
    def read_json(self, path: Union[str, Path], **kwargs: Any) -> Any:
        """Read JSON file."""
        pass

    @abstractmethod
    def write_parquet(self, df: Any, path: Union[str, Path], **kwargs: Any) -> None:
        """Write DataFrame to Parquet format."""
        pass

    @abstractmethod
    def write_csv(self, df: Any, path: Union[str, Path], **kwargs: Any) -> None:
        """Write DataFrame to CSV format."""
        pass

    @abstractmethod
    def write_jsonl(self, df: Any, path: Union[str, Path], **kwargs: Any) -> None:
        """Write DataFrame to JSONL format."""
        pass

    @abstractmethod
    def get_schema(self, df: Any) -> Dict[str, Any]:
        """Get DataFrame schema dictionary."""
        pass

    @abstractmethod
    def get_stats(self, df: Any) -> Dict[str, Any]:
        """Get summary statistics for a DataFrame."""
        pass

