import torch
import torch.nn as nn
from typing import Optional

class DeviceManagement:
    """Device management utilities for models."""
    @staticmethod
    def get_model_device(model: nn.Module) -> torch.device:
        base = model.module if hasattr(model, "module") else model
        if hasattr(base, "parameters"):
            param = next(base.parameters(), None)
            if param is not None: return param.device
        return torch.device("cpu")

    @staticmethod
    def configure_device_settings(allow_tf32: bool = True, matmul_precision: str = "high") -> None:
        if not torch.cuda.is_available(): return
        try:
            if allow_tf32:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.set_float32_matmul_precision(matmul_precision)
            if hasattr(torch.backends.cuda, "sdp_kernel"):
                torch.backends.cuda.sdp_kernel(enable_flash=True, enable_math=False, enable_mem_efficient=True)
        except Exception: pass
