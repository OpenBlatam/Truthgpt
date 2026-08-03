"""
Tests for compiler configuration enum string coercion and unified compiler factory.
"""

import pytest
from compiler import (
    CompilationConfig, CompilationTarget, OptimizationLevel,
    create_compiler, list_available_compilers, get_compiler_info
)
from compiler.aot import AOTCompilationConfig, AOTTarget, AOTOptimizationLevel
from compiler.jit import JITCompilationConfig, JITTarget, JITOptimizationLevel
from compiler.runtime import RuntimeCompilationConfig, RuntimeTarget, RuntimeOptimizationLevel
from compiler.runtime.config import CompilationMode
from compiler.kernels import KernelConfig, KernelTarget, KernelOptimizationLevel
from compiler.tf2tensorrt import TF2TensorRTCompiler, TensorRTConfig, TensorRTOptimizationLevel
from compiler.tf2tensorrt.tf2tensorrt_compiler import TensorRTPrecision
from compiler.tf2xla import XLAConfig, XLAOptimizationLevel
from compiler.tf2xla.tf2xla_compiler import XLATarget
from compiler.distributed import DistributedCompilationConfig
from compiler.distributed.distributed_compiler import DistributedCompilationMode, LoadBalancingStrategy, DistributedCompilationTarget
from compiler.neural import NeuralCompilationConfig
from compiler.neural.neural_compiler import NeuralCompilationMode, NeuralOptimizationStrategy, NeuralCompilationTarget


def test_compilation_config_coercion():
    config = CompilationConfig(target="gpu", optimization_level="aggressive")
    assert config.target == CompilationTarget.GPU
    assert config.optimization_level == OptimizationLevel.AGGRESSIVE


def test_aot_config_coercion():
    config = AOTCompilationConfig(target="cuda", optimization_level="aggressive")
    assert config.target == AOTTarget.CUDA
    assert config.optimization_level == AOTOptimizationLevel.AGGRESSIVE


def test_jit_config_coercion():
    config = JITCompilationConfig(target="interpreter", optimization_level="adaptive")
    assert config.target == JITTarget.INTERPRETER
    assert config.optimization_level == JITOptimizationLevel.ADAPTIVE


def test_runtime_config_coercion():
    config = RuntimeCompilationConfig(
        target="gpu",
        optimization_level="neural_guided",
        compilation_mode="asynchronous"
    )
    assert config.target == RuntimeTarget.GPU
    assert config.optimization_level == RuntimeOptimizationLevel.NEURAL_GUIDED
    assert config.compilation_mode == CompilationMode.ASYNCHRONOUS


def test_kernel_config_coercion():
    config = KernelConfig(target="opencl", optimization_level="aggressive")
    assert config.target == KernelTarget.OPENCL
    assert config.optimization_level == KernelOptimizationLevel.AGGRESSIVE


def test_tensorrt_config_coercion():
    config = TensorRTConfig(optimization_level="aggressive", precision="fp16")
    assert config.optimization_level == TensorRTOptimizationLevel.AGGRESSIVE
    assert config.precision == TensorRTPrecision.FP16


def test_xla_config_coercion():
    config = XLAConfig(target="gpu", optimization_level="aggressive")
    assert config.target == XLATarget.GPU
    assert config.optimization_level == XLAOptimizationLevel.AGGRESSIVE


def test_distributed_config_coercion():
    config = DistributedCompilationConfig(
        compilation_mode="master_worker",
        load_balancing_strategy="adaptive",
        target_metric="maximum_throughput"
    )
    assert config.compilation_mode == DistributedCompilationMode.MASTER_WORKER
    assert config.load_balancing_strategy == LoadBalancingStrategy.ADAPTIVE
    assert config.target_metric == DistributedCompilationTarget.MAXIMUM_THROUGHPUT


def test_neural_config_coercion():
    config = NeuralCompilationConfig(
        compilation_mode="supervised",
        optimization_strategy="adaptive_moment",
        target_metric="performance"
    )
    assert config.compilation_mode == NeuralCompilationMode.SUPERVISED
    assert config.optimization_strategy == NeuralOptimizationStrategy.ADAPTIVE_MOMENT
    assert config.target_metric == NeuralCompilationTarget.PERFORMANCE


def test_create_compiler_unified_factory():
    available_types = list_available_compilers()
    expected_types = [
        "core", "aot", "jit", "mlir", "runtime", "kernel",
        "distributed", "neural", "tf2tensorrt", "tf2xla", "plugin"
    ]
    for ctype in expected_types:
        assert ctype in available_types
        info = get_compiler_info(ctype)
        assert info["type"] == ctype
        compiler_inst = create_compiler(ctype, {})
        assert compiler_inst is not None


def test_create_compiler_with_dict_config():
    aot_comp = create_compiler("aot", {"target": "cuda", "optimization_level": "aggressive"})
    assert aot_comp.config.target == AOTTarget.CUDA
    assert aot_comp.config.optimization_level == AOTOptimizationLevel.AGGRESSIVE
