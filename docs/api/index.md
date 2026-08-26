# 📚 API Reference

Welcome to the comprehensive API Reference for the **TruthGPT Optimization Core**.

---

## 🗂️ API Module Directory

| Module | Description | Primary Classes / Functions |
| :--- | :--- | :--- |
| **[Trainers API](trainers.md)** | Core training orchestration and distributed execution | `GenericTrainer`, `TrainerConfig`, `Callback`, `CheckpointManager` |
| **[Models & Modules API](models_modules.md)** | Transformers, PiMoE, Attention, Encodings | `TransformerModel`, `PiMoEFeedForward`, `FlashAttention`, `RoPE` |
| **[Optimizers API](optimizers.md)** | SOTA optimization algorithms and schedulers | `Lion`, `Sophia`, `AdamW8Bit`, `Muon`, `CosineWarmupScheduler` |
| **[Compiler API](compiler.md)** | JIT/AOT compiler, MLIR dialects, TensorRT | `compile_model`, `TensorRTCompiler`, `MLIROptimizer`, `TritonKernels` |
| **[OpenClaw Agents API](agents.md)** | ReAct agents, swarms, tools, memory, webhooks | `AgentClient`, `SwarmOrchestrator`, `GraphOrchestrator`, `AgentScheduler` |
| **[Polyglot Core API](polyglot.md)** | Rust, C++, Go, Julia, Elixir multi-language bindings | `PolyglotAttentionEngine`, `RustTensorOps`, `CUDAFusedKernels` |
| **[Configuration API](configuration.md)** | YAML schemas, typed configurations, validation rules | `ConfigManager`, `TrainerConfig`, `TransformerConfig`, `ValidationRule` |
| **[Research Papers API](papers.md)** | 48+ SOTA paper implementations & registry | `PaperRegistry`, `PaperSpec`, `get_paper_model` |
| **[Utilities API](utilities.md)** | Health checks, monitoring, metrics export, migration | `health_check`, `monitor_training`, `visualize_training`, `Tracer` |
