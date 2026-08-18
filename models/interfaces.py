"""
Core interfaces, protocols, abstract base classes, and schemas for models.
Provides unified contracts for model wrappers, managers, builders, diffusion pipelines,
and attention modules.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union, runtime_checkable

import torch
import torch.nn as nn

try:
    from pydantic import BaseModel as PydanticBaseModel, Field
    _PYDANTIC_AVAILABLE = True
except ImportError:
    _PYDANTIC_AVAILABLE = False
    class PydanticBaseModel:  # type: ignore
        def __init__(self, **data: Any):
            for k, v in data.items():
                setattr(self, k, v)
        def dict(self) -> Dict[str, Any]:
            return self.__dict__
    def Field(default: Any = None, **kwargs: Any) -> Any:  # type: ignore
        return default


# ---------------------------------------------------------------------------
# Structured Result & Configuration Schemas
# ---------------------------------------------------------------------------

class ModelInfoResult(PydanticBaseModel):
    """Metadata report for a model instance."""
    model_type: str = Field(default="unknown", description="Type identifier of the model")
    model_name: Optional[str] = Field(default=None, description="Name or path of the model")
    device: str = Field(default="cpu", description="Primary device location")
    dtype: Optional[str] = Field(default=None, description="Weight precision dtype")
    num_parameters: int = Field(default=0, description="Total parameter count")
    trainable_parameters: int = Field(default=0, description="Trainable parameter count")
    memory_footprint_mb: float = Field(default=0.0, description="Estimated memory footprint in MB")
    is_compiled: bool = Field(default=False, description="Whether model is torch.compiled")
    is_quantized: bool = Field(default=False, description="Whether model weights are quantized")
    is_peft: bool = Field(default=False, description="Whether LoRA/PEFT adapters are applied")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")


class ModelLoadResult(PydanticBaseModel):
    """Result report after loading a model."""
    success: bool = True
    model_name: str = ""
    model_type: str = ""
    device: str = "cpu"
    dtype: Optional[str] = None
    load_time_seconds: float = 0.0
    is_peft: bool = False
    message: str = "Model loaded successfully"
    extra: Dict[str, Any] = Field(default_factory=dict)


class ModelSaveResult(PydanticBaseModel):
    """Result report after saving a model or checkpoint."""
    success: bool = True
    save_path: str = ""
    saved_tokenizer: bool = False
    saved_peft_adapter: bool = False
    safe_serialization: bool = True
    file_size_bytes: int = 0
    message: str = "Model saved successfully"
    extra: Dict[str, Any] = Field(default_factory=dict)


class ModelInferenceResult(PydanticBaseModel):
    """Structured text inference output."""
    text: str = ""
    prompt: Optional[str] = None
    tokens_generated: int = 0
    latency_seconds: float = 0.0
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GenerationConfig(PydanticBaseModel):
    """Text generation parameters."""
    max_new_tokens: int = Field(default=128, ge=1)
    min_new_tokens: int = Field(default=0, ge=0)
    temperature: float = Field(default=0.7, ge=0.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    top_k: int = Field(default=50, ge=0)
    do_sample: bool = True
    repetition_penalty: float = Field(default=1.0, ge=0.0)
    length_penalty: float = 1.0
    pad_token_id: Optional[int] = None
    eos_token_id: Optional[int] = None
    stop_strings: Optional[List[str]] = None
    use_cache: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_new_tokens": self.max_new_tokens,
            "min_new_tokens": self.min_new_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "do_sample": self.do_sample,
            "repetition_penalty": self.repetition_penalty,
            "length_penalty": self.length_penalty,
            "pad_token_id": self.pad_token_id,
            "eos_token_id": self.eos_token_id,
            "stop_strings": self.stop_strings,
            "use_cache": self.use_cache,
        }


class DiffusionInferenceResult(PydanticBaseModel):
    """Structured output for diffusion image generation."""
    num_images: int = 1
    prompt: str = ""
    negative_prompt: Optional[str] = None
    num_inference_steps: int = 50
    guidance_scale: float = 7.5
    seed: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    latency_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AttentionOptimizationResult(PydanticBaseModel):
    """Result report for attention optimizations applied to a model."""
    backend: str = "torch"
    modules_patched: int = 0
    sdpa_available: bool = True
    flash_attn_available: bool = False
    xformers_available: bool = False
    speedup_estimated: float = 1.0
    message: str = "Attention optimization applied"


# ---------------------------------------------------------------------------
# Protocols (Structural Subtyping)
# ---------------------------------------------------------------------------

@runtime_checkable
class BaseModelProtocol(Protocol):
    """Protocol defining the standard lifecycle of a runnable model."""
    def load(self, cfg: Union[Dict[str, Any], Any]) -> None: ...
    def infer(self, inputs: Union[str, Dict[str, Any], Any]) -> Dict[str, Any]: ...
    def to(self, device: Union[str, torch.device]) -> Any: ...


@runtime_checkable
class BaseModelManagerProtocol(Protocol):
    """Protocol for model manager systems."""
    def load_model(self, model_name: str, **kwargs: Any) -> nn.Module: ...
    def save_model(self, model: nn.Module, path: str, **kwargs: Any) -> None: ...
    def get_model_device(self, model: nn.Module) -> torch.device: ...


@runtime_checkable
class BaseModelBuilderProtocol(Protocol):
    """Protocol for model builders."""
    def with_model_name(self, name: str) -> Any: ...
    def build(self) -> nn.Module: ...


@runtime_checkable
class BaseDiffusionManagerProtocol(Protocol):
    """Protocol for diffusion managers."""
    def load_pipeline(self, model_id: str, **kwargs: Any) -> Any: ...
    def generate(self, prompt: Union[str, List[str]], **kwargs: Any) -> Any: ...


@runtime_checkable
class BaseAttentionModuleProtocol(Protocol):
    """Protocol for attention modules."""
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None, causal: bool = False, **kwargs: Any) -> torch.Tensor: ...


# ---------------------------------------------------------------------------
# Abstract Base Classes (Contract Inheritance)
# ---------------------------------------------------------------------------

class BaseModel(ABC):
    """
    Abstract Base Class for all model implementations in optimization_core.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config: Dict[str, Any] = config or {}
        self.model: Optional[Any] = None
        self.tokenizer: Optional[Any] = None

    @abstractmethod
    def load(self, cfg: Union[Dict[str, Any], Any]) -> None:
        """Load model weights and components from configuration."""
        pass

    @abstractmethod
    def infer(self, inputs: Union[str, Dict[str, Any], Any]) -> Dict[str, Any]:
        """Run inference given input tensors or dictionaries."""
        pass

    def to(self, device: Union[str, torch.device]) -> Any:
        """Move model to target device."""
        if isinstance(device, str):
            dev = torch.device(device)
        else:
            dev = device

        if self.model is not None and hasattr(self.model, "to"):
            self.model.to(dev)
        elif isinstance(self, nn.Module):
            nn.Module.to(self, dev)
        return self

    def to_device(self, device: Optional[Union[str, torch.device]] = None) -> Any:
        """Place model on target device (CUDA, MPS, or CPU)."""
        if device is None:
            if torch.cuda.is_available():
                dev = torch.device("cuda")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                dev = torch.device("mps")
            else:
                dev = torch.device("cpu")
        elif isinstance(device, str):
            dev = torch.device(device)
        else:
            dev = device

        return self.to(dev)

    def eval(self) -> Any:
        """Set model to evaluation mode."""
        if self.model is not None and self.model is not self and hasattr(self.model, "eval"):
            self.model.eval()
        elif isinstance(self, nn.Module):
            nn.Module.eval(self)
        return self

    def train(self, mode: bool = True) -> Any:
        """Set model to training mode."""
        if self.model is not None and self.model is not self and hasattr(self.model, "train"):
            self.model.train(mode)
        elif isinstance(self, nn.Module):
            nn.Module.train(self, mode)
        return self

    def eval_mode(self) -> Any:
        """Set model to evaluation mode (alias)."""
        return self.eval()

    def train_mode(self, mode: bool = True) -> Any:
        """Set model to training mode (alias)."""
        return self.train(mode)

    def count_parameters(self) -> Tuple[int, int]:
        """
        Count total and trainable parameters of the underlying model.
        
        Returns:
            Tuple of (total_parameters, trainable_parameters)
        """
        target = self.model if self.model is not None else (self if isinstance(self, nn.Module) else None)
        if target is None or not hasattr(target, "parameters"):
            return 0, 0
        params = list(target.parameters())
        total = sum(p.numel() for p in params)
        trainable = sum(p.numel() for p in params if p.requires_grad)
        return total, trainable

    def get_info(self) -> Dict[str, Any]:
        """Inspect and return metadata dictionary."""
        total_params, trainable_params = self.count_parameters()
        device_str = "unknown"
        dtype_str = "unknown"

        if self.model is not None and hasattr(self.model, "parameters"):
            params = list(self.model.parameters())
            if params:
                device_str = str(params[0].device)
                dtype_str = str(params[0].dtype)

        return {
            "model_class": self.__class__.__name__,
            "device": device_str,
            "dtype": dtype_str,
            "num_parameters": total_params,
            "trainable_parameters": trainable_params,
            "has_tokenizer": self.tokenizer is not None,
        }


class BaseModelManager(ABC):
    """
    Abstract base class for model lifecycle managers.
    Handles loading, saving, quantization, multi-GPU, compilation, and device placement.
    """

    @abstractmethod
    def load_model(
        self,
        model_name: str,
        torch_dtype: Optional[torch.dtype] = None,
        device_map: Optional[Union[str, Dict[str, Any]]] = None,
        gradient_checkpointing: bool = True,
        lora_config: Optional[Dict[str, Any]] = None,
        trust_remote_code: bool = True,
        **kwargs: Any
    ) -> nn.Module:
        """Load and configure a neural network model."""
        pass

    @abstractmethod
    def save_model(
        self,
        model: nn.Module,
        path: str,
        tokenizer: Optional[Any] = None,
        safe_serialization: bool = True,
        **kwargs: Any
    ) -> None:
        """Save model weights and optional tokenizer to disk."""
        pass

    @abstractmethod
    def get_model_device(self, model: nn.Module) -> torch.device:
        """Get the primary device hosting the model."""
        pass

    @abstractmethod
    def enable_multi_gpu(
        self,
        model: nn.Module,
        device_ids: Optional[List[int]] = None
    ) -> nn.Module:
        """Enable multi-GPU parallelization for the model."""
        pass

    @abstractmethod
    def enable_torch_compile(
        self,
        model: nn.Module,
        mode: str = "default",
        backend: Optional[str] = None
    ) -> nn.Module:
        """Compile model using PyTorch 2.x torch.compile."""
        pass

    @abstractmethod
    def configure_device_settings(
        self,
        allow_tf32: bool = True,
        matmul_precision: str = "high"
    ) -> None:
        """Configure CUDA device runtime settings (TF32, matmul precision)."""
        pass

    def get_total_params(self, model: nn.Module) -> Tuple[int, int]:
        """
        Count total and trainable parameters of the model.
        """
        base = model.module if isinstance(model, nn.DataParallel) else model
        total = sum(p.numel() for p in base.parameters())
        trainable = sum(p.numel() for p in base.parameters() if p.requires_grad)
        return total, trainable

    def get_memory_footprint(self, model: nn.Module) -> int:
        """
        Compute total memory footprint in bytes.
        """
        base = model.module if isinstance(model, nn.DataParallel) else model
        param_bytes = sum(p.numel() * p.element_size() for p in base.parameters())
        buffer_bytes = sum(b.numel() * b.element_size() for b in base.buffers())
        return param_bytes + buffer_bytes


class BaseModelBuilder(ABC):
    """
    Abstract interface for fluent builder constructing models.
    """

    @abstractmethod
    def with_model_name(self, name: str) -> "BaseModelBuilder":
        """Set model name or directory path."""
        pass

    @abstractmethod
    def with_dtype(self, dtype: torch.dtype) -> "BaseModelBuilder":
        """Set torch data type."""
        pass

    @abstractmethod
    def with_device_map(self, device_map: Union[str, Dict[str, Any]]) -> "BaseModelBuilder":
        """Set device mapping strategy."""
        pass

    @abstractmethod
    def with_gradient_checkpointing(self, enabled: bool = True) -> "BaseModelBuilder":
        """Toggle gradient checkpointing."""
        pass

    @abstractmethod
    def with_lora(
        self,
        enabled: bool = True,
        r: int = 16,
        alpha: int = 32,
        dropout: float = 0.05,
        target_modules: Optional[List[str]] = None,
        bias: str = "none"
    ) -> "BaseModelBuilder":
        """Configure LoRA / PEFT fine-tuning."""
        pass

    @abstractmethod
    def with_multi_gpu(self, enabled: bool = True, device_ids: Optional[List[int]] = None) -> "BaseModelBuilder":
        """Toggle multi-GPU execution."""
        pass

    @abstractmethod
    def with_torch_compile(
        self,
        enabled: bool = True,
        mode: str = "default",
        backend: Optional[str] = None
    ) -> "BaseModelBuilder":
        """Toggle PyTorch 2.x compile."""
        pass

    @abstractmethod
    def build(self) -> nn.Module:
        """Construct, configure, and return the fully initialized model."""
        pass


class BaseDiffusionManager(ABC):
    """
    Abstract base class for diffusion model managers.
    """

    @abstractmethod
    def load_pipeline(
        self,
        model_id: str,
        pipeline_type: str = "stable-diffusion",
        variant: Optional[str] = None,
        torch_dtype: Optional[Union[str, torch.dtype]] = None,
        device: Optional[Union[str, torch.device]] = None,
        scheduler_type: Optional[str] = None,
        enable_attention_slicing: bool = True,
        enable_vae_slicing: bool = True,
        enable_vae_tiling: bool = False,
        **kwargs: Any
    ) -> Any:
        """Load and configure diffusion pipeline."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: Union[str, List[str]],
        negative_prompt: Optional[Union[str, List[str]]] = None,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        height: Optional[int] = None,
        width: Optional[int] = None,
        num_images_per_prompt: int = 1,
        seed: Optional[int] = None,
        **kwargs: Any
    ) -> Any:
        """Generate image(s) from prompt(s)."""
        pass

    @abstractmethod
    def enable_xformers(self) -> None:
        """Enable xFormers memory efficient attention."""
        pass

    @abstractmethod
    def enable_model_cpu_offload(self) -> None:
        """Enable model CPU offload for memory saving."""
        pass

    @abstractmethod
    def enable_sequential_cpu_offload(self) -> None:
        """Enable sequential CPU offload."""
        pass


class BaseAttentionModule(nn.Module, ABC):
    """
    Abstract base class for attention modules.
    """

    @abstractmethod
    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        causal: bool = False,
        **kwargs: Any
    ) -> torch.Tensor:
        """Execute forward attention pass."""
        pass


class BaseAttentionOptimizer(ABC):
    """
    Abstract interface for attention kernel optimization and swapping.
    """

    @abstractmethod
    def optimize_model(self, model: nn.Module, **kwargs: Any) -> AttentionOptimizationResult:
        """Apply attention optimizations to a model."""
        pass


# Type aliases for consistency
IModel = BaseModel
IModelManager = BaseModelManager
IModelBuilder = BaseModelBuilder
IDiffusionManager = BaseDiffusionManager
IAttentionModule = BaseAttentionModule
IAttentionOptimizer = BaseAttentionOptimizer

__all__ = [
    # Result & config schemas
    "ModelInfoResult",
    "ModelLoadResult",
    "ModelSaveResult",
    "ModelInferenceResult",
    "GenerationConfig",
    "DiffusionInferenceResult",
    "AttentionOptimizationResult",
    # Protocols & ABCs
    "BaseModelProtocol",
    "BaseModelManagerProtocol",
    "BaseModelBuilderProtocol",
    "BaseDiffusionManagerProtocol",
    "BaseAttentionModuleProtocol",
    "BaseModel",
    "BaseModelManager",
    "BaseModelBuilder",
    "BaseDiffusionManager",
    "BaseAttentionModule",
    "BaseAttentionOptimizer",
    # Aliases
    "IModel",
    "IModelManager",
    "IModelBuilder",
    "IDiffusionManager",
    "IAttentionModule",
    "IAttentionOptimizer",
]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.models."):
        sys.modules["models." + __name__[len("optimization_core.models."):]] = _mod
    elif __name__.startswith("models."):
        sys.modules["optimization_core.models." + __name__[len("models."):]] = _mod
