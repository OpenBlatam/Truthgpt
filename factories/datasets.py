"""
Dataset Factories
=================
Factory functions and registry for loading NLP and multi-modal training datasets.
"""
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Union

from .registry import Registry

DATASETS = Registry(name="DatasetRegistry")


@DATASETS.register("hf")
def build_hf(
    dataset: str,
    subset: Optional[str] = None,
    text_field: str = "text",
    streaming: bool = False,
    limit: Optional[int] = None,
) -> Tuple[Any, Any]:
    """
    Build HuggingFace dataset streams or in-memory text lists.
    
    Returns:
        Tuple of (train_data, validation_data)
    """
    from datasets import load_dataset

    ds = load_dataset(dataset, subset) if subset else load_dataset(dataset)
    if streaming:
        train = ds["train"].to_iterable_dataset()
        val = ds["validation"].to_iterable_dataset()
        return (
            (ex[text_field] for ex in train.take(limit) if text_field in ex) if limit else (ex[text_field] for ex in train if text_field in ex),
            (ex[text_field] for ex in val.take(max(256, (limit or 0) // 10)) if text_field in ex) if limit else (ex[text_field] for ex in val if text_field in ex),
        )
    
    train_data = ds.get("train", [])
    val_data = ds.get("validation", ds.get("test", train_data))
    
    train_lim = limit or len(train_data)
    val_lim = max(1, min(len(val_data), train_lim // 10 or 256))
    
    train_texts = [ex[text_field] for ex in train_data[:train_lim] if text_field in ex]
    val_texts = [ex[text_field] for ex in val_data[:val_lim] if text_field in ex]
    return train_texts, val_texts


@DATASETS.register("jsonl")
def build_jsonl(
    path: str, text_field: str = "text", limit: Optional[int] = None
) -> Tuple[List[str], List[str]]:
    """
    Build dataset from a local JSONL file with train/validation split.
    
    Returns:
        Tuple of (train_texts, validation_texts)
    """
    import json

    def reader(p: str, lim: Optional[int]) -> Iterator[str]:
        count = 0
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    if text_field in obj:
                        yield obj[text_field]
                        count += 1
                        if lim and count >= lim:
                            break
                except Exception:
                    continue

    all_texts = list(reader(path, limit))
    split = max(1, int(len(all_texts) * 0.9))
    return all_texts[:split], all_texts[split:]


@DATASETS.register("webdataset")
def build_webdataset(
    url_or_path: str, text_field: str = "text", limit: Optional[int] = None
) -> Tuple[List[str], List[str]]:
    """
    WebDataset placeholder factory for sharded tarball datasets.
    """
    return [], []




