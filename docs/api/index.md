# 📚 API Reference

Welcome to the comprehensive API Reference for the **TruthGPT Optimization Core**.

---

## 🗂️ API Module Directory

| Module | Description | Primary Classes / Functions |
| :--- | :--- | :--- |
| **[Trainers API](trainers.md)** | Core training orchestration, distributed synchronization & checkpointing | `GenericTrainer`, `TrainerConfig`, `Callback`, `CheckpointManager`, `EMAManager` |
| **[Models & Modules API](models_modules.md)** | Composable transformer components, PiMoE, Attention, Encodings | `TransformerModel`, `FlashAttention2`, `RotaryEmbedding`, `SwiGLUFeedForward`, `MixtureOfExperts` |
| **[Optimizers API](optimizers.md)** | SOTA optimization algorithms and learning rate schedulers | `Lion`, `Sophia`, `AdamW8Bit`, `Muon`, `CosineWarmupScheduler` |
| **[Compiler API](compiler.md)** | JIT/AOT compiler, MLIR dialects, TensorRT & Triton kernels | `compile_model`, `TensorRTCompiler`, `MLIROptimizer`, `fused_rotary_attention` |
| **[OpenClaw Agents API](agents.md)** | ReAct agents, swarms, tools, memory, webhooks & tracing | `AgentClient`, `SwarmOrchestrator`, `GraphOrchestrator`, `AgentScheduler`, `global_tracer` |
| **[Inference API](inference.md)** | High-throughput serving, Paged KV-Cache & Speculative Decoding | `InferenceEngine`, `PagedKVCacheManager`, `AsyncInferenceEngine`, `FastAPIServer` |
| **[Polyglot Core API](polyglot.md)** | Rust, C++, Go, Julia, Elixir multi-language bindings | `PolyglotAttentionEngine`, `RustStreamBuffer`, `CppTensorOps`, `JuliaOptimizer` |
| **[Configuration API](configuration.md)** | YAML schemas, typed configurations, validation rules | `ConfigManager`, `TrainerConfig`, `TransformerConfig`, `ValidationRule` |
| **[Research Papers API](papers.md)** | 48+ SOTA paper implementations & registry | `PaperRegistry`, `PaperSpec`, `get_paper_model` |
| **[Utilities API](utilities.md)** | Health checks, monitoring, metrics export, profiler | `health_check`, `monitor_training`, `visualize_training`, `Tracer` |
