"""
Dataset Factories
=================
Factory functions and registry for loading NLP, multi-modal, Parquet, JSONL, CSV, and synthetic datasets.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Union

from .base import FactoryMetadata
from .registry import Registry
from .utils import safe_import

logger = logging.getLogger(__name__)

DATASETS = Registry(name="DatasetRegistry")


@dataclass
class DatasetConfig:
    """Configuration specification for dataset construction."""

    type: str = "synthetic"
    path_or_name: str = ""
    subset: Optional[str] = None
    text_field: str = "text"
    streaming: bool = False
    limit: Optional[int] = None
    extra_kwargs: Dict[str, Any] = field(default_factory=dict)


@DATASETS.register("hf", priority=100, aliases=["huggingface", "hf_datasets"], description="HuggingFace Datasets Stream/InMemory Builder")
def build_hf(
    dataset: str,
    subset: Optional[str] = None,
    text_field: str = "text",
    streaming: bool = False,
    limit: Optional[int] = None,
    **kwargs: Any,
) -> Tuple[Any, Any]:
    """
    Build HuggingFace dataset streams or in-memory text lists.
    
    Returns:
        Tuple of (train_data, validation_data)
    """
    datasets_lib = safe_import("datasets")
    if datasets_lib is None:
        logger.warning("HuggingFace 'datasets' library is not installed. Returning empty dataset fallback.")
        return [], []

    load_dataset = datasets_lib.load_dataset
    try:
        ds = load_dataset(dataset, subset) if subset else load_dataset(dataset)
        if streaming:
            train = ds["train"].to_iterable_dataset()
            val = ds.get("validation", ds["train"]).to_iterable_dataset()
            return (
                (ex[text_field] for ex in train.take(limit) if text_field in ex) if limit else (ex[text_field] for ex in train if text_field in ex),
                (ex[text_field] for ex in val.take(max(256, (limit or 0) // 10)) if text_field in ex) if limit else (ex[text_field] for ex in val if text_field in ex),
            )

        train_data = ds.get("train", [])
        val_data = ds.get("validation", ds.get("test", train_data))

        train_lim = limit or len(train_data)
        val_lim = max(1, min(len(val_data), train_lim // 10 or 256))

        train_texts = [ex[text_field] for ex in train_data[:train_lim] if isinstance(ex, dict) and text_field in ex]
        val_texts = [ex[text_field] for ex in val_data[:val_lim] if isinstance(ex, dict) and text_field in ex]
        return train_texts, val_texts
    except Exception as e:
        logger.error(f"Error loading HF dataset '{dataset}': {e}")
        return [], []


@DATASETS.register("jsonl", priority=90, aliases=["json_lines"], description="Local JSONL Dataset Loader")
def build_jsonl(
    path: str, text_field: str = "text", limit: Optional[int] = None, **kwargs: Any
) -> Tuple[List[str], List[str]]:
    """
    Build dataset from a local JSONL file with train/validation split.
    
    Returns:
        Tuple of (train_texts, validation_texts)
    """
    def reader(p: str, lim: Optional[int]) -> Iterator[str]:
        count = 0
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        if isinstance(obj, dict) and text_field in obj:
                            yield obj[text_field]
                            count += 1
                            if lim and count >= lim:
                                break
                    except Exception:
                        continue
        except FileNotFoundError:
            logger.error(f"JSONL file not found at path: '{p}'")

    all_texts = list(reader(path, limit))
    if not all_texts:
        return [], []
    split = max(1, int(len(all_texts) * 0.9))
    return all_texts[:split], all_texts[split:]


@DATASETS.register("webdataset", priority=80, aliases=["wds", "tarball"], description="WebDataset Sharded Tarball Loader")
def build_webdataset(
    url_or_path: str, text_field: str = "text", limit: Optional[int] = None, **kwargs: Any
) -> Tuple[List[str], List[str]]:
    """WebDataset loader factory for sharded tarball datasets."""
    wds = safe_import("webdataset")
    if wds is not None:
        try:
            dataset = wds.WebDataset(url_or_path).decode("utf-8").to_tuple(f"{text_field}.txt")
            items = []
            for i, (text,) in enumerate(dataset):
                items.append(text)
                if limit and i >= limit:
                    break
            split = max(1, int(len(items) * 0.9))
            return items[:split], items[split:]
        except Exception as e:
            logger.warning(f"Error initializing WebDataset: {e}")
    return [], []


@DATASETS.register("parquet", priority=70, aliases=["pq"], description="Apache Parquet File Dataset Loader")
def build_parquet(
    path: str, text_field: str = "text", limit: Optional[int] = None, **kwargs: Any
) -> Tuple[List[str], List[str]]:
    """Build dataset from an Apache Parquet file using pandas or pyarrow."""
    pd = safe_import("pandas")
    if pd is not None:
        try:
            df = pd.read_parquet(path)
            if text_field in df.columns:
                texts = df[text_field].dropna().tolist()
                if limit:
                    texts = texts[:limit]
                split = max(1, int(len(texts) * 0.9))
                return texts[:split], texts[split:]
        except Exception as e:
            logger.error(f"Error reading parquet file '{path}': {e}")
    return [], []


@DATASETS.register("csv", priority=65, aliases=["tsv"], description="Local CSV/TSV Dataset Loader")
def build_csv(
    path: str, text_field: str = "text", delimiter: str = ",", limit: Optional[int] = None, **kwargs: Any
) -> Tuple[List[str], List[str]]:
    """Build dataset from a local CSV file."""
    pd = safe_import("pandas")
    if pd is not None:
        try:
            df = pd.read_csv(path, sep=delimiter)
            if text_field in df.columns:
                texts = df[text_field].dropna().astype(str).tolist()
                if limit:
                    texts = texts[:limit]
                split = max(1, int(len(texts) * 0.9))
                return texts[:split], texts[split:]
        except Exception as e:
            logger.error(f"Error reading CSV file '{path}': {e}")
    return [], []


@DATASETS.register("synthetic", priority=60, aliases=["dummy", "mock"], description="Benchmarking Synthetic Text Generator")
def build_synthetic(
    num_samples: int = 100, vocab_size: int = 1000, seq_len: int = 64, **kwargs: Any
) -> Tuple[List[str], List[str]]:
    """Generate synthetic text samples for rapid benchmarking without network or disk dependencies."""
    import random
    words = [f"token_{i}" for i in range(vocab_size)]
    samples = []
    for _ in range(num_samples):
        sample = " ".join(random.choices(words, k=seq_len))
        samples.append(sample)
    split = int(num_samples * 0.9)
    return samples[:split], samples[split:]


__all__ = [
    "DATASETS",
    "DatasetConfig",
    "build_hf",
    "build_jsonl",
    "build_webdataset",
    "build_parquet",
    "build_csv",
    "build_synthetic",
]
