# 🎓 Hands-On Tutorials

Step-by-step, hands-on tutorials for mastering the **TruthGPT Optimization Core**.

---

## 🧭 Tutorial Catalog

<div class="grid cards" markdown>

-   :material-school: **[Fine-Tuning LLMs with LoRA & QLoRA](lora_finetuning.md)**
    -   Mathematical foundation of Low-Rank Adaptation (LoRA).
    -   Configuring LoRA rank, alpha, target projection matrices, and mixed precision.
    -   Launching single-GPU and multi-GPU DDP training jobs.
    -   Exporting and merging standalone `safetensors` weights for production.

-   :material-robot: **[Building Custom OpenClaw Agents](building_custom_agents.md)**
    -   Creating specialized autonomous agents with custom domain knowledge.
    -   Implementing structured reasoning routines and custom tool callers.
    -   Registering custom agents dynamically into the Swarm Router.

-   :material-server-fast: **[High-Throughput Serving with Paged KV-Cache](high_throughput_serving.md)**
    -   Launching the continuous batching inference server.
    -   Configuring Paged KV-Cache memory budgets and speculative decoding draft models.
    -   Simulating concurrent asynchronous client traffic with `httpx` and measuring P95 latency.

-   :material-flask: **[Implementing & Registering a Custom Research Paper](custom_research_papers.md)**
    -   Authoring a novel architectural layer (e.g. sliding window attention).
    -   Registering paper metadata into the TruthGPT SOTA Papers Registry.
    -   Benchmarking training convergence and runtime speed against baseline models.

-   :material-help-circle: **[Troubleshooting & FAQ](troubleshooting_and_faq.md)**
    -   Hands-on resolution workflows for CUDA OOM, NaN loss, and slow compile steps.
    -   Hardware compatibility matrix (NVIDIA Hopper/Ampere, Apple Silicon MPS).

</div>
