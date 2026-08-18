"""
Base device and hardware management utilities.
"""

import logging
import torch
from typing import Optional

logger = logging.getLogger(__name__)


class DeviceManagement:
    """Handles device mapping, GPU discovery, and CUDA configurations."""

    @staticmethod
    def get_model_device(model: torch.nn.Module) -> torch.device:
        """
        Get device where model is located.

        Args:
            model: Model instance

        Returns:
            torch.device where the model parameters reside
        """
        base_model = model
        if isinstance(model, torch.nn.DataParallel):
            base_model = model.module
        elif hasattr(model, "module"):
            base_model = model.module

        if hasattr(base_model, "parameters"):
            param = next(base_model.parameters(), None)
            if param is not None:
                return param.device

        return torch.device("cpu")

    @staticmethod
    def configure_device_settings(
        allow_tf32: bool = True,
        matmul_precision: str = "high"
    ) -> None:
        """
        Configure CUDA device settings for optimal performance.

        Args:
            allow_tf32: Enable TF32 for Ampere+ GPUs
            matmul_precision: Matrix multiplication precision ('highest', 'high', 'medium')
        """
        if not torch.cuda.is_available():
            return

        try:
            if allow_tf32:
                torch.backends.cuda.matmul.allow_tf32 = True
                if hasattr(torch, "set_float32_matmul_precision"):
                    torch.set_float32_matmul_precision(matmul_precision)
                logger.debug("TF32 matrix multiplication enabled")

            if hasattr(torch.backends.cuda, "sdp_kernel"):
                torch.backends.cuda.sdp_kernel(
                    enable_flash=True,
                    enable_math=False,
                    enable_mem_efficient=True
                )
                logger.debug("SDPA kernels configured")
        except Exception as e:
            logger.warning(f"Failed to configure device settings: {e}")
