# 💡 Examples & Benchmark Recipes

Welcome to the runnable examples and benchmark suites for the **TruthGPT Optimization Core**.

---

## 🧭 Featured Walkthroughs

<div class="grid cards" markdown>

-   :material-flash: **[End-to-End LLM Fine-Tuning](basic_training.md)**
    -   Complete reproducible recipe fine-tuning GPT-2 / LLaMA on custom dataset.
    -   Full YAML experiment configuration and CLI execution.
    -   Live training curves with Weights & Biases or TensorBoard.

-   :material-robot: **[Autonomous Research Swarm](agent_swarms.md)**
    -   Deploying multi-agent collaborative swarms with OpenClaw.
    -   Task delegation across ResearchAgent, CodeInterpreter, and DataAnalysisAgent.
    -   Synthesizing multi-source technical reports with citation grounding.

-   :material-speedometer: **[Compiler & Kernel Benchmark Suite](compiler_benchmarks.md)**
    -   Benchmarking PyTorch Eager vs `torch.compile` vs TensorRT vs Native C++/Rust.
    -   Measuring TFLOPS, memory bandwidth utilization, and latency speedups.
    -   Generating performance comparison plots and markdown tables.

</div>

---

## 📂 Repository Runnable Scripts (`examples/`)

The repository includes 37+ production-ready standalone scripts located in the `examples/` directory:

### 🏋️ 1. Training & Fine-Tuning Recipes

| Script | Description | Key Technologies |
| :--- | :--- | :--- |
| `examples/basic_usage.py` | Minimal end-to-end model initialization, dataset loader, and training step. | PyTorch, `GenericTrainer` |
| `examples/modular_training_example.py` | Decoupled training pipeline with configurable callbacks, evaluation, and EMA. | Callbacks, EMA, Checkpointing |
| `examples/train_with_datasets.py` | Training with Hugging Face `datasets` streaming and dynamic token batching. | Hugging Face, Dynamic Bucketing |
| `examples/refactored_example.py` | Modernized training flow using strongly-typed configuration dataclasses. | `TrainerConfig`, YAML Loader |
| `examples/complete_workflow.py` | Full lifecycle: dataset ingest -> training -> validation -> checkpoint export. | End-to-End Pipeline |

### ⚡ 2. High-Throughput Inference & KV-Cache

| Script | Description | Key Technologies |
| :--- | :--- | :--- |
| `examples/kv_cache_demo.py` | PagedAttention KV-Cache demonstration preventing memory fragmentation. | PagedAttention, Continuous Batching |
| `examples/ultra_kv_cache_demo.py` | Ultra-low latency KV-Cache with SnapKV context eviction & INT8 quantization. | SnapKV, INT8 Quantization |
| `examples/modular_inference_example.py` | Decoupled inference engine with asynchronous token streaming. | Async Engine, Fast Tokenizer |
| `examples/inference_examples.py` | Comparative inference benchmarking across PyTorch, TensorRT, and Triton. | TensorRT, Triton Kernels |
| `examples/switch_attention_backend.py` | Dynamic runtime backend switching between FlashAttention-2, SDPA, and Math. | FlashAttention-2, SDPA |

### 🤖 3. OpenClaw Autonomous Agents & Swarms

| Script | Description | Key Technologies |
| :--- | :--- | :--- |
| `examples/openclaw_agents_demo.py` | ReAct agent execution with tool calling, vector search, and webhooks. | ReAct Loop, Tool Registry |
| `examples/custom_agent_example.py` | Blueprint for creating custom domain agents by subclassing `BaseAgent`. | `BaseAgent`, Custom Tools |
| `examples/demo_multi_agent.py` | Collaborative multi-agent swarm with dynamic handoffs and state persistence. | Swarm Router, SQLite Memory |
| `examples/plugin_example.py` | Dynamic plugin loading and runtime tool discovery for agent swarms. | Plugin System, Hot Reloading |

### 🚀 4. SOTA Optimizers & Hardware Acceleration

| Script | Description | Key Technologies |
| :--- | :--- | :--- |
| `examples/advanced_optimization_example.py` | Second-order Sophia, Lion, and 8-bit AdamW optimizer recipes. | Sophia, Lion, BitsAndBytes |
| `examples/super_fast_optimization_demo.py` | Combining TorchInductor, Triton kernels, and fused optimizers for maximum TFLOPS. | TorchInductor, Triton Autotune |
| `examples/extreme_optimization_example.py` | Extreme hardware saturation techniques for NVIDIA Ampere and Hopper GPUs. | FP8, Kernel Fusion |
| `examples/benchmark_tokens_per_sec.py` | Standardized micro-benchmark measuring token throughput across batch sizes. | Latency & Throughput Metrics |
| `examples/example_tensorflow_optimization.py` | Interoperability bridge and optimizations for TensorFlow/Keras models. | TF Interop, Cross-Framework |

### 🖥️ 5. Interactive Interfaces & Web Apps

| Script | Description | Key Technologies |
| :--- | :--- | :--- |
| `examples/gradio_interface.py` | Interactive web dashboard for real-time model generation, parameter tuning, and telemetry. | Gradio, Streaming UI |

---

## 🏃 Running Any Example

All scripts in `examples/` can be launched directly from the repository root:

```bash
# Launch interactive Gradio Web UI
python examples/gradio_interface.py

# Run KV-Cache memory demo
python examples/ultra_kv_cache_demo.py

# Benchmark token generation speed
python examples/benchmark_tokens_per_sec.py
```
