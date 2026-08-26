# ⚡ TruthGPT Optimization Core Documentation

Welcome to the **TruthGPT Optimization Core** enterprise documentation suite. TruthGPT is a modular, ultra-high-performance deep learning ecosystem combining polyglot hardware acceleration, physics-informed mixture of experts (PiMoE), MLIR/JIT graph compilation, and autonomous OpenClaw agent swarms.

---

## 🧭 Navigation Matrix by Role

<div class="grid cards" markdown>

-   :material-flash: **[ML Engineers & Researchers](getting_started/quickstart_training.md)**
    -   [5-Minute Training Quickstart](getting_started/quickstart_training.md)
    -   [Optimization & Performance Tuning](guides/optimization_tuning.md)
    -   [Distributed Training (FSDP / ZeRO)](guides/distributed_training.md)
    -   [SOTA Research Papers Catalog](api/papers.md)

-   :material-robot: **[Agent & App Developers](getting_started/quickstart_agents.md)**
    -   [OpenClaw Agent Quickstart](getting_started/quickstart_agents.md)
    -   [Custom Tools & Specialized Agents](guides/custom_agent_development.md)
    -   [Graph Orchestrator & State Machines](architecture/agent_framework.md)
    -   [Agents & Webhooks API](api/agents.md)

-   :material-cpu-64-bit: **[Systems & Compiler Engineers](getting_started/quickstart_compiler.md)**
    -   [Compiler & Acceleration Quickstart](getting_started/quickstart_compiler.md)
    -   [Polyglot Core Architecture (Rust / C++)](architecture/polyglot_core.md)
    -   [Custom CUDA & Triton Kernels](guides/compiler_and_kernels.md)
    -   [Compiler API & TensorRT Exporter](api/compiler.md)

-   :material-server: **[DevOps & Production Teams](guides/deployment_production.md)**
    -   [Cross-Platform Installation Guide](getting_started/installation.md)
    -   [Production Serving & REST API](guides/deployment_production.md)
    -   [Prometheus Metrics & Health Checks](api/utilities.md)
    -   [Troubleshooting & Diagnostics](guides/troubleshooting.md)

</div>

---

## 🌟 Architectural Highlights

```mermaid
graph LR
    subgraph "TruthGPT Core Pillars"
        P1["⚡ Polyglot Engine<br>(Rust / C++ / CUDA)"]
        P2["🌌 PiMoE Architecture<br>(Physics-Informed MoE)"]
        P3["🔬 MLIR & TensorRT Compiler<br>(JIT / AOT / Kernels)"]
        P4["🤖 OpenClaw Agent Swarms<br>(ReAct / Memory / Tools)"]
    end
```

| Feature | Description | Reference Guide |
| :--- | :--- | :--- |
| **Polyglot Acceleration** | Zero-copy tensor sharing between PyTorch, Rust, and C++ for minimal memory allocation latency. | [Polyglot Core](architecture/polyglot_core.md) |
| **PiMoE (Physics MoE)** | Sparse Mixture of Experts regularized by Hamiltonian conservation laws to eliminate expert collapse. | [PiMoE Architecture](architecture/pimoe.md) |
| **Multi-Stage Compiler** | Graph lowering through MLIR dialects, automatic Triton autotuning, and TensorRT compilation. | [Compiler Runtime](architecture/compiler_runtime.md) |
| **OpenClaw Swarms** | Autonomous ReAct agent ecosystem with vector episodic memory, auto-reflexion, and multi-chat webhooks. | [Agent Framework](architecture/agent_framework.md) |
| **Unified Config System** | Strongly typed YAML/dataclass configurations with automated cross-field validation rules. | [Configuration API](api/configuration.md) |

---

## 📦 Quick Navigation Tree

```
docs/
├── getting_started/         # Installation & 5-minute quickstarts
├── architecture/            # Deep-dive system design & polyglot core
├── api/                     # Full Python & REST API references
├── guides/                  # In-depth optimization, distributed, & deployment guides
├── examples/                # Runnable recipes & benchmark scripts
└── archive/                 # Historical evolution & refactoring logs
```
