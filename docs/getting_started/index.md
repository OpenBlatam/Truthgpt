# 🚀 Getting Started

Welcome to **TruthGPT Optimization Core**. This getting started hub will guide you through installing the platform, running your first training job, orchestrating autonomous agent swarms, and compiling models with high-performance MLIR and CUDA backends.

---

## 🧭 Choose Your Path

<div class="grid cards" markdown>

-   :material-download: **[Installation Guide](installation.md)**
    -   Complete cross-platform setup instructions.
    -   CUDA 11.8/12.x, ROCm, Apple Silicon (MPS), Docker, and Conda.
    -   Polyglot dependencies (Rust, C++, Go, Julia, Elixir).

-   :material-flash: **[5-Minute Training Quickstart](quickstart_training.md)**
    -   Launch LLM fine-tuning or pre-training using CLI presets.
    -   Use the `GenericTrainer` Python API.
    -   Configure LoRA, mixed precision (BF16), and gradient checkpointing.

-   :material-robot: **[OpenClaw Agent Swarms](quickstart_agents.md)**
    -   Deploy autonomous ReAct agents with tool calling.
    -   Route queries across multi-agent swarms.
    -   Enable persistent episodic and vector memory (ChromaDB).

-   :material-cpu-64-bit: **[Compiler & Hardware Acceleration](quickstart_compiler.md)**
    -   Compile models with `torch.compile`, MLIR, and TensorRT.
    -   Benchmark custom CUDA/Triton kernels.
    -   Accelerate inference with high-throughput polyglot engines.

-   :material-cog: **[Configuration System](configuration.md)**
    -   Strongly typed dataclasses & YAML configuration management.
    -   Dynamic CLI parameter overrides and automated schema validation.

-   :material-heart-pulse: **[Health & Diagnostics](health_and_diagnostics.md)**
    -   Run system-wide hardware compatibility and CUDA audit checks.
    -   Benchmark raw tensor operations, attention throughput, and memory bandwidth.

</div>

---

## ⚡ 30-Second Verification

Ensure your environment is ready with our built-in diagnostics:

```bash
# Run the comprehensive system health audit
python utils/health_check.py
```

If you see all checks pass (PyTorch, CUDA accelerators, and core registries), you are ready to begin!
