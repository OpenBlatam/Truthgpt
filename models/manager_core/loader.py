"""
Model loader component supporting HuggingFace, PEFT/LoRA, and custom weight initializers.
"""

import logging
import torch
import torch.nn as nn
from typing import Optional, Dict, Any

from ..exceptions import ModelConfigurationError, ModelLoadError

logger = logging.getLogger(__name__)

try:
    from peft import LoraConfig, get_peft_model
    _PEFT_AVAILABLE = True
except ImportError:
    _PEFT_AVAILABLE = False


class ModelLoader:
    """Handles loading causal language models, configurations, and LoRA adapters."""

    @staticmethod
    def load_model(
        model_name: str,
        torch_dtype: Optional[torch.dtype] = None,
        device_map: Optional[str] = None,
        gradient_checkpointing: bool = True,
        lora_config: Optional[Dict[str, Any]] = None,
        trust_remote_code: bool = True,
        **kwargs: Any
    ) -> nn.Module:
        """
        Load a model by identifier or directory path.

        Args:
            model_name: HuggingFace model hub ID or local path.
            torch_dtype: Desired torch dtype for weights.
            device_map: Device mapping strategy (e.g. 'auto').
            gradient_checkpointing: Whether to enable gradient checkpointing.
            lora_config: Optional LoRA configuration dictionary.
            trust_remote_code: Whether to allow custom code execution from model repo.

        Returns:
            Loaded and configured nn.Module.
        """
        if not model_name or not str(model_name).strip():
            raise ModelConfigurationError("model_name cannot be empty", model_name=str(model_name))

        try:
            logger.info(f"Loading model: {model_name}")
            from transformers import AutoModelForCausalLM

            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch_dtype,
                device_map=device_map,
                trust_remote_code=trust_remote_code,
                **kwargs
            )

            if gradient_checkpointing and hasattr(model, "gradient_checkpointing_enable"):
                model.gradient_checkpointing_enable()
                logger.debug("Gradient checkpointing enabled")

            if hasattr(model, "config"):
                try:
                    model.config.use_cache = False
                except Exception:
                    pass

            if lora_config and lora_config.get("enabled", False):
                if not _PEFT_AVAILABLE:
                    raise RuntimeError("PEFT is required for LoRA but is not installed")

                lconf = LoraConfig(
                    r=lora_config.get("r", 16),
                    lora_alpha=lora_config.get("alpha", 32),
                    lora_dropout=lora_config.get("dropout", 0.05),
                    target_modules=lora_config.get(
                        "target_modules",
                        ["c_attn", "c_proj", "q_proj", "v_proj", "k_proj", "o_proj"]
                    ),
                    bias=lora_config.get("bias", "none"),
                    task_type=lora_config.get("task_type", "CAUSAL_LM"),
                )
                model = get_peft_model(model, lconf)
                logger.info("LoRA adapter attached successfully")

            logger.info(f"Model '{model_name}' loaded successfully")
            return model

        except Exception as e:
            if isinstance(e, (ModelConfigurationError, ModelLoadError)):
                raise
            logger.error(f"Error loading model '{model_name}': {e}", exc_info=True)
            raise ModelLoadError(
                f"Error loading model '{model_name}': {e}",
                model_name=model_name,
                original_exception=e,
            ) from e
