"""
ModelManager implementation composing modular subcomponents.
"""

from typing import Optional, Dict, Any, List
import logging
import torch
import torch.nn as nn

try:
    from ..interfaces import BaseModelManager
except (ImportError, ValueError):
    try:
        from optimization_core.models.interfaces import BaseModelManager
    except (ImportError, ValueError):
        from abc import ABC, abstractmethod

        class BaseModelManager(ABC):  # type: ignore
            """Fallback abstract base model manager."""
            @abstractmethod
            def load_model(self, model_name: str, **kwargs: Any) -> Any:
                pass

            @abstractmethod
            def save_model(self, model: Any, path: str, **kwargs: Any) -> None:
                pass

from .loader import ModelLoader
from .saver import ModelSaver
from .base import DeviceManagement
from .optimizations import ModelOptimizations

logger = logging.getLogger(__name__)


class ModelManager(BaseModelManager):
    """
    Unified manager for model lifecycle: loading, configuration,
    device placement, multi-GPU optimization, compilation, and persistence.
    """

    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs

    def load_model(
        self,
        model_name: str,
        torch_dtype: Optional[torch.dtype] = None,
        device_map: Optional[str] = None,
        gradient_checkpointing: bool = True,
        lora_config: Optional[Dict[str, Any]] = None,
        trust_remote_code: bool = True,
        **kwargs: Any
    ) -> nn.Module:
        """Load a model using the modular loader."""
        return ModelLoader.load_model(
            model_name=model_name,
            torch_dtype=torch_dtype,
            device_map=device_map,
            gradient_checkpointing=gradient_checkpointing,
            lora_config=lora_config,
            trust_remote_code=trust_remote_code,
        )

    def save_model(
        self,
        model: nn.Module,
        path: str,
        tokenizer: Optional[Any] = None,
        safe_serialization: bool = True,
        **kwargs: Any
    ) -> None:
        """Save a model using the modular saver."""
        ModelSaver.save_model(
            model=model,
            path=path,
            tokenizer=tokenizer,
            safe_serialization=safe_serialization,
            **kwargs
        )

    def get_model_device(self, model: nn.Module) -> torch.device:
        """Get device where model is located."""
        return DeviceManagement.get_model_device(model)

    def enable_multi_gpu(
        self,
        model: nn.Module,
        device_ids: Optional[List[int]] = None
    ) -> nn.Module:
        """Enable multi-GPU parallelization."""
        return ModelOptimizations.enable_multi_gpu(model, device_ids=device_ids)

    def enable_torch_compile(
        self,
        model: nn.Module,
        mode: str = "default",
        backend: Optional[str] = None
    ) -> nn.Module:
        """Enable PyTorch 2.0+ compilation."""
        return ModelOptimizations.enable_torch_compile(model, mode=mode)

    def configure_device_settings(
        self,
        allow_tf32: bool = True,
        matmul_precision: str = "high"
    ) -> None:
        """Configure CUDA acceleration options."""
        DeviceManagement.configure_device_settings(
            allow_tf32=allow_tf32,
            matmul_precision=matmul_precision
        )


__all__ = ["ModelManager"]
