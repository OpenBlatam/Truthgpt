# TruthGPT Optimization Core - Documentation

Welcome to the **TruthGPT Optimization Core** documentation. This directory contains the complete technical manuals, architecture diagrams, user guides, API specifications, and tutorials for the ecosystem.

---

## 🧭 Fast Navigation

| Section | Description | Key Links |
| :--- | :--- | :--- |
| **Getting Started** | Fast-track guides for training & inference setup. | [Quickstart](quickstart.md) • [SOTA Ecosystem](quickstart_sota.md) • [Installation](installation.md) |
| **Architecture** | System design, stratified layers & registries. | [Architecture](architecture.md) • [Optimization Guide](optimization.md) |
| **Training Engine** | Distributed training, LoRA, EMA & configuration. | [Overview](training/overview.md) • [Configuration](training/configuration.md) • [Distributed](training/distributed.md) |
| **Compiler & Kernels** | MLIR, TensorRT, TorchInductor & Triton kernels. | [Compiler Overview](compiler/overview.md) • [Triton Kernels](compiler/triton_cuda_kernels.md) • [Integration](compiler/integration_guide.md) |
| **Polyglot Core** | C++, Rust, Elixir, Julia, Go & Scala native engines. | [Polyglot Overview](polyglot/overview.md) • [Rust & C++](polyglot/rust_cpp_kernels.md) • [Distributed Bridge](polyglot/distributed_bridge.md) |
| **Autonomous Agents** | OpenClaw Swarms, ReAct, Vector Memory & Webhooks. | [Agents Overview](agents/overview.md) • [Swarm Orchestration](agents/swarm_orchestration.md) • [Memory & Tools](agents/memory_and_tools.md) |
| **Inference & Serving** | Continuous batching, Paged KV-Cache & REST server. | [Serving Engine](inference/serving.md) • [Paged KV-Cache](inference/kv_cache_and_decoding.md) |
| **Tooling & Terminals** | Dynamic terminals, TUI, CLI & live monitors. | [CLI Reference](cli_and_tools/cli_reference.md) • [Interactive Terminals](cli_and_tools/interactive_terminals.md) |
| **Practical Guides** | In-depth engineering walkthroughs. | [Distributed Setup](guides/distributed_training.md) • [Custom Kernels](guides/custom_kernels.md) • [Deployment](guides/production_deployment.md) |
| **Tutorials & FAQ** | Step-by-step hands-on guides. | [LoRA Fine-Tuning](tutorials/finetune_llama_lora.md) • [High-Throughput Serving](tutorials/high_throughput_serving.md) • [Troubleshooting](tutorials/troubleshooting_and_faq.md) |
| **API Reference** | Full programmatic API documentation. | [API Index](api/index.md) • [Trainer API](api/trainer.md) • [Compiler API](api/compiler.md) • [OpenClaw API](api/openclaw_agents.md) |

---

## 📖 Building the Static Documentation Site

TruthGPT documentation is built with `mkdocs-material`:

```bash
# Install documentation generator dependencies
pip install mkdocs mkdocs-material

# Serve documentation locally at http://127.0.0.1:8000
mkdocs serve -f docs/mkdocs.yml

# Build static HTML distribution into site/
mkdocs build -f docs/mkdocs.yml
```
