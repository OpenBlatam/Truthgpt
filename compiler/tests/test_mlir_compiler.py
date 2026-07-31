"""
Unit tests for MLIR Compiler
"""

import unittest
try:
    from ..mlir.mlir_compiler import MLIRCompiler, create_mlir_compiler, mlir_compilation_context
    from ..core.compiler_core import CompilationConfig, CompilationTarget
except ImportError:
    from compiler.mlir.mlir_compiler import MLIRCompiler, create_mlir_compiler, mlir_compilation_context
    from compiler.core.compiler_core import CompilationConfig, CompilationTarget

class TestMLIRCompiler(unittest.TestCase):
    """Test cases for MLIR compiler."""

    def test_mlir_compilation_config(self):
        config = CompilationConfig(target=CompilationTarget.CPU)
        compiler = MLIRCompiler(config)
        self.assertIsNotNone(compiler)
        self.assertEqual(compiler.config.target, CompilationTarget.CPU)

    def test_mlir_compiler_creation(self):
        config = CompilationConfig(target=CompilationTarget.CPU)
        compiler = create_mlir_compiler(config)
        self.assertIsNotNone(compiler)
        self.assertEqual(compiler.config.target, CompilationTarget.CPU)

    def test_mlir_compilation_context(self):
        config = CompilationConfig(target=CompilationTarget.CPU)
        with mlir_compilation_context(config) as ctx:
            self.assertIsNotNone(ctx)

class TestMLIRCompilation(unittest.TestCase):
    def test_compilation(self):
        config = CompilationConfig(target=CompilationTarget.CPU)
        compiler = create_mlir_compiler(config)
        self.assertIsNotNone(compiler)

class TestMLIROptimization(unittest.TestCase):
    def test_optimization(self):
        config = CompilationConfig(target=CompilationTarget.GPU)
        compiler = create_mlir_compiler(config)
        self.assertEqual(compiler.config.target, CompilationTarget.GPU)

def test_mlir_compiler():
    tc = TestMLIRCompiler()
    tc.test_mlir_compilation_config()
    tc.test_mlir_compiler_creation()

def test_mlir_compilation_context():
    config = CompilationConfig(target=CompilationTarget.CPU)
    with mlir_compilation_context(config) as ctx:
        assert ctx is not None
