"""
Unit Tests for Kernel Compiler Infrastructure
"""

import unittest
try:
    from ..kernels.kernel_compiler import (
        KernelCompiler, KernelConfig, create_kernel_compiler, kernel_compilation_context
    )
except (ImportError, ValueError):
    from compiler.kernels.kernel_compiler import (
        KernelCompiler, KernelConfig, create_kernel_compiler, kernel_compilation_context
    )

class TestKernelCompiler(unittest.TestCase):
    """Test suite for Kernel Compiler"""

    def test_kernel_config(self):
        config = KernelConfig()
        self.assertIsNotNone(config)

    def test_kernel_compiler_creation(self):
        config = KernelConfig()
        compiler = create_kernel_compiler(config)
        self.assertIsNotNone(compiler)

    def test_kernel_compilation(self):
        config = KernelConfig()
        compiler = create_kernel_compiler(config)
        res = compiler.compile({"name": "kernel_model"})
        self.assertTrue(res.success)

    def test_kernel_compilation_context(self):
        config = KernelConfig()
        with kernel_compilation_context(config):
            pass

if __name__ == '__main__':
    unittest.main()

