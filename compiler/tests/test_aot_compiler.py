"""
Unit tests for AOT Compiler
"""

import unittest
try:
    from ..aot.aot_compiler import (
        AOTCompiler, AOTCompilationConfig, AOTTarget,
        AOTOptimizationLevel, create_aot_compiler, aot_compilation_context
    )
except ImportError:
    from compiler.aot.aot_compiler import (
        AOTCompiler, AOTCompilationConfig, AOTTarget,
        AOTOptimizationLevel, create_aot_compiler, aot_compilation_context
    )

class TestAOTCompiler(unittest.TestCase):
    """Test cases for AOT compiler."""

    def test_aot_compilation_config(self):
        config = AOTCompilationConfig(
            target=AOTTarget.NATIVE,
            optimization_level=AOTOptimizationLevel.STANDARD
        )
        self.assertEqual(config.target, AOTTarget.NATIVE)
        self.assertEqual(config.optimization_level, AOTOptimizationLevel.STANDARD)
        self.assertTrue(config.enable_inlining)
        self.assertTrue(config.enable_vectorization)

    def test_aot_compiler_creation(self):
        config = AOTCompilationConfig(target=AOTTarget.NATIVE)
        compiler = create_aot_compiler(config)
        self.assertIsNotNone(compiler)
        self.assertEqual(compiler.config.target, AOTTarget.NATIVE)

    def test_aot_compilation_context(self):
        config = AOTCompilationConfig(target=AOTTarget.NATIVE)
        with aot_compilation_context(config) as ctx:
            self.assertIsNotNone(ctx)

    def test_aot_compile(self):
        config = AOTCompilationConfig(target=AOTTarget.NATIVE)
        compiler = create_aot_compiler(config)
        result = compiler.compile("sample_model")
        self.assertTrue(result.success)

class TestAOTCompilation(unittest.TestCase):
    def test_compilation(self):
        config = AOTCompilationConfig()
        compiler = create_aot_compiler(config)
        self.assertIsNotNone(compiler)

class TestAOTOptimization(unittest.TestCase):
    def test_optimization(self):
        config = AOTCompilationConfig(optimization_level=AOTOptimizationLevel.AGGRESSIVE)
        self.assertEqual(config.optimization_level, AOTOptimizationLevel.AGGRESSIVE)

def test_aot_compiler():
    tc = TestAOTCompiler()
    tc.test_aot_compilation_config()
    tc.test_aot_compiler_creation()
    tc.test_aot_compile()

def test_aot_compilation_context():
    config = AOTCompilationConfig(target=AOTTarget.NATIVE)
    with aot_compilation_context(config) as ctx:
        assert ctx is not None
