"""
Unit Tests for Distributed Compiler Infrastructure
"""

import unittest
try:
    from ..distributed.distributed_compiler import DistributedCompiler, DistributedCompilationConfig, create_distributed_compiler
except (ImportError, ValueError):
    from compiler.distributed.distributed_compiler import DistributedCompiler, DistributedCompilationConfig, create_distributed_compiler

class TestDistributedCompiler(unittest.TestCase):
    """Test suite for Distributed Compiler"""

    def test_distributed_config(self):
        config = DistributedCompilationConfig()
        self.assertIsNotNone(config)

    def test_distributed_compiler_creation(self):
        config = DistributedCompilationConfig()
        compiler = create_distributed_compiler(config)
        self.assertIsNotNone(compiler)

    def test_distributed_compilation(self):
        config = DistributedCompilationConfig()
        compiler = create_distributed_compiler(config)
        res = compiler.compile({"name": "dist_model"})
        self.assertTrue(res.success)

if __name__ == '__main__':
    unittest.main()

