"""
Unit tests for Compiler Core
"""

import unittest
try:
    from ..core.compiler_core import (
        CompilationConfig, CompilationTarget, OptimizationLevel,
        CompilationResult, create_compiler_core, compilation_context
    )
except ImportError:
    from compiler.core.compiler_core import (
        CompilationConfig, CompilationTarget, OptimizationLevel,
        CompilationResult, create_compiler_core, compilation_context
    )

class TestCompilerCore(unittest.TestCase):
    """Test cases for compiler core."""

    def test_compilation_config(self):
        config = CompilationConfig(
            target=CompilationTarget.CPU,
            optimization_level=OptimizationLevel.STANDARD
        )
        self.assertEqual(config.target, CompilationTarget.CPU)
        self.assertEqual(config.optimization_level, OptimizationLevel.STANDARD)
        self.assertFalse(config.enable_quantization)
        self.assertTrue(config.enable_fusion)

    def test_compilation_result(self):
        result = CompilationResult(success=True, compilation_time=1.0)
        self.assertTrue(result.success)
        self.assertEqual(result.compilation_time, 1.0)

    def test_compiler_core_creation(self):
        config = CompilationConfig(target=CompilationTarget.CPU)
        compiler = create_compiler_core(config)
        self.assertIsNotNone(compiler)
        self.assertEqual(compiler.config.target, CompilationTarget.CPU)

    def test_compilation_context(self):
        config = CompilationConfig(target=CompilationTarget.CPU)
        with compilation_context(config) as ctx:
            self.assertIsNotNone(ctx)

class TestCompilationConfig(unittest.TestCase):
    def test_config_flags(self):
        config = CompilationConfig(enable_quantization=True)
        self.assertTrue(config.enable_quantization)

class TestCompilationResult(unittest.TestCase):
    def test_result_defaults(self):
        result = CompilationResult(success=True)
        self.assertTrue(result.success)

def test_compiler_core():
    tc = TestCompilerCore()
    tc.test_compilation_config()
    tc.test_compilation_result()
    tc.test_compiler_core_creation()

def test_compilation_context():
    config = CompilationConfig(target=CompilationTarget.CPU)
    with compilation_context(config) as ctx:
        assert ctx is not None
