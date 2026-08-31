# TruthGPT Optimization Core - Documentation

Welcome to the **TruthGPT Optimization Core** enterprise documentation suite. This directory contains the complete technical manuals, architecture blueprints, user guides, API specifications, tutorials, and runnable benchmarks.

---

## 🧭 Fast Navigation

| Section | Description | Key Links |
| :--- | :--- | :--- |
| **🚀 Getting Started** | Fast-track onboarding, cross-platform installation & quickstarts. | [Overview](getting_started/index.md) • [Installation](getting_started/installation.md) • [Training Quickstart](getting_started/quickstart_training.md) • [Agents Quickstart](getting_started/quickstart_agents.md) • [Compiler Quickstart](getting_started/quickstart_compiler.md) |
| **🏗️ Architecture** | System design, stratified layers, PiMoE, and polyglot engines. | [Overview](architecture/overview.md) • [Polyglot Core](architecture/polyglot_core.md) • [Compiler Runtime](architecture/compiler_runtime.md) • [PiMoE](architecture/pimoe.md) • [Agent Framework](architecture/agent_framework.md) |
| **📚 API Reference** | Full programmatic Python & REST API documentation. | [API Index](api/index.md) • [Trainers](api/trainers.md) • [Models & Modules](api/models_modules.md) • [Optimizers](api/optimizers.md) • [Compiler](api/compiler.md) • [Agents](api/agents.md) • [Inference](api/inference.md) • [Polyglot](api/polyglot.md) • [Papers](api/papers.md) |
| **📖 Guides & Deep Dives** | In-depth engineering walkthroughs and best practices. | [Optimization & Tuning](guides/optimization_tuning.md) • [Distributed Multi-GPU](guides/distributed_training.md) • [Custom Agents](guides/custom_agent_development.md) • [Swarm Ensemble](guides/swarm_ensemble_vs_single_model.md) • [Custom Kernels](guides/compiler_and_kernels.md) • [KV-Cache Memory](guides/kv_cache_optimization.md) • [Production Deployment](guides/deployment_production.md) • [CLI & Terminals](guides/cli_and_terminals.md) • [Troubleshooting](guides/troubleshooting.md) |
| **🎓 Hands-On Tutorials** | Step-by-step practical implementation recipes. | [LoRA Fine-Tuning](tutorials/lora_finetuning.md) • [Custom Agents](tutorials/building_custom_agents.md) • [High-Throughput Serving](tutorials/high_throughput_serving.md) • [Custom Research Papers](tutorials/custom_research_papers.md) • [FAQ](tutorials/troubleshooting_and_faq.md) |
| **💡 Examples & Benchmarks** | Ready-to-run recipes and performance benchmarks. | [Basic Training](examples/basic_training.md) • [Agent Swarms](examples/agent_swarms.md) • [Compiler Benchmarks](examples/compiler_benchmarks.md) |
| **🇪🇸 Suite en Español** | Documentación completa en español. | [Portal Español](spanish/index.md) • [Inicio Rápido](spanish/QUICK_START.md) • [Manual](spanish/README.md) • [Ensemble vs Modelo Único](spanish/features/Ensemble_Vs_Single_Model.md) |
| **📦 Historical Archive** | Milestone logs, legacy specs, proposals & test reports. | [Archive Index](archive/index.md) |

---

## 📖 Local Documentation Server & Static Site

### Option 1: Standalone Python Documentation Server (Zero Dependencies)

Run our built-in interactive documentation server with live search, dark/light theme, code copy buttons, and Mermaid rendering:

```bash
# Serve documentation locally at http://localhost:8000
python docs/serve_docs.py
```

### Option 2: MkDocs Material

Build and serve the static documentation site with `mkdocs-material`:

```bash
# Install documentation generator dependencies
pip install mkdocs mkdocs-material

# Serve documentation locally with live reload at http://127.0.0.1:8000
mkdocs serve -f docs/mkdocs.yml

# Build static HTML distribution into site/
mkdocs build -f docs/mkdocs.yml
```
