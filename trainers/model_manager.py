"""
Model Manager - Handles model loading, tokenizer configuration, LoRA setup, and compilation.

Separated from trainer for modularity, clean architecture, and testability.
"""
import logging
from typing import Optional, List, Tuple, Any, Dict
import torch
import torch.nn as nn

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    AutoModelForCausalLM = Any
    AutoTokenizer = Any

from .config import ModelConfig, HardwareConfig, TrainingConfig
from .interfaces import BaseModelManager
from .exceptions import ModelManagerError, ModelInitializationError

try:
    from peft import LoraConfig, get_peft_model, TaskType
    _PEFT_AVAILABLE = True
except ImportError:
    _PEFT_AVAILABLE = False

logger = logging.getLogger(__name__)


class ModelManager(BaseModelManager):
    """
    Manages model loading, initialization, LoRA integration, and device placement.
    
    Responsibilities:
    - Load tokenizer and handle pad token defaults
    - Load CausalLM model with precision settings
    - Configure LoRA adapters via PEFT if enabled
    - Enable gradient checkpointing and torch.compile
    - Handle multi-GPU / DDP wrapping
    """
    
    def __init__(
        self,
        model_config: ModelConfig,
        hardware_config: HardwareConfig,
        training_config: TrainingConfig,
        device: torch.device,
    ) -> None:
        self.model_config = model_config
        self.hardware_config = hardware_config
        self.training_config = training_config
        self.device = device
        self.tokenizer: Optional[Any] = None
        self.model: Optional[nn.Module] = None
        self._is_parallel = False
        self._is_ddp = False
    
    def load_tokenizer(self) -> Any:
        """Load and configure HuggingFace AutoTokenizer."""
        if not _TRANSFORMERS_AVAILABLE:
            raise ModelManagerError(
                "HuggingFace transformers is not installed.",
                error_code="ERR_TRANSFORMERS_MISSING",
                suggested_action="Install transformers with `pip install transformers`"
            )
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.model_config.name_or_path)
            if tokenizer.pad_token is None:
                if tokenizer.eos_token is not None:
                    tokenizer.pad_token = tokenizer.eos_token
                    logger.info(f"Set tokenizer pad_token to eos_token: {tokenizer.eos_token}")
                else:
                    tokenizer.add_special_tokens({"pad_token": "[PAD]"})
                    logger.info("Added special [PAD] token to tokenizer")
            self.tokenizer = tokenizer
            return tokenizer
        except Exception as e:
            logger.error(f"Failed to load tokenizer for '{self.model_config.name_or_path}': {e}", exc_info=True)
            raise ModelManagerError(
                f"Failed to load tokenizer for '{self.model_config.name_or_path}': {e}",
                context={"model_name": self.model_config.name_or_path}
            ) from e

    def load_model(self) -> nn.Module:
        """Load, configure, and initialize PyTorch model."""
        if not _TRANSFORMERS_AVAILABLE:
            raise ModelManagerError(
                "HuggingFace transformers is not installed.",
                error_code="ERR_TRANSFORMERS_MISSING"
            )
        load_dtype = None
        if self.device.type == "cuda":
            mixed_prec = getattr(self.training_config, "mixed_precision", "none")
            if mixed_prec == "bf16":
                load_dtype = torch.bfloat16
            elif mixed_prec == "fp16":
                load_dtype = torch.float16
        
        try:
            model = AutoModelForCausalLM.from_pretrained(
                self.model_config.name_or_path,
                torch_dtype=load_dtype,
                device_map=None,
                trust_remote_code=False,
            )
            
            if self.model_config.gradient_checkpointing:
                if hasattr(model, "gradient_checkpointing_enable"):
                    model.gradient_checkpointing_enable()
                    logger.info("Gradient checkpointing enabled")
                else:
                    logger.warning("Gradient checkpointing not supported by this model architecture")
            
            if hasattr(model, "config"):
                try:
                    model.config.use_cache = False
                except Exception:
                    pass
            
            if self.model_config.lora_enabled:
                model = self._apply_lora(model)
            
            model.to(self.device)
            
            if getattr(self.hardware_config, "torch_compile", False):
                model = self._compile_model(model)
            
            total_params, trainable_params = self._count_parameters(model)
            pct = (trainable_params / max(1, total_params)) * 100.0
            logger.info(f"Model loaded: {total_params:,} total params, {trainable_params:,} trainable params ({pct:.2f}%)")
            
            self.model = model
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model '{self.model_config.name_or_path}': {e}", exc_info=True)
            raise ModelManagerError(
                f"Failed to load model '{self.model_config.name_or_path}': {e}",
                context={"model_name": self.model_config.name_or_path}
            ) from e

    def _apply_lora(self, model: nn.Module) -> nn.Module:
        """Apply PEFT LoRA adapter modules to model."""
        if not _PEFT_AVAILABLE:
            raise ModelManagerError(
                "PEFT library is not installed.",
                error_code="ERR_PEFT_MISSING",
                suggested_action="Install peft with `pip install peft` to use LoRA."
            )
        
        target_modules = self._detect_lora_target_modules(model)
        logger.info(f"Applying LoRA: r={self.model_config.lora_r}, alpha={self.model_config.lora_alpha}, targets={target_modules}")
        
        try:
            task_type = getattr(TaskType, 'CAUSAL_LM', "CAUSAL_LM")
            lora_config = LoraConfig(
                r=self.model_config.lora_r,
                lora_alpha=self.model_config.lora_alpha,
                lora_dropout=self.model_config.lora_dropout,
                target_modules=target_modules,
                bias="none",
                task_type=task_type,
            )
            peft_model = get_peft_model(model, lora_config)
            logger.info("LoRA adapters successfully injected")
            return peft_model
        except Exception as e:
            logger.error(f"Failed to apply LoRA: {e}", exc_info=True)
            raise ModelManagerError(f"Failed to apply LoRA: {e}") from e

    def _detect_lora_target_modules(self, model: nn.Module) -> List[str]:
        """Detect architecture target projection modules for LoRA injection."""
        default_modules = ["q_proj", "v_proj", "k_proj", "o_proj", "c_attn", "c_proj"]
        
        if hasattr(model, "config"):
            model_type = getattr(model.config, "model_type", "").lower()
            
            if any(k in model_type for k in ["llama", "mistral", "qwen", "gemma", "deepseek"]):
                return ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
            elif "gpt" in model_type:
                return ["c_attn", "c_proj", "c_fc"]
            elif any(k in model_type for k in ["bert", "roberta"]):
                return ["query", "key", "value", "dense"]
            elif any(k in model_type for k in ["t5", "ul2"]):
                return ["q", "k", "v", "o"]
            elif "opt" in model_type:
                return ["q_proj", "k_proj", "v_proj", "out_proj"]
        
        return default_modules

    def _compile_model(self, model: nn.Module) -> nn.Module:
        """Apply torch.compile optimization."""
        if not hasattr(torch, "compile"):
            logger.warning("torch.compile is not supported in this PyTorch version")
            return model
        
        try:
            compile_mode = getattr(self.hardware_config, "compile_mode", "default")
            compiled = torch.compile(model, mode=compile_mode)
            logger.info(f"Model compiled with mode '{compile_mode}'")
            return compiled
        except Exception as e:
            logger.warning(f"Failed to compile model with torch.compile: {e}")
            return model

    def setup_parallel(self, multi_gpu: bool = False, ddp: bool = False) -> None:
        """Setup multi-GPU DataParallel or DistributedDataParallel wrapping."""
        if self.model is None:
            return
            
        if ddp:
            try:
                import torch.distributed as dist
                from torch.nn.parallel import DistributedDataParallel as DDP
                
                if dist.is_initialized():
                    local_rank = dist.get_rank() % max(1, torch.cuda.device_count())
                    self.device = torch.device(f"cuda:{local_rank}")
                    self.model.to(self.device)
                    self.model = DDP(
                        self.model,
                        device_ids=[local_rank],
                        output_device=local_rank,
                        find_unused_parameters=False,
                    )
                    self._is_ddp = True
                    logger.info(f"DDP initialized on rank {dist.get_rank()}")
                else:
                    logger.warning("DDP requested but torch.distributed is not initialized")
            except Exception as e:
                logger.warning(f"Failed to setup DDP: {e}")
        
        elif multi_gpu and torch.cuda.device_count() > 1:
            self.model = nn.DataParallel(self.model)
            self._is_parallel = True
            logger.info(f"Using DataParallel across {torch.cuda.device_count()} GPUs")

    def get_model_for_operations(self) -> nn.Module:
        """Unwrap parallel wrappers to access underlying base module."""
        model = self.model
        if model is None:
            raise ModelManagerError("Model has not been loaded.")
        if self._is_parallel or self._is_ddp:
            model = getattr(model, "module", model)
        if hasattr(model, "module"):
            model = getattr(model, "module")
        return model

    def _count_parameters(self, model: nn.Module) -> Tuple[int, int]:
        total = sum(p.numel() for p in model.parameters())
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        return total, trainable

    def get_total_params(self) -> Tuple[int, int]:
        """Get parameter metrics (total, trainable)."""
        if self.model is None:
            return 0, 0
        return self._count_parameters(self.get_model_for_operations())


__all__ = ["ModelManager"]
