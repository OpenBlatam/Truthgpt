"""
Data Manager - Handles data loading and preprocessing.

Separated from trainer for better modularity.
"""
import logging
from typing import List, Dict, Any, Optional, Callable
import torch
from torch.utils.data import DataLoader, Dataset

from trainers.config import TrainingConfig, HardwareConfig
from factories.collate import COLLATE

logger = logging.getLogger(__name__)


class HFTextDataset(Dataset):
    """Simple dataset for HuggingFace tokenized text."""
    
    def __init__(self, tokenizer, texts: List[str], max_length: int):
        self.tokenizer = tokenizer
        self.texts = texts
        self.max_length = max_length
    
    def __len__(self) -> int:
        return len(self.texts)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
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


class DataManager:
    """
    Manages data loading and preprocessing.
    
    Responsibilities:
    - Create DataLoaders with proper configuration
    - Handle dynamic padding and bucketing
    - Configure workers and prefetching
    """
    
    def __init__(
        self,
        training_config: TrainingConfig,
        hardware_config: HardwareConfig,
        tokenizer,
        text_field_max_len: int = 512,
        data_options: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize DataManager.
        
        Args:
            training_config: Training configuration
            hardware_config: Hardware configuration
            tokenizer: Tokenizer instance
            text_field_max_len: Maximum text length
            data_options: Additional data options (collate, bucketing, etc.)
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
    ) -> tuple[DataLoader, DataLoader]:
        """
        Create training and validation DataLoaders.
        
        Args:
            train_texts: Training texts
            val_texts: Validation texts
            
        Returns:
            Tuple of (train_loader, val_loader)
        """
        # Determine collate function
        collate_name = str(self.data_options.get("collate", "lm"))
        use_lm_collate = collate_name == "lm"
        collate_fn: Optional[Callable] = None
        
        if use_lm_collate:
            collate_fn = COLLATE.build("lm")(self.tokenizer, self.text_field_max_len)
        
        # Check for bucketing
        bucket_by_length = bool(self.data_options.get("bucket_by_length", False)) and use_lm_collate
        bucket_bins = list(self.data_options.get("bucket_bins", [64, 128, 256, 512]))
        
        # Create train loader
        if collate_fn is not None:
            train_dataset = list(train_texts)
            val_dataset = list(val_texts)
            
            batch_sampler = None
            if bucket_by_length:
                batch_sampler = self._create_bucket_sampler(train_dataset, bucket_bins)
            
            self.train_loader = DataLoader(
                train_dataset,
                batch_size=None if batch_sampler is not None else self.training_config.train_batch_size,
                shuffle=(batch_sampler is None),
                num_workers=self.hardware_config.num_workers,
                pin_memory=True,
                prefetch_factor=self.hardware_config.prefetch_factor if self.hardware_config.num_workers > 0 else None,
                persistent_workers=self.hardware_config.persistent_workers if self.hardware_config.num_workers > 0 else False,
                collate_fn=collate_fn,
                batch_sampler=batch_sampler,
            )
            
            self.val_loader = DataLoader(
                val_dataset,
                batch_size=self.training_config.eval_batch_size,
                shuffle=False,
                num_workers=self.hardware_config.num_workers,
                pin_memory=True,
                prefetch_factor=self.hardware_config.prefetch_factor if self.hardware_config.num_workers > 0 else None,
                persistent_workers=self.hardware_config.persistent_workers if self.hardware_config.num_workers > 0 else False,
                collate_fn=collate_fn,
            )
        else:
            # Fallback to static padding
            self.train_loader = DataLoader(
                HFTextDataset(self.tokenizer, train_texts, self.text_field_max_len),
                batch_size=self.training_config.train_batch_size,
                shuffle=True,
                num_workers=self.hardware_config.num_workers,
                pin_memory=True,
                prefetch_factor=self.hardware_config.prefetch_factor if self.hardware_config.num_workers > 0 else None,
                persistent_workers=self.hardware_config.persistent_workers if self.hardware_config.num_workers > 0 else False,
            )
            
            self.val_loader = DataLoader(
                HFTextDataset(self.tokenizer, val_texts, self.text_field_max_len),
                batch_size=self.training_config.eval_batch_size,
                shuffle=False,
                num_workers=self.hardware_config.num_workers,
                pin_memory=True,
                prefetch_factor=self.hardware_config.prefetch_factor if self.hardware_config.num_workers > 0 else None,
                persistent_workers=self.hardware_config.persistent_workers if self.hardware_config.num_workers > 0 else False,
            )
        
        logger.info(f"Created DataLoaders: train={len(self.train_loader)}, val={len(self.val_loader)}")
        return self.train_loader, self.val_loader
    
    def _create_bucket_sampler(self, dataset: List[str], bucket_bins: List[int]):
        """Create batch sampler with length bucketing."""
        # Precompute lengths
        lengths = [len(self.tokenizer.encode(t, add_special_tokens=False)) for t in dataset]
        
        # Assign to bins
        bin_indices: Dict[int, List[int]] = {b: [] for b in bucket_bins}
        for idx, length in enumerate(lengths):
            # Find appropriate bin
            bin_size = next((bb for bb in bucket_bins if length <= bb), bucket_bins[-1])
            bin_indices[bin_size].append(idx)
        
        # Create batches per bin
        batches: List[List[int]] = []
        batch_size = self.training_config.train_batch_size
        for bin_size in bucket_bins:
            indices = bin_indices[bin_size]
            for i in range(0, len(indices), batch_size):
                batches.append(indices[i:i + batch_size])
        
        # Create sampler
        class BucketBatchSampler:
            def __iter__(self):
                for batch in batches:
                    yield batch
            
            def __len__(self):
                return len(batches)
        
        logger.info(f"Created bucket sampler with {len(batches)} batches")
        return BucketBatchSampler()



