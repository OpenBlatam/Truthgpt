"""
Enhanced GenericTrainer with best practices for PyTorch, Transformers, and LLM training.

Follows best practices for:
- Mixed precision training (FP16/BF16)
- Gradient accumulation and clipping
- Weight initialization and normalization
- Error handling and NaN detection
- Multi-GPU support (DataParallel/DDP)
- Efficient data loading with dynamic padding
- EMA (Exponential Moving Average) weights
- Comprehensive logging and monitoring
"""
import math
import os
import random
from dataclasses import dataclass
from typing import Dict, Optional, List, Any, Union, Tuple
import logging
import time

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.cuda.amp import autocast, GradScaler

from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    get_cosine_schedule_with_warmup,
    get_linear_schedule_with_warmup,
)
from factories.optimizer import OPTIMIZERS
from trainers.callbacks import Callback
from factories.collate import COLLATE
from utils.logging_utils import TrainingLogger

try:
    from peft import LoraConfig, get_peft_model, TaskType
    _PEFT_AVAILABLE = True
except ImportError:
    _PEFT_AVAILABLE = False

try:
    import torch.distributed as dist
    from torch.nn.parallel import DistributedDataParallel as DDP
    _DISTRIBUTED_AVAILABLE = True
except ImportError:
    _DISTRIBUTED_AVAILABLE = False

logger = logging.getLogger(__name__)


def set_seed(seed: int) -> None:
    """
    Set random seeds for reproducibility.
    
    Args:
        seed: Random seed value
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        # Ensure deterministic behavior
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


@dataclass
class TrainerConfig:
    seed: int = 42
    run_name: str = "run"
    output_dir: str = "runs/run"

    model_name: str = "gpt2"
    gradient_checkpointing: bool = True

    lora_enabled: bool = False
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05

    epochs: int = 3
    train_batch_size: int = 8
    eval_batch_size: int = 8
    grad_accum_steps: int = 2
    max_grad_norm: float = 1.0
    learning_rate: float = 5e-5
    weight_decay: float = 0.01
    warmup_ratio: float = 0.06
    scheduler: str = "cosine"
    mixed_precision: str = "bf16"  # one of: none|fp16|bf16
    early_stopping_patience: int = 2
    log_interval: int = 50
    eval_interval: int = 500

    device: str = "auto"
    # Multi-GPU support
    multi_gpu: bool = False  # Use DataParallel if multiple GPUs available
    ddp: bool = False  # Use DistributedDataParallel (requires proper setup)
    # Performance
    allow_tf32: bool = True
    torch_compile: bool = False
    compile_mode: str = "default"  # default|reduce-overhead|max-autotune
    num_workers: int = 4
    prefetch_factor: int = 2
    persistent_workers: bool = True
    fused_adamw: bool = True
    detect_anomaly: bool = False
    use_profiler: bool = False
    save_safetensors: bool = True
    optimizer_type: str = "adamw"
    select_best_by: str = "loss"  # loss|ppl
    # Checkpointing / EMA
    ckpt_interval_steps: int = 1000
    ckpt_keep_last: int = 3
    ema_enabled: bool = True
    ema_decay: float = 0.999
    # Resume training
    resume_from_checkpoint: Optional[str] = None
    resume_enabled: bool = False  # Auto-resume from latest checkpoint if no explicit path
    resume_checkpoint_dir: Optional[str] = None  # Directory to search for checkpoints


class HFTextDataset(torch.utils.data.Dataset):
    def __init__(self, tokenizer, texts, max_length: int) -> None:
        self.tokenizer = tokenizer
        self.texts = texts
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        text = self.texts[idx]
        tokens = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        input_ids = tokens["input_ids"].squeeze(0)
        attn_mask = tokens["attention_mask"].squeeze(0)
        labels = input_ids.clone()
        return {"input_ids": input_ids, "attention_mask": attn_mask, "labels": labels}


class GenericTrainer:
    def __init__(
        self,
        cfg: TrainerConfig,
        train_texts,
        val_texts,
        text_field_max_len: int = 512,
        callbacks: Optional[List[Callback]] = None,
        data_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.cfg = cfg
        set_seed(cfg.seed)
        self.callbacks = callbacks or []
        self.data_options = data_options or {}
        self._ema_shadow: Optional[Dict[str, torch.Tensor]] = None
        self._ema_backup: Optional[Dict[str, torch.Tensor]] = None

        self.device = self._resolve_device(cfg.device)
        
        # Load tokenizer with proper error handling
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(cfg.model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                logger.info(f"Set pad_token to eos_token: {self.tokenizer.eos_token}")
        except Exception as e:
            logger.error(f"Failed to load tokenizer from {cfg.model_name}: {e}", exc_info=True)
            raise

        # Determine model dtype for loading
        load_dtype = None
        if self._use_amp():
            load_dtype = torch.bfloat16 if self.cfg.mixed_precision == "bf16" else torch.float16
            logger.info(f"Loading model with {self.cfg.mixed_precision} dtype")
        
        # Load model with proper error handling and optimization flags
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                cfg.model_name,
                torch_dtype=load_dtype,
                device_map=None,  # We'll move manually for better control
                trust_remote_code=False,  # Security best practice
            )
            
            # Enable gradient checkpointing for memory efficiency
            if cfg.gradient_checkpointing:
                if hasattr(self.model, "gradient_checkpointing_enable"):
                    self.model.gradient_checkpointing_enable()
                    logger.info("Gradient checkpointing enabled")
                else:
                    logger.warning("Gradient checkpointing requested but not available for this model")
            
            # Disable cache during training to save memory
            if hasattr(self.model, "config"):
                try:
                    self.model.config.use_cache = False
                except Exception as e:
                    logger.debug(f"Could not disable use_cache: {e}")
            
            # Apply proper weight initialization if needed (for new layers)
            self._initialize_weights()
            
        except Exception as e:
            logger.error(f"Failed to load model from {cfg.model_name}: {e}", exc_info=True)
            raise

        # Apply LoRA if enabled
        if cfg.lora_enabled:
            if not _PEFT_AVAILABLE:
                raise RuntimeError("PEFT not available but LoRA was requested. Install with: pip install peft")
            
            # Detect target modules automatically if possible
            target_modules = self._detect_lora_target_modules()
            logger.info(f"Applying LoRA with r={cfg.lora_r}, alpha={cfg.lora_alpha}, target_modules={target_modules}")
            
            try:
                lconf = LoraConfig(
                    r=cfg.lora_r,
                    lora_alpha=cfg.lora_alpha,
                    lora_dropout=cfg.lora_dropout,
                    target_modules=target_modules,
                    bias="none",
                    task_type=TaskType.CAUSAL_LM if hasattr(TaskType, 'CAUSAL_LM') else "CAUSAL_LM",
                )
                self.model = get_peft_model(self.model, lconf)
                logger.info("LoRA successfully applied to model")
            except Exception as e:
                logger.error(f"Failed to apply LoRA: {e}", exc_info=True)
                raise

        # Enable TF32 where beneficial
        if self.device.type == "cuda" and cfg.allow_tf32:
            try:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.set_float32_matmul_precision("high")
                if hasattr(torch.backends.cuda, "sdp_kernel"):
                    torch.backends.cuda.sdp_kernel(enable_flash=True, enable_math=False, enable_mem_efficient=True)
            except Exception:
                pass

        # Optional torch.compile
        if cfg.torch_compile and hasattr(torch, "compile"):
            try:
                self.model = torch.compile(self.model, mode=cfg.compile_mode)
            except Exception:
                pass

        # Move model to device
        self.model.to(self.device)
        
        # Log model information
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        logger.info(f"Model loaded: {total_params:,} total parameters, {trainable_params:,} trainable")

        # Decide collate
        collate_name = str(self.data_options.get("collate", "lm"))
        use_lm_collate = collate_name == "lm"
        collate_fn = None
        if use_lm_collate:
            collate_fn = COLLATE.build("lm")(self.tokenizer, text_field_max_len)

        # Optional length bucketing
        bucket_by_length = bool(self.data_options.get("bucket_by_length", False)) and use_lm_collate
        bucket_bins = list(self.data_options.get("bucket_bins", [64, 128, 256, 512]))

        if collate_fn is not None:
            # Use raw texts and dynamic padding via collate
            train_dataset = list(train_texts)
            val_dataset = list(val_texts)

            batch_sampler = None
            if bucket_by_length:
                # Precompute lengths
                lengths = [len(self.tokenizer.encode(t, add_special_tokens=False)) for t in train_dataset]
                # Assign bins
                bin_indices: Dict[int, List[int]] = {b: [] for b in bucket_bins}
                for idx, L in enumerate(lengths):
                    b = next((bb for bb in bucket_bins if L <= bb), bucket_bins[-1])
                    bin_indices[b].append(idx)
                # Build batches per bin
                batches: List[List[int]] = []
                bs = self.cfg.train_batch_size
                for b in bucket_bins:
                    inds = bin_indices[b]
                    for i in range(0, len(inds), bs):
                        batches.append(inds[i:i+bs])
                # Simple sampler yielding indices in order
                class _BatchSampler:
                    def __iter__(self_inner):
                        for batch in batches:
                            yield batch
                    def __len__(self_inner):
                        return len(batches)
                batch_sampler = _BatchSampler()

            self.train_loader = DataLoader(
                train_dataset,
                batch_size=None if batch_sampler is not None else self.cfg.train_batch_size,
                shuffle=(batch_sampler is None),
                num_workers=self.cfg.num_workers,
                pin_memory=True,
                prefetch_factor=self.cfg.prefetch_factor if self.cfg.num_workers > 0 else None,
                persistent_workers=self.cfg.persistent_workers if self.cfg.num_workers > 0 else False,
                collate_fn=collate_fn,
                batch_sampler=batch_sampler,
            )
            self.val_loader = DataLoader(
                val_dataset,
                batch_size=self.cfg.eval_batch_size,
                shuffle=False,
                num_workers=self.cfg.num_workers,
                pin_memory=True,
                prefetch_factor=self.cfg.prefetch_factor if self.cfg.num_workers > 0 else None,
                persistent_workers=self.cfg.persistent_workers if self.cfg.num_workers > 0 else False,
                collate_fn=collate_fn,
            )
        else:
            # Fallback to static padding dataset
            self.train_loader = DataLoader(
                HFTextDataset(self.tokenizer, train_texts, text_field_max_len),
                batch_size=cfg.train_batch_size,
                shuffle=True,
                num_workers=cfg.num_workers,
                pin_memory=True,
                prefetch_factor=cfg.prefetch_factor if cfg.num_workers > 0 else None,
                persistent_workers=cfg.persistent_workers if cfg.num_workers > 0 else False,
            )
            self.val_loader = DataLoader(
                HFTextDataset(self.tokenizer, val_texts, text_field_max_len),
                batch_size=cfg.eval_batch_size,
                shuffle=False,
                num_workers=cfg.num_workers,
                pin_memory=True,
                prefetch_factor=cfg.prefetch_factor if cfg.num_workers > 0 else None,
                persistent_workers=cfg.persistent_workers if cfg.num_workers > 0 else False,
            )

        # Build optimizer via registry for modularity
        try:
            self.optimizer = OPTIMIZERS.build(
                cfg.optimizer_type,
                self.model.parameters(),
                lr=cfg.learning_rate,
                weight_decay=cfg.weight_decay,
                fused=cfg.fused_adamw,
            )
        except Exception:
            adamw_kwargs = {"lr": cfg.learning_rate, "weight_decay": cfg.weight_decay}
            if self.device.type == "cuda":
                try:
                    adamw_kwargs["fused"] = bool(cfg.fused_adamw)
                except TypeError:
                    pass
            self.optimizer = torch.optim.AdamW(self.model.parameters(), **adamw_kwargs)

        num_train_steps = max(1, (len(self.train_loader) * cfg.epochs) // max(1, cfg.grad_accum_steps))
        num_warmup = int(cfg.warmup_ratio * num_train_steps)
        self.lr_scheduler = get_cosine_schedule_with_warmup(
            self.optimizer, num_warmup_steps=num_warmup, num_training_steps=num_train_steps
        )

        # Setup gradient scaler for mixed precision training
        self.scaler = GradScaler(
            enabled=self._use_amp(),
            init_scale=2.**16,  # Good default for FP16
            growth_factor=2.0,
            backoff_factor=0.5,
            growth_interval=2000,
        )
        
        # Create output directory
        os.makedirs(cfg.output_dir, exist_ok=True)
        logger.info(f"Output directory: {cfg.output_dir}")
        
        # Initialize EMA if enabled
        if self.cfg.ema_enabled:
            self._init_ema()
            logger.info(f"EMA enabled with decay={self.cfg.ema_decay}")
        
        self._start_step = 0
        
        # Setup training logger
        self.training_logger = TrainingLogger(logger)
        
        # Enable multi-GPU training if requested and available
        self._is_parallel = False
        self._is_ddp = False
        
        if cfg.ddp and _DISTRIBUTED_AVAILABLE:
            # DistributedDataParallel setup (requires proper initialization)
            if dist.is_initialized():
                local_rank = dist.get_rank() % torch.cuda.device_count()
                self.device = torch.device(f"cuda:{local_rank}")
                self.model.to(self.device)
                self.model = DDP(
                    self.model,
                    device_ids=[local_rank],
                    output_device=local_rank,
                    find_unused_parameters=False,  # Set to True if needed
                )
                self._is_ddp = True
                logger.info(f"Using DistributedDataParallel (rank {dist.get_rank()})")
            else:
                logger.warning("DDP requested but distributed not initialized. Falling back to single GPU.")
        elif cfg.multi_gpu and torch.cuda.device_count() > 1:
            # Use DataParallel for simple multi-GPU training
            logger.info(f"Using DataParallel with {torch.cuda.device_count()} GPUs")
            self.model = nn.DataParallel(self.model)
            self._is_parallel = True

    def _resolve_device(self, target: str) -> torch.device:
        """Resolve device from string specification."""
        if target == "auto":
            if torch.cuda.is_available():
                device = torch.device("cuda")
                logger.info(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
                return device
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                logger.info("Using Apple MPS device")
                return torch.device("mps")
            logger.info("Using CPU device")
            return torch.device("cpu")
        return torch.device(target)
    
    def _detect_lora_target_modules(self) -> List[str]:
        """
        Automatically detect target modules for LoRA based on model architecture.
        
        Returns:
            List of module names to apply LoRA to
        """
        # Default modules for GPT-style models
        default_modules = ["c_attn", "c_proj", "q_proj", "v_proj", "k_proj", "o_proj"]
        
        # Try to detect model-specific modules
        if hasattr(self.model, "config"):
            model_type = getattr(self.model.config, "model_type", "").lower()
            
            if "gpt" in model_type or "llama" in model_type or "mistral" in model_type:
                return default_modules
            elif "bert" in model_type or "roberta" in model_type:
                return ["query", "key", "value", "dense"]
            elif "t5" in model_type or "ul2" in model_type:
                return ["q", "k", "v", "o"]
            elif "opt" in model_type:
                return ["q_proj", "k_proj", "v_proj", "out_proj"]
        
        # Fallback to default
        logger.warning(f"Could not auto-detect LoRA modules, using defaults: {default_modules}")
        return default_modules
    
    def _initialize_weights(self) -> None:
        """
        Initialize weights for new/modified layers following best practices.
        Only initializes layers that haven't been loaded from pretrained weights.
        """
        # Apply xavier_uniform or kaiming_normal initialization to new layers
        # Only initialize if weights are zero or randomly initialized
        for name, module in self.model.named_modules():
            # Skip if already pretrained (this is mainly for new layers)
            if isinstance(module, (nn.Linear, nn.Conv1d, nn.Conv2d)):
                # Check if weights are essentially zero (new layer)
                if hasattr(module, 'weight') and module.weight is not None:
                    weight_std = module.weight.std().item()
                    if weight_std < 1e-6:  # Essentially uninitialized
                        # Use kaiming normal for better initialization
                        nn.init.kaiming_normal_(module.weight, mode='fan_out', nonlinearity='relu')
                        if hasattr(module, 'bias') and module.bias is not None:
                            nn.init.constant_(module.bias, 0)

    def _use_amp(self) -> bool:
        if self.device.type == "cuda" and self.cfg.mixed_precision in ("fp16", "bf16"):
            return True
        return False

    def _amp_dtype(self):
        if self.cfg.mixed_precision == "bf16":
            return torch.bfloat16
        if self.cfg.mixed_precision == "fp16":
            return torch.float16
        return None

    def _try_resume(self) -> int:
        """Try to resume training from checkpoint if available."""
        if not self.cfg.resume_from_checkpoint:
            return 0
        
        checkpoint_path = self.cfg.resume_from_checkpoint
        if not os.path.exists(checkpoint_path):
            logger.warning(f"Resume checkpoint not found: {checkpoint_path}")
            return 0
        
        try:
            # Load model and optimizer state
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            if isinstance(self.model, nn.DataParallel):
                self.model.module.load_state_dict(checkpoint.get("model_state_dict", checkpoint))
            else:
                self.model.load_state_dict(checkpoint.get("model_state_dict", checkpoint))
            
            if "optimizer_state_dict" in checkpoint:
                self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            if "scheduler_state_dict" in checkpoint:
                self.lr_scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
            if "scaler_state_dict" in checkpoint:
                self.scaler.load_state_dict(checkpoint["scaler_state_dict"])
            
            step = checkpoint.get("global_step", checkpoint.get("step", 0))
            logger.info(f"Resumed from checkpoint: {checkpoint_path} at step {step}")
            return step
        except Exception as e:
            logger.error(f"Error loading checkpoint {checkpoint_path}: {e}", exc_info=True)
            return 0

    def train(self) -> None:
        """Main training loop with improved error handling and logging."""
        best_val = math.inf
        best_metric = math.inf
        bad_epochs = 0
        global_step = 0
        
        # Resume from checkpoint if enabled and available
        resume_step = self._try_resume()
        if resume_step > 0:
            global_step = resume_step
            self.training_logger.log_info(f"Resumed training from step {global_step}")
        
        self.model.train()
        if self.cfg.detect_anomaly:
            torch.autograd.set_detect_anomaly(True)
            logger.warning("Anomaly detection enabled - this may slow down training")

        # Optional profiler
        profiler = None
        if self.cfg.use_profiler:
            profiler = torch.profiler.profile(
                activities=[
                    torch.profiler.ProfilerActivity.CPU,
                    torch.profiler.ProfilerActivity.CUDA,
                ],
                schedule=torch.profiler.schedule(wait=1, warmup=1, active=3, repeat=2),
                on_trace_ready=torch.profiler.tensorboard_trace_handler(self.cfg.output_dir),
            )
            profiler.start()

        try:
            for epoch in range(self.cfg.epochs):
                running_loss = 0.0
                epoch_start = time.perf_counter()
                tokens_accum = 0
                step_count = 0
                
                logger.info(f"Starting epoch {epoch + 1}/{self.cfg.epochs}")
                
                for step, batch in enumerate(self.train_loader, start=1):
                    try:
                        batch = {k: v.to(self.device, non_blocking=True) for k, v in batch.items()}

                        with autocast(enabled=self._use_amp(), dtype=self._amp_dtype()):
                            outputs = self.model(**batch)
                            loss = outputs.loss / self.cfg.grad_accum_steps
                            # Handle DataParallel
                            if isinstance(loss, dict):
                                loss = loss.get("loss", list(loss.values())[0]) / self.cfg.grad_accum_steps
                            elif hasattr(loss, "mean"):
                                loss = loss.mean() / self.cfg.grad_accum_steps

                        # Check for NaN/Inf in loss
                        if not torch.isfinite(loss):
                            logger.warning(
                                f"Skipping step {step} due to non-finite loss: {loss.item()}. "
                                "This may indicate numerical instability."
                            )
                            self.optimizer.zero_grad(set_to_none=True)
                            continue
                        
                        # Backward pass with gradient scaling
                        self.scaler.scale(loss).backward()
                        
                        # Check for NaN in gradients
                        has_nan_grad = False
                        model_for_check = self.model.module if self._is_parallel or self._is_ddp else self.model
                        if hasattr(model_for_check, "module"):  # Handle wrapped models
                            model_for_check = model_for_check.module
                            
                        for name, param in model_for_check.named_parameters():
                            if param.grad is not None:
                                if not torch.isfinite(param.grad).all():
                                    logger.warning(f"NaN/Inf gradient detected in {name}")
                                    has_nan_grad = True
                                    break
                        
                        if has_nan_grad:
                            logger.warning("Skipping optimizer step due to NaN gradients")
                            self.scaler.update()  # Update scaler even on skip
                            self.optimizer.zero_grad(set_to_none=True)
                            continue

                        # Gradient accumulation and update
                        if step % self.cfg.grad_accum_steps == 0:
                            # Unscale gradients before clipping
                            self.scaler.unscale_(self.optimizer)
                            
                            # Get model for gradient clipping (handle parallel models)
                            model_for_clipping = self.model
                            if self._is_parallel or self._is_ddp:
                                model_for_clipping = self.model.module
                            if hasattr(model_for_clipping, "module"):
                                model_for_clipping = model_for_clipping.module
                            
                            # Gradient clipping with error handling
                            try:
                                grad_norm = torch.nn.utils.clip_grad_norm_(
                                    model_for_clipping.parameters(),
                                    self.cfg.max_grad_norm,
                                    error_if_nonfinite=False,  # Don't raise on NaN, just return inf
                                )
                                
                                # Check if gradient norm is finite
                                if not torch.isfinite(torch.tensor(grad_norm)):
                                    logger.warning(f"Non-finite gradient norm: {grad_norm}")
                                    self.scaler.update()
                                    self.optimizer.zero_grad(set_to_none=True)
                                    continue
                                
                            except Exception as e:
                                logger.error(f"Error during gradient clipping: {e}", exc_info=True)
                                self.scaler.update()
                                self.optimizer.zero_grad(set_to_none=True)
                                continue
                            
                            # Optimizer step
                            self.scaler.step(self.optimizer)
                            self.scaler.update()
                            
                            # Update EMA if enabled
                            if self.cfg.ema_enabled:
                                self._update_ema()
                            
                            # Zero gradients efficiently
                            self.optimizer.zero_grad(set_to_none=True)
                            
                            # Update learning rate scheduler
                            self.lr_scheduler.step()
                            
                            global_step += 1
                            step_count += 1

                        running_loss += loss.detach().item()
                        # Rough tokens/sec using attention_mask or input length
                        if "attention_mask" in batch:
                            tokens_accum += int(batch["attention_mask"].sum().item())
                        elif "input_ids" in batch:
                            tokens_accum += int(batch["input_ids"].numel())

                        if profiler:
                            profiler.step()

                        if global_step and global_step % self.cfg.log_interval == 0:
                            avg_loss = running_loss / max(1, step_count)
                            elapsed = max(1e-6, time.perf_counter() - epoch_start)
                            tps = tokens_accum / elapsed if tokens_accum > 0 else 0.0
                            current_lr = self.lr_scheduler.get_last_lr()[0]
                            
                            self.training_logger.log_step(
                                step=global_step,
                                epoch=epoch + 1,
                                loss=avg_loss,
                                learning_rate=current_lr,
                                tokens_per_sec=tps
                            )
                            
                            for cb in self.callbacks:
                                try:
                                    cb.on_log({
                                        "step": global_step,
                                        "loss": avg_loss,
                                        "tokens_per_sec": tps,
                                        "learning_rate": current_lr
                                    })
                                except Exception as e:
                                    logger.debug(f"Callback error: {e}")
                            
                            running_loss = 0.0
                            tokens_accum = 0
                            step_count = 0
                            epoch_start = time.perf_counter()

                        if global_step and global_step % self.cfg.eval_interval == 0:
                            val_loss = self.evaluate()
                            ppl = math.exp(min(20.0, max(-20.0, val_loss))) if val_loss == val_loss else float("inf")
                            metric_value = ppl if self.cfg.select_best_by == "ppl" else val_loss
                            improved = metric_value < (best_metric if self.cfg.select_best_by == "ppl" else best_val)
                            
                            self.training_logger.log_eval(
                                step=global_step,
                                val_loss=val_loss,
                                perplexity=ppl,
                                improved=improved
                            )
                            
                            if improved:
                                best_val = val_loss
                                best_metric = metric_value
                                bad_epochs = 0
                                self._save_checkpoint("best.pt")
                                self.training_logger.log_checkpoint(global_step, "best.pt", is_best=True)
                            else:
                                bad_epochs += 1
                                if bad_epochs >= self.cfg.early_stopping_patience:
                                    logger.info("Early stopping triggered")
                                    self._save_checkpoint("last.pt")
                                    return
                            
                            for cb in self.callbacks:
                                try:
                                    cb.on_eval({
                                        "step": global_step,
                                        "val_loss": val_loss,
                                        "perplexity": ppl,
                                        "improved": improved
                                    })
                                except Exception as e:
                                    logger.debug(f"Callback error: {e}")

                        if global_step and (global_step % max(1, self.cfg.ckpt_interval_steps) == 0):
                            self._save_checkpoint(f"step_{global_step}.pt")
                            self._prune_checkpoints()

                    except Exception as e:
                        logger.error(f"Error in training step {step}: {e}", exc_info=True)
                        # Continue training after error
                        self.optimizer.zero_grad(set_to_none=True)
                        continue

            self._save_checkpoint("last.pt")
            logger.info("Training completed successfully")
            
        except KeyboardInterrupt:
            logger.warning("Training interrupted by user")
            self._save_checkpoint("last.pt")
            raise
        except Exception as e:
            logger.error(f"Training error: {e}", exc_info=True)
            self._save_checkpoint("last.pt")
            raise
        finally:
            if profiler:
                profiler.stop()

    @torch.no_grad()
    def evaluate(self) -> float:
        """Evaluate model on validation set with proper error handling."""
        if self.cfg.ema_enabled and self._ema_shadow is not None:
            self._apply_ema()
        
        self.model.eval()
        total, count = 0.0, 0
        
        try:
            for batch in self.val_loader:
                try:
                    batch = {k: v.to(self.device, non_blocking=True) for k, v in batch.items()}
                    with autocast(enabled=self._use_amp(), dtype=self._amp_dtype()):
                        outputs = self.model(**batch)
                        loss = outputs.loss
                        # Handle DataParallel
                        if isinstance(loss, dict):
                            loss = loss.get("loss", list(loss.values())[0])
                        elif hasattr(loss, "mean"):
                            loss = loss.mean()
                    
                    if torch.isfinite(loss):
                        total += float(loss.detach().item())
                        count += 1
                    else:
                        logger.warning(f"Non-finite loss encountered during evaluation: {loss.item()}")
                except Exception as e:
                    logger.error(f"Error in evaluation batch: {e}", exc_info=True)
                    continue
        finally:
            self.model.train()
            if self.cfg.ema_enabled and self._ema_shadow is not None:
                self._restore_from_ema()
        
        if count == 0:
            logger.warning("No valid evaluation samples processed")
            return float("inf")
        
        avg_loss = total / count
        logger.debug(f"Evaluation completed: avg_loss={avg_loss:.4f}, samples={count}")
        return avg_loss

    def _save_checkpoint(self, filename: str) -> None:
        """Save model checkpoint with improved error handling."""
        try:
            path = os.path.join(self.cfg.output_dir, filename)
            os.makedirs(path, exist_ok=True)
            
            # Handle DataParallel
            to_save = self.model
            if self._is_parallel:
                to_save = self.model.module
            elif hasattr(self.model, "module"):
                to_save = self.model.module
            
            to_save.save_pretrained(path, safe_serialization=bool(self.cfg.save_safetensors))
            self.tokenizer.save_pretrained(path)
            
            # Save additional training state for resuming
            checkpoint_state = {
                "model_state_dict": to_save.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "scheduler_state_dict": self.lr_scheduler.state_dict(),
                "scaler_state_dict": self.scaler.state_dict(),
            }
            torch.save(checkpoint_state, os.path.join(path, "training_state.pt"))
            
            logger.debug(f"Checkpoint saved to {path}")
            for cb in self.callbacks:
                try:
                    cb.on_save({"path": path})
                except Exception as e:
                    logger.debug(f"Callback error on save: {e}")
        except Exception as e:
            logger.error(f"Error saving checkpoint {filename}: {e}", exc_info=True)
            raise

    # EMA utilities
    def _get_model_for_ema(self):
        """Get the base model for EMA operations (handle DataParallel)."""
        return self.model.module if self._is_parallel else self.model
    
    def _init_ema(self) -> None:
        """Initialize Exponential Moving Average shadow parameters."""
        self._ema_shadow = {}
        model = self._get_model_for_ema()
        for n, p in model.named_parameters():
            if p.requires_grad:
                self._ema_shadow[n] = p.detach().clone().to(device=p.device)

    @torch.no_grad()
    def _update_ema(self) -> None:
        """Update EMA shadow parameters."""
        if self._ema_shadow is None:
            return
        d = self.cfg.ema_decay
        model = self._get_model_for_ema()
        for n, p in model.named_parameters():
            if not p.requires_grad:
                continue
            if n in self._ema_shadow:
                self._ema_shadow[n].mul_(d).add_(p.detach(), alpha=1.0 - d)

    def _apply_ema(self) -> None:
        """Apply EMA shadow parameters to model."""
        if self._ema_shadow is None:
            return
        self._ema_backup = {}
        model = self._get_model_for_ema()
        for n, p in model.named_parameters():
            if n in self._ema_shadow and p.requires_grad:
                self._ema_backup[n] = p.detach().clone()
                p.data.copy_(self._ema_shadow[n].data)

    def _restore_from_ema(self) -> None:
        """Restore model parameters from EMA backup."""
        if not self._ema_backup:
            return
        model = self._get_model_for_ema()
        for n, p in model.named_parameters():
            if n in self._ema_backup and p.requires_grad:
                p.data.copy_(self._ema_backup[n].data)
        self._ema_backup = {}

    def _prune_checkpoints(self) -> None:
        try:
            files = [f for f in os.listdir(self.cfg.output_dir) if f.startswith("step_") and f.endswith(".pt")]
            files.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))
            excess = max(0, len(files) - max(0, self.cfg.ckpt_keep_last))
            for i in range(excess):
                try:
                    os.remove(os.path.join(self.cfg.output_dir, files[i]))
                except Exception:
                    pass
        except Exception:
            pass

    @torch.no_grad()
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 64,
        temperature: float = 0.8,
        top_p: float = 0.95,
        top_k: int = 50,
        repetition_penalty: float = 1.1
    ) -> str:
        """
        Generate text from prompt with improved error handling.
        
        Args:
            prompt: Input text prompt
            max_new_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            repetition_penalty: Repetition penalty factor
        
        Returns:
            Generated text
        """
        try:
            # Validate inputs
            if not prompt or not isinstance(prompt, str):
                raise ValueError("Prompt must be a non-empty string")
            if temperature <= 0:
                raise ValueError("Temperature must be positive")
            if max_new_tokens <= 0:
                raise ValueError("max_new_tokens must be positive")
            
            self.model.eval()
            
            # Handle DataParallel for generation
            model_for_gen = self.model.module if self._is_parallel else self.model
            
            prev_use_cache = None
            if hasattr(model_for_gen, "config"):
                prev_use_cache = getattr(model_for_gen.config, "use_cache", None)
                try:
                    model_for_gen.config.use_cache = True
                except Exception:
                    pass
            
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            with autocast(enabled=self._use_amp(), dtype=self._amp_dtype()):
                output_ids = model_for_gen.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=True,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    repetition_penalty=repetition_penalty,
                    pad_token_id=self.tokenizer.eos_token_id,
                )
            
            text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
            
            # Restore use_cache setting
            if prev_use_cache is not None:
                try:
                    model_for_gen.config.use_cache = prev_use_cache
                except Exception:
                    pass
            
            self.model.train()
            return text
            
        except Exception as e:
            logger.error(f"Error during generation: {e}", exc_info=True)
            self.model.train()
            raise
