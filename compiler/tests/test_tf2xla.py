"""
Unit tests for TF2XLA Compiler
"""

import unittest
from ..tf2xla.tf2xla_compiler import (
    XLAConfig, XLAOptimizationLevel, XLATarget,
    create_tf2xla_compiler, tf2xla_compilation_context
)


class TestTF2XLA(unittest.TestCase):
    """Test cases for TF2XLA compiler."""

    def test_xla_config(self):
        config = XLAConfig(
            target=XLATarget.CPU,
            optimization_level=XLAOptimizationLevel.STANDARD
        )
        self.assertEqual(config.target, XLATarget.CPU)
        self.assertEqual(config.optimization_level, XLAOptimizationLevel.STANDARD)
        self.assertTrue(config.enable_fusion)

    def test_xla_compiler_creation(self):
        config = XLAConfig(target=XLATarget.CPU)
        compiler = create_tf2xla_compiler(config)
        self.assertIsNotNone(compiler)
        self.assertEqual(compiler.config.target, XLATarget.CPU)

    def test_xla_context(self):
        config = XLAConfig(target=XLATarget.CPU)
        with tf2xla_compilation_context(config) as ctx:
            self.assertIsNotNone(ctx)


class TestXLACompilation(unittest.TestCase):
    def test_compilation(self):
        config = XLAConfig()
        compiler = create_tf2xla_compiler(config)
        self.assertIsNotNone(compiler)


class TestXLAOptimization(unittest.TestCase):
    def test_optimization(self):
        config = XLAConfig(optimization_level=XLAOptimizationLevel.AGGRESSIVE)
        self.assertEqual(config.optimization_level, XLAOptimizationLevel.AGGRESSIVE)


def test_tf2xla():
    tc = TestTF2XLA()
    tc.test_xla_config()
    tc.test_xla_compiler_creation()


def test_xla_context():
    config = XLAConfig(target=XLATarget.CPU)
    with tf2xla_compilation_context(config) as ctx:
        assert ctx is not None


if __name__ == '__main__':
    unittest.main()
