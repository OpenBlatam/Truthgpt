from abc import ABC, abstractmethod
import logging
from typing import Dict, List, Any, Union
import torch

logger = logging.getLogger(__name__)


class BaseCollator(ABC):
    """Abstract base class for all data collators."""

    @abstractmethod
    def __call__(self, batch: Any) -> Dict[str, torch.Tensor]:
        """Collate a batch of samples into PyTorch tensors."""
        pass


class ClassificationCollator(BaseCollator):
    """
    Data collator for sequence classification tasks.
    """

    def __init__(
        self,
        tokenizer: Any,
        max_length: int = 512,
        text_key: str = "text",
        label_key: str = "label",
    ):
        if tokenizer is None:
            raise ValueError("tokenizer cannot be None")
        if max_length <= 0:
            raise ValueError(f"max_length must be positive, got {max_length}")
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.text_key = text_key
        self.label_key = label_key

    def __call__(self, batch: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        if not batch:
            raise ValueError("Cannot collate an empty batch")

        texts = [item[self.text_key] for item in batch]
        labels = [item[self.label_key] for item in batch]

        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        encoded["labels"] = torch.tensor(labels, dtype=torch.long)
        return encoded


class LMCollator(BaseCollator):
    """
    Language modeling collator with dynamic padding, custom truncation side, and optional label masking.
    """
    
    def __init__(
        self,
        tokenizer: Any,
        max_length: int = 512,
        ignore_index: int = -100,
        pad_labels: bool = True,
        truncation_side: str = "right",
        text_key: str = "text",
        label_key: str = "labels",
    ):
        """
        Initialize collator.
        
        Args:
            tokenizer: Tokenizer instance (PreTrainedTokenizer or compatible mock)
            max_length: Maximum sequence length
            ignore_index: Target index for padded tokens in labels (default -100)
            pad_labels: If True, set pad token locations in labels to ignore_index
            truncation_side: Truncation side ("right" or "left")
            text_key: Key name for text in batch dictionaries
            label_key: Target key name for labels tensor
        """
        if tokenizer is None:
            raise ValueError("tokenizer cannot be None")
        if max_length <= 0:
            raise ValueError(f"max_length must be positive, got {max_length}")
        if truncation_side not in ("right", "left"):
            raise ValueError(f"truncation_side must be 'right' or 'left', got '{truncation_side}'")

        self.tokenizer = tokenizer
        self.max_length = max_length
        self.ignore_index = ignore_index
        self.pad_labels = pad_labels
        self.truncation_side = truncation_side
        self.text_key = text_key
        self.label_key = label_key
        
        # Configure tokenizer truncation side if attribute exists
        if hasattr(self.tokenizer, "truncation_side"):
            try:
                self.tokenizer.truncation_side = self.truncation_side
            except Exception as e:
                logger.debug(f"Could not set tokenizer.truncation_side: {e}")
        
        # Ensure pad token is set if missing
        if getattr(self.tokenizer, "pad_token", None) is None:
            if hasattr(self.tokenizer, "eos_token") and self.tokenizer.eos_token:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            elif hasattr(self.tokenizer, "pad_token_id") and self.tokenizer.pad_token_id is not None:
                pass
            else:
                logger.debug("Tokenizer has no pad_token or eos_token defined")

    def __call__(self, batch: Union[List[str], List[Dict[str, Any]]]) -> Dict[str, torch.Tensor]:
        """
        Collate a batch of text strings or feature dictionaries.
        
        Args:
            batch: List of text strings or feature dictionaries
        
        Returns:
            Dictionary containing 'input_ids', 'attention_mask', and labels tensors.
        """
        if not batch:
            raise ValueError("Cannot collate an empty batch")

        # Handle list of text strings vs dictionaries
        if isinstance(batch[0], str):
            encoded = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )
        elif isinstance(batch[0], dict):
            # If items are already dictionaries, extract texts or combine tensors
            if self.text_key in batch[0]:
                texts = [item[self.text_key] for item in batch]
                encoded = self.tokenizer(
                    texts,
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors="pt",
                )
            else:
                # Direct tensor dictionary batching
                return {
                    k: torch.stack([torch.as_tensor(item[k]) for item in batch])
                    for k in batch[0]
                }
        else:
            raise TypeError(f"Unsupported batch item type: {type(batch[0])}")

        input_ids = encoded["input_ids"]
        attention_mask = encoded["attention_mask"]

        # Create labels for language modeling
        labels = input_ids.clone()
        
        if self.pad_labels:
            pad_id = getattr(self.tokenizer, "pad_token_id", None)
            if pad_id is not None:
                labels[labels == pad_id] = self.ignore_index

        res = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            self.label_key: labels,
        }

        # Include additional tokenizer fields if present (e.g., token_type_ids)
        for key in encoded:
            if key not in res and key != "labels":
                res[key] = encoded[key]

        return res





