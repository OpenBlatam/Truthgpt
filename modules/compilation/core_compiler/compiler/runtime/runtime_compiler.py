"""
Enhanced Runtime Compiler for TruthGPT
Refactored into modular runtime_core package.
"""

from .runtime_core import (
    RuntimeTarget,
    RuntimeOptimizationLevel,
    CompilationMode,
    OptimizationTrigger,
    RuntimeOptimizationStrategy,
    RuntimeCompilationConfig,
    RuntimeCompilationResult,
    NeuralGuidanceModel,
    QuantumOptimizationState,
    CompilationPipeline,
    RuntimeCompiler,
    create_runtime_compiler
)

def runtime_compilation_context(config: RuntimeCompilationConfig):
    """Create a runtime compilation context"""
    from ..core.compiler_core import CompilationContext
    return CompilationContext(config)

__all__ = [
    'RuntimeTarget',
    'RuntimeOptimizationLevel',
    'CompilationMode',
    'OptimizationTrigger',
    'RuntimeOptimizationStrategy',
    'RuntimeCompilationConfig',
    'RuntimeCompilationResult',
    'NeuralGuidanceModel',
    'QuantumOptimizationState',
    'CompilationPipeline',
    'RuntimeCompiler',
    'create_runtime_compiler',
    'runtime_compilation_context'
]
