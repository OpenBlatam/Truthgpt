import logging
import torch
import torch.nn as nn
from typing import Optional

logger = logging.getLogger(__name__)

class ModelOptimizations:
    """Model optimization utilities (Parallelism, Compilation)."""
    @staticmethod
    def enable_multi_gpu(model: nn.Module, device_ids: Optional[list] = None) -> nn.Module:
        if torch.cuda.device_count() > 1:
            logger.info(f"Using DataParallel with {torch.cuda.device_count()} GPUs")
            return nn.DataParallel(model, device_ids=device_ids)
        return model

    @staticmethod
    def enable_torch_compile(model: nn.Module, mode: str = "default") -> nn.Module:
        if hasattr(torch, "compile"):
            try: return torch.compile(model, mode=mode)
            except Exception as e: logger.warning(f"Failed to compile: {e}")
        return model
