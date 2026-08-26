# TruthGPT Optimization Core - Documentation Hub

Welcome to the central documentation gateway for **TruthGPT Optimization Core**.

---

## 🗂️ Table of Contents

### 🚀 [Getting Started](getting_started/index.md)
- [Installation Guide](getting_started/installation.md) - Linux, macOS, Windows, CUDA 11/12, ROCm, Docker, and Polyglot tools
- [Quickstart: LLM Training](getting_started/quickstart_training.md) - Train models in 5 minutes via CLI presets or Python API
- [Quickstart: OpenClaw Agents](getting_started/quickstart_agents.md) - Autonomous ReAct agents and Swarm orchestration
- [Quickstart: Compiler & Acceleration](getting_started/quickstart_compiler.md) - JIT/AOT, MLIR, and TensorRT compilation

### 🏗️ [Architecture & Design](architecture/overview.md)
- [System Architecture Overview](architecture/overview.md) - 4-layer design, registries, and execution sequences
- [Polyglot Core Engine](architecture/polyglot_core.md) - Rust, C++, Go, Julia, and Elixir acceleration
- [Compiler Runtime Architecture](architecture/compiler_runtime.md) - MLIR passes, Triton autotuning, and TensorRT
- [PiMoE Architecture](architecture/pimoe.md) - Physics-Informed Mixture of Experts
- [OpenClaw Agent Framework](architecture/agent_framework.md) - ReAct loops, vector memory, reflexion, and graph DAGs

### 📚 [API Reference](api/index.md)
- [Trainers API](api/trainers.md) - `GenericTrainer`, `TrainerConfig`, and Callbacks
- [Models & Modules API](api/models_modules.md) - Transformer models, Attention backends, and Positional Encodings
- [Optimizers API](api/optimizers.md) - Lion, Sophia, AdamW 8-bit, Muon, and LR Schedulers
- [Compiler API](api/compiler.md) - `compile_model`, `TensorRTCompiler`, and Triton kernels
- [OpenClaw Agents API](api/agents.md) - `AgentClient`, Swarms, Graph Orchestrator, and REST endpoints
- [Polyglot Core API](api/polyglot.md) - Multi-language bindings and C-ABI interfaces
- [Configuration Schema](api/configuration.md) - YAML configuration schema and validation rules
- [Research Papers Registry](api/papers.md) - 48+ SOTA paper implementations
- [Utilities API](api/utilities.md) - Health checks, live monitors, and metric exporters

### 📖 [Guides & In-Depth Tutorials](guides/optimization_tuning.md)
- [Optimization & Performance Tuning](guides/optimization_tuning.md) - FlashAttention, TF32, Mixed Precision, and Dynamic Bucketing
- [Distributed Training Guide](guides/distributed_training.md) - Multi-GPU DDP, FSDP, and DeepSpeed ZeRO 1/2/3
- [Custom Agent Development](guides/custom_agent_development.md) - Building specialized agents, tools, and webhooks
- [Compiler & Custom Kernels](guides/compiler_and_kernels.md) - Handcrafted Triton and CUDA kernels
- [Production Deployment & Serving](guides/deployment_production.md) - REST API server, Docker, Kubernetes, and Prometheus
- [Troubleshooting & Diagnostics](guides/troubleshooting.md) - Resolving OOMs, NaN losses, and deadlocks

### 💡 [Runnable Examples](examples/basic_training.md)
- [End-to-End LLM Fine-Tuning](examples/basic_training.md) - Complete Python fine-tuning script
- [Autonomous Research Swarm](examples/agent_swarms.md) - Multi-agent research query and code execution
- [Compiler & Kernel Benchmarks](examples/compiler_benchmarks.md) - Performance comparison across backends

### 📦 [Archive & Evolution](archive/)
- [Test Evolution Archive](archive/test_evolution/) - Historical test reports and benchmarks
- [Refactoring History](archive/refactoring_history/) - Architecture migration logs and summaries
- [PiMoE Summaries](archive/pimoe_summaries/) - Evolution records of Physics-Informed MoE
