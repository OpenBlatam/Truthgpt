"""
PyTorch-based Optimization Framework
Following deep learning best practices for LLM optimization
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import autocast, GradScaler
from torch.utils.data import DataLoader
import logging
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
import numpy as np
from pathlib import Path
import json
import time
from contextlib import contextmanager


@dataclass
class OptimizationConfig:
    """Configuration class for optimization parameters"""
    # Model parameters
    model_name: str = "truthgpt"
    max_sequence_length: int = 2048
    hidden_size: int = 768
    num_attention_heads: int = 12
    num_layers: int = 12
    
    # Training parameters
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    batch_size: int = 32
    num_epochs: int = 100
    gradient_accumulation_steps: int = 1
    
    # Optimization parameters
    use_mixed_precision: bool = True
    use_gradient_clipping: bool = True
    max_grad_norm: float = 1.0
    warmup_steps: int = 1000
    
    # Hardware parameters
    device: str = "auto"  # auto, cpu, cuda, mps
    num_workers: int = 4
    pin_memory: bool = True
    
    # Logging and checkpointing
    log_interval: int = 100
    save_interval: int = 1000
    checkpoint_dir: str = "./checkpoints"
    experiment_name: str = "truthgpt_optimization"
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Create checkpoint directory
        Path(self.checkpoint_dir).mkdir(parents=True, exist_ok=True)


class PyTorchOptimizerBase(nn.Module):
    """
    Base class for PyTorch-based optimizers following deep learning best practices
    """
    
    def __init__(self, config: OptimizationConfig):
        super().__init__()
        self.config = config
        self.device = torch.device(config.device)
        self.scaler = GradScaler() if config.use_mixed_precision else None
        
        # Initialize logging
        self.logger = self._setup_logging()
        
        # Training state
        self.current_epoch = 0
        self.global_step = 0
        self.best_loss = float('inf')
        
        # Move to device
        self.to(self.device)
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(f"{self.__class__.__name__}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @contextmanager
    def training_context(self):
        """Context manager for training with proper setup"""
        self.train()
        try:
            yield
        finally:
            pass
    
    def forward(self, *args, **kwargs):
        """Forward pass - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement forward method")
    
    def compute_loss(self, outputs: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """Compute loss - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement compute_loss method")
    
    def optimize_step(self, batch: Dict[str, torch.Tensor], optimizer: optim.Optimizer) -> Dict[str, float]:
        """
        Single optimization step with mixed precision and gradient clipping
        
        Args:
            batch: Input batch dictionary
            optimizer: PyTorch optimizer
            
        Returns:
            Dictionary with loss and metrics
        """
        metrics = {}
        
        with self.training_context():
            if self.config.use_mixed_precision and self.scaler is not None:
                with autocast():
                    outputs = self.forward(**batch)
                    loss = self.compute_loss(outputs, batch.get('targets', outputs))
            else:
                outputs = self.forward(**batch)
                loss = self.compute_loss(outputs, batch.get('targets', outputs))
            
            # Scale loss for gradient accumulation
            loss = loss / self.config.gradient_accumulation_steps
            
            # Backward pass
            if self.config.use_mixed_precision and self.scaler is not None:
                self.scaler.scale(loss).backward()
            else:
                loss.backward()
            
            # Gradient accumulation
            if (self.global_step + 1) % self.config.gradient_accumulation_steps == 0:
                # Gradient clipping
                if self.config.use_gradient_clipping:
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
            
            metrics['loss'] = loss.item() * self.config.gradient_accumulation_steps
            metrics['learning_rate'] = optimizer.param_groups[0]['lr']
            
        return metrics
    
    def train_epoch(self, dataloader: DataLoader, optimizer: optim.Optimizer) -> Dict[str, float]:
        """
        Train for one epoch with proper error handling and logging
        
        Args:
            dataloader: PyTorch DataLoader
            optimizer: PyTorch optimizer
            
        Returns:
            Dictionary with epoch metrics
        """
        epoch_metrics = {'loss': 0.0, 'learning_rate': 0.0}
        num_batches = len(dataloader)
        
        self.logger.info(f"Starting epoch {self.current_epoch}")
        
        try:
            for batch_idx, batch in enumerate(dataloader):
                # Move batch to device
                batch = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v 
                        for k, v in batch.items()}
                
                # Optimization step
                step_metrics = self.optimize_step(batch, optimizer)
                
                # Update metrics
                for key, value in step_metrics.items():
                    epoch_metrics[key] += value
                
                # Logging
                if batch_idx % self.config.log_interval == 0:
                    self.logger.info(
                        f"Epoch {self.current_epoch}, Batch {batch_idx}/{num_batches}, "
                        f"Loss: {step_metrics['loss']:.4f}, "
                        f"LR: {step_metrics['learning_rate']:.2e}"
                    )
                
                # Checkpointing
                if self.global_step % self.config.save_interval == 0:
                    self.save_checkpoint(optimizer)
                
                self.global_step += 1
            
            # Average metrics
            for key in epoch_metrics:
                epoch_metrics[key] /= num_batches
            
            self.current_epoch += 1
            return epoch_metrics
            
        except Exception as e:
            self.logger.error(f"Error during training epoch: {e}")
            raise
    
    def save_checkpoint(self, optimizer: optim.Optimizer, is_best: bool = False):
        """Save model checkpoint with proper error handling"""
        try:
            checkpoint = {
                'epoch': self.current_epoch,
                'global_step': self.global_step,
                'model_state_dict': self.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'config': self.config,
                'best_loss': self.best_loss
            }
            
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
    
    def load_checkpoint(self, checkpoint_path: Union[str, Path], optimizer: Optional[optim.Optimizer] = None):
        """Load model checkpoint with proper error handling"""
        try:
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            
            self.load_state_dict(checkpoint['model_state_dict'])
            self.current_epoch = checkpoint.get('epoch', 0)
            self.global_step = checkpoint.get('global_step', 0)
            self.best_loss = checkpoint.get('best_loss', float('inf'))
            
            if optimizer is not None and 'optimizer_state_dict' in checkpoint:
                optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            
            if self.scaler is not None and 'scaler_state_dict' in checkpoint:
                self.scaler.load_state_dict(checkpoint['scaler_state_dict'])
            
            self.logger.info(f"Checkpoint loaded from {checkpoint_path}")
            
        except Exception as e:
            self.logger.error(f"Error loading checkpoint: {e}")
            raise
    
    def get_learning_rate_schedule(self, optimizer: optim.Optimizer) -> optim.lr_scheduler._LRScheduler:
        """Get learning rate scheduler with warmup"""
        def lr_lambda(step):
            if step < self.config.warmup_steps:
                return step / self.config.warmup_steps
            else:
                return 1.0
        
        return optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    
    def validate(self, dataloader: DataLoader) -> Dict[str, float]:
        """Validate model with proper evaluation mode"""
        self.eval()
        val_metrics = {'loss': 0.0}
        
        with torch.no_grad():
            for batch in dataloader:
                batch = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v 
                        for k, v in batch.items()}
                
                if self.config.use_mixed_precision:
                    with autocast():
                        outputs = self.forward(**batch)
                        loss = self.compute_loss(outputs, batch.get('targets', outputs))
                else:
                    outputs = self.forward(**batch)
                    loss = self.compute_loss(outputs, batch.get('targets', outputs))
                
                val_metrics['loss'] += loss.item()
        
        # Average validation metrics
        for key in val_metrics:
            val_metrics[key] /= len(dataloader)
        
        return val_metrics
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information for debugging and monitoring"""
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        
        return {
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'model_size_mb': total_params * 4 / (1024 * 1024),  # Assuming float32
            'device': str(self.device),
            'current_epoch': self.current_epoch,
            'global_step': self.global_step,
            'best_loss': self.best_loss
        }


