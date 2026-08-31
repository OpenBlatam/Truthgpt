# ⚡ Compiler & Hardware Acceleration API Reference

The `compiler` module provides a comprehensive graph compilation suite, ahead-of-time (AOT) and just-in-time (JIT) compilers, MLIR dialect lowering passes, custom GPU kernel compilers, distributed compilers, and TensorRT / XLA optimization engines.

---

## 🏛️ Unified Compiler Factory

**Location**: `compiler.__init__`

```python
from compiler import create_compiler

# Create a CompilerCore instance
compiler = create_compiler(
    compiler_type="core",
    config={"target": "gpu", "optimization_level": "advanced"}
)
```

### Supported `compiler_type` Options

| Type | Class | Target Use Case |
| :--- | :--- | :--- |
| `"core"` | `CompilerCore` | General-purpose model compilation and graph optimization |
| `"aot"` | `AOTCompiler` | Ahead-of-time binary serialization and target codegen |
| `"jit"` | `JITCompiler` | Just-in-time trace compilation and hot-spot optimization |
| `"mlir"` | `MLIRCompiler` | Multi-Level Intermediate Representation dialect lowering |
| `"runtime"` | `RuntimeCompiler` | Dynamic execution-time kernel and memory optimization |
| `"kernel"` | `KernelCompiler` | CUDA and Triton fused kernel compilation |
| `"distributed"` | `DistributedCompiler` | Multi-node / multi-GPU tensor sharding compilation |
| `"neural"` | `NeuralCompiler` | Learned neural compilation heuristic optimization |
| `"tensorrt"` | `TF2TensorRTCompiler` | NVIDIA TensorRT FP16/INT8 execution plan generation |
| `"xla"` | `TF2XLACompiler` | Accelerated Linear Algebra compilation |

---

## 🚀 `CompilerCore`

**Location**: `compiler.core.compiler_core`

```python
from compiler.core.compiler_core import (
    CompilerCore,
    CompilationTarget,
    OptimizationLevel,
    CompilationConfig,
    create_compiler_core
)

config = CompilationConfig(
    target=CompilationTarget.GPU,
    opt_level=OptimizationLevel.ADVANCED,
    enable_profiling=True
)

compiler = create_compiler_core(config)
result = compiler.compile(model, sample_inputs)
```

### Enumerations & Configurations
- **`CompilationTarget`**: `CPU`, `GPU`, `TPU`, `HYBRID`
- **`OptimizationLevel`**: `BASIC`, `STANDARD`, `ADVANCED`, `AGGRESSIVE`, `MAXIMUM`
- **`CompilationResult`**: Container for the compiled model artifact, execution metrics, and optimization statistics.

---

## 🏎️ `TF2TensorRTCompiler`

**Location**: `compiler.tf2tensorrt.tf2tensorrt_compiler`

```python
from compiler.tf2tensorrt.tf2tensorrt_compiler import (
    TF2TensorRTCompiler,
    TensorRTConfig,
    create_tf2tensorrt_compiler
)

config = TensorRTConfig(
    precision_mode="FP16",
    max_workspace_size_bytes=4 * 1024 * 1024 * 1024,  # 4 GB
    minimum_segment_size=3
)

trt_compiler = create_tf2tensorrt_compiler(config)
compiled_engine = trt_compiler.compile_model(model)
```

---

## 🔬 `MLIRCompiler`

**Location**: `compiler.mlir.mlir_compiler`

```python
from compiler.mlir.mlir_compiler import (
    MLIRCompiler,
    MLIRDialect,
    MLIROptimizationPass,
    create_mlir_compiler
)

mlir_compiler = create_mlir_compiler()
mlir_result = mlir_compiler.compile_to_mlir(model)
```

---

## 🧩 `PluginManager`

**Location**: `compiler.plugin.plugin_system`

```python
from compiler.plugin.plugin_system import (
    CompilerPlugin,
    PluginManager,
    create_plugin_manager
)

plugin_manager = create_plugin_manager()
plugin_manager.register_plugin("custom_fusion", custom_plugin_instance)
```

---

## 🎛️ `KernelCompiler`

**Location**: `compiler.kernels.kernel_compiler`

```python
from compiler.kernels.kernel_compiler import (
    KernelCompiler,
    KernelConfig,
    create_kernel_compiler
)

kernel_compiler = create_kernel_compiler(KernelConfig(target="cuda", autotune=True))
fused_op = kernel_compiler.compile_kernel(kernel_source)
```
