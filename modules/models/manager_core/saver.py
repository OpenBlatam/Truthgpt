import os
import logging
import torch
import torch.nn as nn
from typing import Optional
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)

class ModelSaver:
    """Model saving utilities."""
    @staticmethod
    def save_model(model: torch.nn.Module, path: str, tokenizer: Optional[AutoTokenizer] = None, safe_serialization: bool = True, **kwargs) -> None:
        try:
            os.makedirs(path, exist_ok=True)
            m = model.module if hasattr(model, "module") else model
            m.save_pretrained(path, safe_serialization=safe_serialization, **kwargs)
            if tokenizer: tokenizer.save_pretrained(path)
            logger.info(f"Model saved to {path}")
        except Exception as e:
            logger.error(f"Error saving model to {path}: {e}")
            raise
