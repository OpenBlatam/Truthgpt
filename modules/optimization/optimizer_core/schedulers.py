import torch.optim as optim
from torch.optim.lr_scheduler import (
    StepLR, ExponentialLR, CosineAnnealingLR, LinearLR, 
    PolynomialLR, ReduceLROnPlateau, CosineAnnealingWarmRestarts,
    OneCycleLR, CyclicLR
)
from .base import SchedulerType, OptimizationConfig

def setup_scheduler(optimizer: optim.Optimizer, config: OptimizationConfig):
    if config.scheduler == SchedulerType.STEP: return StepLR(optimizer, config.step_size, config.gamma)
    if config.scheduler == SchedulerType.EXPONENTIAL: return ExponentialLR(optimizer, config.gamma)
    if config.scheduler == SchedulerType.COSINE: return CosineAnnealingLR(optimizer, config.T_max, config.eta_min)
    if config.scheduler == SchedulerType.LINEAR: return LinearLR(optimizer, 1.0, 0.0, config.total_steps)
    if config.scheduler == SchedulerType.POLYNOMIAL: return PolynomialLR(optimizer, config.total_steps, 2.0)
    if config.scheduler == SchedulerType.PLATEAU: return ReduceLROnPlateau(optimizer, config.mode, config.gamma, config.step_size, min_lr=config.min_lr)
    if config.scheduler == SchedulerType.COSINE_WARM_RESTARTS: return CosineAnnealingWarmRestarts(optimizer, config.T_0, config.T_mult, config.eta_min)
    if config.scheduler == SchedulerType.ONE_CYCLE: return OneCycleLR(optimizer, config.max_lr, config.total_steps, 0.3, 'cos', True, 0.85, 0.95, 25.0, 10000.0)
    if config.scheduler == SchedulerType.CYCLIC: return CyclicLR(optimizer, config.base_lr, config.max_lr, config.step_size_up, config.step_size_down, config.mode, config.scale_mode, config.cycle_momentum, config.base_momentum, config.max_momentum)
    return None
