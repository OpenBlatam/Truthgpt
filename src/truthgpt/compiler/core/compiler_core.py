"""
Core Compiler Infrastructure for TruthGPT
Base compiler classes and interfaces
"""

import enum
import hashlib
import logging
import time
from typing import Dict, List, Optional, Any, Union, Callable, Type
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

logger = logging.getLogger(__name__)

class CompilationTarget(enum.Enum):
    """Target platforms for compilation"""
    CPU = "cpu"
    GPU = "gpu"
    TPU = "tpu"
    NEURAL_ENGINE = "neural_engine"
    QUANTUM = "quantum"
    HETEROGENEOUS = "heterogeneous"

class OptimizationLevel(enum.Enum):
    """Optimization levels for compilation"""
    NONE = 0
    BASIC = 1
    STANDARD = 2
    AGGRESSIVE = 3
    EXTREME = 4
    QUANTUM = 5

def coerce_enum(val: Any, enum_cls: type) -> Any:
    """Coerce a value (string, int, or enum instance) to an enum instance of enum_cls.
    
    If coercion fails or value is None, returns the original value.
    """
    if val is None or isinstance(val, enum_cls):
        return val
    if isinstance(val, str):
        val_clean = val.strip()
        # Try lookup by name uppercase
        try:
            return enum_cls[val_clean.upper()]
        except (KeyError, AttributeError):
            pass
        # Try lookup by value lowercased
        try:
            return enum_cls(val_clean.lower())
        except (ValueError, TypeError):
            pass
        # Try direct value match
        try:
            return enum_cls(val_clean)
        except (ValueError, TypeError):
            pass
    elif isinstance(val, int):
        try:
            return enum_cls(val)
        except (ValueError, TypeError):
            pass
    return val


coerce_enum_field = coerce_enum


@dataclass
class CompilationConfig:
    """Configuration for compilation process"""
    target: CompilationTarget = CompilationTarget.CPU
    optimization_level: OptimizationLevel = OptimizationLevel.STANDARD
    enable_quantization: bool = False
    enable_fusion: bool = True
    enable_parallelization: bool = True
    memory_limit: Optional[int] = None
    timeout: Optional[float] = None
    debug_mode: bool = False
    custom_flags: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if type(self) is CompilationConfig:
            self.target = coerce_enum(self.target, CompilationTarget)
            self.optimization_level = coerce_enum(self.optimization_level, OptimizationLevel)

def resolve_config(config: Any, config_cls: type) -> Any:
    """Helper to resolve a config argument (None, dict, or instance) to a config dataclass instance."""
    if config is None:
        return config_cls()
    if isinstance(config, dict):
        return config_cls(**config)
    return config

@dataclass
class CompilationResult:
    """Result of compilation process"""
    success: bool
    compiled_model: Optional[Any] = None
    compilation_time: float = 0.0
    memory_usage: float = 0.0
    optimization_metrics: Dict[str, float] = None
    warnings: List[str] = None
    errors: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.optimization_metrics is None:
            self.optimization_metrics = {}
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}

class CompilationError(Exception):
    """Base exception raised during compilation"""
    pass

class CompilerConfigError(CompilationError):
    """Exception raised for invalid compiler configurations"""
    pass

class ModelValidationError(CompilationError):
    """Exception raised when model validation fails"""
    pass

class CompilationTargetError(CompilationError):
    """Exception raised for invalid or unsupported compilation targets"""
    pass

class CompilationTimeoutError(CompilationError):
    """Exception raised when compilation times out"""
    pass

class OptimizationError(CompilationError):
    """Exception raised during optimization pass failures"""
    pass

class PluginError(CompilationError):
    """Exception raised for compiler plugin errors"""
    pass

class KernelCompilationError(CompilationError):
    """Exception raised for kernel compilation errors"""
    pass

class DistributedCompilationError(CompilationError):
    """Exception raised during distributed compilation errors"""
    pass


class CompilationContext:
    """Context manager for compilation process.

    On exit, ``elapsed`` (seconds) and ``memory_used`` (bytes) are stored as
    instance attributes so that callers can reference them after the ``with``
    block completes.
    """

    def __init__(self, config: CompilationConfig):
        self.config = config
        self.start_time: Optional[float] = None
        self.memory_start: Optional[int] = None
        self.elapsed: float = 0.0
        self.memory_used: int = 0

    def __enter__(self):
        self.start_time = time.time()
        if _HAS_PSUTIL:
            self.memory_start = psutil.Process().memory_info().rss
        else:
            self.memory_start = 0
        logger.info(f"Starting compilation with target: {self.config.target}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            self.elapsed = time.time() - self.start_time
            if _HAS_PSUTIL and self.memory_start is not None:
                self.memory_used = psutil.Process().memory_info().rss - self.memory_start
            else:
                self.memory_used = 0
            logger.info(
                f"Compilation completed in {self.elapsed:.2f}s, "
                f"memory used: {self.memory_used / 1024 / 1024:.2f}MB"
            )

class CompilerCore(ABC):
    """Base class for all compiler implementations"""

    _DEFAULT_PROFILE: Dict[str, Any] = {
        "execution_count": 0,
        "total_time": 0.0,
        "last_execution": 0.0,
        "optimization_level": 0,
    }

    def __init__(self, config: CompilationConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def compile(self, model: Any, input_spec: Optional[Dict] = None) -> CompilationResult:
        """Compile a model for the target platform"""
        pass

    @abstractmethod
    def optimize(self, model: Any, optimization_passes: List[str] = None) -> CompilationResult:
        """Apply optimizations to a model"""
        pass

    def validate_input(self, model: Any) -> bool:
        """Validate input model"""
        if model is None:
            raise CompilationError("Model cannot be None")
        return True

    def get_compilation_info(self) -> Dict[str, Any]:
        """Get information about the compiler"""
        return {
            "compiler_type": self.__class__.__name__,
            "target": self.config.target.value,
            "optimization_level": self.config.optimization_level.value,
            "quantization_enabled": self.config.enable_quantization,
            "fusion_enabled": self.config.enable_fusion
        }

    @staticmethod
    def generate_cache_key(model: Any, config: Any, input_spec: Optional[Dict] = None) -> str:
        """Generate a deterministic cache key for a model/config/input_spec triple."""
        model_str = str(id(model))
        config_str = str(config.__dict__) if hasattr(config, '__dict__') else str(config)
        input_str = str(input_spec) if input_spec else ""
        combined = f"{model_str}_{config_str}_{input_str}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def get_or_create_profile(
        self,
        profiles: Dict[int, Dict[str, Any]],
        model: Any,
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Return the execution profile for *model*, creating one if absent."""
        model_id = id(model)
        if model_id not in profiles:
            profile = dict(self._DEFAULT_PROFILE)
            if extra_fields:
                profile.update(extra_fields)
            profiles[model_id] = profile
        return profiles[model_id]

class TruthGPTCompilerCore(CompilerCore):
    """Specialized compiler core for TruthGPT models"""
    
    def __init__(self, config: CompilationConfig):
        super().__init__(config)
        self.truthgpt_optimizations = self._initialize_truthgpt_optimizations()
        
    def _initialize_truthgpt_optimizations(self) -> Dict[str, Callable]:
        """Initialize TruthGPT-specific optimizations"""
        return {
            "attention_fusion": self._optimize_attention_fusion,
            "mlp_fusion": self._optimize_mlp_fusion,
            "quantization": self._optimize_quantization,
            "memory_optimization": self._optimize_memory,
            "parallel_processing": self._optimize_parallel_processing
        }
    
    def compile(self, model: Any, input_spec: Optional[Dict] = None) -> CompilationResult:
        """Compile TruthGPT model with specialized optimizations"""
        try:
            self.validate_input(model)
            
            with CompilationContext(self.config) as ctx:
                optimized_model = self._apply_truthgpt_optimizations(model)
                compiled_model = self._compile_for_target(optimized_model)
                
                return CompilationResult(
                    success=True,
                    compiled_model=compiled_model,
                    compilation_time=ctx.elapsed,
                    optimization_metrics=self._get_optimization_metrics(),
                    metadata=self.get_compilation_info()
                )
                
        except Exception as e:
            self.logger.error(f"Compilation failed: {str(e)}")
            return CompilationResult(
                success=False,
                errors=[str(e)]
            )
    
    def optimize(self, model: Any, optimization_passes: List[str] = None) -> CompilationResult:
        """Apply specific optimizations to TruthGPT model"""
        if optimization_passes is None:
            optimization_passes = list(self.truthgpt_optimizations.keys())
            
        try:
            optimized_model = model
            for pass_name in optimization_passes:
                if pass_name in self.truthgpt_optimizations:
                    optimized_model = self.truthgpt_optimizations[pass_name](optimized_model)
                    
            return CompilationResult(
                success=True,
                compiled_model=optimized_model,
                optimization_metrics=self._get_optimization_metrics()
            )
            
        except Exception as e:
            self.logger.error(f"Optimization failed: {str(e)}")
            return CompilationResult(
                success=False,
                errors=[str(e)]
            )
    
    def _apply_truthgpt_optimizations(self, model: Any) -> Any:
        """Apply all TruthGPT optimizations"""
        optimized_model = model
        
        for opt_name, opt_func in self.truthgpt_optimizations.items():
            if self._should_apply_optimization(opt_name):
                optimized_model = opt_func(optimized_model)
                
        return optimized_model
    
    def _should_apply_optimization(self, opt_name: str) -> bool:
        """Determine if optimization should be applied based on config"""
        if opt_name == "quantization":
            return self.config.enable_quantization
        elif opt_name in ["attention_fusion", "mlp_fusion"]:
            return self.config.enable_fusion
        elif opt_name == "parallel_processing":
            return self.config.enable_parallelization
        return True
    
    def _optimize_attention_fusion(self, model: Any) -> Any:
        self.logger.info("Applying attention fusion optimization")
        return model
    
    def _optimize_mlp_fusion(self, model: Any) -> Any:
        self.logger.info("Applying MLP fusion optimization")
        return model
    
    def _optimize_quantization(self, model: Any) -> Any:
        self.logger.info("Applying quantization optimization")
        return model
    
    def _optimize_memory(self, model: Any) -> Any:
        self.logger.info("Applying memory optimization")
        return model
    
    def _optimize_parallel_processing(self, model: Any) -> Any:
        self.logger.info("Applying parallel processing optimization")
        return model
    
    def _compile_for_target(self, model: Any) -> Any:
        if self.config.target == CompilationTarget.GPU:
            return self._compile_for_gpu(model)
        elif self.config.target == CompilationTarget.CPU:
            return self._compile_for_cpu(model)
        elif self.config.target == CompilationTarget.TPU:
            return self._compile_for_tpu(model)
        else:
            return model
    
    def _compile_for_gpu(self, model: Any) -> Any:
        self.logger.info("Compiling for GPU execution")
        return model
    
    def _compile_for_cpu(self, model: Any) -> Any:
        self.logger.info("Compiling for CPU execution")
        return model
    
    def _compile_for_tpu(self, model: Any) -> Any:
        self.logger.info("Compiling for TPU execution")
        return model
    
    def _get_optimization_metrics(self) -> Dict[str, float]:
        return {
            "optimization_level": self.config.optimization_level.value,
            "quantization_enabled": float(self.config.enable_quantization),
            "fusion_enabled": float(self.config.enable_fusion),
            "parallelization_enabled": float(self.config.enable_parallelization)
        }

def create_compiler_core(config: Optional[Union[CompilationConfig, dict]] = None) -> CompilerCore:
    """Create a compiler core instance."""
    if config is None:
        config = CompilationConfig()
    elif isinstance(config, dict):
        config = CompilationConfig(**config)
    return TruthGPTCompilerCore(config)

def compilation_context(config: Optional[Union[CompilationConfig, dict]] = None) -> CompilationContext:
    """Create a compilation context."""
    if config is None:
        config = CompilationConfig()
    elif isinstance(config, dict):
        config = CompilationConfig(**config)
    return CompilationContext(config)

def make_factory(config_cls: Type, compiler_cls: Type) -> Callable:
    """Generate a standard create_* factory function for a compiler."""
    def factory(config=None):
        resolved = resolve_config(config, config_cls)
        return compiler_cls(resolved)
    factory.__doc__ = f"Create a {compiler_cls.__name__} instance."
    return factory

def make_context_factory(config_cls: Type) -> Callable:
    """Generate a standard *_compilation_context factory function."""
    def context_factory(config=None):
        resolved = resolve_config(config, config_cls)
        return CompilationContext(resolved)
    context_factory.__doc__ = f"Create a CompilationContext for {config_cls.__name__}."
    return context_factory
