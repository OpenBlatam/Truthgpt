"""
Modern TruthGPT Optimizer
Following deep learning best practices for LLM optimization
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.cuda.amp import autocast, GradScaler
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoTokenizer, AutoModel, AutoConfig,
    get_linear_schedule_with_warmup,
    AdamW, get_cosine_schedule_with_warmup
)
from typing import Dict, Any, Optional, List, Tuple, Union
import logging
import math
import numpy as np
from pathlib import Path
import json
import time
from dataclasses import dataclass
from contextlib import contextmanager
import wandb
from tqdm import tqdm


@dataclass
class TruthGPTConfig:
    """Configuration for TruthGPT optimization"""
    # Model parameters
    model_name: str = "microsoft/DialoGPT-medium"
    max_length: int = 2048
    hidden_size: int = 768
    num_attention_heads: int = 12
    num_layers: int = 12
    vocab_size: int = 50257
    
    # Training parameters
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    batch_size: int = 32
    gradient_accumulation_steps: int = 4
    num_epochs: int = 100
    warmup_steps: int = 1000
    max_grad_norm: float = 1.0
    
    # Optimization techniques
    use_mixed_precision: bool = True
    use_gradient_checkpointing: bool = True
    use_flash_attention: bool = True
    use_lora: bool = False
    lora_rank: int = 16
    lora_alpha: int = 32
    
    # Hardware
    device: str = "auto"
    num_workers: int = 4
    pin_memory: bool = True
    
    # Logging and checkpointing
    log_interval: int = 100
    save_interval: int = 1000
    checkpoint_dir: str = "./checkpoints"
    experiment_name: str = "truthgpt_optimization"
    
    def __post_init__(self):
        """Auto-detect device and create directories"""
        if self.device == "auto":
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"
        
        Path(self.checkpoint_dir).mkdir(parents=True, exist_ok=True)


class TruthGPTDataset(Dataset):
    """Dataset class for TruthGPT training data"""
    
    def __init__(self, texts: List[str], tokenizer, max_length: int = 2048):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        
        # Tokenize text
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': encoding['input_ids'].squeeze()
        }


class LoRALayer(nn.Module):
    """LoRA (Low-Rank Adaptation) layer for efficient fine-tuning"""
    
    def __init__(self, in_features: int, out_features: int, rank: int = 16, alpha: int = 32):
        super().__init__()
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        
        self.lora_A = nn.Linear(in_features, rank, bias=False)
        self.lora_B = nn.Linear(rank, out_features, bias=False)
        
        # Initialize weights
        nn.init.kaiming_uniform_(self.lora_A.weight)
        nn.init.zeros_(self.lora_B.weight)
    
    def forward(self, x):
        return self.lora_B(self.lora_A(x)) * self.scaling


class ModernTruthGPTOptimizer(nn.Module):
    """
    Modern TruthGPT optimizer following deep learning best practices
    """
    
    def __init__(self, config: TruthGPTConfig):
        super().__init__()
        self.config = config
        self.device = torch.device(config.device)
        self.scaler = GradScaler() if config.use_mixed_precision else None
        
        # Initialize logging
        self.logger = self._setup_logging()
        
        # Initialize model and tokenizer
        self._initialize_model()
        
        # Setup optimizations
        self._setup_optimizations()
        
        # Training state
        self.current_epoch = 0
        self.global_step = 0
        self.best_loss = float('inf')
        
        # Move to device
        self.to(self.device)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("ModernTruthGPTOptimizer")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_model(self):
        """Initialize transformer model and tokenizer"""
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            self.model = AutoModel.from_pretrained(
                self.config.model_name,
                torch_dtype=torch.float16 if self.config.use_mixed_precision else torch.float32
            )
            
            # Apply LoRA if enabled
            if self.config.use_lora:
                self._apply_lora()
            
            # Move to device
            self.model.to(self.device)
            
            self.logger.info(f"Initialized model: {self.config.model_name}")
            
        except Exception as e:
            self.logger.error(f"Error initializing model: {e}")
            raise
    
    def _apply_lora(self):
        """Apply LoRA to model layers"""
        for name, module in self.model.named_modules():
            if isinstance(module, nn.Linear) and 'attention' in name:
                # Replace with LoRA layer
                lora_layer = LoRALayer(
                    module.in_features,
                    module.out_features,
                    rank=self.config.lora_rank,
                    alpha=self.config.lora_alpha
                )
                setattr(self.model, name, lora_layer)
    
    def _setup_optimizations(self):
        """Setup various optimizations"""
        # Enable gradient checkpointing
        if self.config.use_gradient_checkpointing and hasattr(self.model, 'gradient_checkpointing_enable'):
            self.model.gradient_checkpointing_enable()
        
        # Setup flash attention if available
        if self.config.use_flash_attention:
            self._setup_flash_attention()
    
    def _setup_flash_attention(self):
        """Setup flash attention optimization"""
        try:
            # Check if flash attention is available
            if hasattr(F, 'scaled_dot_product_attention'):
                self.use_flash_attention = True
                self.logger.info("Flash attention enabled")
            else:
                self.use_flash_attention = False
                self.logger.warning("Flash attention not available")
        except Exception as e:
            self.logger.error(f"Error setting up flash attention: {e}")
            self.use_flash_attention = False
    
    def forward(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None,
                labels: Optional[torch.Tensor] = None, **kwargs) -> Dict[str, torch.Tensor]:
        """
        Forward pass with optimizations
        
        Args:
            input_ids: Tokenized input sequences
            attention_mask: Attention mask for padding
            labels: Target labels for training
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with model outputs
        """
        try:
            # Prepare inputs
            model_inputs = {
                'input_ids': input_ids,
                'attention_mask': attention_mask,
                'return_dict': True
            }
            
            # Forward pass with mixed precision
            if self.config.use_mixed_precision:
                with autocast():
                    outputs = self.model(**model_inputs)
            else:
                outputs = self.model(**model_inputs)
            
            # Compute loss if labels provided
            loss = None
            if labels is not None:
                # Shift logits and labels for language modeling
                shift_logits = outputs.last_hidden_state[..., :-1, :].contiguous()
                shift_labels = labels[..., 1:].contiguous()
                
                # Flatten for loss computation
                shift_logits = shift_logits.view(-1, shift_logits.size(-1))
                shift_labels = shift_labels.view(-1)
                
                # Compute cross-entropy loss
                loss = F.cross_entropy(shift_logits, shift_labels, ignore_index=-100)
            
            return {
                'logits': outputs.last_hidden_state,
                'loss': loss,
                'hidden_states': outputs.hidden_states,
                'attentions': outputs.attentions
            }
            
        except Exception as e:
            self.logger.error(f"Error in forward pass: {e}")
            raise
    
    def compute_loss(self, outputs: Dict[str, torch.Tensor], targets: torch.Tensor) -> torch.Tensor:
        """Compute loss from model outputs"""
        if outputs['loss'] is not None:
            return outputs['loss']
        
        # Fallback loss computation
        logits = outputs['logits']
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = targets[..., 1:].contiguous()
        
        shift_logits = shift_logits.view(-1, shift_logits.size(-1))
        shift_labels = shift_labels.view(-1)
        
        return F.cross_entropy(shift_logits, shift_labels, ignore_index=-100)
    
    def train_epoch(self, dataloader: DataLoader, optimizer: torch.optim.Optimizer,
                   scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None) -> Dict[str, float]:
        """
        Train for one epoch with proper error handling
        
        Args:
            dataloader: PyTorch DataLoader
            optimizer: PyTorch optimizer
            scheduler: Learning rate scheduler
            
        Returns:
            Dictionary with epoch metrics
        """
        self.train()
        epoch_metrics = {'loss': 0.0, 'learning_rate': 0.0}
        num_batches = len(dataloader)
        
        self.logger.info(f"Starting epoch {self.current_epoch}")
        
        try:
            progress_bar = tqdm(dataloader, desc=f"Epoch {self.current_epoch}")
            
            for batch_idx, batch in enumerate(progress_bar):
                # Move batch to device
                batch = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v 
                        for k, v in batch.items()}
                
                # Forward pass
                if self.config.use_mixed_precision:
                    with autocast():
                        outputs = self.forward(**batch)
                        loss = self.compute_loss(outputs, batch.get('labels'))
                else:
                    outputs = self.forward(**batch)
                    loss = self.compute_loss(outputs, batch.get('labels'))
                
                # Scale loss for gradient accumulation
                loss = loss / self.config.gradient_accumulation_steps
                
                # Backward pass
                if self.scaler is not None:
                    self.scaler.scale(loss).backward()
                else:
                    loss.backward()
                
                # Gradient accumulation
                if (self.global_step + 1) % self.config.gradient_accumulation_steps == 0:
                    # Gradient clipping
                    if self.scaler is not None:
                        self.scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(self.parameters(), self.config.max_grad_norm)
                    
                    # Optimizer step
                    if self.scaler is not None:
                        self.scaler.step(optimizer)
                        self.scaler.update()
                    else:
                        optimizer.step()
                    
                    optimizer.zero_grad()
                    
                    # Update scheduler
                    if scheduler is not None:
                        scheduler.step()
                
                # Update metrics
                epoch_metrics['loss'] += loss.item() * self.config.gradient_accumulation_steps
                epoch_metrics['learning_rate'] = optimizer.param_groups[0]['lr']
                
                # Update progress bar
                progress_bar.set_postfix({
                    'loss': f"{loss.item():.4f}",
                    'lr': f"{optimizer.param_groups[0]['lr']:.2e}"
                })
                
                # Logging
                if batch_idx % self.config.log_interval == 0:
                    self.logger.info(
                        f"Epoch {self.current_epoch}, Batch {batch_idx}/{num_batches}, "
                        f"Loss: {loss.item():.4f}, LR: {optimizer.param_groups[0]['lr']:.2e}"
                    )
                
                # Checkpointing
                if self.global_step % self.config.save_interval == 0:
                    self.save_checkpoint(optimizer, scheduler)
                
                self.global_step += 1
            
            # Average metrics
            for key in epoch_metrics:
                epoch_metrics[key] /= num_batches
            
            self.current_epoch += 1
            return epoch_metrics
            
        except Exception as e:
            self.logger.error(f"Error during training epoch: {e}")
            raise
    
    def validate(self, dataloader: DataLoader) -> Dict[str, float]:
        """Validate model with proper evaluation mode"""
        self.eval()
        val_metrics = {'loss': 0.0}
        
        with torch.no_grad():
            for batch in tqdm(dataloader, desc="Validation"):
                batch = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v 
                        for k, v in batch.items()}
                
                if self.config.use_mixed_precision:
                    with autocast():
                        outputs = self.forward(**batch)
                        loss = self.compute_loss(outputs, batch.get('labels'))
                else:
                    outputs = self.forward(**batch)
                    loss = self.compute_loss(outputs, batch.get('labels'))
                
                val_metrics['loss'] += loss.item()
        
        # Average validation metrics
        for key in val_metrics:
            val_metrics[key] /= len(dataloader)
        
        return val_metrics
    
    def generate(self, input_text: str, max_length: int = 100, 
                 temperature: float = 1.0, top_p: float = 0.9,
                 do_sample: bool = True, **kwargs) -> str:
        """
        Generate text using the model
        
        Args:
            input_text: Input text for generation
            max_length: Maximum generation length
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            do_sample: Whether to use sampling
            
        Returns:
            Generated text
        """
        self.eval()
        
        # Tokenize input
        input_ids = self.tokenizer.encode(input_text, return_tensors='pt').to(self.device)
        
        with torch.no_grad():
            generated = input_ids.clone()
            
            for _ in range(max_length):
                # Get model outputs
                outputs = self.forward(generated, **kwargs)
                logits = outputs['logits'][:, -1, :] / temperature
                
                # Apply top-p filtering
                if top_p < 1.0:
                    sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                    
                    # Remove tokens with cumulative probability above the threshold
                    sorted_indices_to_remove = cumulative_probs > top_p
                    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                    sorted_indices_to_remove[..., 0] = 0
                    
                    indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
                    logits[indices_to_remove] = float('-inf')
                
                # Sample next token
                if do_sample:
                    probs = F.softmax(logits, dim=-1)
                    next_token = torch.multinomial(probs, num_samples=1)
                else:
                    next_token = torch.argmax(logits, dim=-1, keepdim=True)
                
                # Append to generated sequence
                generated = torch.cat([generated, next_token], dim=-1)
                
                # Check for EOS token
                if next_token.item() == self.tokenizer.eos_token_id:
                    break
            
            # Decode generated text
            generated_text = self.tokenizer.decode(generated[0], skip_special_tokens=True)
            return generated_text
    
    def get_optimizer(self) -> torch.optim.Optimizer:
        """Get optimized optimizer for training"""
        return AdamW(
            self.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
            betas=(0.9, 0.999),
            eps=1e-8
        )
    
    def get_scheduler(self, optimizer: torch.optim.Optimizer, 
                     num_training_steps: int) -> torch.optim.lr_scheduler._LRScheduler:
        """Get learning rate scheduler with warmup"""
        return get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=self.config.warmup_steps,
            num_training_steps=num_training_steps
        )
    
    def save_checkpoint(self, optimizer: torch.optim.Optimizer, 
                       scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None,
                       is_best: bool = False):
        """Save model checkpoint"""
        try:
            checkpoint = {
                'epoch': self.current_epoch,
                'global_step': self.global_step,
                'model_state_dict': self.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'config': self.config,
                'best_loss': self.best_loss
            }
            
            if scheduler is not None:
                checkpoint['scheduler_state_dict'] = scheduler.state_dict()
            
            if self.scaler is not None:
                checkpoint['scaler_state_dict'] = self.scaler.state_dict()
            
            # Save regular checkpoint
            checkpoint_path = Path(self.config.checkpoint_dir) / f"checkpoint_step_{self.global_step}.pt"
            torch.save(checkpoint, checkpoint_path)
            
            # Save best model
            if is_best:
                best_path = Path(self.config.checkpoint_dir) / "best_model.pt"
                torch.save(checkpoint, best_path)
                self.logger.info(f"New best model saved at step {self.global_step}")
            
        except Exception as e:
            self.logger.error(f"Error saving checkpoint: {e}")
    
    def load_checkpoint(self, checkpoint_path: Union[str, Path], 
                       optimizer: Optional[torch.optim.Optimizer] = None,
                       scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None):
        """Load model checkpoint"""
        try:
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            
            self.load_state_dict(checkpoint['model_state_dict'])
            self.current_epoch = checkpoint.get('epoch', 0)
            self.global_step = checkpoint.get('global_step', 0)
            self.best_loss = checkpoint.get('best_loss', float('inf'))
            
            if optimizer is not None and 'optimizer_state_dict' in checkpoint:
                optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            
            if scheduler is not None and 'scheduler_state_dict' in checkpoint:
                scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
            
            if self.scaler is not None and 'scaler_state_dict' in checkpoint:
                self.scaler.load_state_dict(checkpoint['scaler_state_dict'])
            
            self.logger.info(f"Checkpoint loaded from {checkpoint_path}")
            
        except Exception as e:
            self.logger.error(f"Error loading checkpoint: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        
        return {
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'model_size_mb': total_params * 4 / (1024 * 1024),
            'device': str(self.device),
            'current_epoch': self.current_epoch,
            'global_step': self.global_step,
            'best_loss': self.best_loss,
            'config': self.config
        }


