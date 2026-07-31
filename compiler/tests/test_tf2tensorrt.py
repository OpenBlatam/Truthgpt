"""
Unit Tests for TF2TensorRT Compiler Infrastructure
"""

import unittest
try:
    from ..tf2tensorrt.tf2tensorrt_compiler import (
        TF2TensorRTCompiler, TensorRTConfig, TensorRTOptimizationLevel,
        TensorRTPrecision, create_tf2tensorrt_compiler, tf2tensorrt_compilation_context
    )
except ImportError:
    from compiler.tf2tensorrt.tf2tensorrt_compiler import (
        TF2TensorRTCompiler, TensorRTConfig, TensorRTOptimizationLevel,
        TensorRTPrecision, create_tf2tensorrt_compiler, tf2tensorrt_compilation_context
    )

class TestTF2TensorRT(unittest.TestCase):
    """Test suite for TensorRT compiler"""

    def test_tensorrt_config(self):
        config = TensorRTConfig(
            optimization_level=TensorRTOptimizationLevel.STANDARD,
            precision=TensorRTPrecision.FP16
        )
        self.assertEqual(config.optimization_level, TensorRTOptimizationLevel.STANDARD)
        self.assertEqual(config.precision, TensorRTPrecision.FP16)

    def test_tensorrt_compiler_creation(self):
        config = TensorRTConfig()
        compiler = create_tf2tensorrt_compiler(config)
        self.assertIsNotNone(compiler)

    def test_tensorrt_context(self):
        config = TensorRTConfig()
        with tf2tensorrt_compilation_context(config):
            pass

class TestTensorRTCompilation(unittest.TestCase):
    def test_compilation(self):
        config = TensorRTConfig()
        compiler = create_tf2tensorrt_compiler(config)
        res = compiler.compile({"name": "test_model"})
        self.assertTrue(res.success)

class TestTensorRTOptimization(unittest.TestCase):
    def test_optimization(self):
        config = TensorRTConfig()
        compiler = create_tf2tensorrt_compiler(config)
        res = compiler.optimize({"name": "test_model"})
        self.assertTrue(res.success)

def test_tf2tensorrt():
    tc = TestTF2TensorRT()
    tc.test_tensorrt_config()
    tc.test_tensorrt_compiler_creation()

def test_tensorrt_context():
    config = TensorRTConfig()
    with tf2tensorrt_compilation_context(config):
        pass

