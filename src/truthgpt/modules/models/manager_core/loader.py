import logging
import torch
from typing import Optional, Dict, Any
from transformers import AutoModelForCausalLM

logger = logging.getLogger(__name__)

try:
    from peft import LoraConfig, get_peft_model
    _PEFT_AVAILABLE = True
except ImportError:
    _PEFT_AVAILABLE = False

class ModelLoader:
    """Model loading and configuration utilities."""
    @staticmethod
    def load_model(model_name: str, torch_dtype: Optional[torch.dtype] = None, device_map: Optional[str] = None, gradient_checkpointing: bool = True, lora_config: Optional[Dict[str, Any]] = None, trust_remote_code: bool = True) -> torch.nn.Module:
        try:
            logger.info(f"Loading model: {model_name}")
            model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch_dtype, device_map=device_map, trust_remote_code=trust_remote_code)
            if gradient_checkpointing and hasattr(model, "gradient_checkpointing_enable"): model.gradient_checkpointing_enable()
            if hasattr(model, "config"):
                try: model.config.use_cache = False
                except Exception: pass
            if lora_config and lora_config.get("enabled", False):
                if not _PEFT_AVAILABLE: raise RuntimeError("PEFT not available but LoRA was requested")
                lconf = LoraConfig(r=lora_config.get("r", 16), lora_alpha=lora_config.get("alpha", 32), lora_dropout=lora_config.get("dropout", 0.05), target_modules=["c_attn", "c_proj", "q_proj", "v_proj", "k_proj", "o_proj"], bias="none", task_type="CAUSAL_LM")
                model = get_peft_model(model, lconf)
            return model
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            raise
