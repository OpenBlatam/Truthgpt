import torch
import torch.nn as nn
import torch.cuda.amp as amp
from torch.optim.lr_scheduler import ReduceLROnPlateau
import time
from typing import Dict, List, Any

from .base import OptimizationConfig
from .factory import setup_optimizer
from .schedulers import setup_scheduler

class AdvancedOptimizer:
    """Advanced optimizer with cutting-edge features"""
    def __init__(self, config: OptimizationConfig, model: nn.Module):
        self.config, self.model = config, model
        self.optimizer = setup_optimizer(model, config)
        self.scheduler = setup_scheduler(self.optimizer, config)
        self.scaler = amp.GradScaler() if config.use_mixed_precision else None
        self.metrics, self.optimization_history = {}, []

    def optimize(self, loss: torch.Tensor) -> Dict[str, Any]:
        self.optimizer.zero_grad()
        if self.scaler: self.scaler.scale(loss).backward()
        else: loss.backward()
        if self.config.use_gradient_clipping:
            if self.scaler: self.scaler.unscale_(self.optimizer)
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.gradient_clip_norm)
        if self.scaler:
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else: self.optimizer.step()
        if self.scheduler:
            if isinstance(self.scheduler, ReduceLROnPlateau): self.scheduler.step(loss.item())
            else: self.scheduler.step()
        self.metrics.update({"loss": loss.item(), "learning_rate": self.optimizer.param_groups[0]["lr"]})
        self.optimization_history.append({"loss": loss.item(), "learning_rate": self.optimizer.param_groups[0]["lr"], "timestamp": time.time()})
        return self.metrics

    def get_learning_rate(self) -> float: return self.optimizer.param_groups[0]["lr"]
    def set_learning_rate(self, lr: float):
        for pg in self.optimizer.param_groups: pg["lr"] = lr
    def get_optimization_history(self) -> List[Dict[str, Any]]: return self.optimization_history

    def save_optimizer_state(self, path: str):
        torch.save({"optimizer_state_dict": self.optimizer.state_dict(), "scheduler_state_dict": self.scheduler.state_dict() if self.scheduler else None, "scaler_state_dict": self.scaler.state_dict() if self.scaler else None, "config": self.config}, path)

    def load_optimizer_state(self, path: str):
        ckpt = torch.load(path, map_location="cpu")
        self.optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        if ckpt["scheduler_state_dict"] and self.scheduler: self.scheduler.load_state_dict(ckpt["scheduler_state_dict"])
        if ckpt["scaler_state_dict"] and self.scaler: self.scaler.load_state_dict(ckpt["scaler_state_dict"])
