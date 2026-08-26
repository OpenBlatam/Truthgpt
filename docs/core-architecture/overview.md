# Core System Architecture

TruthGPT Optimization Core is engineered as a **modular, registry-driven, polyglot deep learning framework**. This decoupled architecture isolates user configuration, runtime orchestration, algorithmic optimization, and hardware acceleration into clean, interoperable abstraction layers.

---

## 🏛️ Stratified Architectural Layers

The system is organized into four distinct architectural layers:

```mermaid
graph TB
    subgraph "Layer 1: Orchestration & Configuration"
        A1["ConfigManager & Dataclasses"]
        A2["Unified Registries (OPTIMIZER, MODEL, AGENT)"]
        A3["Factory Pattern Instantiators"]
    end

    subgraph "Layer 2: Engine & Execution Lifecycle"
        B1["GenericTrainer & Distributed Runners (DDP/FSDP/ZeRO)"]
        B2["Inference Serving Engine (Continuous Batching)"]
        B3["Zero-Padding Dynamic Bucketing Data Pipeline"]
        B4["Telemetry & Callbacks (W&B, TensorBoard, Prometheus)"]
    end

    subgraph "Layer 3: Algorithmic Optimization & Models"
        C1["Transformer / Modular Blocks (SwiGLU, RoPE)"]
        C2["PiMoE (Physics-Informed Mixture of Experts)"]
        C3["Advanced Optimizers (SOAP, Muon, Sophia, AdamW)"]
        C4["Paged KV-Cache & Speculative Draft Decoders"]
    end

    subgraph "Layer 4: Hardware & Compilation Acceleration"
        D1["TorchDynamo & TorchInductor Graph Compilers"]
        D2["Custom Triton & CUDA Fused Kernels"]
        D3["Polyglot Native Bridges (Rust Core, C++20 Core, Go Core)"]
    end

    A1 --> A2 --> A3
    A3 --> B1 & B2 & B3
    B1 & B2 --> C1 & C2 & C3 & C4
    C1 & C2 & C3 & C4 --> D1 & D2 & D3
```

---

## 🧩 1. Registry & Factory Decoupling

TruthGPT uses dynamic registries to decouple model component definitions from core training routines. This allows developers to introduce new optimizers, attention backends, or agent architectures without modifying trainer loops:

```python
from registries.unified_registry import OPTIMIZER_REGISTRY
import torch.optim as optim

# Register a custom optimizer
@OPTIMIZER_REGISTRY.register("custom_adaptive_opt")
def build_custom_optimizer(model_params, lr=1e-3, **kwargs):
    return optim.AdamW(model_params, lr=lr, weight_decay=0.01)
```

---

## ⚡ 2. Component Execution Lifecycle

During a model training or inference session, the runtime manages state transitions deterministically:

1. **Pre-flight Validation**: `ConfigManager` audits all hardware flags, hyperparameter constraints, and GPU memory budgets.
2. **Factory Initialization**: The model, optimizer, learning rate scheduler, and loss criterion are constructed via `registries/`.
3. **Graph Compilation Pass**: If `compile_model=True`, PyTorch Dynamo captures computation graphs, applies fusion passes via TorchInductor, and generates optimized Triton code.
4. **Data Stream Ingestion**: Datasets are partitioned into length-matched buckets to eliminate zero-padding memory waste.
5. **Execution Loop**: Batches execute through forward, loss calculation, backward, gradient clipping, optimizer step, and telemetry hooks.
6. **Persistence & Recovery**: Model weights, optimizer state dicts, and RNG seeds are saved via asynchronous atomic checkpoints.
