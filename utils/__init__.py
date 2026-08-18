"""
TruthGPT Optimization Core Utilities
====================================

Unified, modular, enterprise-grade utilities for deep learning optimization,
hardware management, metrics collection, distributed orchestration, and training tools.

Submodules:
- `truthgpt`: TruthGPT-specific optimizers, configuration, and integrated adapters
- `optimizers`: Hyper-speed, quantum, evolutionary, and neural optimization engines
- `systems`: Quantum deep learning, multiverse optimization, and distributed systems
- `training_tools`: Checkpoint visualization, run comparison, monitoring, and cleanup
- `adapters`: ObjectStore, dynamic runtime adapters, and TruthGPT connectors
- `ai`: Autonomous agents, NAS, ML optimizers, and AI reasoning tools
- `enterprise`: Cloud integration, enterprise auth, caching, and enterprise metrics
- `gpu`: CUDA kernels, RMSNorm/LayerNorm kernels, and GPU memory telemetry
- `memory`: Memory pooling, activation caching, and tensor pool optimizers
- `monitoring`: Real-time training telemetry, alerting, and dashboard monitors
- `quantum`: Quantum circuit simulation, VQE, QAOA, and deep learning engines
- `training`: Advanced training utilities, evaluators, and optimization loops
- `modules`: Polyglot compilation, optimization layers, and high-order modules
"""

from __future__ import annotations

import contextlib
import importlib
import logging
import os
import sys
import time
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union

# Version metadata
__version__ = "4.5.0"

# Module Aliasing across namespaces
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.utils":
        sys.modules.setdefault("utils", _mod)
    elif __name__ == "utils":
        sys.modules.setdefault("optimization_core.utils", _mod)

# Submodules registry
_SUBMODULES: Dict[str, str] = {
    'truthgpt': '.truthgpt',
    'optimizers': '.optimizers',
    'systems': '.systems',
    'training_tools': '.training_tools',
    'adapters': '.adapters',
    'ai': '.ai',
    'enterprise': '.enterprise',
    'gpu': '.gpu',
    'memory': '.memory',
    'monitoring': '.monitoring',
    'quantum': '.quantum',
    'training': '.training',
    'modules': '.modules',
    'logging': '.logging',
    'metrics': '.metrics',
}

# Direct imports for training tools to ensure functions take precedence over module names
from .visualize_training import (
    visualize_checkpoints,
    summarize_run,
    plot_loss_curves,
    visualize_memory_profile,
)
from .compare_runs import (
    compare_runs,
    get_run_info,
)
from .cleanup_runs import (
    cleanup_runs,
    cleanup_old_runs,
    cleanup_checkpoints,
)

# Lazy exports mapping (Symbol -> (Relative Module Path, Target Attribute Name))
_LAZY_EXPORTS: Dict[str, Tuple[str, str]] = {
    # Base utilities
    'BaseOptimizationModel': ('.base', 'BaseOptimizationModel'),
    'CudaResourceManager': ('.base', 'CudaResourceManager'),
    'system_metrics_collector': ('.base', 'system_metrics_collector'),
    # Logging (via consolidated logging subpackage)
    'setup_logger': ('.logging.basic', 'setup_logger'),
    'get_logger': ('.logging.basic', 'get_logger'),
    'TrainingLogger': ('.logging.basic', 'TrainingLogger'),
    # Visualization & Training Tools
    'visualize_checkpoints': ('.visualize_training', 'visualize_checkpoints'),
    'summarize_run': ('.visualize_training', 'summarize_run'),
    'plot_loss_curves': ('.visualize_training', 'plot_loss_curves'),
    'visualize_memory_profile': ('.visualize_training', 'visualize_memory_profile'),
    'compare_runs': ('.compare_runs', 'compare_runs'),
    'get_run_info': ('.compare_runs', 'get_run_info'),
    'monitor_training': ('.monitor_training', 'get_gpu_stats'),
    'cleanup_runs': ('.cleanup_runs', 'cleanup_runs'),
    'cleanup_old_runs': ('.cleanup_runs', 'cleanup_old_runs'),
    'cleanup_checkpoints': ('.cleanup_runs', 'cleanup_checkpoints'),
    # TruthGPT Core (via truthgpt subpackage)
    'TruthGPTConfig': ('.truthgpt.core', 'TruthGPTConfig'),
    'create_truthgpt_config': ('.truthgpt.core', 'create_truthgpt_config'),
    'create_truthgpt_optimizer': ('.truthgpt.core', 'create_truthgpt_optimizer'),
    'quick_truthgpt_optimization': ('.truthgpt.core', 'quick_truthgpt_optimization'),
    'truthgpt_optimization_context': ('.truthgpt.core', 'truthgpt_optimization_context'),
    'OptimizationLevel': ('.truthgpt.core', 'OptimizationLevel'),
    'DeviceType': ('.truthgpt.core', 'DeviceType'),
    'PrecisionType': ('.truthgpt.core', 'PrecisionType'),
    'BaseTruthGPTOptimizer': ('.truthgpt.core', 'BaseTruthGPTOptimizer'),
    'TruthGPTDeviceManager': ('.truthgpt.core', 'TruthGPTDeviceManager'),
    'TruthGPTPrecisionManager': ('.truthgpt.core', 'TruthGPTPrecisionManager'),
    'TruthGPTMemoryManager': ('.truthgpt.core', 'TruthGPTMemoryManager'),
    'TruthGPTPerformanceManager': ('.truthgpt.core', 'TruthGPTPerformanceManager'),
    'TruthGPTIntegratedOptimizer': ('.truthgpt.core', 'TruthGPTIntegratedOptimizer'),
    # Memory Optimizations (via memory subpackage)
    'MemoryOptimizer': ('.memory.optimizations', 'MemoryOptimizer'),
    'MemoryOptimizationConfig': ('.memory.optimizations', 'MemoryOptimizationConfig'),
    'create_memory_optimizer': ('.memory.optimizations', 'create_memory_optimizer'),
    'TensorPool': ('.memory.pooling', 'TensorPool'),
    'ActivationCache': ('.memory.pooling', 'ActivationCache'),
    'MemoryUtils': ('.memory.memory_utils', 'MemoryUtils'),
    # GPU & Kernels (via gpu subpackage)
    'GPUUtils': ('.gpu.gpu_utils', 'GPUUtils'),
    'CUDAOptimizations': ('.gpu.cuda_kernels', 'CUDAOptimizations'),
    'OptimizedLayerNorm': ('.gpu.cuda_kernels', 'OptimizedLayerNorm'),
    'OptimizedRMSNorm': ('.gpu.cuda_kernels', 'OptimizedRMSNorm'),
    'EnhancedCUDAOptimizations': ('.gpu.enhanced_cuda_kernels', 'EnhancedCUDAOptimizations'),
    # Performance & Optimizers
    'HyperSpeedOptimizer': ('.hyper_speed_optimizer', 'HyperSpeedOptimizer'),
    'AutoPerformanceOptimizer': ('.auto_performance_optimizer', 'AutoPerformanceOptimizer'),
    'NeuralEvolutionaryOptimizer': ('.neural_evolutionary_optimizer', 'NeuralEvolutionaryOptimizer'),
    'UltraAIOptimizer': ('.ai.ultra_ai_optimizer', 'UltraAIOptimizer'),
    'AIUtils': ('.ai.ai_utils', 'AIUtils'),
    # Enterprise & Cloud (via enterprise subpackage)
    'EnterpriseAuth': ('.enterprise.auth', 'EnterpriseAuth'),
    'EnterpriseCache': ('.enterprise.cache', 'EnterpriseCache'),
    'EnterpriseMonitor': ('.enterprise.monitor', 'EnterpriseMonitor'),
    'EnterpriseMetrics': ('.enterprise.metrics', 'EnterpriseMetrics'),
    'EnterpriseCloudIntegration': ('.enterprise.cloud_integration', 'EnterpriseCloudIntegration'),
    'EnterpriseTruthGPTAdapter': ('.enterprise.truthgpt_adapter', 'EnterpriseTruthGPTAdapter'),
    # Experiment & Metrics
    'ExperimentTracker': ('.experiment_tracker', 'ExperimentTracker'),
}

_import_cache: Dict[str, Any] = {}


# --- Foundational Utility Helpers ---

def format_bytes(size_bytes: Union[int, float]) -> str:
    """Format bytes into a human-readable string (KB, MB, GB, TB)."""
    if size_bytes < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(size_bytes)
    unit_idx = 0
    while size >= 1024.0 and unit_idx < len(units) - 1:
        size /= 1024.0
        unit_idx += 1
    return f"{size:.2f} {units[unit_idx]}"


def get_gpu_info() -> Dict[str, Any]:
    """Retrieve comprehensive GPU hardware and memory information."""
    try:
        from .base import CudaResourceManager
        return CudaResourceManager.get_device_info()
    except Exception:
        return {"device": "cpu", "available": False}


def get_memory_info() -> Dict[str, Any]:
    """Retrieve standardized system and GPU memory metrics."""
    try:
        from .base import system_metrics_collector
        return system_metrics_collector()
    except Exception:
        return {"timestamp": time.time(), "cpu_percent": 0.0, "memory_used_gb": 0.0, "gpu_used_mb": 0.0}


@contextlib.contextmanager
def timed_block(name: str = "Block", logger_fn: Optional[Callable[[str], None]] = None) -> Iterator[Dict[str, float]]:
    """Context manager to measure execution time of a code block."""
    result: Dict[str, float] = {"elapsed_sec": 0.0}
    start = time.perf_counter()
    try:
        yield result
    finally:
        elapsed = time.perf_counter() - start
        result["elapsed_sec"] = elapsed
        if logger_fn:
            logger_fn(f"[{name}] Completed in {elapsed:.4f}s")


def safe_run(fn: Callable[..., Any], *args: Any, default: Any = None, **kwargs: Any) -> Any:
    """Execute a callable safely, returning default on exception."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        logging.getLogger(__name__).warning(f"safe_run encountered exception in {fn}: {e}")
        return default


def benchmark_function(
    fn: Callable[..., Any],
    *args: Any,
    iterations: int = 10,
    warmup: int = 2,
    **kwargs: Any,
) -> Dict[str, float]:
    """Benchmark the execution time of a callable over multiple iterations."""
    for _ in range(warmup):
        fn(*args, **kwargs)

    latencies: List[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn(*args, **kwargs)
        latencies.append(time.perf_counter() - t0)

    avg_sec = sum(latencies) / len(latencies) if latencies else 0.0
    min_sec = min(latencies) if latencies else 0.0
    max_sec = max(latencies) if latencies else 0.0

    return {
        "iterations": float(iterations),
        "avg_ms": round(avg_sec * 1000.0, 3),
        "min_ms": round(min_sec * 1000.0, 3),
        "max_ms": round(max_sec * 1000.0, 3),
        "throughput_per_sec": round(1.0 / avg_sec, 2) if avg_sec > 0 else 0.0,
    }


# --- Dynamic Submodule & Attribute Resolution ---

def __getattr__(name: str) -> Any:
    """Dynamic lazy importer for submodules, components, and helper utilities."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    if name in _import_cache:
        return _import_cache[name]

    # Check registered submodules
    if name in _SUBMODULES:
        module_path = _SUBMODULES[name]
        try:
            module = importlib.import_module(module_path, package=__name__)
            _import_cache[name] = module
            return module
        except (ImportError, AttributeError) as e:
            raise AttributeError(f"module '{__name__}' has no subpackage '{name}'. Failed: {e}") from e

    # Check lazy exports
    if name in _LAZY_EXPORTS:
        module_path, attr_name = _LAZY_EXPORTS[name]
        try:
            module = importlib.import_module(module_path, package=__name__)
            value = getattr(module, attr_name)
            _import_cache[name] = value
            return value
        except (ImportError, AttributeError) as e:
            raise AttributeError(f"module '{__name__}' could not import '{name}' from '{module_path}': {e}") from e

    # Fallback: try direct module in package
    try:
        module = importlib.import_module(f".{name}", package=__name__)
        _import_cache[name] = module
        return module
    except ImportError:
        pass

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> List[str]:
    """Return all accessible symbols, submodules, and lazy exports."""
    all_symbols = set(globals().keys())
    all_symbols.update(_SUBMODULES.keys())
    all_symbols.update(_LAZY_EXPORTS.keys())
    return sorted(all_symbols)


# --- Discovery & Introspection APIs ---

def list_available_utility_modules() -> List[str]:
    """List all registered utility submodules."""
    return list(_SUBMODULES.keys())


def get_utility_module_info(module_name: str) -> Dict[str, Any]:
    """Get metadata information about a utility submodule."""
    if module_name not in _SUBMODULES:
        raise ValueError(f"Unknown utility module: {module_name}. Available: {list_available_utility_modules()}")

    return {
        "name": module_name,
        "import_path": f"{__name__}.{module_name}",
        "relative_path": _SUBMODULES[module_name],
        "cached": module_name in _import_cache,
    }


def list_all_utilities() -> Dict[str, List[str]]:
    """Return an overview dictionary mapping each submodule category to its available components."""
    categories: Dict[str, List[str]] = {
        "submodules": list_available_utility_modules(),
        "base": ["BaseOptimizationModel", "CudaResourceManager", "system_metrics_collector", "format_bytes", "get_gpu_info", "get_memory_info", "timed_block", "safe_run", "benchmark_function"],
        "logging": ["setup_logger", "get_logger", "TrainingLogger"],
        "training_tools": ["visualize_checkpoints", "summarize_run", "plot_loss_curves", "visualize_memory_profile", "compare_runs", "get_run_info", "monitor_training", "cleanup_runs"],
        "truthgpt": ["TruthGPTConfig", "create_truthgpt_config", "create_truthgpt_optimizer", "OptimizationLevel", "DeviceType", "PrecisionType"],
        "memory": ["MemoryOptimizer", "MemoryOptimizationConfig", "create_memory_optimizer", "TensorPool", "ActivationCache", "MemoryUtils"],
        "gpu": ["GPUUtils", "CUDAOptimizations", "OptimizedLayerNorm", "OptimizedRMSNorm", "EnhancedCUDAOptimizations"],
        "optimizers": ["HyperSpeedOptimizer", "AutoPerformanceOptimizer", "NeuralEvolutionaryOptimizer", "UltraAIOptimizer", "AIUtils"],
        "enterprise": ["EnterpriseAuth", "EnterpriseCache", "EnterpriseMonitor", "EnterpriseMetrics", "EnterpriseCloudIntegration", "EnterpriseTruthGPTAdapter"],
    }
    return categories


__all__ = [
    "__version__",
    # Submodules
    "truthgpt",
    "optimizers",
    "systems",
    "training_tools",
    "adapters",
    "ai",
    "enterprise",
    "gpu",
    "memory",
    "monitoring",
    "quantum",
    "training",
    "modules",
    # Foundational base & helpers
    "BaseOptimizationModel",
    "CudaResourceManager",
    "system_metrics_collector",
    "format_bytes",
    "get_gpu_info",
    "get_memory_info",
    "timed_block",
    "safe_run",
    "benchmark_function",
    # Logging
    "setup_logger",
    "get_logger",
    "TrainingLogger",
    # Training tools & visualization
    "visualize_checkpoints",
    "summarize_run",
    "plot_loss_curves",
    "visualize_memory_profile",
    "compare_runs",
    "get_run_info",
    "monitor_training",
    "cleanup_runs",
    "cleanup_old_runs",
    "cleanup_checkpoints",
    # TruthGPT Core
    "TruthGPTConfig",
    "create_truthgpt_config",
    "create_truthgpt_optimizer",
    "quick_truthgpt_optimization",
    "truthgpt_optimization_context",
    "OptimizationLevel",
    "DeviceType",
    "PrecisionType",
    "BaseTruthGPTOptimizer",
    "TruthGPTDeviceManager",
    "TruthGPTPrecisionManager",
    "TruthGPTMemoryManager",
    "TruthGPTPerformanceManager",
    "TruthGPTIntegratedOptimizer",
    # Memory
    "MemoryOptimizer",
    "MemoryOptimizationConfig",
    "create_memory_optimizer",
    "TensorPool",
    "ActivationCache",
    "MemoryUtils",
    # GPU
    "GPUUtils",
    "CUDAOptimizations",
    "OptimizedLayerNorm",
    "OptimizedRMSNorm",
    "EnhancedCUDAOptimizations",
    # Optimizers
    "HyperSpeedOptimizer",
    "AutoPerformanceOptimizer",
    "NeuralEvolutionaryOptimizer",
    "UltraAIOptimizer",
    "AIUtils",
    # Enterprise
    "EnterpriseAuth",
    "EnterpriseCache",
    "EnterpriseMonitor",
    "EnterpriseMetrics",
    "EnterpriseCloudIntegration",
    "EnterpriseTruthGPTAdapter",
    # Experiment
    "ExperimentTracker",
    # Discovery APIs
    "list_available_utility_modules",
    "get_utility_module_info",
    "list_all_utilities",
]
