"""
Data Adapters — Pydantic-First Architecture.

The ``process()`` method performs dataset operations and stores loaded datasets
in the global ObjectStore, returning typed Pydantic response payloads with lightweight
``data_id`` handles that downstream tools and adapters can consume.
"""

from __future__ import annotations

import json as _json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, computed_field

# Dual module registration for backward compatibility
_mod = sys.modules.get(__name__)
if _mod:
    sys.modules["adapters.data_adapter"] = _mod
    sys.modules["optimization_core.adapters.data_adapter"] = _mod

try:
    from optimization_core.adapters.base import (
        AdapterConfigurationError,
        AdapterExecutionError,
        BaseDynamicAdapter,
        ObjectNotFoundError,
    )
except ImportError:
    from .base import (
        AdapterConfigurationError,
        AdapterExecutionError,
        BaseDynamicAdapter,
        ObjectNotFoundError,
    )

logger: logging.Logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Response Models
# ---------------------------------------------------------------------------

class DataSplitStats(BaseModel):
    """Summary statistics for a dataset split."""
    num_samples: int = Field(default=0, description="Total sample count in dataset split")
    avg_word_length: float = Field(default=0.0, description="Average word count per sample")


class DataLoadResult(BaseModel):
    """Typed response model from a dataset load operation."""
    status: str = Field(default="success", description="Status of load operation")
    data_id: str = Field(description="Unique object store ID for the dataset")
    train_samples: int = Field(description="Number of samples in training split")
    val_samples: int = Field(description="Number of samples in validation split")

    @computed_field  # type: ignore[misc]
    @property
    def total_samples(self) -> int:
        """Calculate total number of samples across training and validation splits."""
        return self.train_samples + self.val_samples


class DataInfoResult(BaseModel):
    """Typed response model for dataset metadata info query."""
    status: str = Field(default="success", description="Status of info query")
    data_id: str = Field(description="Target dataset identifier")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Dataset metadata parameters")


class DataListResult(BaseModel):
    """Typed response model listing available datasets in store."""
    status: str = Field(default="success", description="Status of listing operation")
    datasets: List[str] = Field(default_factory=list, description="List of active dataset object IDs")


# ---------------------------------------------------------------------------
# Core Data Adapter Classes
# ---------------------------------------------------------------------------

class DataAdapter(BaseDynamicAdapter):
    """Base dynamic adapter for data loading and dataset inspection operations."""

    name: str = "data_adapter"
    description: str = (
        "Adapter to load and analyze datasets. Input JSON: "
        "{'action': 'load'|'info'|'list', 'source': 'str', 'kwargs': {}}"
    )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically process dataset operations based on action payload.

        Args:
            input_data: Dictionary payload containing 'action' and operation kwargs.

        Returns:
            Dictionary response serialized from corresponding Pydantic result model.

        Raises:
            ValueError: If an unknown action is provided or missing parameter.
            AdapterConfigurationError: If missing required payload fields.
        """
        action = input_data.get("action")
        kwargs: Dict[str, Any] = input_data.get("kwargs", {})

        if action == "load":
            source = input_data.get("source", "")
            if not source and "dataset_name" in kwargs:
                source = str(kwargs.get("dataset_name", ""))

            train_data, val_data = self.load_data(source, **kwargs)
            data_id = self.store.put(
                {"train": train_data, "val": val_data},
                kind="dataset",
                meta={
                    "source": source,
                    "train_samples": len(train_data),
                    "val_samples": len(val_data),
                },
            )
            return DataLoadResult(
                data_id=data_id,
                train_samples=len(train_data),
                val_samples=len(val_data),
            ).model_dump()

        elif action == "info":
            data_id = input_data.get("data_id", "")
            if data_id:
                meta = self.store.get_meta(data_id)
                return DataInfoResult(data_id=data_id, meta=meta).model_dump()
            return {"status": "success", "message": "Pass a data_id to retrieve info."}

        elif action == "list":
            ids = self.store.list_ids(kind="dataset")
            return DataListResult(datasets=ids).model_dump()

        else:
            raise ValueError(f"Unknown data action: '{action}'. Supported actions: 'load', 'info', 'list'.")

    def load_data(self, source: str, **kwargs: Any) -> Tuple[List[str], List[str]]:
        """
        Load training and validation data splits. Must be overridden in subclasses.

        Args:
            source: Source path or dataset name string.
            **kwargs: Class-specific loading options.

        Returns:
            Tuple of (train_texts, val_texts).

        Raises:
            NotImplementedError: If not implemented in derived subclass.
        """
        raise NotImplementedError("Subclasses must implement load_data().")

    def get_data_info(self, data: List[str]) -> DataSplitStats:
        """
        Compute summary statistics for a data split.

        Args:
            data: List of text strings.

        Returns:
            DataSplitStats model instance.
        """
        if not data:
            return DataSplitStats(num_samples=0, avg_word_length=0.0)

        avg_len = sum(len(text.split()) for text in data) / max(1, len(data))
        return DataSplitStats(num_samples=len(data), avg_word_length=round(avg_len, 2))


class HuggingFaceDataAdapter(DataAdapter):
    """Adapter for loading datasets from HuggingFace Hub."""

    name: str = "hf_data_adapter"
    description: str = (
        "Load datasets from HuggingFace Hub. Input JSON: "
        "{'action': 'load', 'source': 'dataset_name', 'kwargs': {'subset': 'optional', 'text_field': 'text'}}"
    )

    def load_data(self, source: str, **kwargs: Any) -> Tuple[List[str], List[str]]:
        """
        Load data split from HuggingFace Hub.

        Args:
            source: Dataset repository identifier on HuggingFace Hub.
            **kwargs: Extra arguments (subset, text_field, streaming).

        Returns:
            Tuple of (train_samples, val_samples).

        Raises:
            ImportError: If 'datasets' library is missing.
            ValueError: If source/dataset_name is empty.
        """
        try:
            from datasets import load_dataset
        except ImportError as err:
            raise ImportError(
                "HuggingFace 'datasets' package is required for HuggingFaceDataAdapter. "
                "Install it via `pip install datasets`."
            ) from err

        dataset_name = str(kwargs.get("dataset_name", source))
        subset = kwargs.get("subset")
        text_field = str(kwargs.get("text_field", "text"))
        streaming = bool(kwargs.get("streaming", False))

        if not dataset_name:
            raise ValueError("Dataset name or source must be provided for HuggingFaceDataAdapter.")

        if subset:
            ds = load_dataset(dataset_name, str(subset), streaming=streaming)
        else:
            ds = load_dataset(dataset_name, streaming=streaming)

        train_data = ds["train"][text_field] if not streaming else ds["train"]

        if "validation" in ds:
            val_data = ds["validation"][text_field] if not streaming else ds["validation"]
        elif "val" in ds:
            val_data = ds["val"][text_field] if not streaming else ds["val"]
        else:
            val_data = train_data

        train_list = list(train_data) if not isinstance(train_data, list) else train_data
        val_list = list(val_data) if not isinstance(val_data, list) else val_data

        return train_list, val_list


class JSONLDataAdapter(DataAdapter):
    """Adapter for loading datasets from local JSONL files."""

    name: str = "jsonl_data_adapter"
    description: str = (
        "Load datasets from local JSONL files. Input JSON: "
        "{'action': 'load', 'source': '/path/to/file.jsonl', 'kwargs': {'text_field': 'text', 'train_split': 0.9}}"
    )

    def load_data(self, source: str, **kwargs: Any) -> Tuple[List[str], List[str]]:
        """
        Load text dataset from local JSONL file.

        Args:
            source: Local filesystem path to JSONL file.
            **kwargs: Additional parameters ('text_field', 'train_split').

        Returns:
            Tuple of (train_samples, val_samples).

        Raises:
            ValueError: If source is missing or train_split is out of bounds [0.0, 1.0].
            FileNotFoundError: If source path does not exist on disk.
        """
        if not source:
            raise ValueError("File source path must be specified for JSONLDataAdapter.")

        if not os.path.exists(source):
            raise FileNotFoundError(f"JSONL dataset source file not found: '{source}'")

        text_field = str(kwargs.get("text_field", "text"))
        train_split = float(kwargs.get("train_split", 0.9))

        if not (0.0 <= train_split <= 1.0):
            raise ValueError(f"train_split must be between 0.0 and 1.0, got: {train_split}")

        texts: List[str] = []
        is_gz = source.endswith(".gz")
        if is_gz:
            import gzip
            open_fn = lambda p: gzip.open(p, "rt", encoding="utf-8", errors="ignore")
        else:
            open_fn = lambda p: open(p, "r", encoding="utf-8", errors="ignore")

        with open_fn(source) as f:
            for line_idx, line in enumerate(f, start=1):
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    data = _json.loads(line_str)
                except _json.JSONDecodeError as exc:
                    logger.warning("JSONL parse error on line %d of '%s': %s", line_idx, source, exc)
                    continue

                if isinstance(data, dict) and text_field in data:
                    texts.append(str(data[text_field]))

        split_idx = int(len(texts) * train_split)
        return texts[:split_idx], texts[split_idx:]


__all__ = [
    "DataSplitStats",
    "DataLoadResult",
    "DataInfoResult",
    "DataListResult",
    "DataAdapter",
    "HuggingFaceDataAdapter",
    "JSONLDataAdapter",
]
