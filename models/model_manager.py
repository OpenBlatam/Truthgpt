"""
Model Management Module
=======================
Manages model loading, saving, quantization, LoRA configuration, compilation,
device placement, parameter statistics, and tokenizer management with high-performance defaults.
"""

from __future__ import annotations

import gc
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn

from .exceptions import (
    DevicePlacementError,
    ModelInitializationError,
    ModelLoadError,
    ModelOptimizationError,
    ModelSaveError,
    ModelConfigurationError,
    QuantizationError,
)
from .interfaces import BaseModelManager
from .registry import register_model

logger = logging.getLogger(__name__)

# Lazy detection of optional libraries
try:
    from peft import LoraConfig, get_peft_model, PeftModel
    _PEFT_AVAILABLE = True
except ImportError:
    _PEFT_AVAILABLE = False
    LoraConfig = None
    get_peft_model = None
    PeftModel = None

try:
    from transformers import (
        AutoConfig,
        AutoModel,
        AutoModelForCausalLM,
        AutoModelForSeq2SeqLM,
        AutoTokenizer,
        BitsAndBytesConfig,
    )
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    AutoConfig = None
    AutoModel = None
    AutoModelForCausalLM = None
    AutoModelForSeq2SeqLM = None
    AutoTokenizer = None
    BitsAndBytesConfig = None


@register_model("manager", aliases=["model_manager", "model-manager"])
class ModelManager(BaseModelManager):
    """
    Enterprise-grade model management for loading, configuring, saving, and optimizing models.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, default_device: Optional[Union[str, torch.device]] = None) -> None:
        self.config = config or {}
        if default_device is not None:
            self.default_device = torch.device(default_device) if isinstance(default_device, str) else default_device
        else:
            self.default_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._loaded_models: Dict[str, nn.Module] = {}
        self._loaded_tokenizers: Dict[str, Any] = {}

    def load_model(
        self,
        model_name: str,
        model_class: Optional[str] = None,
        torch_dtype: Optional[Union[str, torch.dtype]] = None,
        device_map: Optional[Union[str, Dict[str, Any]]] = None,
        gradient_checkpointing: bool = True,
        gradient_checkpointing_kwargs: Optional[Dict[str, Any]] = None,
        lora_config: Optional[Dict[str, Any]] = None,
        quantization_config: Optional[Dict[str, Any]] = None,
        quantization: Optional[Any] = None,
        attn_implementation: Optional[str] = None,
        flash_attention: bool = False,
        trust_remote_code: bool = True,
        **kwargs: Any,
    ) -> nn.Module:
        """
        Load a pretrained or custom model with optimization features.
        """
        if not model_name or not isinstance(model_name, str):
            raise ModelConfigurationError("model_name must be a non-empty string", model_name=str(model_name))

        if not _TRANSFORMERS_AVAILABLE:
            raise ModelLoadError(
                "transformers package is required to load pretrained models",
                model_name=model_name,
            )

        try:
            logger.info(f"Loading model: '{model_name}' (dtype={torch_dtype}, device_map={device_map})")

            # Resolve dtype
            resolved_dtype = self._resolve_dtype(torch_dtype)

            # Build from_pretrained kwargs
            load_kwargs: Dict[str, Any] = {
                "trust_remote_code": trust_remote_code,
                **kwargs,
            }

            if resolved_dtype is not None:
                load_kwargs["torch_dtype"] = resolved_dtype

            if device_map is not None:
                load_kwargs["device_map"] = device_map

            if flash_attention:
                attn_implementation = "flash_attention_2"

            if attn_implementation is not None:
                load_kwargs["attn_implementation"] = attn_implementation

            # Quantization configuration
            q_cfg = quantization_config
            if q_cfg is None and quantization is not None:
                q_cfg = {"bits": 4 if "4" in str(quantization) else 8}

            if q_cfg:
                bnb_config = self._build_quantization_config(q_cfg)
                if bnb_config is not None:
                    load_kwargs["quantization_config"] = bnb_config

            # Select model loader class
            loader_cls = self._select_model_class(model_class)

            # Instantiate model
            model = loader_cls.from_pretrained(model_name, **load_kwargs)

            # Enable gradient checkpointing
            if gradient_checkpointing:
                self._enable_gradient_checkpointing(model, gradient_checkpointing_kwargs)

            # Disable KV cache during training mode if applicable
            if hasattr(model, "config") and hasattr(model.config, "use_cache"):
                if lora_config and lora_config.get("enabled", False):
                    try:
                        model.config.use_cache = False
                    except Exception:
                        pass

            # Apply LoRA / PEFT if configured
            if lora_config and lora_config.get("enabled", False):
                model = self._apply_lora(model, lora_config, model_name=model_name)

            self._loaded_models[model_name] = model
            logger.info(f"Model '{model_name}' loaded successfully")
            return model

        except Exception as e:
            if isinstance(e, (ModelLoadError, ModelOptimizationError, QuantizationError, ModelConfigurationError)):
                raise
            logger.error(f"Error loading model '{model_name}': {e}", exc_info=True)
            raise ModelLoadError(
                f"Failed to load model '{model_name}': {e}",
                model_name=model_name,
                details={"cause": str(e)},
                original_exception=e,
            ) from e

    def load_tokenizer(
        self,
        model_name: str,
        trust_remote_code: bool = True,
        pad_token_to_eos: bool = True,
        **kwargs: Any,
    ) -> Any:
        """
        Load AutoTokenizer for the given model with sensible fallbacks.
        """
        if not _TRANSFORMERS_AVAILABLE:
            raise ModelLoadError("transformers package is required for tokenization", model_name=model_name)

        try:
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=trust_remote_code,
                **kwargs,
            )
            if pad_token_to_eos and tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token or "<|pad|>"

            self._loaded_tokenizers[model_name] = tokenizer
            return tokenizer
        except Exception as e:
            logger.error(f"Error loading tokenizer for '{model_name}': {e}", exc_info=True)
            raise ModelLoadError(f"Failed to load tokenizer: {e}", model_name=model_name, original_exception=e) from e

    def save_model(
        self,
        model: nn.Module,
        path: str,
        tokenizer: Optional[Any] = None,
        safe_serialization: bool = True,
        save_peft_adapters: bool = True,
        merge_and_unload_lora: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Save model weights, LoRA adapters, tokenizer, and metadata to disk.
        """
        try:
            os.makedirs(path, exist_ok=True)

            # Unwrap DataParallel if present
            model_to_save = model
            if isinstance(model, nn.DataParallel):
                model_to_save = model.module
            elif hasattr(model, "module"):
                model_to_save = model.module

            # Merge LoRA if requested
            if merge_and_unload_lora and _PEFT_AVAILABLE and isinstance(model_to_save, PeftModel):
                logger.info("Merging LoRA adapter into base model before saving")
                model_to_save = model_to_save.merge_and_unload()

            # Save model
            if hasattr(model_to_save, "save_pretrained"):
                model_to_save.save_pretrained(
                    path,
                    safe_serialization=safe_serialization,
                    **kwargs,
                )
            else:
                state_dict = model_to_save.state_dict()
                torch.save(state_dict, os.path.join(path, "model.pt"))
                torch.save(state_dict, os.path.join(path, "pytorch_model.bin"))

            # Save tokenizer if provided
            if tokenizer is not None and hasattr(tokenizer, "save_pretrained"):
                tokenizer.save_pretrained(path)

            # Save metadata if provided
            if metadata is not None:
                meta_path = os.path.join(path, "model_metadata.json")
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2)

            logger.info(f"Model successfully saved to '{path}'")

        except Exception as e:
            logger.error(f"Error saving model to '{path}': {e}", exc_info=True)
            raise ModelSaveError(f"Failed to save model: {e}", path=path, original_exception=e) from e

    def get_model_device(self, model: nn.Module) -> torch.device:
        """
        Detect and return primary device where model parameters reside.
        """
        base_model = model
        if isinstance(model, nn.DataParallel):
            base_model = model.module
        elif hasattr(model, "module"):
            base_model = model.module

        if hasattr(base_model, "parameters"):
            try:
                param = next(base_model.parameters(), None)
                if param is not None:
                    return param.device
            except Exception:
                pass

        if torch.cuda.is_available():
            return torch.device("cuda:0")
        return torch.device("cpu")

    def get_total_params(self, model: nn.Module) -> Tuple[int, int]:
        """
        Count total and trainable parameters.
        
        Returns:
            Tuple of (total_parameters, trainable_parameters)
        """
        base = model.module if isinstance(model, nn.DataParallel) else model
        total = sum(p.numel() for p in base.parameters())
        trainable = sum(p.numel() for p in base.parameters() if p.requires_grad)
        return total, trainable

    def get_memory_footprint(self, model: nn.Module) -> int:
        """
        Calculate total memory footprint in bytes.
        """
        base = model.module if isinstance(model, nn.DataParallel) else model
        total_bytes = 0
        for p in base.parameters():
            total_bytes += p.numel() * p.element_size()
        for b in base.buffers():
            total_bytes += b.numel() * b.element_size()
        return total_bytes

    def enable_multi_gpu(
        self,
        model: nn.Module,
        device_ids: Optional[List[int]] = None,
    ) -> nn.Module:
        """
        Wrap model with DataParallel if multiple GPUs are available.
        """
        if torch.cuda.is_available() and torch.cuda.device_count() > 1:
            logger.info(f"Enabling DataParallel across {torch.cuda.device_count()} CUDA GPUs")
            return nn.DataParallel(model, device_ids=device_ids)
        logger.debug("Only single device or CPU available; DataParallel bypassed")
        return model

    def enable_torch_compile(
        self,
        model: nn.Module,
        mode: str = "default",
        dynamic: bool = False,
        fullgraph: bool = False,
        backend: Optional[str] = None,
    ) -> nn.Module:
        """
        Apply torch.compile with dynamic shape and backend controls.
        """
        if not hasattr(torch, "compile"):
            logger.warning("torch.compile is not available in this PyTorch version")
            return model

        try:
            logger.info(f"Applying torch.compile (mode={mode}, dynamic={dynamic}, backend={backend})")
            compile_kwargs: Dict[str, Any] = {
                "mode": mode,
                "dynamic": dynamic,
                "fullgraph": fullgraph,
            }
            if backend:
                compile_kwargs["backend"] = backend
            return torch.compile(model, **compile_kwargs)
        except Exception as e:
            logger.warning(f"torch.compile failed, falling back to eager execution: {e}")
            return model

    def configure_device_settings(
        self,
        allow_tf32: bool = True,
        matmul_precision: str = "high",
        enable_sdpa_flash: bool = True,
        enable_sdpa_mem_efficient: bool = True,
        enable_sdpa_math: bool = False,
    ) -> None:
        """
        Optimize CUDA device execution settings for Tensor Cores and SDPA.
        """
        if not torch.cuda.is_available():
            return

        try:
            if allow_tf32 and hasattr(torch.backends, "cuda") and hasattr(torch.backends.cuda, "matmul"):
                torch.backends.cuda.matmul.allow_tf32 = True
                if hasattr(torch.backends, "cudnn"):
                    torch.backends.cudnn.allow_tf32 = True
                if hasattr(torch, "set_float32_matmul_precision"):
                    torch.set_float32_matmul_precision(matmul_precision)
                logger.debug(f"TF32 and matmul precision set to '{matmul_precision}'")

            # Configure PyTorch 2.0 SDPA kernels
            if hasattr(torch.backends, "cuda") and hasattr(torch.backends.cuda, "sdp_kernel"):
                torch.backends.cuda.sdp_kernel(
                    enable_flash=enable_sdpa_flash,
                    enable_mem_efficient=enable_sdpa_mem_efficient,
                    enable_math=enable_sdpa_math,
                )
                logger.debug("PyTorch SDPA hardware kernels configured")
        except Exception as e:
            logger.warning(f"Device configuration encountered an issue: {e}")

    def get_model_info(self, model: nn.Module) -> Dict[str, Any]:
        """
        Inspect model parameters, memory usage, and execution device.
        """
        base_model = model.module if isinstance(model, nn.DataParallel) else model
        total_params, trainable_params = self.get_total_params(model)
        dtype_str = "unknown"
        device_str = str(self.get_model_device(model))

        if hasattr(base_model, "parameters"):
            params = list(base_model.parameters())
            if params:
                dtype_str = str(params[0].dtype)

        bytes_per_param = 4
        if "16" in dtype_str:
            bytes_per_param = 2
        elif "8" in dtype_str:
            bytes_per_param = 1
        est_mem_mb = (total_params * bytes_per_param) / (1024 * 1024)

        return {
            "device": device_str,
            "dtype": dtype_str,
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "trainable_percentage": (trainable_params / max(1, total_params)) * 100.0,
            "estimated_memory_mb": round(est_mem_mb, 2),
            "is_peft": _PEFT_AVAILABLE and isinstance(base_model, PeftModel),
        }

    # -----------------------------------------------------------------------
    # Internal Helpers
    # -----------------------------------------------------------------------

    def _resolve_dtype(self, dtype: Optional[Union[str, torch.dtype]]) -> Optional[torch.dtype]:
        if dtype is None:
            return None
        if isinstance(dtype, torch.dtype):
            return dtype
        dtype_str = str(dtype).lower()
        if dtype_str in ("bf16", "bfloat16"):
            return torch.bfloat16
        if dtype_str in ("fp16", "float16"):
            return torch.float16
        if dtype_str in ("fp32", "float32"):
            return torch.float32
        return None

    def _select_model_class(self, model_class: Optional[str]) -> Any:
        if not _TRANSFORMERS_AVAILABLE:
            raise ModelLoadError("transformers is not installed")

        if model_class is None or model_class.lower() in ("causal_lm", "causal", "default"):
            return AutoModelForCausalLM
        if model_class.lower() in ("seq2seq", "seq2seq_lm"):
            return AutoModelForSeq2SeqLM
        if model_class.lower() in ("auto", "base"):
            return AutoModel
        return AutoModelForCausalLM

    def _enable_gradient_checkpointing(
        self,
        model: nn.Module,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        if hasattr(model, "gradient_checkpointing_enable"):
            try:
                gc_kwargs = kwargs or {"use_reentrant": False}
                try:
                    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs=gc_kwargs)
                except TypeError:
                    model.gradient_checkpointing_enable()
                logger.debug("Gradient checkpointing enabled")
            except Exception as e:
                logger.warning(f"Could not enable gradient checkpointing: {e}")

    def _build_quantization_config(self, q_cfg: Dict[str, Any]) -> Any:
        if not _TRANSFORMERS_AVAILABLE or BitsAndBytesConfig is None:
            raise QuantizationError("BitsAndBytesConfig is not available in current environment")

        bits = q_cfg.get("bits", 4)
        if bits == 4:
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type=q_cfg.get("quant_type", "nf4"),
                bnb_4bit_use_double_quant=q_cfg.get("double_quant", True),
                bnb_4bit_compute_dtype=q_cfg.get("compute_dtype", torch.float16),
            )
        elif bits == 8:
            return BitsAndBytesConfig(load_in_8bit=True)
        else:
            raise QuantizationError(f"Unsupported quantization bit width: {bits} (must be 4 or 8)")

    def _apply_lora(
        self,
        model: nn.Module,
        lora_config: Dict[str, Any],
        model_name: Optional[str] = None,
    ) -> nn.Module:
        if not _PEFT_AVAILABLE:
            raise ModelOptimizationError("peft package is required for LoRA but not installed")

        try:
            target_modules = lora_config.get(
                "target_modules",
                ["c_attn", "c_proj", "q_proj", "v_proj", "k_proj", "o_proj"],
            )
            lconf = LoraConfig(
                r=lora_config.get("r", 16),
                lora_alpha=lora_config.get("alpha", 32),
                lora_dropout=lora_config.get("dropout", 0.05),
                target_modules=target_modules,
                bias=lora_config.get("bias", "none"),
                task_type=lora_config.get("task_type", "CAUSAL_LM"),
            )
            model = get_peft_model(model, lconf)
            logger.info(f"LoRA successfully applied (r={lconf.r}, alpha={lconf.lora_alpha})")
            return model
        except Exception as e:
            logger.error(f"Failed to apply LoRA to model '{model_name}': {e}", exc_info=True)
            raise ModelOptimizationError(f"LoRA application failed: {e}", model_name=model_name, original_exception=e) from e


def create_model_manager(config: Optional[Dict[str, Any]] = None) -> ModelManager:
    """Factory helper to create a ModelManager instance."""
    config = config or {}
    return ModelManager(config=config, default_device=config.get("default_device"))


def __getattr__(name: str) -> Any:
    if name == "ModelBuilder":
        from .model_builder import ModelBuilder
        return ModelBuilder
    if name == "create_model_builder":
        from .model_builder import create_model_builder
        return create_model_builder
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "ModelManager",
    "create_model_manager",
]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.models."):
        sys.modules["models." + __name__[len("optimization_core.models."):]] = _mod
    elif __name__.startswith("models."):
        sys.modules["optimization_core.models." + __name__[len("models."):]] = _mod
