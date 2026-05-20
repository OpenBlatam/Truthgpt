"""
Model Manager - Handles model loading, configuration, and LoRA setup.

Separated from trainer for better modularity and testability.
"""
import logging
from typing import Optional, List, Tuple
import torch
import torch.nn as nn
from transformers import AutoModelForCausalLM, AutoTokenizer

from trainers.config import ModelConfig, HardwareConfig, TrainingConfig

try:
    from peft import LoraConfig, get_peft_model, TaskType
    _PEFT_AVAILABLE = True
except ImportError:
    _PEFT_AVAILABLE = False

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manages model loading, initialization, and configuration.
    
    Responsibilities:
    - Load tokenizer and model
    - Configure LoRA if needed
    - Enable gradient checkpointing
    - Apply torch.compile if requested
    - Handle device placement
    """
    
    def __init__(
        self,
        model_config: ModelConfig,
        hardware_config: HardwareConfig,
        training_config: TrainingConfig,
        device: torch.device,
    ):
        """
        Initialize ModelManager.
        
        Args:
            model_config: Model configuration
            hardware_config: Hardware configuration
            training_config: Training configuration (for mixed_precision)
            device: Target device
        """
        self.model_config = model_config
        self.hardware_config = hardware_config
        self.training_config = training_config
        self.device = device
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[nn.Module] = None
        self._is_parallel = False
        self._is_ddp = False
    
    def load_tokenizer(self) -> AutoTokenizer:
        """Load and configure tokenizer."""
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.model_config.name_or_path)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
                logger.info(f"Set pad_token to eos_token: {tokenizer.eos_token}")
            self.tokenizer = tokenizer
            return tokenizer
        except Exception as e:
            logger.error(f"Failed to load tokenizer: {e}", exc_info=True)
            raise
    
    def load_model(self) -> nn.Module:
        """Load and configure model."""
        # Determine dtype from training config
        load_dtype = None
        if self.device.type == "cuda":
            if self.training_config.mixed_precision == "bf16":
                load_dtype = torch.bfloat16
            elif self.training_config.mixed_precision == "fp16":
                load_dtype = torch.float16
        
        try:
            model = AutoModelForCausalLM.from_pretrained(
                self.model_config.name_or_path,
                torch_dtype=load_dtype,
                device_map=None,  # Manual placement
                trust_remote_code=False,
            )
            
            # Enable gradient checkpointing
            if self.model_config.gradient_checkpointing:
                if hasattr(model, "gradient_checkpointing_enable"):
                    model.gradient_checkpointing_enable()
                    logger.info("Gradient checkpointing enabled")
                else:
                    logger.warning("Gradient checkpointing not available for this model")
            
            # Disable cache during training
            if hasattr(model, "config"):
                try:
                    model.config.use_cache = False
                except Exception:
                    pass
            
            # Apply LoRA if needed
            if self.model_config.lora_enabled:
                model = self._apply_lora(model)
            
            # Move to device
            model.to(self.device)
            
            # Apply torch.compile if requested
            if self.hardware_config.torch_compile:
                model = self._compile_model(model)
            
            # Initialize weights for new layers
            self._initialize_weights(model)
            
            # Log model info
            total_params = sum(p.numel() for p in model.parameters())
            trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
            logger.info(f"Model loaded: {total_params:,} total params, {trainable_params:,} trainable")
            
            self.model = model
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise
    
    def _apply_lora(self, model: nn.Module) -> nn.Module:
        """Apply LoRA to model."""
        if not _PEFT_AVAILABLE:
            raise RuntimeError("PEFT not available. Install with: pip install peft")
        
        target_modules = self._detect_lora_target_modules(model)
        logger.info(f"Applying LoRA: r={self.model_config.lora_r}, alpha={self.model_config.lora_alpha}")
        
        try:
            lora_config = LoraConfig(
                r=self.model_config.lora_r,
                lora_alpha=self.model_config.lora_alpha,
                lora_dropout=self.model_config.lora_dropout,
                target_modules=target_modules,
                bias="none",
                task_type=TaskType.CAUSAL_LM if hasattr(TaskType, 'CAUSAL_LM') else "CAUSAL_LM",
            )
            model = get_peft_model(model, lora_config)
            logger.info("LoRA successfully applied")
            return model
        except Exception as e:
            logger.error(f"Failed to apply LoRA: {e}", exc_info=True)
            raise
    
    def _detect_lora_target_modules(self, model: nn.Module) -> List[str]:
        """Detect target modules for LoRA based on model architecture."""
        default_modules = ["c_attn", "c_proj", "q_proj", "v_proj", "k_proj", "o_proj"]
        
        if hasattr(model, "config"):
            model_type = getattr(model.config, "model_type", "").lower()
            
            if "gpt" in model_type or "llama" in model_type or "mistral" in model_type:
                return default_modules
            elif "bert" in model_type or "roberta" in model_type:
                return ["query", "key", "value", "dense"]
            elif "t5" in model_type or "ul2" in model_type:
                return ["q", "k", "v", "o"]
            elif "opt" in model_type:
                return ["q_proj", "k_proj", "v_proj", "out_proj"]
        
        logger.warning(f"Could not auto-detect LoRA modules, using defaults: {default_modules}")
        return default_modules
    
    def _compile_model(self, model: nn.Module) -> nn.Module:
        """Apply torch.compile to model."""
        if not hasattr(torch, "compile"):
            logger.warning("torch.compile not available")
            return model
        
        try:
            compiled = torch.compile(model, mode=self.hardware_config.compile_mode)
            logger.info(f"Model compiled with mode: {self.hardware_config.compile_mode}")
            return compiled
        except Exception as e:
            logger.warning(f"Failed to compile model: {e}")
            return model
    
    def _initialize_weights(self, model: nn.Module) -> None:
        """Initialize weights for new/modified layers."""
        for module in model.modules():
            if isinstance(module, (nn.Linear, nn.Conv1d, nn.Conv2d)):
                if hasattr(module, 'weight') and module.weight is not None:
                    weight_std = module.weight.std().item()
                    if weight_std < 1e-6:  # Essentially uninitialized
                        nn.init.kaiming_normal_(module.weight, mode='fan_out', nonlinearity='relu')
                        if hasattr(module, 'bias') and module.bias is not None:
                            nn.init.constant_(module.bias, 0)
    
    def setup_parallel(self, multi_gpu: bool = False, ddp: bool = False) -> None:
        """
        Setup multi-GPU training.
        
        Args:
            multi_gpu: Use DataParallel
            ddp: Use DistributedDataParallel
        """
        if ddp:
            try:
                import torch.distributed as dist
                from torch.nn.parallel import DistributedDataParallel as DDP
                
                if dist.is_initialized():
                    local_rank = dist.get_rank() % torch.cuda.device_count()
                    self.device = torch.device(f"cuda:{local_rank}")
                    self.model.to(self.device)
                    self.model = DDP(
                        self.model,
                        device_ids=[local_rank],
                        output_device=local_rank,
                        find_unused_parameters=False,
                    )
                    self._is_ddp = True
                    logger.info(f"Using DDP (rank {dist.get_rank()})")
                else:
                    logger.warning("DDP requested but not initialized")
            except ImportError:
                logger.warning("Distributed training not available")
        
        elif multi_gpu and torch.cuda.device_count() > 1:
            self.model = nn.DataParallel(self.model)
            self._is_parallel = True
            logger.info(f"Using DataParallel with {torch.cuda.device_count()} GPUs")
    
    def get_model_for_operations(self) -> nn.Module:
        """Get the base model for operations (handles parallel wrappers)."""
        model = self.model
        if self._is_parallel or self._is_ddp:
            model = model.module
        if hasattr(model, "module"):
            model = model.module
        return model
    
    def get_total_params(self) -> Tuple[int, int]:
        """Get total and trainable parameter counts."""
        model = self.get_model_for_operations()
        total = sum(p.numel() for p in model.parameters())
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        return total, trainable

