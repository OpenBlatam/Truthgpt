# System Architecture Overview

> [!NOTE]
> The full architectural breakdown has been expanded in our structured documentation portal at **[Core Architecture: System Overview](core-architecture/overview.md)**.

The TruthGPT Optimization Core is designed as a **modular, registry-based, polyglot framework** with four stratified layers:

1. **Configuration Layer**: Unified YAML & Dataclass management.
2. **Factory Layer**: Registry pattern decoupling components from orchestrators.
3. **Core Engine**: Training, Inference, and Multi-Agent engines.
4. **Hardware & Polyglot Runtime**: Custom CUDA/Triton kernels and Rust/C++ bridges.

---

## 📚 Architecture Deep Dives

- **[System Overview](core-architecture/overview.md)**
- **[Training Engine](core-architecture/trainers.md)**
- **[Data Pipeline & Dynamic Bucketing](core-architecture/data_pipeline.md)**
- **[Models & Layer Architecture](core-architecture/models_and_layers.md)**
- **[High-Throughput Inference](inference/inference_engine.md)**
- **[Compiler Subsystem](compiler/compiler_system.md)**
- **[OpenClaw Agents & Swarm](agents-and-swarm/openclaw_sdk.md)**
- **[Polyglot Acceleration](polyglot/polyglot_subsystem.md)**
