import torch.optim as optim
from torch.optim.lr_scheduler import (
    StepLR, ExponentialLR, CosineAnnealingLR, LinearLR, 
    PolynomialLR, ReduceLROnPlateau, CosineAnnealingWarmRestarts,
    OneCycleLR, CyclicLR
)
from .base import SchedulerType, OptimizationConfig

def setup_scheduler(optimizer: optim.Optimizer, config: OptimizationConfig):
    if config.scheduler == SchedulerType.STEP: return StepLR(optimizer, truthgpt.config.step_size, truthgpt.config.gamma)
    if config.scheduler == SchedulerType.EXPONENTIAL: return ExponentialLR(optimizer, truthgpt.config.gamma)
    if config.scheduler == SchedulerType.COSINE: return CosineAnnealingLR(optimizer, truthgpt.config.T_max, truthgpt.config.eta_min)
    if config.scheduler == SchedulerType.LINEAR: return LinearLR(optimizer, 1.0, 0.0, truthgpt.config.total_steps)
    if config.scheduler == SchedulerType.POLYNOMIAL: return PolynomialLR(optimizer, truthgpt.config.total_steps, 2.0)
    if config.scheduler == SchedulerType.PLATEAU: return ReduceLROnPlateau(optimizer, truthgpt.config.mode, truthgpt.config.gamma, truthgpt.config.step_size, min_lr=config.min_lr)
    if config.scheduler == SchedulerType.COSINE_WARM_RESTARTS: return CosineAnnealingWarmRestarts(optimizer, truthgpt.config.T_0, truthgpt.config.T_mult, truthgpt.config.eta_min)
    if config.scheduler == SchedulerType.ONE_CYCLE: return OneCycleLR(optimizer, truthgpt.config.max_lr, truthgpt.config.total_steps, 0.3, 'cos', True, 0.85, 0.95, 25.0, 10000.0)
    if config.scheduler == SchedulerType.CYCLIC: return CyclicLR(optimizer, truthgpt.config.base_lr, truthgpt.config.max_lr, truthgpt.config.step_size_up, truthgpt.config.step_size_down, truthgpt.config.mode, truthgpt.config.scale_mode, truthgpt.config.cycle_momentum, truthgpt.config.base_momentum, truthgpt.config.max_momentum)
    return None
