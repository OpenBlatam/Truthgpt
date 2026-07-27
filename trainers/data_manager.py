"""
Data Manager - Handles data loading, collating, dynamic sequence bucketing, and DataLoader setup.

Separated from trainer for better modularity and dataset isolation.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple, Callable
import torch
from torch.utils.data import DataLoader

from .config import TrainingConfig, HardwareConfig
from .dataset import HFTextDataset, BucketBatchSampler as LengthBucketBatchSampler
from .interfaces import BaseDataManager
from .exceptions import DataManagerError, DataLoadingError

try:
    from factories.collate import COLLATE
    _COLLATE_REGISTRY_AVAILABLE = True
except Exception as e:
    _COLLATE_REGISTRY_AVAILABLE = False
    COLLATE = None

# Backward compatibility alias
BucketBatchSampler = LengthBucketBatchSampler

logger = logging.getLogger(__name__)


class DataManager(BaseDataManager):
    """
    Manages data loading and DataLoader creation.
    
    Responsibilities:
    - Instantiate training and validation DataLoaders
    - Handle collators (LM collate via registry with fallback)
    - Apply dynamic sequence length bucketing sampler
    - Configure num_workers, prefetch_factor, and persistent_workers
    """
    
    def __init__(
        self,
        training_config: TrainingConfig,
        hardware_config: HardwareConfig,
        tokenizer: Any,
        text_field_max_len: int = 512,
        data_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize DataManager.
        
        Args:
            training_config: Training configuration
            hardware_config: Hardware configuration
            tokenizer: Tokenizer instance
            text_field_max_len: Maximum text sequence length
            data_options: Optional collation or bucketing options
        """
        self.training_config = training_config
        self.hardware_config = hardware_config
        self.tokenizer = tokenizer
        self.text_field_max_len = text_field_max_len
        self.data_options = data_options or {}
        self.train_loader: Optional[DataLoader] = None
        self.val_loader: Optional[DataLoader] = None
    
    def create_loaders(
        self,
        train_texts: List[str],
        val_texts: List[str],
    ) -> Tuple[DataLoader, DataLoader]:
        """
        Create training and validation DataLoaders.
        
        Args:
            train_texts: Training corpus strings
            val_texts: Validation corpus strings
            
        Returns:
            Tuple of (train_loader, val_loader)
        """
        if not train_texts:
            raise DataLoadingError("train_texts cannot be empty.", context={"len_train_texts": 0})
        if not val_texts:
            raise DataLoadingError("val_texts cannot be empty.", context={"len_val_texts": 0})

        collate_name = str(self.data_options.get("collate", "lm"))
        use_lm_collate = collate_name == "lm"
        collate_fn: Optional[Callable] = None
        
        if use_lm_collate and _COLLATE_REGISTRY_AVAILABLE and COLLATE is not None:
            try:
                collate_fn = COLLATE.build("lm")(self.tokenizer, self.text_field_max_len)
            except Exception as e:
                logger.warning(f"Could not build 'lm' collator from registry: {e}. Falling back to HFTextDataset.")
                collate_fn = None
        
        bucket_by_length = bool(self.data_options.get("bucket_by_length", False)) and use_lm_collate
        bucket_bins = list(self.data_options.get("bucket_bins", [64, 128, 256, 512]))
        
        num_workers = max(0, getattr(self.hardware_config, "num_workers", 0))
        prefetch_factor = getattr(self.hardware_config, "prefetch_factor", 2) if num_workers > 0 else None
        persistent_workers = getattr(self.hardware_config, "persistent_workers", False) if num_workers > 0 else False
        
        if collate_fn is not None:
            train_dataset = list(train_texts)
            val_dataset = list(val_texts)
            
            batch_sampler = None
            if bucket_by_length and self.tokenizer is not None:
                batch_sampler = BucketBatchSampler(
                    dataset=train_dataset,
                    tokenizer=self.tokenizer,
                    batch_size=self.training_config.train_batch_size,
                    bucket_bins=bucket_bins,
                )
            
            self.train_loader = DataLoader(
                train_dataset,
                batch_size=None if batch_sampler is not None else self.training_config.train_batch_size,
                shuffle=(batch_sampler is None),
                num_workers=num_workers,
                pin_memory=torch.cuda.is_available(),
                prefetch_factor=prefetch_factor,
                persistent_workers=persistent_workers,
                collate_fn=collate_fn,
                batch_sampler=batch_sampler,
            )
            
            self.val_loader = DataLoader(
                val_dataset,
                batch_size=self.training_config.eval_batch_size,
                shuffle=False,
                num_workers=num_workers,
                pin_memory=torch.cuda.is_available(),
                prefetch_factor=prefetch_factor,
                persistent_workers=persistent_workers,
                collate_fn=collate_fn,
            )
        else:
            self.train_loader = DataLoader(
                HFTextDataset(self.tokenizer, train_texts, self.text_field_max_len),
                batch_size=self.training_config.train_batch_size,
                shuffle=True,
                num_workers=num_workers,
                pin_memory=torch.cuda.is_available(),
                prefetch_factor=prefetch_factor,
                persistent_workers=persistent_workers,
            )
            
            self.val_loader = DataLoader(
                HFTextDataset(self.tokenizer, val_texts, self.text_field_max_len),
                batch_size=self.training_config.eval_batch_size,
                shuffle=False,
                num_workers=num_workers,
                pin_memory=torch.cuda.is_available(),
                prefetch_factor=prefetch_factor,
                persistent_workers=persistent_workers,
            )
            
        logger.info(
            f"DataLoaders created: {len(train_texts)} train samples ({len(self.train_loader)} batches), "
            f"{len(val_texts)} val samples ({len(self.val_loader)} batches)."
        )
        return self.train_loader, self.val_loader


__all__ = ["DataManager", "BucketBatchSampler"]
