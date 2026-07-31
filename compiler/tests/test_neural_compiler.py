"""
Unit Tests for Neural Compiler Infrastructure
"""

import unittest
try:
    from ..neural.neural_compiler import NeuralCompiler, NeuralCompilationConfig, create_neural_compiler
except (ImportError, ValueError):
    from compiler.neural.neural_compiler import NeuralCompiler, NeuralCompilationConfig, create_neural_compiler

class TestNeuralCompiler(unittest.TestCase):
    """Test suite for Neural Compiler"""

    def test_neural_config(self):
        config = NeuralCompilationConfig()
        self.assertIsNotNone(config)

    def test_neural_compiler_creation(self):
        config = NeuralCompilationConfig()
        compiler = create_neural_compiler(config)
        self.assertIsNotNone(compiler)

    def test_neural_compilation(self):
        config = NeuralCompilationConfig()
        compiler = create_neural_compiler(config)
        res = compiler.compile({"name": "neural_model"})
        self.assertTrue(res.success)

    def test_unsupervised_compilation(self):
        from compiler.neural.neural_compiler import NeuralCompilationMode
        config = NeuralCompilationConfig(compilation_mode=NeuralCompilationMode.UNSUPERVISED)
        compiler = create_neural_compiler(config)
        res = compiler.compile({"name": "unsupervised_model"})
        self.assertTrue(res.success)
        self.assertEqual(res.compilation_mode, "unsupervised")

    def test_reinforcement_compilation(self):
        from compiler.neural.neural_compiler import NeuralCompilationMode
        config = NeuralCompilationConfig(compilation_mode=NeuralCompilationMode.REINFORCEMENT)
        compiler = create_neural_compiler(config)
        res = compiler.compile({"name": "rl_model"})
        self.assertTrue(res.success)
        self.assertEqual(res.compilation_mode, "reinforcement")

    def test_meta_learning_compilation(self):
        from compiler.neural.neural_compiler import NeuralCompilationMode
        config = NeuralCompilationConfig(compilation_mode=NeuralCompilationMode.META_LEARNING)
        compiler = create_neural_compiler(config)
        res = compiler.compile({"name": "meta_model"})
        self.assertTrue(res.success)
        self.assertEqual(res.compilation_mode, "meta_learning")

    def test_transfer_compilation(self):
        from compiler.neural.neural_compiler import NeuralCompilationMode
        config = NeuralCompilationConfig(compilation_mode=NeuralCompilationMode.TRANSFER)
        compiler = create_neural_compiler(config)
        res = compiler.compile({"name": "transfer_model"})
        self.assertTrue(res.success)
        self.assertEqual(res.compilation_mode, "transfer")

if __name__ == '__main__':
    unittest.main()


