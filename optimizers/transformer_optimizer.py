"""
Transformer-specific optimization techniques for LLMs
Following best practices for transformer optimization
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.cuda.amp import autocast
from transformers import (
    AutoTokenizer, AutoModel, AutoConfig,
    get_linear_schedule_with_warmup,
    AdamW
)
from typing import Dict, Any, Optional, List, Tuple
import math
import logging
from .pytorch_optimizer_base import PyTorchOptimizerBase, OptimizationConfig


class TransformerOptimizer(PyTorchOptimizerBase):
    """
    Advanced transformer optimizer with LLM-specific techniques
    """
    
    def __init__(self, config: OptimizationConfig, model_name: str = "microsoft/DialoGPT-medium"):
        super().__init__(config)
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.attention_cache = {}
        
        # Initialize model and tokenizer
        self._initialize_model()
        
        # Transformer-specific optimizations
        self._setup_transformer_optimizations()
    
    def _initialize_model(self):
        """Initialize transformer model and tokenizer"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model = AutoModel.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.config.use_mixed_precision else torch.float32
            )
            
            # Move to device
            self.model.to(self.device)
            
            self.logger.info(f"Initialized model: {self.model_name}")
            
        except Exception as e:
            self.logger.error(f"Error initializing model: {e}")
            raise
    
    def _setup_transformer_optimizations(self):
        """Setup transformer-specific optimizations"""
        # Enable gradient checkpointing for memory efficiency
        if hasattr(self.model, 'gradient_checkpointing_enable'):
            self.model.gradient_checkpointing_enable()
        
        # Setup attention optimizations
        self._setup_attention_optimizations()
        
        # Setup memory optimizations
        self._setup_memory_optimizations()
    
    def _setup_attention_optimizations(self):
        """Setup attention mechanism optimizations"""
        # Flash Attention if available
        if hasattr(F, 'scaled_dot_product_attention'):
            self.use_flash_attention = True
        else:
            self.use_flash_attention = False
        
        # Attention caching for inference
        self.attention_cache = {}
    
    def _setup_memory_optimizations(self):
        """Setup memory optimization techniques"""
        # Enable memory efficient attention
        if hasattr(torch.backends.cuda, 'enable_flash_sdp'):
            torch.backends.cuda.enable_flash_sdp(True)
        
        # Setup gradient accumulation
        self.gradient_accumulation_steps = self.config.gradient_accumulation_steps
    
    def forward(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None, 
                labels: Optional[torch.Tensor] = None, **kwargs) -> Dict[str, torch.Tensor]:
        """
        Forward pass with transformer optimizations
        
        Args:
            input_ids: Tokenized input sequences
            attention_mask: Attention mask for padding
            labels: Target labels for training
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with model outputs
        """
        outputs = {}
        
        try:
            # Prepare inputs
            model_inputs = {
                'input_ids': input_ids,
                'attention_mask': attention_mask,
                'return_dict': True
            }
            
            # Add past_key_values for generation
            if 'past_key_values' in kwargs:
                model_inputs['past_key_values'] = kwargs['past_key_values']
            
            # Forward pass with optimizations
            if self.config.use_mixed_precision:
                with autocast():
                    model_outputs = self.model(**model_inputs)
            else:
                model_outputs = self.model(**model_inputs)
            
            # Extract outputs
            outputs['logits'] = model_outputs.last_hidden_state
            outputs['hidden_states'] = model_outputs.hidden_states
            outputs['attentions'] = model_outputs.attentions
            
            # Add past key values for generation
            if hasattr(model_outputs, 'past_key_values'):
                outputs['past_key_values'] = model_outputs.past_key_values
            
            return outputs
            
        except Exception as e:
            self.logger.error(f"Error in forward pass: {e}")
            raise
    
    def compute_loss(self, outputs: Dict[str, torch.Tensor], targets: torch.Tensor) -> torch.Tensor:
        """
        Compute loss with proper handling for transformer models
        
        Args:
            outputs: Model outputs dictionary
            targets: Target tokens
            
        Returns:
            Computed loss tensor
        """
        try:
            logits = outputs['logits']
            
            # Shift logits and targets for language modeling
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = targets[..., 1:].contiguous()
            
            # Flatten for loss computation
            shift_logits = shift_logits.view(-1, shift_logits.size(-1))
            shift_labels = shift_labels.view(-1)
            
            # Compute cross-entropy loss
            loss = F.cross_entropy(shift_logits, shift_labels, ignore_index=-100)
            
            return loss
            
        except Exception as e:
            self.logger.error(f"Error computing loss: {e}")
            raise
    
    def generate(self, input_ids: torch.Tensor, max_length: int = 100, 
                 temperature: float = 1.0, top_p: float = 0.9, 
                 do_sample: bool = True, **kwargs) -> torch.Tensor:
        """
        Generate text using the transformer model
        
        Args:
            input_ids: Input token IDs
            max_length: Maximum generation length
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            do_sample: Whether to use sampling
            
        Returns:
            Generated token IDs
        """
        self.eval()
        
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
            
            return generated
    
    def get_optimizer(self) -> torch.optim.Optimizer:
        """Get optimized optimizer for transformer training"""
        # Use AdamW with proper weight decay
        optimizer = AdamW(
            self.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
            betas=(0.9, 0.999),
            eps=1e-8
        )
        
        return optimizer
    
    def get_scheduler(self, optimizer: torch.optim.Optimizer, 
                     num_training_steps: int) -> torch.optim.lr_scheduler._LRScheduler:
        """Get learning rate scheduler with warmup"""
        return get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=self.config.warmup_steps,
            num_training_steps=num_training_steps
        )
    
    def apply_gradient_accumulation(self, loss: torch.Tensor, optimizer: torch.optim.Optimizer):
        """Apply gradient accumulation for large models"""
        loss = loss / self.gradient_accumulation_steps
        
        if self.config.use_mixed_precision and self.scaler is not None:
            self.scaler.scale(loss).backward()
        else:
            loss.backward()
        
        if (self.global_step + 1) % self.gradient_accumulation_steps == 0:
            if self.config.use_gradient_clipping:
                if self.scaler is not None:
                    self.scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(self.parameters(), self.config.max_grad_norm)
            
            if self.scaler is not None:
                self.scaler.step(optimizer)
                self.scaler.update()
            else:
                optimizer.step()
            
            optimizer.zero_grad()
    
    def optimize_attention_patterns(self, attention_weights: torch.Tensor) -> torch.Tensor:
        """Optimize attention patterns for better performance"""
        # Apply attention dropout
        if self.training:
            attention_weights = F.dropout(attention_weights, p=0.1, training=True)
        
        # Apply attention scaling
        attention_weights = attention_weights / math.sqrt(attention_weights.size(-1))
        
        return attention_weights
    
    def get_attention_visualization(self, input_ids: torch.Tensor, 
                                  layer_idx: int = -1) -> torch.Tensor:
        """Get attention weights for visualization"""
        self.eval()
        
        with torch.no_grad():
            outputs = self.forward(input_ids)
            
            if 'attentions' in outputs and outputs['attentions'] is not None:
                attention_weights = outputs['attentions'][layer_idx]
                return attention_weights.mean(dim=1)  # Average over heads
        
        return None
    
    def apply_quantization(self, quantization_type: str = "int8"):
        """Apply model quantization for inference optimization"""
        if quantization_type == "int8":
            # Apply dynamic quantization
            self.model = torch.quantization.quantize_dynamic(
                self.model, {nn.Linear}, dtype=torch.qint8
            )
        elif quantization_type == "fp16":
            # Apply half precision
            self.model = self.model.half()
        
        self.logger.info(f"Applied {quantization_type} quantization")
    
    def get_model_efficiency_metrics(self) -> Dict[str, float]:
        """Get model efficiency metrics"""
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        
        # Memory usage estimation
        model_size_mb = total_params * 4 / (1024 * 1024)  # Assuming float32
        
        return {
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'model_size_mb': model_size_mb,
            'efficiency_ratio': trainable_params / total_params,
            'memory_efficiency': 1.0 - (trainable_params / total_params)
        }


