from .base import OptimizerType, SchedulerType, OptimizationStrategy, OptimizationConfig
from .engine import AdvancedOptimizer
from .factory import setup_optimizer
from .schedulers import setup_scheduler

def create_optimizer(config: OptimizationConfig, model: nn.Module) -> AdvancedOptimizer:
    return AdvancedOptimizer(config, model)

def create_optimization_config(**kwargs) -> OptimizationConfig:
    return OptimizationConfig(**kwargs)

__all__ = [
    'OptimizerType',
    'SchedulerType',
    'OptimizationStrategy',
    'OptimizationConfig',
    'AdvancedOptimizer',
    'setup_optimizer',
    'setup_scheduler',
    'create_optimizer',
    'create_optimization_config'
]
