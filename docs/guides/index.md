# 📖 Guides & Deep Dives

Welcome to the engineering guides for the **TruthGPT Optimization Core**. These practical deep dives provide best practices, hardware tuning tips, and step-by-step technical blueprints for building high-performance ML systems.

---

## 🧭 Practical Guides

<div class="grid cards" markdown>

-   :material-speedometer: **[Optimization & Performance Tuning](optimization_tuning.md)**
    -   PyTorch 2.x TorchInductor & TorchDynamo compiler modes (`default`, `reduce-overhead`, `max-autotune`).
    -   Mixed precision matrix (TF32, BF16, FP16, FP8) and fused optimizers.
    -   Memory optimization with gradient checkpointing and dynamic padding.

-   :material-server-network: **[Distributed Multi-GPU Training](distributed_training.md)**
    -   Distributed Data Parallel (DDP) and Fully Sharded Data Parallel (FSDP).
    -   DeepSpeed ZeRO-1, ZeRO-2, and ZeRO-3 configuration recipes.
    -   Multi-node cluster launch scripts via `torchrun` and Slurm.

-   :material-robot: **[Custom Agent & Tool Development](custom_agent_development.md)**
    -   Building custom ReAct agents by subclassing `BaseAgent`.
    -   Creating and registering custom tools with the `@tool` decorator.
    -   Connecting specialized agents to the Swarm Orchestrator and Webhooks.

-   :material-cpu-64-bit: **[Compiler & Custom Kernels](compiler_and_kernels.md)**
    -   Writing block-level fused GPU kernels with OpenAI Triton.
    -   Configuring automated kernel autotuning for target GPU architectures.
    -   Registering custom kernels into the Polyglot Core registry.

-   :material-memory: **[KV-Cache Memory Optimization](kv_cache_optimization.md)**
    -   PagedAttention memory allocation preventing VRAM fragmentation.
    -   SnapKV and sparse context compression for long-context inference.
    -   INT8 and FP8 KV-Cache quantization benchmarks.

-   :material-docker: **[Production Deployment & Serving](deployment_production.md)**
    -   High-throughput FastAPI/Uvicorn microservice clustering.
    -   Enterprise Docker containers and Kubernetes deployment manifests.
    -   Prometheus metrics, Grafana dashboards, and health probes.

-   :material-console: **[CLI Reference & Interactive Terminals](cli_and_terminals.md)**
    -   Complete reference for `truthgpt`, `openclaw`, and training CLIs.
    -   Full-screen dynamic TUI terminals and telemetry dashboards.
    -   Real-time training log tails and ASCII loss sparklines.

-   :material-bee: **[Swarm Ensemble vs Single Model](swarm_ensemble_vs_single_model.md)**
    -   Architectural advantages of multi-agent swarm vs single foundation model.
    -   Consensus voting, multi-round structured debate, and speculative race.
    -   Bayesian self-certainty confidence weighting and fault tolerance.

-   :material-bug: **[Troubleshooting & Diagnostics](troubleshooting.md)**
    -   Diagnosing and resolving `CUDA Out of Memory (OOM)` errors.
    -   Fixing `Loss is NaN / Inf` and exploding gradients in mixed precision.
    -   Resolving distributed multi-GPU deadlocks and PyTorch compile latency.

</div>
