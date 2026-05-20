"""
Model adapters for abstracting model loading/saving implementations.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import torch

logger = logging.getLogger(__name__)


class ModelAdapter(ABC):
    """Base adapter for model operations."""
    
    @abstractmethod
    def load_model(self, model_path: str, **kwargs) -> torch.nn.Module:
        """Load a model."""
        pass
    
    @abstractmethod
    def save_model(self, model: torch.nn.Module, path: str, **kwargs) -> None:
        """Save a model."""
        pass
    
    @abstractmethod
    def get_model_info(self, model: torch.nn.Module) -> Dict[str, Any]:
        """Get model information."""
        pass


class HuggingFaceModelAdapter(ModelAdapter):
    """Adapter for HuggingFace models."""
    
    def load_model(self, model_path: str, **kwargs) -> torch.nn.Module:
        """Load HuggingFace model."""
        from transformers import AutoModelForCausalLM
        
        return AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=kwargs.get("torch_dtype"),
            device_map=kwargs.get("device_map"),
            trust_remote_code=kwargs.get("trust_remote_code", True),
        )
    
    def save_model(self, model: torch.nn.Module, path: str, **kwargs) -> None:
        """Save HuggingFace model."""
        model_to_save = model
        if hasattr(model, "module"):
            model_to_save = model.module
        
        model_to_save.save_pretrained(
            path,
            safe_serialization=kwargs.get("safe_serialization", True),
        )
    
    def get_model_info(self, model: torch.nn.Module) -> Dict[str, Any]:
        """Get model information."""
        base_model = model.module if hasattr(model, "module") else model
        
        info = {
            "num_parameters": sum(p.numel() for p in model.parameters()),
            "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
        }
        
        if hasattr(base_model, "config"):
            info["model_type"] = getattr(base_model.config, "model_type", "unknown")
            info["vocab_size"] = getattr(base_model.config, "vocab_size", 0)
        
        return info


