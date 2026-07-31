"""
Unit Tests for Runtime Compiler Infrastructure
"""

import unittest
from ..runtime.runtime_compiler import (
    RuntimeCompiler, RuntimeCompilationConfig, RuntimeTarget,
    create_runtime_compiler, runtime_compilation_context
)


class TestRuntimeCompiler(unittest.TestCase):
    """Test suite for Runtime compiler"""

    def test_runtime_compilation_config(self):
        config = RuntimeCompilationConfig(target=RuntimeTarget.CPU)
        self.assertEqual(config.target, RuntimeTarget.CPU)

    def test_runtime_compiler_creation(self):
        config = RuntimeCompilationConfig()
        compiler = create_runtime_compiler(config)
        self.assertIsNotNone(compiler)

    def test_runtime_compilation_context(self):
        config = RuntimeCompilationConfig()
        with runtime_compilation_context(config) as ctx:
            self.assertIsNotNone(ctx)


def test_runtime_compiler():
    tc = TestRuntimeCompiler()
    tc.test_runtime_compilation_config()
    tc.test_runtime_compiler_creation()


def test_runtime_compilation_context():
    config = RuntimeCompilationConfig()
    with runtime_compilation_context(config) as ctx:
        assert ctx is not None


if __name__ == '__main__':
    unittest.main()
