"""
Ultra-Optimization System
Maximum performance optimization with zero-copy operations, model compilation, GPU acceleration, and intelligent caching.
"""

from .zero_copy_optimizer import ZeroCopyOptimizer, ZeroCopyConfig
from .model_compiler import ModelCompiler, CompilationConfig, CompilationTarget
from .gpu_accelerator import GPUAccelerator, GPUConfig
from .dynamic_batcher import DynamicBatcher, BatchingConfig

try:
    from .intelligent_cacher import IntelligentCacher, CachingConfig
except Exception:
    IntelligentCacher, CachingConfig = None, None

try:
    from .distributed_optimizer import DistributedOptimizer, DistributedConfig
except Exception:
    DistributedOptimizer, DistributedConfig = None, None

try:
    from .real_time_optimizer import RealTimeOptimizer, RealTimeConfig
except Exception:
    RealTimeOptimizer, RealTimeConfig = None, None

try:
    from .energy_optimizer import EnergyOptimizer, EnergyConfig
except Exception:
    EnergyOptimizer, EnergyConfig = None, None

try:
    from .pipeline_optimizer import PipelineOptimizer, PipelineConfig
except Exception:
    PipelineOptimizer, PipelineConfig = None, None

try:
    from .memory_optimizer import UltraMemoryOptimizer, UltraMemoryConfig
except Exception:
    UltraMemoryOptimizer, UltraMemoryConfig = None, None

try:
    from .optimization_orchestrator import OptimizationOrchestrator, OrchestratorConfig
except Exception:
    OptimizationOrchestrator, OrchestratorConfig = None, None

try:
    from .optimization_factory import UltraOptimizationFactory, create_ultra_optimizer
except Exception:
    UltraOptimizationFactory, create_ultra_optimizer = None, None

try:
    from .optimization_registry import UltraOptimizationRegistry, register_ultra_optimizer, get_ultra_optimizer
except Exception:
    UltraOptimizationRegistry, register_ultra_optimizer, get_ultra_optimizer = None, None, None

__all__ = [
    # Zero-Copy Optimization
    'ZeroCopyOptimizer',
    'ZeroCopyConfig',
    
    # Model Compilation
    'ModelCompiler',
    'CompilationConfig',
    
    # GPU Acceleration
    'GPUAccelerator',
    'GPUConfig',
    
    # Dynamic Batching
    'DynamicBatcher',
    'BatchingConfig',
    
    # Intelligent Caching
    'IntelligentCacher',
    'CachingConfig',
    
    # Distributed Optimization
    'DistributedOptimizer',
    'DistributedConfig',
    
    # Real-Time Optimization
    'RealTimeOptimizer',
    'RealTimeConfig',
    
    # Energy Optimization
    'EnergyOptimizer',
    'EnergyConfig',
    
    # Pipeline Optimization
    'PipelineOptimizer',
    'PipelineConfig',
    
    # Ultra Memory Optimization
    'UltraMemoryOptimizer',
    'UltraMemoryConfig',
    
    # Optimization Orchestration
    'OptimizationOrchestrator',
    'OrchestratorConfig',
    
    # Factory and Registry
    'UltraOptimizationFactory',
    'create_ultra_optimizer',
    'UltraOptimizationRegistry',
    'register_ultra_optimizer',
    'get_ultra_optimizer'
]




