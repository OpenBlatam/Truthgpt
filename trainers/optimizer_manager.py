"""
Optimizer Manager - Handles optimizer and scheduler setup.

Separated from trainer for better modularity.
"""
import logging
from typing import Optional
import torch
from torch.optim import Optimizer
from torch.cuda.amp import GradScaler

from transformers import (
    get_cosine_schedule_with_warmup,
    get_linear_schedule_with_warmup,
)

from trainers.config import TrainingConfig
from factories.optimizer import OPTIMIZERS

logger = logging.getLogger(__name__)


class OptimizerManager:
    """
    Manages optimizer and learning rate scheduler.
    
    Responsibilities:
    - Create optimizer via registry
    - Setup learning rate scheduler
    - Manage gradient scaler for mixed precision
    """
    
    def __init__(
        self,
        training_config: TrainingConfig,
        model: torch.nn.Module,
        use_amp: bool,
    ):
        """
        Initialize OptimizerManager.
        
        Args:
            training_config: Training configuration
            model: Model to optimize
            use_amp: Whether to use automatic mixed precision
        """
        self.training_config = training_config
        self.model = model
        self.use_amp = use_amp
        self.optimizer: Optional[Optimizer] = None
        self.scheduler: Optional[object] = None
        self.scaler: Optional[GradScaler] = None
    
    def create_optimizer(self, optimizer_type: str = "adamw") -> Optimizer:
        """
        Create optimizer.
        
        Args:
            optimizer_type: Type of optimizer (adamw|lion|adafactor)
            
        Returns:
            Optimizer instance
        """
        try:
            optimizer = OPTIMIZERS.build(
                optimizer_type,
                self.model.parameters(),
                lr=self.training_config.learning_rate,
                weight_decay=self.training_config.weight_decay,
                fused=True,  # Use fused if available
            )
            logger.info(f"Created {optimizer_type} optimizer")
            self.optimizer = optimizer
            return optimizer
        except Exception as e:
            logger.warning(f"Failed to create optimizer via registry: {e}. Using fallback AdamW.")
            # Fallback to standard AdamW
            optimizer = torch.optim.AdamW(
                self.model.parameters(),
                lr=self.training_config.learning_rate,
                weight_decay=self.training_config.weight_decay,
            )
            self.optimizer = optimizer
            return optimizer
    
    def create_scheduler(self, num_training_steps: int) -> object:
        """
        Create learning rate scheduler.
        
        Args:
            num_training_steps: Total number of training steps
            
        Returns:
            Scheduler instance
        """
        if self.optimizer is None:
            raise RuntimeError("Must create optimizer before scheduler")
        
        num_warmup_steps = int(self.training_config.warmup_ratio * num_training_steps)
        
        if self.training_config.scheduler == "cosine":
            scheduler = get_cosine_schedule_with_warmup(
                self.optimizer,
                num_warmup_steps=num_warmup_steps,
                num_training_steps=num_training_steps,
            )
        elif self.training_config.scheduler == "linear":
            scheduler = get_linear_schedule_with_warmup(
                self.optimizer,
                num_warmup_steps=num_warmup_steps,
                num_training_steps=num_training_steps,
            )
        else:
            logger.warning(f"Unknown scheduler type: {self.training_config.scheduler}. Using cosine.")
            scheduler = get_cosine_schedule_with_warmup(
                self.optimizer,
                num_warmup_steps=num_warmup_steps,
                num_training_steps=num_training_steps,
            )
        
        logger.info(f"Created {self.training_config.scheduler} scheduler with {num_warmup_steps} warmup steps")
        self.scheduler = scheduler
        return scheduler
    
    def create_scaler(self) -> GradScaler:
        """
        Create gradient scaler for mixed precision training.
        
        Returns:
            GradScaler instance
        """
        scaler = GradScaler(
            enabled=self.use_amp,
            init_scale=2.**16,
            growth_factor=2.0,
            backoff_factor=0.5,
            growth_interval=2000,
        )
        self.scaler = scaler
        return scaler
    
    def step(self, scale_loss: bool = True) -> None:
        """
        Perform optimizer step.
        
        Args:
            scale_loss: Whether to scale loss (for mixed precision)
        """
        if self.optimizer is None:
            raise RuntimeError("Optimizer not created")
        
        if scale_loss and self.scaler is not None:
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            self.optimizer.step()
    
    def scheduler_step(self) -> None:
        """Step learning rate scheduler."""
        if self.scheduler is None:
            raise RuntimeError("Scheduler not created")
        self.scheduler.step()
    
    def zero_grad(self, set_to_none: bool = True) -> None:
        """
        Zero gradients.
        
        Args:
            set_to_none: Set gradients to None instead of zero (more efficient)
        """
        if self.optimizer is None:
            raise RuntimeError("Optimizer not created")
        self.optimizer.zero_grad(set_to_none=set_to_none)
    
    def get_lr(self) -> float:
        """Get current learning rate."""
        if self.optimizer is None:
            return 0.0
        return self.optimizer.param_groups[0]['lr']



