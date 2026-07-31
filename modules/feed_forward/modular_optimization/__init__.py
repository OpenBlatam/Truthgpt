"""
Modular Performance Optimization System
Specialized modules for performance optimization, memory management, and computational efficiency.
"""

from .base_optimizer import BaseOptimizer, OptimizerConfig, OptimizationResult, OptimizationType
from .memory_optimizer import MemoryOptimizer, MemoryOptimizerConfig

try:
    from .computational_optimizer import ComputationalOptimizer, ComputationalOptimizerConfig
except ImportError:
    ComputationalOptimizer, ComputationalOptimizerConfig = None, None

try:
    from .quantization_optimizer import QuantizationOptimizer, QuantizationOptimizerConfig
except ImportError:
    QuantizationOptimizer, QuantizationOptimizerConfig = None, None

try:
    from .pruning_optimizer import PruningOptimizer, PruningOptimizerConfig
except ImportError:
    PruningOptimizer, PruningOptimizerConfig = None, None

try:
    from .distillation_optimizer import DistillationOptimizer, DistillationOptimizerConfig
except ImportError:
    DistillationOptimizer, DistillationOptimizerConfig = None, None

try:
    from .parallel_optimizer import ParallelOptimizer, ParallelOptimizerConfig
except ImportError:
    ParallelOptimizer, ParallelOptimizerConfig = None, None

try:
    from .cache_optimizer import CacheOptimizer, CacheOptimizerConfig
except ImportError:
    CacheOptimizer, CacheOptimizerConfig = None, None

try:
    from .hardware_optimizer import HardwareOptimizer, HardwareOptimizerConfig
except ImportError:
    HardwareOptimizer, HardwareOptimizerConfig = None, None

try:
    from .optimization_scheduler import OptimizationScheduler, OptimizationSchedulerConfig
except ImportError:
    OptimizationScheduler, OptimizationSchedulerConfig = None, None

try:
    from .optimization_factory import OptimizationFactory, create_optimizer, create_optimization_suite
except ImportError:
    OptimizationFactory, create_optimizer, create_optimization_suite = None, None, None

try:
    from .optimization_registry import OptimizationRegistry, register_optimizer, get_optimizer
except ImportError:
    OptimizationRegistry, register_optimizer, get_optimizer = None, None, None

__all__ = [
    # Base Optimizer
    'BaseOptimizer',
    'OptimizerConfig',
    'OptimizationResult',
    'OptimizationType',
    
    # Specialized Optimizers
    'MemoryOptimizer',
    'MemoryOptimizerConfig',
    'ComputationalOptimizer',
    'ComputationalOptimizerConfig',
    'QuantizationOptimizer',
    'QuantizationOptimizerConfig',
    'PruningOptimizer',
    'PruningOptimizerConfig',
    'DistillationOptimizer',
    'DistillationOptimizerConfig',
    'ParallelOptimizer',
    'ParallelOptimizerConfig',
    'CacheOptimizer',
    'CacheOptimizerConfig',
    'HardwareOptimizer',
    'HardwareOptimizerConfig',
    
    # Optimization Management
    'OptimizationScheduler',
    'OptimizationSchedulerConfig',
    
    # Factory and Registry
    'OptimizationFactory',
    'create_optimizer',
    'create_optimization_suite',
    'OptimizationRegistry',
    'register_optimizer',
    'get_optimizer'
]




