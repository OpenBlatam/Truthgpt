"""
Data Collator Factories
=======================
Factory functions and registry for data batching, dynamic padding, sequence packing (zero-padding),
masked language modeling collators, vision collators, and multimodal collation.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import torch

from .registry import Registry

logger = logging.getLogger(__name__)

COLLATE = Registry(name="CollatorRegistry")
COLLATORS = COLLATE


@dataclass
class CollateConfig:
    """Configuration specification for data collator construction."""

    type: str = "lm"
    max_length: int = 2048
    pad_to_multiple_of: Optional[int] = 8
    pack_sequences: bool = False
    extra_kwargs: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate collator configuration attributes."""
        if self.max_length <= 0:
            raise ValueError(f"max_length must be positive, got {self.max_length}")
        return True


@COLLATE.register(
    "lm",
    priority=100,
    aliases=["causal_lm", "language_modeling", "seq"],
    description="Build language modeling collate function with dynamic padding.",
    tags=["lm", "dynamic_padding", "text"],
)
def build_lm_collate(
    tokenizer: Any, max_length: int = 2048, pad_to_multiple_of: Optional[int] = 8, **kwargs: Any
) -> Callable[[List[Union[str, Dict[str, Any]]]], Dict[str, torch.Tensor]]:
    """
    Build language modeling collate function with dynamic padding.

    Args:
        tokenizer: HuggingFace tokenizer or equivalent callable.
        max_length: Maximum sequence length.
        pad_to_multiple_of: Pad sequence lengths to multiples of this value (e.g. 8 for Tensor Cores).

    Returns:
        Collate function processing batches into tensors.
    """

    def collate_fn(batch: List[Union[str, Dict[str, Any]]]) -> Dict[str, torch.Tensor]:
        try:
            if not batch:
                return {
                    "input_ids": torch.empty((0, max_length), dtype=torch.long),
                    "attention_mask": torch.empty((0, max_length), dtype=torch.long),
                    "labels": torch.empty((0, max_length), dtype=torch.long),
                }

            if isinstance(batch[0], str):
                tokens = tokenizer(
                    batch,
                    truncation=True,
                    max_length=max_length,
                    padding=False,
                    return_tensors=None,
                    add_special_tokens=True,
                )
                input_ids_list = [t["input_ids"] if isinstance(t, dict) else t for t in tokens]
            elif isinstance(batch[0], dict) and "input_ids" in batch[0]:
                input_ids_list = [item["input_ids"] for item in batch]
            else:
                input_ids_list = batch

            batch_max_len = min(max(len(ids) for ids in input_ids_list), max_length)
            if pad_to_multiple_of and pad_to_multiple_of > 1:
                remainder = batch_max_len % pad_to_multiple_of
                if remainder != 0:
                    batch_max_len = min(max_length, batch_max_len + (pad_to_multiple_of - remainder))

            padded_input_ids = []
            padded_attn_masks = []
            pad_id = getattr(tokenizer, "pad_token_id", 0)
            if pad_id is None:
                pad_id = 0

            for ids in input_ids_list:
                ids_truncated = ids[:batch_max_len]
                mask = [1] * len(ids_truncated)
                pad_len = batch_max_len - len(ids_truncated)

                if pad_len > 0:
                    ids_padded = ids_truncated + [pad_id] * pad_len
                    mask_padded = mask + [0] * pad_len
                else:
                    ids_padded = ids_truncated
                    mask_padded = mask

                padded_input_ids.append(ids_padded)
                padded_attn_masks.append(mask_padded)

            input_ids_tensor = torch.tensor(padded_input_ids, dtype=torch.long)
            attn_mask_tensor = torch.tensor(padded_attn_masks, dtype=torch.long)
            labels_tensor = input_ids_tensor.clone()

            labels_tensor[attn_mask_tensor == 0] = -100

            return {
                "input_ids": input_ids_tensor,
                "attention_mask": attn_mask_tensor,
                "labels": labels_tensor,
            }
        except Exception as e:
            logger.error(f"Error in build_lm_collate execution: {e}", exc_info=True)
            return {
                "input_ids": torch.empty((0, max_length), dtype=torch.long),
                "attention_mask": torch.empty((0, max_length), dtype=torch.long),
                "labels": torch.empty((0, max_length), dtype=torch.long),
            }

    return collate_fn


build_seq_collate = build_lm_collate


@COLLATE.register(
    "packed_lm",
    priority=90,
    aliases=["sequence_packing", "zero_padding"],
    description="Pack multiple sequences into a single continuous 1D tensor without pad tokens.",
    tags=["packed", "zero_bubble", "efficient"],
)
def build_packed_lm_collate(
    tokenizer: Any, max_length: int = 2048, **kwargs: Any
) -> Callable[[List[str]], Dict[str, torch.Tensor]]:
    """Build sequence packing collator for zero-bubble dynamic sequence packing."""

    def collate_fn(batch_texts: List[str]) -> Dict[str, torch.Tensor]:
        tokens = tokenizer(batch_texts, truncation=False, padding=False, return_tensors=None)
        all_ids: List[int] = []
        cu_seqlens = [0]

        for t in tokens:
            ids = t["input_ids"] if isinstance(t, dict) else t
            all_ids.extend(ids)
            cu_seqlens.append(len(all_ids))

        target_len = min(len(all_ids), max_length * len(batch_texts))
        input_ids_tensor = torch.tensor([all_ids[:target_len]], dtype=torch.long)
        cu_seqlens_tensor = torch.tensor(cu_seqlens, dtype=torch.int32)

        return {
            "input_ids": input_ids_tensor,
            "cu_seqlens": cu_seqlens_tensor,
            "labels": input_ids_tensor.clone(),
        }

    return collate_fn


@COLLATE.register(
    "masked_lm",
    priority=80,
    aliases=["mlm", "bert"],
    description="Build Masked Language Modeling collate function with random token masking.",
    tags=["mlm", "bert", "masking"],
)
def build_masked_lm_collate(
    tokenizer: Any, mlm_probability: float = 0.15, max_length: int = 512, **kwargs: Any
) -> Callable[[List[str]], Dict[str, torch.Tensor]]:
    """Build BERT-style Masked Language Modeling collator."""
    lm_collator = build_lm_collate(tokenizer, max_length=max_length)

    def collate_fn(batch: List[str]) -> Dict[str, torch.Tensor]:
        res = lm_collator(batch)
        input_ids = res["input_ids"]
        labels = input_ids.clone()

        probability_matrix = torch.full(labels.shape, mlm_probability)
        mask_id = getattr(tokenizer, "mask_token_id", 103)
        masked_indices = torch.bernoulli(probability_matrix).bool() & (res["attention_mask"] == 1)

        labels[~masked_indices] = -100
        input_ids[masked_indices] = mask_id
        res["input_ids"] = input_ids
        res["labels"] = labels
        return res

    return collate_fn


@COLLATE.register(
    "cv",
    priority=70,
    aliases=["vision", "image_classification"],
    description="Build Computer Vision collate function with image normalization and tensor stacking.",
    tags=["vision", "cv", "images"],
)
def build_cv_collate(image_transform: Optional[Any] = None, **kwargs: Any) -> Callable[..., Dict[str, torch.Tensor]]:
    """Build computer vision image batch collator."""

    def collate_fn(batch: List[Tuple[Any, Any]]) -> Dict[str, torch.Tensor]:
        images = []
        labels = []
        for img, lbl in batch:
            if image_transform is not None:
                img = image_transform(img)
            images.append(img if isinstance(img, torch.Tensor) else torch.tensor(img))
            labels.append(lbl if isinstance(lbl, torch.Tensor) else torch.tensor(lbl))

        return {
            "pixel_values": torch.stack(images, dim=0),
            "labels": torch.stack(labels, dim=0),
        }

    return collate_fn


@COLLATE.register(
    "vl",
    priority=60,
    aliases=["multimodal", "vision_language"],
    description="Build Vision-Language multimodal collate function.",
    tags=["multimodal", "vision_language", "vl"],
)
def build_vl_collate(processor: Any, max_length: int = 2048, **kwargs: Any) -> Callable[..., Dict[str, torch.Tensor]]:
    """Build vision-language multimodal batch collator."""

    def collate_fn(batch: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        images = [b["image"] for b in batch if "image" in b]
        texts = [b["text"] for b in batch if "text" in b]
        if hasattr(processor, "__call__"):
            return processor(images=images, text=texts, return_tensors="pt", padding=True, truncation=True)
        return {}

    return collate_fn


__all__ = [
    "COLLATE",
    "COLLATORS",
    "CollateConfig",
    "build_lm_collate",
    "build_seq_collate",
    "build_packed_lm_collate",
    "build_masked_lm_collate",
    "build_cv_collate",
    "build_vl_collate",
]
