import torch
import torch.nn as nn
from transformers import AutoTokenizer
from typing import Optional, Dict, Any

from optimization_core.core.interfaces import BaseModelManager
from .loader import ModelLoader
from .saver import ModelSaver
from .base import DeviceManagement
from .optimizations import ModelOptimizations

class ModelManager(BaseModelManager):
    """Manages model loading, saving, and configuration."""
    def load_model(self, model_name: str, torch_dtype: Optional[torch.dtype] = None, device_map: Optional[str] = None, gradient_checkpointing: bool = True, lora_config: Optional[Dict[str, Any]] = None, trust_remote_code: bool = True) -> torch.nn.Module:
        return ModelLoader.load_model(model_name, torch_dtype, device_map, gradient_checkpointing, lora_config, trust_remote_code)

    def save_model(self, model: torch.nn.Module, path: str, tokenizer: Optional[AutoTokenizer] = None, safe_serialization: bool = True, **kwargs) -> None:
        ModelSaver.save_model(model, path, tokenizer, safe_serialization, **kwargs)

    def get_model_device(self, model: torch.nn.Module) -> torch.device:
        return DeviceManagement.get_model_device(model)

    def enable_multi_gpu(self, model: torch.nn.Module, device_ids: Optional[list] = None) -> torch.nn.Module:
        return ModelOptimizations.enable_multi_gpu(model, device_ids)

    def enable_torch_compile(self, model: torch.nn.Module, mode: str = "default") -> torch.nn.Module:
        return ModelOptimizations.enable_torch_compile(model, mode)

    def configure_device_settings(self, allow_tf32: bool = True, matmul_precision: str = "high") -> None:
        DeviceManagement.configure_device_settings(allow_tf32, matmul_precision)
