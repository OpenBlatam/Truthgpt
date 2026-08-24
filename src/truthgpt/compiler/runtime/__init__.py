"""
Runtime Compilation for TruthGPT Compiler
Runtime compilation and adaptive optimization
"""

from .runtime_compiler import (
    RuntimeCompiler, RuntimeCompilationConfig, RuntimeOptimizationStrategy,
    RuntimeCompilationResult, RuntimeTarget, RuntimeOptimizationLevel,
    create_runtime_compiler, runtime_compilation_context
)

# Backward-compatibility aliases
AdaptiveCompiler = RuntimeCompiler
AdaptiveCompilationConfig = RuntimeCompilationConfig
AdaptiveOptimizationStrategy = RuntimeOptimizationStrategy
create_adaptive_compiler = create_runtime_compiler
adaptive_compilation_context = runtime_compilation_context

ProfileGuidedCompiler = RuntimeCompiler
ProfileGuidedConfig = RuntimeCompilationConfig
ProfileGuidedOptimization = RuntimeOptimizationStrategy
create_profile_guided_compiler = create_runtime_compiler
profile_guided_context = runtime_compilation_context

__all__ = [
    'RuntimeCompiler',
    'RuntimeCompilationConfig',
    'RuntimeOptimizationStrategy',
    'RuntimeCompilationResult',
    'RuntimeTarget',
    'RuntimeOptimizationLevel',
    'create_runtime_compiler',
    'runtime_compilation_context',
    'AdaptiveCompiler',
    'AdaptiveCompilationConfig',
    'AdaptiveOptimizationStrategy',
    'create_adaptive_compiler',
    'adaptive_compilation_context',
    'ProfileGuidedCompiler',
    'ProfileGuidedConfig',
    'ProfileGuidedOptimization',
    'create_profile_guided_compiler',
    'profile_guided_context'
]






