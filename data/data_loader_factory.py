"""
Factory for creating DataLoaders with various configurations.
"""
import logging
from typing import List, Dict, Any, Optional
import torch
from torch.utils.data import DataLoader, Dataset, BatchSampler, Sampler

try:
    from factories.collate import COLLATE
except ImportError:
    try:
        from optimization_core.factories.collate import COLLATE
    except ImportError:
        COLLATE = None

from .collators import LMCollator

logger = logging.getLogger(__name__)


class LengthBucketBatchSampler(BatchSampler):
    """
    Batch sampler that groups text samples into buckets of similar lengths
    to minimize padding overhead during training.
    """
    
    def __init__(
        self,
        texts: List[str],
        tokenizer: Any,
        batch_size: int,
        bucket_bins: Optional[List[int]] = None,
        drop_last: bool = False,
        shuffle: bool = True,
        seed: Optional[int] = None,
    ):
        """
        Initialize length bucket batch sampler.
        
        Args:
            texts: List of text samples
            tokenizer: Tokenizer instance for length calculation
            batch_size: Target batch size
            bucket_bins: Bin boundary list (default: [64, 128, 256, 512])
            drop_last: Whether to drop incomplete final batches per bin
            shuffle: Whether to shuffle batches and samples within bins
            seed: Random seed for shuffling
        """
        if not texts:
            raise ValueError("texts cannot be empty for length bucket sampling")
        if batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {batch_size}")
            
        self.texts = texts
        self.tokenizer = tokenizer
        self.batch_size = batch_size
        self.drop_last = drop_last
        self.shuffle = shuffle
        self.seed = seed
        
        sorted_bins = sorted(bucket_bins) if bucket_bins else [64, 128, 256, 512]
        self.bucket_bins = sorted_bins
        
        # Precompute lengths
        lengths = []
        for t in texts:
            if hasattr(tokenizer, "encode"):
                try:
                    toks = tokenizer.encode(t, add_special_tokens=False)
                except (TypeError, Exception):
                    try:
                        toks = tokenizer.encode(t)
                    except Exception:
                        toks = str(t).split()
                lengths.append(len(toks) if hasattr(toks, "__len__") else 1)
            elif callable(tokenizer):
                try:
                    res = tokenizer(t)
                    if isinstance(res, dict) and "input_ids" in res:
                        lengths.append(len(res["input_ids"]))
                    elif hasattr(res, "__len__"):
                        lengths.append(len(res))
                    else:
                        lengths.append(len(str(t).split()))
                except Exception:
                    lengths.append(len(str(t).split()))
            else:
                lengths.append(len(str(t).split()))

        # Assign to bins
        bin_indices: Dict[int, List[int]] = {b: [] for b in sorted_bins}
        for idx, length in enumerate(lengths):
            bin_size = next((b for b in sorted_bins if length <= b), sorted_bins[-1])
            bin_indices[bin_size].append(idx)
        
        # Build batches per bin
        self.batches: List[List[int]] = []
        for bin_size in sorted_bins:
            indices = bin_indices[bin_size]
            for i in range(0, len(indices), batch_size):
                batch = indices[i:i + batch_size]
                if not drop_last or len(batch) == batch_size:
                    self.batches.append(batch)
        
        logger.debug(
            f"Created LengthBucketBatchSampler with {len(self.batches)} batches "
            f"across {len(sorted_bins)} bins"
        )
    
    def __iter__(self):
        if self.shuffle:
            g = torch.Generator()
            if self.seed is not None:
                g.manual_seed(self.seed)
            perm = torch.randperm(len(self.batches), generator=g).tolist()
            for idx in perm:
                yield self.batches[idx]
        else:
            for batch in self.batches:
                yield batch
    
    def __len__(self) -> int:
        return len(self.batches)


class DataLoaderFactory:
    """Factory for creating optimized DataLoaders."""
    
    @staticmethod
    def create_loader(
        dataset: Dataset,
        batch_size: int,
        shuffle: bool = True,
        collate_fn: Optional[Any] = None,
        num_workers: int = 4,
        prefetch_factor: int = 2,
        persistent_workers: bool = True,
        pin_memory: bool = True,
        batch_sampler: Optional[Any] = None,
        drop_last: bool = False,
        generator: Optional[torch.Generator] = None,
    ) -> DataLoader:
        """
        Create a DataLoader with optimized settings.
        
        Args:
            dataset: PyTorch Dataset
            batch_size: Batch size (ignored if batch_sampler is provided)
            shuffle: Whether to shuffle
            collate_fn: Collate function
            num_workers: Number of worker processes
            prefetch_factor: Prefetch factor for workers
            persistent_workers: Keep workers alive between epochs
            pin_memory: Pin memory for faster GPU transfer
            batch_sampler: Optional batch sampler
            drop_last: Whether to drop last incomplete batch
            generator: Optional PyTorch random generator
        
        Returns:
            Configured DataLoader
        """
        if batch_sampler is not None:
            return DataLoader(
                dataset,
                batch_sampler=batch_sampler,
                collate_fn=collate_fn,
                num_workers=num_workers,
                prefetch_factor=prefetch_factor if num_workers > 0 else None,
                persistent_workers=persistent_workers if num_workers > 0 else False,
                pin_memory=pin_memory,
            )
        
        return DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            collate_fn=collate_fn,
            num_workers=num_workers,
            prefetch_factor=prefetch_factor if num_workers > 0 else None,
            persistent_workers=persistent_workers if num_workers > 0 else False,
            pin_memory=pin_memory,
            drop_last=drop_last,
            generator=generator,
        )
    
    @staticmethod
    def create_train_loader(
        texts: List[str],
        tokenizer: Any,
        max_length: int,
        batch_size: int,
        collate_type: str = "lm",
        bucket_by_length: bool = False,
        bucket_bins: Optional[List[int]] = None,
        num_workers: int = 4,
        prefetch_factor: int = 2,
        persistent_workers: bool = True,
        pin_memory: bool = True,
        drop_last: bool = False,
        seed: Optional[int] = None,
    ) -> DataLoader:
        """
        Create training DataLoader with optional length bucketing.
        
        Args:
            texts: List of text samples
            tokenizer: Tokenizer instance
            max_length: Maximum sequence length
            batch_size: Batch size
            collate_type: Type of collator (lm|cv)
            bucket_by_length: Whether to use length bucketing
            bucket_bins: Bucket size bins for length bucketing
            num_workers: Number of workers
            prefetch_factor: Prefetch factor
            persistent_workers: Keep workers alive
            pin_memory: Pin memory configuration
            drop_last: Drop last incomplete batch
            seed: Random seed for bucketing sampler
        
        Returns:
            Configured training DataLoader
        """
        collate_fn = DataLoaderFactory._get_collate_fn(collate_type, tokenizer, max_length)
        
        batch_sampler = None
        if bucket_by_length and collate_type == "lm":
            batch_sampler = LengthBucketBatchSampler(
                texts=texts,
                tokenizer=tokenizer,
                batch_size=batch_size,
                bucket_bins=bucket_bins or [64, 128, 256, 512],
                drop_last=drop_last,
                shuffle=True,
                seed=seed,
            )
        
        generator = None
        if seed is not None:
            generator = torch.Generator()
            generator.manual_seed(seed)

        return DataLoaderFactory.create_loader(
            dataset=list(texts),
            batch_size=batch_size,
            shuffle=(batch_sampler is None),
            collate_fn=collate_fn,
            num_workers=num_workers,
            prefetch_factor=prefetch_factor,
            persistent_workers=persistent_workers,
            pin_memory=pin_memory,
            batch_sampler=batch_sampler,
            drop_last=drop_last if batch_sampler is None else False,
            generator=generator if batch_sampler is None else None,
        )
    
    @staticmethod
    def _get_collate_fn(collate_type: str, tokenizer: Any, max_length: int) -> Any:
        """Helper to safely build collator function with fallback."""
        if COLLATE is not None:
            try:
                return COLLATE.build(collate_type)(tokenizer, max_length)
            except Exception as e:
                logger.warning(f"Could not build '{collate_type}' from COLLATE registry: {e}. Falling back to LMCollator.")
        return LMCollator(tokenizer, max_length=max_length)

    @staticmethod
    def create_val_loader(
        texts: List[str],
        tokenizer: Any,
        max_length: int,
        batch_size: int,
        collate_type: str = "lm",
        num_workers: int = 4,
        prefetch_factor: int = 2,
        persistent_workers: bool = True,
        pin_memory: bool = True,
    ) -> DataLoader:
        """
        Create validation DataLoader.
        
        Args:
            texts: List of text samples
            tokenizer: Tokenizer instance
            max_length: Maximum sequence length
            batch_size: Batch size
            collate_type: Type of collator (lm|cv)
            num_workers: Number of workers
            prefetch_factor: Prefetch factor
            persistent_workers: Keep workers alive
            pin_memory: Pin memory
        
        Returns:
            Configured validation DataLoader
        """
        collate_fn = DataLoaderFactory._get_collate_fn(collate_type, tokenizer, max_length)
        
        return DataLoaderFactory.create_loader(
            dataset=list(texts),
            batch_size=batch_size,
            shuffle=False,
            collate_fn=collate_fn,
            num_workers=num_workers,
            prefetch_factor=prefetch_factor,
            persistent_workers=persistent_workers,
            pin_memory=pin_memory,
        )
    
    @staticmethod
    def _create_length_bucket_sampler(
        texts: List[str],
        tokenizer: Any,
        batch_size: int,
        bucket_bins: List[int],
    ) -> Any:
        """Backward compatibility helper to build length bucket batch sampler."""
        return LengthBucketBatchSampler(
            texts=texts,
            tokenizer=tokenizer,
            batch_size=batch_size,
            bucket_bins=bucket_bins,
            shuffle=False,
        )


class DataLoaderBuilder:
    """
    Builder pattern for creating DataLoaders.
    Allows fluent API for configuration.
    """
    
    def __init__(self):
        self._texts: Optional[List[str]] = None
        self._tokenizer: Optional[Any] = None
        self._max_length: int = 512
        self._batch_size: int = 8
        self._collate_type: str = "lm"
        self._bucket_by_length: bool = False
        self._bucket_bins: Optional[List[int]] = None
        self._num_workers: int = 4
        self._prefetch_factor: int = 2
        self._persistent_workers: bool = True
        self._pin_memory: bool = True
        self._shuffle: bool = True
        self._drop_last: bool = False
        self._seed: Optional[int] = None
    
    def with_texts(self, texts: List[str]) -> "DataLoaderBuilder":
        """Set text samples."""
        self._texts = texts
        return self
    
    def with_tokenizer(self, tokenizer: Any) -> "DataLoaderBuilder":
        """Set tokenizer."""
        self._tokenizer = tokenizer
        return self
    
    def with_max_length(self, max_length: int) -> "DataLoaderBuilder":
        """Set maximum sequence length."""
        self._max_length = max_length
        return self
    
    def with_batch_size(self, batch_size: int) -> "DataLoaderBuilder":
        """Set batch size."""
        self._batch_size = batch_size
        return self
    
    def with_collate_type(self, collate_type: str) -> "DataLoaderBuilder":
        """Set collate type."""
        self._collate_type = collate_type
        return self
    
    def with_length_bucketing(
        self,
        enabled: bool = True,
        bins: Optional[List[int]] = None
    ) -> "DataLoaderBuilder":
        """Enable/disable length bucketing."""
        self._bucket_by_length = enabled
        if bins:
            self._bucket_bins = bins
        return self
    
    def with_workers(
        self,
        num_workers: int = 4,
        prefetch_factor: int = 2,
        persistent: bool = True
    ) -> "DataLoaderBuilder":
        """Configure worker processes."""
        self._num_workers = num_workers
        self._prefetch_factor = prefetch_factor
        self._persistent_workers = persistent
        return self

    def with_pin_memory(self, pin_memory: bool = True) -> "DataLoaderBuilder":
        """Set pin_memory configuration."""
        self._pin_memory = pin_memory
        return self
    
    def with_shuffle(self, shuffle: bool = True) -> "DataLoaderBuilder":
        """Enable/disable shuffling."""
        self._shuffle = shuffle
        return self

    def with_drop_last(self, drop_last: bool = True) -> "DataLoaderBuilder":
        """Enable/disable dropping last batch."""
        self._drop_last = drop_last
        return self

    def with_seed(self, seed: Optional[int]) -> "DataLoaderBuilder":
        """Set seed for random generation."""
        self._seed = seed
        return self
    
    def build_train(self) -> DataLoader:
        """Build training DataLoader."""
        if not self._texts or not self._tokenizer:
            raise ValueError("texts and tokenizer must be set")
        
        return DataLoaderFactory.create_train_loader(
            texts=self._texts,
            tokenizer=self._tokenizer,
            max_length=self._max_length,
            batch_size=self._batch_size,
            collate_type=self._collate_type,
            bucket_by_length=self._bucket_by_length,
            bucket_bins=self._bucket_bins,
            num_workers=self._num_workers,
            prefetch_factor=self._prefetch_factor,
            persistent_workers=self._persistent_workers,
            pin_memory=self._pin_memory,
            drop_last=self._drop_last,
            seed=self._seed,
        )
    
    def build_val(self) -> DataLoader:
        """Build validation DataLoader."""
        if not self._texts or not self._tokenizer:
            raise ValueError("texts and tokenizer must be set")
        
        return DataLoaderFactory.create_val_loader(
            texts=self._texts,
            tokenizer=self._tokenizer,
            max_length=self._max_length,
            batch_size=self._batch_size,
            collate_type=self._collate_type,
            num_workers=self._num_workers,
            prefetch_factor=self._prefetch_factor,
            persistent_workers=self._persistent_workers,
            pin_memory=self._pin_memory,
        )


LengthBucketSampler = LengthBucketBatchSampler

