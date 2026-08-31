# 🏗️ System Architecture Overview

TruthGPT Optimization Core is built on a **modular, layered, registry-driven architecture**. This design cleanly decouples component definitions, hardware compilation targets, training orchestration, and agentic workflows.

---

## 🏛️ Four-Layer Architectural Model

```mermaid
graph TD
    subgraph "Layer 1: User & Interface Layer"
        CLI[CLI & Terminal UI]
        REST[FastAPI REST / gRPC API]
        SDK[Python SDK / OpenClaw]
        CFG[Unified YAML Configs]
    end

    subgraph "Layer 2: Orchestration & Intelligence Layer"
        Trainer[GenericTrainer / Distributed Engine]
        Swarm[Swarm & Graph Orchestrator]
        RAG[ChromaDB Vector / Episodic Memory]
        PaperReg[SOTA Papers Registry]
    end

    subgraph "Layer 3: Model & Component Registry Layer"
        Models[Transformer / PiMoE Models]
        AttnReg[Attention Factory: FlashAttn / SDPA / Sparse]
        OptReg[Optimizer Factory: Lion / Sophia / Muon]
        DataReg[Dynamic Padding & Bucketing Dataloaders]
    end

    subgraph "Layer 4: Hardware & Execution Engine Layer"
        Polyglot[Polyglot Core: Rust / C++ / Go / Julia / Elixir]
        Compiler[Compiler Stack: MLIR / JIT / AOT / TensorRT]
        CUDA[CUDA 12 / Triton Kernels / TF32]
        DistEngine[FSDP / ZeRO / PyTorch DDP]
    end

    CLI --> CFG
    REST --> CFG
    SDK --> CFG
    CFG --> Trainer
    CFG --> Swarm

    Trainer --> Models
    Trainer --> AttnReg
    Trainer --> OptReg
    Trainer --> DataReg
    Swarm --> RAG
    Swarm --> PaperReg

    Models --> Polyglot
    Models --> Compiler
    AttnReg --> CUDA
    OptReg --> CUDA
    Trainer --> DistEngine
```

---

## 🧩 Core Architectural Subsystems

### 1. Unified Configuration & Validation
All training, compilation, and agent parameters are specified in typed dataclasses (`TrainerConfig`, `TransformerConfig`, `AgentConfig`) with automatic YAML/JSON serialization and schema validation.

### 2. Registry & Factory Pattern
Components (optimizers, attention mechanisms, loss functions, tokenizers, schedulers) register dynamically using decorators (`@REGISTRY.register("name")`). This allows swapping deep learning kernels without modifying training loops.

### 3. Polyglot Core Acceleration
Performance-critical components are implemented across native languages:
- **Rust Core (`rust_core`)**: Zero-overhead memory allocators, parallel tokenizers, and concurrent streaming buffers.
- **C++ Core (`cpp_core`)**: Custom CUDA kernel wrappers, fused matrix multiplication, and TensorRT bindings.
- **Elixir / Julia / Go / Scala**: Concurrent task distribution, scientific tensor calculations, and IPC bridges.

### 4. Compiler Runtime Pipeline
- **MLIR Dialects**: Hardware-independent intermediate representation and graph transformation passes.
- **JIT / AOT Engine**: PyTorch Inductor and Triton kernel generation with automatic autotuning.
- **TensorRT Pipeline**: Graph parsing, weight quantization (FP16/INT8/FP8), and engine serialization.

### 5. OpenClaw Autonomous Agent System
- **ReAct Execution Engine**: Dynamic prompt formatting, scratchpad thought-action-observation cycles.
- **Semantic Swarm Router**: Embeds incoming queries and routes them to specialized agents.
- **Memory & Reflexion**: SQLite episodic memory, ChromaDB semantic memory, and iterative response self-critique.

---

## 🔄 End-to-End Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as Developer / CLI
    participant Config as ConfigManager
    participant Factory as Component Factory
    participant Trainer as GenericTrainer
    participant Hardware as CUDA / Polyglot Core
    participant Monitor as Telemetry / WandB

    User->>Config: Load YAML / CLI args
    Config->>Config: Validate Schema & Types
    Config-->>Trainer: Validated TrainerConfig
    Trainer->>Factory: Build Model, Optimizer & Attention Backend
    Factory-->>Trainer: Instantiated PyTorch / Native Modules
    Trainer->>Hardware: Compile Graph (torch.compile / MLIR)
    loop Every Training Step
        Trainer->>Hardware: Forward Pass (Mixed Precision BF16)
        Trainer->>Hardware: Backward Pass & Scaled Gradients
        Trainer->>Hardware: Optimizer Step (Fused AdamW / Lion)
        Trainer->>Monitor: Stream Loss & Hardware Telemetry
    end
    Trainer->>Trainer: Checkpoint Model & State (safetensors)
    Trainer-->>User: Training Complete & Metrics Summary
```

---

## 📚 Section Breakdown

- [System Architecture Index](index.md)
- [Polyglot Core Architecture](polyglot_core.md)
- [Compiler Runtime Architecture](compiler_runtime.md)
- [PiMoE Physics-Informed MoE](pimoe.md)
- [OpenClaw Agent Framework](agent_framework.md)
- [Data Pipeline & Dynamic Bucketing](data_pipeline.md)
- [Models & Modular Layers](models_and_layers.md)
