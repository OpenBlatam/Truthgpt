"""
Model optimization component supporting multi-GPU DataParallel and torch.compile.
"""

import logging
import torch
import torch.nn as nn
from typing import Optional, List

logger = logging.getLogger(__name__)


class ModelOptimizations:
    """Handles runtime performance optimizations for PyTorch models."""

    @staticmethod
    def enable_multi_gpu(
        model: nn.Module,
        device_ids: Optional[List[int]] = None
    ) -> nn.Module:
        """
        Wrap model with DataParallel for multi-GPU training/inference.

        Args:
            model: PyTorch model.
            device_ids: Optional list of GPU IDs to use.

        Returns:
            DataParallel wrapped model or original model if single/no GPU.
        """
        if torch.cuda.is_available() and torch.cuda.device_count() > 1:
            logger.info(f"Using DataParallel across {torch.cuda.device_count()} GPUs")
            return nn.DataParallel(model, device_ids=device_ids)
        else:
            logger.debug("DataParallel skipped (single GPU or CPU environment)")
            return model

    @staticmethod
    def enable_torch_compile(
        model: nn.Module,
        mode: str = "default"
    ) -> nn.Module:
        """
        Compile model using PyTorch 2.0+ torch.compile.

        Args:
            model: PyTorch model.
            mode: Compilation mode ('default', 'reduce-overhead', 'max-autotune').

        Returns:
            Compiled model or original model if unsupported.
        """
        if hasattr(torch, "compile"):
            try:
                logger.info(f"Compiling model with torch.compile (mode='{mode}')")
                return torch.compile(model, mode=mode)
            except Exception as e:
                logger.warning(f"torch.compile failed: {e}. Falling back to uncompiled model.")
                return model
        else:
            logger.warning("torch.compile is not available in this PyTorch version.")
            return model
