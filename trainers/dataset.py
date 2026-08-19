"""
Dataset module for trainers.

Provides specialized Dataset classes for tokenized texts, raw sequences,
streaming iterables, and block packing.
"""
from typing import List, Dict, Any, Optional, Iterator, Callable
import torch
from torch.utils.data import Dataset, IterableDataset

from .exceptions import DataManagerError, DataLoadingError


class HFTextDataset(Dataset):
    """Dataset wrapper for HuggingFace tokenized text sequences."""

    def __init__(self, tokenizer: Any, texts: List[str], max_length: int = 512):
        if not texts:
            raise DataLoadingError("HFTextDataset texts list cannot be empty.")
        if tokenizer is None:
            raise DataLoadingError("tokenizer cannot be None.")
        self.tokenizer = tokenizer
        self.texts = texts
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        if idx < 0 or idx >= len(self.texts):
            raise IndexError(f"Index {idx} out of bounds for dataset of length {len(self.texts)}")
        try:
            text = self.texts[idx]
            tokens = self.tokenizer(
                text,
                truncation=True,
                max_length=self.max_length,
                padding="max_length",
                return_tensors="pt",
            )
            input_ids = tokens["input_ids"].squeeze(0)
            attn_mask = tokens["attention_mask"].squeeze(0)
            labels = input_ids.clone()
            return {"input_ids": input_ids, "attention_mask": attn_mask, "labels": labels}
        except Exception as e:
            if isinstance(e, IndexError):
                raise
            raise DataLoadingError(f"Failed to tokenize sample at index {idx}: {e}") from e


class TextDataset(Dataset):
    """Generic text dataset supporting pre-tokenized or raw string inputs."""

    def __init__(self, data: List[Any]):
        self.data = data

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Any:
        if idx < 0 or idx >= len(self.data):
            raise IndexError(f"Index {idx} out of bounds for dataset of length {len(self.data)}")
        return self.data[idx]


class IterableTextDataset(IterableDataset):
    """Streaming iterable text dataset for memory-efficient loading of large datasets."""

    def __init__(self, generator_fn: Callable[[], Iterator[str]], tokenizer: Any, max_length: int = 512):
        self.generator_fn = generator_fn
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __iter__(self) -> Iterator[Dict[str, torch.Tensor]]:
        for text in self.generator_fn():
            tokens = self.tokenizer(
                text,
                truncation=True,
                max_length=self.max_length,
                padding="max_length",
                return_tensors="pt",
            )
            input_ids = tokens["input_ids"].squeeze(0)
            attn_mask = tokens["attention_mask"].squeeze(0)
            yield {"input_ids": input_ids, "attention_mask": attn_mask, "labels": input_ids.clone()}


class PackedDataset(Dataset):
    """Packed sequence dataset concatenating short sequences into fixed-length blocks."""

    def __init__(self, token_ids_list: List[List[int]], block_size: int = 512):
        if block_size <= 0:
            raise DataLoadingError(f"Block size must be positive, got {block_size}")
        self.blocks: List[List[int]] = []
        all_ids: List[int] = []
        for ids in token_ids_list:
            all_ids.extend(ids)
        for i in range(0, len(all_ids) - block_size + 1, block_size):
            self.blocks.append(all_ids[i:i + block_size])

    def __len__(self) -> int:
        return len(self.blocks)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        if idx < 0 or idx >= len(self.blocks):
            raise IndexError(f"Index {idx} out of bounds for dataset of length {len(self.blocks)}")
        block = torch.tensor(self.blocks[idx], dtype=torch.long)
        return {"input_ids": block, "attention_mask": torch.ones_like(block), "labels": block.clone()}


class BucketBatchSampler:
    """Batch sampler that groups sequences by length into buckets to minimize padding."""

    def __init__(
        self,
        dataset: List[str],
        tokenizer: Any,
        batch_size: int,
        bucket_bins: Optional[List[int]] = None,
        drop_last: bool = False,
    ):
        self.dataset = dataset
        self.tokenizer = tokenizer
        self.batch_size = max(1, batch_size)
        self.bucket_bins = bucket_bins or [64, 128, 256, 512]
        self.drop_last = drop_last
        self.batches = self._prepare_batches()

    def _prepare_batches(self) -> List[List[int]]:
        lengths = [
            len(self.tokenizer.encode(t, add_special_tokens=False))
            if hasattr(self.tokenizer, "encode") else len(t.split())
            for t in self.dataset
        ]
        bin_indices: Dict[int, List[int]] = {b: [] for b in self.bucket_bins}
        max_bin = self.bucket_bins[-1]
        for idx, length in enumerate(lengths):
            chosen_bin = next((b for b in self.bucket_bins if length <= b), max_bin)
            bin_indices[chosen_bin].append(idx)
        batches: List[List[int]] = []
        for bin_size in self.bucket_bins:
            indices = bin_indices[bin_size]
            for i in range(0, len(indices), self.batch_size):
                batch = indices[i:i + self.batch_size]
                if self.drop_last and len(batch) < self.batch_size:
                    continue
                batches.append(batch)
        return batches

    def __iter__(self) -> Iterator[List[int]]:
        for batch in self.batches:
            yield batch

    def __len__(self) -> int:
        return len(self.batches)


__all__ = ["HFTextDataset", "TextDataset", "IterableTextDataset", "PackedDataset", "BucketBatchSampler"]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.trainers."):
        sys.modules["trainers." + __name__[len("optimization_core.trainers."):]] = _mod
    elif __name__.startswith("trainers."):
        sys.modules["optimization_core.trainers." + __name__[len("trainers."):]] = _mod
