"""
AOT (Ahead-of-Time) Compiler for TruthGPT
Compile models ahead of time for optimal performance
"""

from .aot_compiler import (
    AOTCompiler, AOTCompilationConfig, AOTOptimizationStrategy,
    AOTCompilationResult, AOTTarget, AOTOptimizationLevel,
    create_aot_compiler, aot_compilation_context
)

try:
    from .static_analysis import (
        StaticAnalyzer, StaticAnalysisResult, CodeAnalyzer,
        create_static_analyzer, static_analysis_context
    )
except ImportError:
    pass

try:
    from .code_generation import (
        CodeGenerator, CodeGenConfig, CodeGenResult,
        create_code_generator, code_generation_context
    )
except ImportError:
    pass

__all__ = [
    'AOTCompiler',
    'AOTCompilationConfig',
    'AOTOptimizationStrategy',
    'AOTCompilationResult',
    'AOTTarget',
    'AOTOptimizationLevel',
    'create_aot_compiler',
    'aot_compilation_context',
    'StaticAnalyzer',
    'StaticAnalysisResult',
    'CodeAnalyzer',
    'create_static_analyzer',
    'static_analysis_context',
    'CodeGenerator',
    'CodeGenConfig',
    'CodeGenResult',
    'create_code_generator',
    'code_generation_context'
]





