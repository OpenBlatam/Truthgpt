"""
Model saver component supporting standard checkpoints, safetensors, tokenizers, and metadata.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class ModelSaver:
    """Handles serialization and persistence of models, weights, tokenizers, and metadata."""

    @staticmethod
    def save_model(
        model: nn.Module,
        path: str,
        tokenizer: Optional[Any] = None,
        safe_serialization: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Save a model and optional tokenizer and metadata to the specified path.

        Args:
            model: PyTorch model instance.
            path: Target directory path or file path.
            tokenizer: Optional HuggingFace tokenizer instance.
            safe_serialization: Whether to use SafeTensors format if supported.
            metadata: Optional metadata dictionary to serialize into model_metadata.json.
            **kwargs: Additional keyword arguments passed to save_pretrained.
        """
        try:
            # Check if path is directory or file
            if path.endswith(".pt") or path.endswith(".bin") or path.endswith(".safetensors"):
                target_dir = os.path.dirname(path) or "."
                target_file = path
            else:
                target_dir = path
                target_file = os.path.join(path, "model.pt")

            os.makedirs(target_dir, exist_ok=True)

            model_to_save = model
            if isinstance(model, nn.DataParallel):
                model_to_save = model.module
            elif hasattr(model, "module"):
                model_to_save = model.module

            # Try HuggingFace save_pretrained if target is directory and model supports it
            saved_hf = False
            if target_dir == path and hasattr(model_to_save, "save_pretrained") and not path.endswith(".pt"):
                try:
                    model_to_save.save_pretrained(
                        target_dir,
                        safe_serialization=safe_serialization,
                        **kwargs,
                    )
                    saved_hf = True
                except Exception as e:
                    logger.debug(f"save_pretrained failed ({e}), falling back to standard torch.save")

            if not saved_hf:
                torch.save(model_to_save.state_dict(), target_file)
                # Also create pytorch_model.bin if directory
                if target_dir == path:
                    bin_path = os.path.join(target_dir, "pytorch_model.bin")
                    if not os.path.exists(bin_path):
                        torch.save(model_to_save.state_dict(), bin_path)

            if tokenizer and hasattr(tokenizer, "save_pretrained"):
                tokenizer.save_pretrained(target_dir)

            if metadata:
                meta_path = os.path.join(target_dir, "model_metadata.json")
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2, default=str)

            logger.info(f"Model saved successfully to '{path}'")

        except Exception as e:
            logger.error(f"Error saving model to '{path}': {e}", exc_info=True)
            raise
