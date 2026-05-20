"""
JIT (Just-in-Time) Compiler for TruthGPT
Dynamic compilation and optimization at runtime
"""

from .jit_compiler import (
    JITCompiler, JITCompilationConfig, JITOptimizationStrategy,
    JITCompilationResult, JITTarget, JITOptimizationLevel,
    create_jit_compiler, jit_compilation_context
)

from .dynamic_optimization import (
    DynamicOptimizer, RuntimeOptimizer, AdaptiveOptimizer,
    create_dynamic_optimizer, dynamic_optimization_context
)

from .hotspot_detection import (
    HotspotDetector, HotspotAnalyzer, PerformanceProfiler,
    create_hotspot_detector, hotspot_analysis_context
)

__all__ = [
    'JITCompiler',
    'JITCompilationConfig',
    'JITOptimizationStrategy',
    'JITCompilationResult',
    'JITTarget',
    'JITOptimizationLevel',
    'create_jit_compiler',
    'jit_compilation_context',
    'DynamicOptimizer',
    'RuntimeOptimizer',
    'AdaptiveOptimizer',
    'create_dynamic_optimizer',
    'dynamic_optimization_context',
    'HotspotDetector',
    'HotspotAnalyzer',
    'PerformanceProfiler',
    'create_hotspot_detector',
    'hotspot_analysis_context'
]





