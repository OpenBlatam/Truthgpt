"""
Model Builder Module
====================
Fluent builder pattern for assembling, configuring, optimizing, and compiling models.
Supports quantization, LoRA/PEFT, multi-GPU, torch.compile, SDPA/FlashAttention, and device tuning.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn

from .exceptions import ModelConfigurationError, ModelLoadError
from .interfaces import BaseModelBuilder, BaseModelManager
from .registry import register_model

logger = logging.getLogger(__name__)


@register_model("builder", aliases=["model_builder", "model-builder"])
class ModelBuilder(BaseModelBuilder):
    """
    Fluent builder for configuring and instantiating deep learning models.
    """

    def __init__(self, manager: Optional[BaseModelManager] = None) -> None:
        if manager is not None:
            self._manager = manager
        else:
            from .model_manager import ModelManager
            self._manager = ModelManager()

        self._model_name: Optional[str] = None
        self._model_class: Optional[str] = None
        self._torch_dtype: Optional[torch.dtype] = None
        self._device: Optional[Union[str, torch.device]] = None
        self._device_map: Optional[Union[str, Dict[str, Any]]] = None
        self._gradient_checkpointing: bool = True
        self._gradient_checkpointing_kwargs: Dict[str, Any] = {"use_reentrant": False}
        self._lora_config: Optional[Dict[str, Any]] = None
        self._quantization_config: Optional[Dict[str, Any]] = None
        self._attn_implementation: Optional[str] = None
        self._trust_remote_code: bool = True
        self._multi_gpu: bool = False
        self._device_ids: Optional[List[int]] = None
        self._torch_compile: bool = False
        self._compile_mode: str = "default"
        self._compile_dynamic: bool = False
        self._compile_fullgraph: bool = False
        self._compile_backend: Optional[str] = None
        self._device_settings: Dict[str, Any] = {}
        self._truthgpt_config: Optional[Any] = None
        self._custom_config: Dict[str, Any] = {}

    def with_model_name(self, name: str) -> "ModelBuilder":
        """Set model identifier or local path."""
        self._model_name = name
        return self

    def with_model_class(self, model_class: str) -> "ModelBuilder":
        """Set model architecture class (e.g., 'causal_lm', 'seq2seq', 'auto')."""
        self._model_class = model_class
        return self

    def with_dtype(self, dtype: Union[str, torch.dtype]) -> "ModelBuilder":
        """Set model weight precision."""
        if isinstance(dtype, str):
            dtype_map = {
                "float32": torch.float32,
                "fp32": torch.float32,
                "float16": torch.float16,
                "fp16": torch.float16,
                "bfloat16": torch.bfloat16,
                "bf16": torch.bfloat16,
                "int8": torch.int8,
            }
            resolved = dtype_map.get(dtype.lower())
            if resolved is None:
                raise ModelConfigurationError(f"Unsupported dtype string: '{dtype}'")
            self._torch_dtype = resolved
        else:
            self._torch_dtype = dtype
        return self

    def with_device(self, device: Union[str, torch.device]) -> "ModelBuilder":
        """Set primary execution device."""
        self._device = device
        return self

    def with_device_map(self, device_map: Union[str, Dict[str, Any]]) -> "ModelBuilder":
        """Set device mapping strategy (e.g. 'auto', 'balanced', or custom dict)."""
        self._device_map = device_map
        return self

    def with_gradient_checkpointing(
        self,
        enabled: bool = True,
        use_reentrant: bool = False,
    ) -> "ModelBuilder":
        """Enable or disable gradient checkpointing for memory efficiency."""
        self._gradient_checkpointing = enabled
        self._gradient_checkpointing_kwargs = {"use_reentrant": use_reentrant}
        return self

    def with_lora(
        self,
        enabled: bool = True,
        r: int = 16,
        alpha: int = 32,
        dropout: float = 0.05,
        target_modules: Optional[List[str]] = None,
        bias: str = "none",
        task_type: str = "CAUSAL_LM",
    ) -> "ModelBuilder":
        """Configure Low-Rank Adaptation (LoRA / PEFT)."""
        self._lora_config = {
            "enabled": enabled,
            "r": r,
            "alpha": alpha,
            "dropout": dropout,
            "target_modules": target_modules or ["c_attn", "c_proj", "q_proj", "v_proj", "k_proj", "o_proj"],
            "bias": bias,
            "task_type": task_type,
        }
        return self

    def with_quantization(
        self,
        bits: Optional[Union[int, str]] = 4,
        quant_type: str = "nf4",
        double_quant: bool = True,
        compute_dtype: Optional[torch.dtype] = None,
    ) -> "ModelBuilder":
        """Configure BitsAndBytes quantization (4-bit or 8-bit)."""
        if isinstance(bits, str):
            bit_count = 4 if "4" in bits else 8
        else:
            bit_count = bits or 4
        self._quantization_config = {
            "bits": bit_count,
            "quant_type": quant_type,
            "double_quant": double_quant,
            "compute_dtype": compute_dtype or torch.float16,
        }
        return self

    def with_attn_implementation(self, attn_implementation: str) -> "ModelBuilder":
        """Configure attention backend ('flash_attention_2', 'sdpa', 'eager')."""
        self._attn_implementation = attn_implementation
        return self

    def with_trust_remote_code(self, trust: bool = True) -> "ModelBuilder":
        """Set whether to trust remote code from HuggingFace."""
        self._trust_remote_code = trust
        return self

    def with_multi_gpu(
        self,
        enabled: bool = True,
        device_ids: Optional[List[int]] = None,
    ) -> "ModelBuilder":
        """Enable DataParallel multi-GPU support."""
        self._multi_gpu = enabled
        self._device_ids = device_ids
        return self

    def with_torch_compile(
        self,
        enabled: bool = True,
        mode: str = "default",
        dynamic: bool = False,
        fullgraph: bool = False,
        backend: Optional[str] = None,
    ) -> "ModelBuilder":
        """Enable PyTorch 2.0+ torch.compile optimization."""
        self._torch_compile = enabled
        self._compile_mode = mode
        self._compile_dynamic = dynamic
        self._compile_fullgraph = fullgraph
        self._compile_backend = backend
        return self

    def with_device_settings(
        self,
        allow_tf32: bool = True,
        matmul_precision: str = "high",
    ) -> "ModelBuilder":
        """Configure CUDA hardware performance settings (TF32, matmul precision)."""
        self._device_settings = {
            "allow_tf32": allow_tf32,
            "matmul_precision": matmul_precision,
        }
        return self

    def with_truthgpt_config(self, config: Any) -> "ModelBuilder":
        """Configure native TruthGPT transformer architecture."""
        self._truthgpt_config = config
        return self

    def with_config(self, config: Dict[str, Any]) -> "ModelBuilder":
        """Apply a comprehensive configuration dictionary to the builder."""
        if not config:
            return self

        if "model_name" in config:
            self.with_model_name(config["model_name"])
        elif "name_or_path" in config:
            self.with_model_name(config["name_or_path"])
        elif "name" in config:
            self.with_model_name(config["name"])

        if "truthgpt_config" in config:
            self.with_truthgpt_config(config["truthgpt_config"])

        if "dtype" in config:
            self.with_dtype(config["dtype"])

        if "device_map" in config:
            self.with_device_map(config["device_map"])
        elif "device" in config:
            self.with_device(config["device"])

        if "gradient_checkpointing" in config:
            self.with_gradient_checkpointing(bool(config["gradient_checkpointing"]))

        if "lora" in config:
            lora_cfg = config["lora"]
            if isinstance(lora_cfg, dict):
                self.with_lora(**lora_cfg)
            elif isinstance(lora_cfg, bool):
                self.with_lora(enabled=lora_cfg)

        if "quantization" in config:
            q_cfg = config["quantization"]
            if isinstance(q_cfg, dict):
                self.with_quantization(**q_cfg)
            elif isinstance(q_cfg, (int, str)):
                self.with_quantization(bits=q_cfg)

        if "attn_implementation" in config:
            self.with_attn_implementation(config["attn_implementation"])

        if "torch_compile" in config:
            tc = config["torch_compile"]
            if isinstance(tc, dict):
                self.with_torch_compile(**tc)
            else:
                self.with_torch_compile(enabled=bool(tc))

        if "multi_gpu" in config:
            self.with_multi_gpu(enabled=bool(config["multi_gpu"]))

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Export current builder configuration."""
        return {
            "model_name": self._model_name,
            "model_class": self._model_class,
            "torch_dtype": str(self._torch_dtype) if self._torch_dtype else None,
            "device": str(self._device) if self._device else None,
            "device_map": self._device_map,
            "gradient_checkpointing": self._gradient_checkpointing,
            "lora_config": self._lora_config,
            "quantization_config": self._quantization_config,
            "attn_implementation": self._attn_implementation,
            "trust_remote_code": self._trust_remote_code,
            "multi_gpu": self._multi_gpu,
            "torch_compile": self._torch_compile,
            "compile_mode": self._compile_mode,
            "device_settings": self._device_settings,
        }

    def build(self) -> nn.Module:
        """
        Build and optimize the configured model.

        Returns:
            Instantiated and configured PyTorch Module.
        """
        if not self._model_name and self._truthgpt_config is None:
            raise ModelConfigurationError("Either model_name or truthgpt_config must be configured before calling build()")

        # Apply device hardware settings
        if self._device_settings and hasattr(self._manager, "configure_device_settings"):
            self._manager.configure_device_settings(**self._device_settings)

        # Build native TruthGPT model if configured
        if self._truthgpt_config is not None:
            from .models import create_truthgpt_model
            model = create_truthgpt_model(self._truthgpt_config)
        else:
            # Delegate model load to ModelManager
            model = self._manager.load_model(
                model_name=self._model_name,
                model_class=self._model_class,
                torch_dtype=self._torch_dtype,
                device_map=self._device_map,
                gradient_checkpointing=self._gradient_checkpointing,
                gradient_checkpointing_kwargs=self._gradient_checkpointing_kwargs,
                lora_config=self._lora_config,
                quantization_config=self._quantization_config,
                attn_implementation=self._attn_implementation,
                trust_remote_code=self._trust_remote_code,
            )

        # Move to explicit device if configured and not device_mapped
        if self._device and self._device_map is None:
            if hasattr(model, "to"):
                model.to(self._device)

        # Multi-GPU DataParallel
        if self._multi_gpu and hasattr(self._manager, "enable_multi_gpu"):
            model = self._manager.enable_multi_gpu(model, device_ids=self._device_ids)

        # Torch Compile
        if self._torch_compile and hasattr(self._manager, "enable_torch_compile"):
            model = self._manager.enable_torch_compile(
                model,
                mode=self._compile_mode,
                dynamic=self._compile_dynamic,
                fullgraph=self._compile_fullgraph,
                backend=self._compile_backend,
            )

        return model

    def build_with_tokenizer(self) -> Tuple[nn.Module, Any]:
        """
        Build model and instantiate its corresponding AutoTokenizer.

        Returns:
            Tuple of (model, tokenizer).
        """
        model = self.build()
        tokenizer = None
        if hasattr(self._manager, "load_tokenizer") and self._model_name:
            tokenizer = self._manager.load_tokenizer(
                self._model_name,
                trust_remote_code=self._trust_remote_code,
            )
        return model, tokenizer


def create_model_builder(config: Optional[Dict[str, Any]] = None) -> ModelBuilder:
    """Factory helper to create a ModelBuilder instance."""
    builder = ModelBuilder()
    if config:
        builder.with_config(config)
    return builder


__all__ = [
    "ModelBuilder",
    "create_model_builder",
]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.models."):
        sys.modules["models." + __name__[len("optimization_core.models."):]] = _mod
    elif __name__.startswith("models."):
        sys.modules["optimization_core.models." + __name__[len("models."):]] = _mod
