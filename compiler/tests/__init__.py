"""
Test Suite for TruthGPT Compiler
Comprehensive testing framework for all compiler components
"""

from .test_compiler_core import (
    TestCompilerCore, TestCompilationConfig, TestCompilationResult
)

from .test_aot_compiler import (
    TestAOTCompiler, TestAOTCompilation, TestAOTOptimization
)

from .test_jit_compiler import (
    TestJITCompiler, TestJITCompilation, TestJITOptimization
)

from .test_mlir_compiler import (
    TestMLIRCompiler, TestMLIRCompilation, TestMLIROptimization
)

from .test_plugin_system import (
    TestPluginSystem, TestPluginManager, TestPluginRegistry
)

from .test_tf2tensorrt import (
    TestTF2TensorRT, TestTensorRTCompilation, TestTensorRTOptimization
)

from .test_tf2xla import (
    TestTF2XLA, TestXLACompilation, TestXLAOptimization
)

from .test_runtime_compiler import (
    TestRuntimeCompiler
)

from .test_runner import (
    TestRunner, TestSuite, TestResult, TestConfig,
    create_test_runner, run_all_tests
)

__all__ = [
    'TestCompilerCore',
    'TestCompilationConfig',
    'TestCompilationResult',
    'TestAOTCompiler',
    'TestAOTCompilation',
    'TestAOTOptimization',
    'TestJITCompiler',
    'TestJITCompilation',
    'TestJITOptimization',
    'TestMLIRCompiler',
    'TestMLIRCompilation',
    'TestMLIROptimization',
    'TestPluginSystem',
    'TestPluginManager',
    'TestPluginRegistry',
    'TestTF2TensorRT',
    'TestTensorRTCompilation',
    'TestTensorRTOptimization',
    'TestTF2XLA',
    'TestXLACompilation',
    'TestXLAOptimization',
    'TestRuntimeCompiler',
    'TestRunner',
    'TestSuite',
    'TestResult',
    'TestConfig',
    'create_test_runner',
    'run_all_tests'
]
