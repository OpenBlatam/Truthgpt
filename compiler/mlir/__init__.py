"""
MLIR Compiler Infrastructure for TruthGPT
Multi-Level Intermediate Representation compiler
"""

from .mlir_compiler import (
    MLIRCompiler, MLIRDialect, MLIROptimizationPass, MLIRCompilationResult,
    MLIRTarget, MLIROptimizationLevel, MLIRPassManager,
    create_mlir_compiler, mlir_compilation_context
)

from .dialect_manager import (
    DialectManager, DialectRegistry, DialectInfo,
    create_dialect_manager, dialect_context
)

from .pass_manager import (
    PassManager, OptimizationPass, PassResult,
    create_pass_manager, pass_context
)

__all__ = [
    'MLIRCompiler',
    'MLIRDialect',
    'MLIROptimizationPass',
    'MLIRCompilationResult',
    'MLIRTarget',
    'MLIROptimizationLevel',
    'MLIRPassManager',
    'create_mlir_compiler',
    'mlir_compilation_context',
    'DialectManager',
    'DialectRegistry',
    'DialectInfo',
    'create_dialect_manager',
    'dialect_context',
    'PassManager',
    'OptimizationPass',
    'PassResult',
    'create_pass_manager',
    'pass_context'
]





