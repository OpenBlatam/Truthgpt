from dataclasses import dataclass, field
from typing import Optional, List, Union, Dict, Any
import numpy as np
from .backend import Backend, get_best_backend, is_backend_available

from .constants import *

class TokenizerConfig:
    """
    Configuration for tokenizer.
    
    Attributes:
        model_name: Model name or path
        max_length: Maximum sequence length
        padding: Whether to pad sequences
        truncation: Whether to truncate sequences
        return_tensors: Tensor type to return (np, pt, tf)
        add_special_tokens: Whether to add special tokens
    """
    model_name: str = DEFAULT_MODEL_NAME
    max_length: int = DEFAULT_MAX_LENGTH
    padding: bool = True
    truncation: bool = True
    return_tensors: str = TENSOR_TYPE_NUMPY
    add_special_tokens: bool = True
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if not self.model_name:
            raise ValueError("model_name cannot be empty")
        if self.max_length <= 0:
            raise ValueError(f"max_length must be positive, got {self.max_length}")
        valid_tensor_types = [TENSOR_TYPE_NUMPY, TENSOR_TYPE_PYTORCH, TENSOR_TYPE_TENSORFLOW]
        if self.return_tensors not in valid_tensor_types:
            raise ValueError(
                f"return_tensors must be one of {valid_tensor_types}, "
                f"got {self.return_tensors}"
            )

