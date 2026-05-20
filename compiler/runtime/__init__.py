"""
Runtime Compilation for TruthGPT Compiler
Runtime compilation and adaptive optimization
"""

from .runtime_compiler import (
    RuntimeCompiler, RuntimeCompilationConfig, RuntimeOptimizationStrategy,
    RuntimeCompilationResult, RuntimeTarget, RuntimeOptimizationLevel,
    create_runtime_compiler, runtime_compilation_context
)

from .adaptive_compiler import (
    AdaptiveCompiler, AdaptiveCompilationConfig, AdaptiveOptimizationStrategy,
    create_adaptive_compiler, adaptive_compilation_context
)

from .profile_guided_compiler import (
    ProfileGuidedCompiler, ProfileGuidedConfig, ProfileGuidedOptimization,
    create_profile_guided_compiler, profile_guided_context
)

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





