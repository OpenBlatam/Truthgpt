"""
Enhanced Runtime Compiler for TruthGPT
Advanced runtime compilation with adaptive optimization, neural-guided compilation, and quantum-inspired techniques.
Refactored using SOLID and Clean Architecture principles.
"""

import logging
import time
import queue
import hashlib
from typing import Dict, List, Optional, Any, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import numpy as np
import psutil
import gc

from ..core.compiler_core import CompilerCore, CompilationContext, resolve_config

# Import configurations & enums
from .config import (
    RuntimeTarget,
    RuntimeOptimizationLevel,
    CompilationMode,
    OptimizationTrigger,
    RuntimeOptimizationStrategy,
    RuntimeCompilationConfig,
    RuntimeCompilationResult
)

# Import modular subsystems
from .subsystems.neural import NeuralGuidanceModel, NeuralGuidanceEngine
from .subsystems.quantum import QuantumOptimizationState, QuantumOptimizationEngine
from .subsystems.pipeline import CompilationPipeline, PipelineEngine
from .subsystems.monitoring import RuntimePerformanceMonitor

# Import strategies and generators
from .strategies.registry import OptimizationStrategyRegistry
from .generators.registry import CodeGeneratorRegistry

logger = logging.getLogger(__name__)


class RuntimeCompiler(CompilerCore):
    """
    Enhanced Runtime Compiler for TruthGPT models.
    Refactored orchestrator composing specialized subsystems.
    """

    def __init__(self, config: Union[RuntimeCompilationConfig, dict, None] = None):
        resolved_config = resolve_config(config, RuntimeCompilationConfig)
        super().__init__(resolved_config)
        self.config = resolved_config
        self.execution_profiles: Dict[int, Dict[str, Any]] = {}
        self.compilation_cache: Dict[str, Any] = {}

        # Strategy and Generator registries
        self.strategy_registry = OptimizationStrategyRegistry(config)
        self.code_generator_registry = CodeGeneratorRegistry()

        # Advanced subsystem engines
        self.neural_engine = NeuralGuidanceEngine(
            model_path=config.neural_model_path,
            confidence_threshold=config.neural_guidance_threshold
        ) if config.enable_neural_guidance else None

        self.quantum_engine = QuantumOptimizationEngine(
            simulation_depth=config.quantum_simulation_depth,
            iterations=config.quantum_optimization_iterations
        ) if config.enable_quantum_optimization else None

        self.pipeline_engine = PipelineEngine(
            buffer_size=config.pipeline_buffer_size,
            stages_count=config.pipeline_stages,
            streaming_enabled=config.enable_streaming_compilation
        ) if config.enable_pipeline_compilation else None

        self.performance_monitor = RuntimePerformanceMonitor(
            config=config,
            execution_profiles=self.execution_profiles,
            compilation_cache=self.compilation_cache
        )

        # Threading and async support
        self.compilation_queue = queue.Queue(maxsize=config.pipeline_buffer_size)
        self.result_queue = queue.Queue()
        self.thread_pool = ThreadPoolExecutor(max_workers=config.pipeline_stages)
        self.process_pool = ProcessPoolExecutor(max_workers=2)

        # Start monitoring if profiling enabled
        if config.enable_profiling:
            self.performance_monitor.start_monitoring()

    @property
    def optimization_strategies(self) -> Dict[str, RuntimeOptimizationStrategy]:
        """Backward compatibility property returning metadata strategies dictionary"""
        return self.strategy_registry.metadata_strategies

    @property
    def neural_guidance_model(self) -> Optional[NeuralGuidanceModel]:
        return self.neural_engine.model if self.neural_engine else None

    @property
    def quantum_optimization_state(self) -> Optional[QuantumOptimizationState]:
        return self.quantum_engine.state if self.quantum_engine else None

    @property
    def compilation_pipeline(self) -> Optional[CompilationPipeline]:
        return self.pipeline_engine.pipeline if self.pipeline_engine else None

    @property
    def monitoring_active(self) -> bool:
        return self.performance_monitor.monitoring_active

    @property
    def profiling_data(self):
        return self.performance_monitor.profiling_data

    def compile(self, model: Any, input_spec: Optional[Dict] = None) -> RuntimeCompilationResult:
        """Enhanced compile method with advanced runtime optimizations"""
        try:
            self.validate_input(model)

            model_id = id(model)
            if model_id not in self.execution_profiles:
                self.execution_profiles[model_id] = {
                    "execution_count": 0,
                    "total_time": 0.0,
                    "last_execution": 0.0,
                    "optimization_level": 0,
                    "neural_guidance_score": 0.0,
                    "quantum_optimization_factor": 1.0,
                    "transcendent_level": 0
                }

            profile = self.execution_profiles[model_id]
            profile["execution_count"] += 1
            profile["last_execution"] = time.time()

            if self.config.compilation_mode == CompilationMode.ASYNCHRONOUS:
                return self._compile_asynchronous(model, input_spec, profile)
            elif self.config.compilation_mode == CompilationMode.STREAMING:
                return self._compile_streaming(model, input_spec, profile)
            elif self.config.compilation_mode == CompilationMode.PIPELINE:
                return self._compile_pipeline(model, input_spec, profile)
            else:
                return self._compile_synchronous(model, input_spec, profile)

        except Exception as e:
            logger.error(f"Runtime compilation failed: {str(e)}")
            return RuntimeCompilationResult(
                success=False,
                errors=[str(e)]
            )

    def _compile_synchronous(self, model: Any, input_spec: Optional[Dict] = None, profile: Dict[str, Any] = None) -> RuntimeCompilationResult:
        try:
            if not self._should_compile(profile):
                return RuntimeCompilationResult(
                    success=True,
                    compiled_model=model,
                    execution_count=profile["execution_count"],
                    compilation_trigger="cached",
                    compilation_mode="synchronous"
                )

            cache_key = self._get_cache_key(model, input_spec)
            if cache_key in self.compilation_cache:
                logger.info("Using cached runtime compilation result")
                cached_result = self.compilation_cache[cache_key]
                cached_result.compilation_mode = "synchronous"
                return cached_result

            start_time = time.time()

            # Apply neural guidance
            neural_signals = {}
            if self.neural_engine:
                neural_signals = self.neural_engine.apply_guidance(model, profile, self._estimate_model_size)
                profile["neural_guidance_score"] = neural_signals.get("confidence", 0.0)

            # Apply quantum optimization
            quantum_states = {}
            if self.quantum_engine:
                quantum_states = self.quantum_engine.apply_quantum_optimization(model, profile)
                profile["quantum_optimization_factor"] = quantum_states.get("optimization_factor", 1.0)

            # Apply transcendent optimization
            transcendent_level = 0
            if self.config.enable_transcendent_compilation and self.quantum_engine:
                transcendent_level = self.quantum_engine.apply_transcendent_optimization(model, profile)
                profile["transcendent_level"] = transcendent_level

            # Apply runtime optimizations via strategy registry
            optimized_model = self.strategy_registry.apply_all_enabled(model, profile)

            # Generate runtime code via code generator registry
            compiled_model = self.code_generator_registry.generate(self.config.target, optimized_model, input_spec)

            compilation_time = time.time() - start_time
            memory_efficiency = self.performance_monitor.calculate_memory_efficiency(compiled_model, self._estimate_model_size)
            energy_efficiency = self.performance_monitor.calculate_energy_efficiency(compiled_model, self._estimate_model_size)

            profile["total_time"] += compilation_time
            profile["optimization_level"] = len(self._get_applied_optimizations(profile))

            result = RuntimeCompilationResult(
                success=True,
                compiled_model=compiled_model,
                compilation_time=compilation_time,
                execution_count=profile["execution_count"],
                compilation_trigger="runtime_compilation",
                optimization_applied=self._get_applied_optimizations(profile),
                performance_metrics=self._get_performance_metrics(profile),
                runtime_info=self._get_runtime_info(profile),
                neural_guidance_score=profile["neural_guidance_score"],
                quantum_optimization_factor=profile["quantum_optimization_factor"],
                transcendent_level=transcendent_level,
                memory_efficiency=memory_efficiency,
                energy_efficiency=energy_efficiency,
                compilation_mode="synchronous",
                neural_signals=neural_signals,
                quantum_states=quantum_states
            )

            self.compilation_cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Synchronous compilation failed: {str(e)}")
            return RuntimeCompilationResult(
                success=False,
                errors=[str(e)],
                compilation_mode="synchronous"
            )

    def _compile_asynchronous(self, model: Any, input_spec: Optional[Dict] = None, profile: Dict[str, Any] = None) -> RuntimeCompilationResult:
        try:
            future = self.thread_pool.submit(self._compile_synchronous, model, input_spec, profile)
            result = RuntimeCompilationResult(
                success=True,
                compiled_model=model,
                execution_count=profile["execution_count"],
                compilation_trigger="async_submitted",
                compilation_mode="asynchronous"
            )
            result.async_future = future
            return result
        except Exception as e:
            logger.error(f"Asynchronous compilation failed: {str(e)}")
            return RuntimeCompilationResult(
                success=False,
                errors=[str(e)],
                compilation_mode="asynchronous"
            )

    def _compile_streaming(self, model: Any, input_spec: Optional[Dict] = None, profile: Dict[str, Any] = None) -> RuntimeCompilationResult:
        try:
            compilation_task = {
                "model": model,
                "input_spec": input_spec,
                "profile": profile,
                "timestamp": time.time()
            }
            self.compilation_queue.put(compilation_task)
            return self._process_streaming_compilation(compilation_task)
        except Exception as e:
            logger.error(f"Streaming compilation failed: {str(e)}")
            return RuntimeCompilationResult(
                success=False,
                errors=[str(e)],
                compilation_mode="streaming"
            )

    def _compile_pipeline(self, model: Any, input_spec: Optional[Dict] = None, profile: Dict[str, Any] = None) -> RuntimeCompilationResult:
        try:
            if not self.pipeline_engine:
                return self._compile_synchronous(model, input_spec, profile)

            return self.pipeline_engine.execute_pipeline(
                model=model,
                profile=profile,
                optimization_fn=self.strategy_registry.apply_all_enabled,
                code_gen_fn=lambda m, s: self.code_generator_registry.generate(self.config.target, m, s),
                get_applied_opt_fn=self._get_applied_optimizations,
                get_metrics_fn=self._get_performance_metrics,
                get_info_fn=self._get_runtime_info
            )
        except Exception as e:
            logger.error(f"Pipeline compilation failed: {str(e)}")
            return RuntimeCompilationResult(
                success=False,
                errors=[str(e)],
                compilation_mode="pipeline"
            )

    def _process_streaming_compilation(self, compilation_task: Dict[str, Any]) -> RuntimeCompilationResult:
        if self.pipeline_engine:
            return self.pipeline_engine.process_streaming(
                compilation_task,
                lambda m, p: self.strategy_registry.apply_all_enabled(m, p)
            )
        return self._compile_synchronous(compilation_task["model"], compilation_task["input_spec"], compilation_task["profile"])

    def optimize(self, model: Any, optimization_passes: List[str] = None) -> RuntimeCompilationResult:
        model_id = id(model)
        if model_id not in self.execution_profiles:
            self.execution_profiles[model_id] = {
                "execution_count": 0,
                "total_time": 0.0,
                "last_execution": 0.0,
                "optimization_level": 0
            }

        profile = self.execution_profiles[model_id]
        if optimization_passes is None:
            optimization_passes = [name for name, strategy in self.strategy_registry.metadata_strategies.items() if strategy.enabled]

        try:
            optimized_model = model
            applied_optimizations = []

            for pass_name in optimization_passes:
                if pass_name in self.strategy_registry.metadata_strategies:
                    strategy = self.strategy_registry.metadata_strategies[pass_name]
                    if strategy.enabled:
                        optimized_model = self.strategy_registry.apply_pass(pass_name, optimized_model, profile)
                        applied_optimizations.append(pass_name)

            profile["optimization_level"] = len(applied_optimizations)

            return RuntimeCompilationResult(
                success=True,
                compiled_model=optimized_model,
                execution_count=profile["execution_count"],
                optimization_applied=applied_optimizations,
                performance_metrics=self._get_performance_metrics(profile)
            )
        except Exception as e:
            return RuntimeCompilationResult(
                success=False,
                errors=[str(e)]
            )

    def _should_compile(self, profile: Dict[str, Any]) -> bool:
        if profile["execution_count"] < self.config.compilation_threshold:
            return False
        return True

    def _estimate_model_size(self, model: Any) -> int:
        try:
            if hasattr(model, 'parameters'):
                return sum(p.numel() for p in model.parameters())
            return 100000
        except Exception:
            return 100000

    def _get_applied_optimizations(self, profile: Dict[str, Any]) -> List[str]:
        return [name for name, strategy in self.strategy_registry.metadata_strategies.items() if strategy.enabled]

    def _get_performance_metrics(self, profile: Dict[str, Any]) -> Dict[str, float]:
        return {
            "execution_count": float(profile["execution_count"]),
            "total_time": profile["total_time"],
            "average_time": profile["total_time"] / max(profile["execution_count"], 1),
            "optimization_level": float(profile["optimization_level"])
        }

    def _get_runtime_info(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "execution_count": profile["execution_count"],
            "total_execution_time": profile["total_time"],
            "last_execution": profile["last_execution"],
            "optimization_level": profile["optimization_level"]
        }

    def _get_cache_key(self, model: Any, input_spec: Optional[Dict] = None) -> str:
        """Generate cache key for model — delegates to base class utility."""
        return self.generate_cache_key(model, self.config, input_spec)

    def profile_execution(self, model: Any, execution_time: float):
        model_id = id(model)
        if model_id not in self.execution_profiles:
            self.execution_profiles[model_id] = {
                "execution_count": 0,
                "total_time": 0.0,
                "last_execution": 0.0,
                "optimization_level": 0
            }
        profile = self.execution_profiles[model_id]
        profile["execution_count"] += 1
        profile["total_time"] += execution_time
        profile["last_execution"] = time.time()

    def get_execution_profiles(self) -> Dict[int, Dict[str, Any]]:
        return self.execution_profiles

    def clear_cache(self):
        self.compilation_cache.clear()

    def get_compilation_stats(self) -> Dict[str, Any]:
        return {
            "cached_compilations": len(self.compilation_cache),
            "profiled_models": len(self.execution_profiles),
            "total_executions": sum(profile["execution_count"] for profile in self.execution_profiles.values())
        }

    def cleanup(self):
        try:
            self.performance_monitor.stop_monitoring()
            try:
                self.thread_pool.shutdown(wait=True, cancel_futures=True)
            except TypeError:
                self.thread_pool.shutdown(wait=True)

            try:
                self.process_pool.shutdown(wait=True, cancel_futures=True)
            except TypeError:
                self.process_pool.shutdown(wait=True)

            self.compilation_cache.clear()
            self.execution_profiles.clear()

            while not self.compilation_queue.empty():
                try:
                    self.compilation_queue.get_nowait()
                except queue.Empty:
                    break

            while not self.result_queue.empty():
                try:
                    self.result_queue.get_nowait()
                except queue.Empty:
                    break

            self.neural_engine = None
            self.quantum_engine = None
            self.pipeline_engine = None

            gc.collect()
            logger.info("Enhanced runtime compiler cleanup completed")
        except Exception as e:
            logger.error(f"Runtime compiler cleanup failed: {e}")

    def get_advanced_statistics(self) -> Dict[str, Any]:
        try:
            return {
                "basic_stats": {
                    "execution_profiles": len(self.execution_profiles),
                    "compilation_cache": len(self.compilation_cache),
                    "profiling_data_points": len(self.performance_monitor.profiling_data)
                },
                "advanced_features": {
                    "neural_guidance_enabled": self.neural_engine is not None,
                    "quantum_optimization_enabled": self.quantum_engine is not None,
                    "pipeline_enabled": self.pipeline_engine is not None,
                    "monitoring_active": self.performance_monitor.monitoring_active
                },
                "performance_metrics": {
                    "avg_compilation_time": np.mean([
                        p.get("total_time", 0) / max(1, p.get("execution_count", 1))
                        for p in self.execution_profiles.values()
                    ]) if self.execution_profiles else 0.0,
                    "total_compilations": sum(p.get("execution_count", 0) for p in self.execution_profiles.values()),
                    "cache_hit_rate": len(self.compilation_cache) / max(1, len(self.execution_profiles))
                },
                "system_metrics": {
                    "cpu_usage": psutil.cpu_percent(),
                    "memory_usage": psutil.virtual_memory().percent,
                    "available_memory": psutil.virtual_memory().available
                }
            }
        except Exception as e:
            logger.error(f"Failed to get advanced statistics: {e}")
            return {}


def create_runtime_compiler(config: Optional[Union[RuntimeCompilationConfig, dict]] = None) -> RuntimeCompiler:
    """Create a runtime compiler instance"""
    if config is None:
        config = RuntimeCompilationConfig()
    elif isinstance(config, dict):
        config = RuntimeCompilationConfig(**config)
    return RuntimeCompiler(config)


def runtime_compilation_context(config: Optional[Union[RuntimeCompilationConfig, dict]] = None):
    """Create a runtime compilation context"""
    from ..core.compiler_core import CompilationContext
    if config is None:
        config = RuntimeCompilationConfig()
    elif isinstance(config, dict):
        config = RuntimeCompilationConfig(**config)
    return CompilationContext(config)

