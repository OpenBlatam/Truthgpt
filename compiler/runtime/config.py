"""
Runtime Compiler Configurations and Enums
"""

import enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from ..core.compiler_core import CompilationConfig, CompilationResult

class RuntimeTarget(enum.Enum):
    """Runtime compilation targets"""
    INTERPRETER = "interpreter"
    BYTECODE = "bytecode"
    NATIVE = "native"
    CUDA = "cuda"
    ROCM = "rocm"
    METAL = "metal"

class RuntimeOptimizationLevel(enum.Enum):
    """Runtime optimization levels"""
    NONE = 0
    BASIC = 1
    STANDARD = 2
    AGGRESSIVE = 3
    ADAPTIVE = 4
    NEURAL_GUIDED = 5
    QUANTUM_INSPIRED = 6
    TRANSCENDENT = 7

class CompilationMode(enum.Enum):
    """Runtime compilation modes"""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    STREAMING = "streaming"
    BATCH = "batch"
    PIPELINE = "pipeline"

class OptimizationTrigger(enum.Enum):
    """Optimization trigger conditions"""
    EXECUTION_COUNT = "execution_count"
    PERFORMANCE_THRESHOLD = "performance_threshold"
    MEMORY_PRESSURE = "memory_pressure"
    HOTSPOT_DETECTION = "hotspot_detection"
    NEURAL_SIGNAL = "neural_signal"
    QUANTUM_STATE = "quantum_state"
    TEMPORAL_PATTERN = "temporal_pattern"

@dataclass
class RuntimeOptimizationStrategy:
    """Runtime optimization strategy metadata"""
    name: str
    description: str
    enabled: bool = True
    priority: int = 0
    trigger_condition: Optional[Any] = None
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RuntimeCompilationConfig(CompilationConfig):
    """Enhanced configuration for runtime compilation"""
    target: RuntimeTarget = RuntimeTarget.NATIVE
    optimization_level: RuntimeOptimizationLevel = RuntimeOptimizationLevel.ADAPTIVE
    compilation_mode: CompilationMode = CompilationMode.ASYNCHRONOUS
    
    # Core features
    enable_profiling: bool = True
    enable_hotspot_detection: bool = True
    enable_adaptive_optimization: bool = True
    enable_incremental_compilation: bool = True
    enable_parallel_compilation: bool = True
    enable_speculation: bool = True
    enable_deoptimization: bool = True
    
    # Advanced features
    enable_neural_guidance: bool = True
    enable_quantum_optimization: bool = False
    enable_transcendent_compilation: bool = False
    enable_streaming_compilation: bool = True
    enable_pipeline_compilation: bool = True
    enable_memory_aware_compilation: bool = True
    enable_energy_efficient_compilation: bool = True
    
    # Thresholds and limits
    compilation_threshold: int = 100
    optimization_threshold: int = 1000
    max_compilation_time: float = 0.1
    max_optimization_time: float = 1.0
    cache_size: int = 1000
    memory_limit_mb: int = 1024
    cpu_limit_percent: int = 80
    
    # Sampling and monitoring
    profiling_sample_rate: float = 0.1
    monitoring_interval: float = 1.0
    performance_window_size: int = 100
    
    # Neural guidance
    neural_model_path: Optional[str] = None
    neural_guidance_threshold: float = 0.7
    neural_learning_rate: float = 0.001
    
    # Quantum features
    quantum_simulation_depth: int = 10
    quantum_optimization_iterations: int = 100
    
    # Pipeline settings
    pipeline_stages: int = 4
    pipeline_buffer_size: int = 1000
    enable_pipeline_parallelism: bool = True
    
    # Custom parameters
    custom_parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RuntimeCompilationResult(CompilationResult):
    """Enhanced result of runtime compilation"""
    execution_count: int = 0
    compilation_trigger: str = ""
    optimization_applied: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    runtime_info: Dict[str, Any] = field(default_factory=dict)
    
    # Advanced metrics
    neural_guidance_score: float = 0.0
    quantum_optimization_factor: float = 1.0
    transcendent_level: int = 0
    memory_efficiency: float = 1.0
    energy_efficiency: float = 1.0
    pipeline_throughput: float = 0.0
    streaming_latency: float = 0.0
    
    # Compilation metadata
    compilation_mode: str = "synchronous"
    optimization_triggers: List[str] = field(default_factory=list)
    neural_signals: Dict[str, float] = field(default_factory=dict)
    quantum_states: Dict[str, Any] = field(default_factory=dict)
    temporal_patterns: Dict[str, Any] = field(default_factory=dict)
    async_future: Optional[Any] = None
