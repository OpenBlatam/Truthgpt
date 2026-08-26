# 🏗️ TruthGPT Optimization Core Architecture

> [!NOTE]
> TruthGPT Optimization Core is engineered as a **modular, stratified, registry-based foundation framework**. It decouples component definitions from runtime orchestration, providing extreme extensibility and hardware acceleration across both training and serving workloads.

---

## 🏛️ Stratified Multi-Layer Architecture

The system is organized into five tightly integrated layers:

```mermaid
graph TB
    subgraph Layer1 ["1. Client & Application Layer"]
        CLI["TruthGPT CLI / OpenClaw"]
        REST["FastAPI & gRPC Servers"]
        SDK["Python SDK / Jupyter Workspaces"]
    end

    subgraph Layer2 ["2. Agent Swarm & Orchestration Layer (`agents/`)"]
        Swarm["Multi-Agent Swarm Orchestrator"]
        ReAct["ReAct Reasoning Loop & Reflexion"]
        Tools["Dynamic Tools (Code, Search, DB)"]
        Memory["Vector RAG (ChromaDB) & SQLite Memory"]
        Webhooks["Multi-Platform Webhooks (Discord, Telegram, Slack)"]
    end

    subgraph Layer3 ["3. Optimization & Training Engine (`trainers/`, `papers/`)"]
        Trainer["GenericTrainer (DDP / FSDP / ZeRO / LoRA)"]
        Papers["SOTA Papers Registry (48+ Paper Plugins)"]
        Optimizers["Optimizers Suite (Lion, Sophia, Fused, 8-Bit)"]
        Configs["Unified TrainerConfig & YAML Presets"]
    end

    subgraph Layer4 ["4. Compiler & Acceleration Subsystem (`compiler/`)"]
        TorchInductor["TorchInductor / Dynamo Graph JIT"]
        MLIR_TRT["MLIR Passes & TensorRT Engines"]
        XLA["Accelerated Linear Algebra (TF2XLA)"]
        TritonKernels["Custom Triton & CUDA Kernels"]
    end

    subgraph Layer5 ["5. Polyglot Native Backends (`polyglot_core/`)"]
        RustCore["Rust Engine (PyO3) - Zero-Copy Paged KV & Buffers"]
        CppCore["C++ Core (PyBind11) - SIMD & CUDA GEMMs"]
        GoCore["Go Backends - Networking & Swarm Dispatch"]
        PyFallback["Pure Python Fallback (NumPy / Torch)"]
    end

    Layer1 --> Layer2
    Layer1 --> Layer3
    Layer2 --> Layer3
    Layer3 --> Layer4
    Layer4 --> Layer5
```

---

## 🧩 1. The Dynamic Registry System

Modularity is achieved via the **Registry Pattern**. Subsystems discover classes dynamically through string identifiers, allowing configuration via YAML without code alterations.

```python
# 1. Component Registration (e.g. in optimization_core/optimizers/pytorch/lion.py)
from factories.registry import OPTIMIZERS

@OPTIMIZERS.register("lion")
class LionOptimizer(torch.optim.Optimizer):
    def __init__(self, params, lr=1e-4, ...):
        ...

# 2. Declarative Specification (in config.yaml)
# optimizer:
#   type: lion
#   lr: 0.0001

# 3. Dynamic Factory Instantiation (in trainers/trainer.py)
self.optimizer = OPTIMIZERS.build(cfg.optimizer.type, model.parameters(), lr=cfg.optimizer.lr)
```

---

## 🔄 2. Complete Execution Lifecycle

Understanding the end-to-end training and inference lifecycle:

```mermaid
sequenceDiagram
    participant User as User / CLI
    participant Config as ConfigManager
    participant Factory as Dynamic Factory
    participant Trainer as GenericTrainer
    participant Compiler as CompilerSubsystem
    participant Hardware as GPU / Accelerators

    User->>Config: Load YAML / CLI Overrides
    Config->>Config: Validate Schema & Pre-flight
    Config-->>User: Validated TrainerConfig

    User->>Trainer: Initialize(config)
    Trainer->>Factory: Build Model, Optimizer, Loss, Data
    Factory-->>Trainer: Initialized Components

    Trainer->>Compiler: Optimize Model Graph (TorchInductor / Triton)
    Compiler->>Hardware: Compile PTX & TensorRT Engines
    Compiler-->>Trainer: Compiled Executable Graph

    loop Training Epochs & Batches
        Trainer->>Hardware: Forward Pass (Mixed Precision BF16)
        Trainer->>Hardware: Scaled Backward Pass
        Trainer->>Hardware: Optimizer Step & Gradient Clipping
        Trainer->>Trainer: Async Checkpointing & Metrics Log
    end
```

---

## 🌐 3. Polyglot Multi-Language Interoperability

TruthGPT pairs Python's rapid prototyping with low-level systems languages:

| Language | Integration Technology | Core Responsibilities |
| :--- | :--- | :--- |
| **Python** | Host Language | User APIs, high-level training loops, agent orchestration, PyTorch model definitions. |
| **Rust** | PyO3 / C-FFI | Thread-safe Paged KV-Cache allocation, zero-copy buffer pooling, tokenization. |
| **C++** | PyBind11 / CUDA C++ | Custom CUDA GEMM kernels, FlashAttention wrappers, SIMD AVX-512 tensor math. |
| **Go** | C-Shared / gRPC | High-concurrency network proxies, swarm message brokers, microservice dispatch. |

---

## 📚 Related Documentation Links
- [API Reference: Compiler Subsystem](api/compiler.md)
- [API Reference: Polyglot Core](api/polyglot_core.md)
- [API Reference: Generic Trainer](api/trainer.md)
- [API Reference: OpenClaw Agents SDK](api/openclaw_agents.md)
- [Engineering Guide: Distributed Training](guides/distributed_training.md)
- [Engineering Guide: KV-Cache Optimization](guides/kv_cache_optimization.md)
