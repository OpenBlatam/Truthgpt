"""
Unit tests for JIT Compiler
"""

import unittest
try:
    from ..jit.jit_compiler import (
        JITCompiler, JITCompilationConfig, JITTarget,
        JITOptimizationLevel, create_jit_compiler, jit_compilation_context
    )
except ImportError:
    from compiler.jit.jit_compiler import (
        JITCompiler, JITCompilationConfig, JITTarget,
        JITOptimizationLevel, create_jit_compiler, jit_compilation_context
    )

class TestJITCompiler(unittest.TestCase):
    """Test cases for JIT compiler."""

    def test_jit_compilation_config(self):
        config = JITCompilationConfig(
            target=JITTarget.NATIVE,
            optimization_level=JITOptimizationLevel.ADAPTIVE
        )
        self.assertEqual(config.target, JITTarget.NATIVE)
        self.assertEqual(config.optimization_level, JITOptimizationLevel.ADAPTIVE)
        self.assertTrue(config.enable_profiling)
        self.assertTrue(config.enable_hotspot_detection)

    def test_jit_compiler_creation(self):
        config = JITCompilationConfig(target=JITTarget.NATIVE)
        compiler = create_jit_compiler(config)
        self.assertIsNotNone(compiler)
        self.assertEqual(compiler.config.target, JITTarget.NATIVE)

    def test_jit_compilation_context(self):
        config = JITCompilationConfig(target=JITTarget.NATIVE)
        with jit_compilation_context(config) as ctx:
            self.assertIsNotNone(ctx)

class TestJITCompilation(unittest.TestCase):
    def test_compilation(self):
        config = JITCompilationConfig()
        compiler = create_jit_compiler(config)
        self.assertIsNotNone(compiler)

class TestJITOptimization(unittest.TestCase):
    def test_optimization(self):
        config = JITCompilationConfig(optimization_level=JITOptimizationLevel.AGGRESSIVE)
        self.assertEqual(config.optimization_level, JITOptimizationLevel.AGGRESSIVE)

def test_jit_compiler():
    tc = TestJITCompiler()
    tc.test_jit_compilation_config()
    tc.test_jit_compiler_creation()

def test_jit_compilation_context():
    config = JITCompilationConfig(target=JITTarget.NATIVE)
    with jit_compilation_context(config) as ctx:
        assert ctx is not None
