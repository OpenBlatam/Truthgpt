# CLI Reference, Interactive Terminals & Dashboards

TruthGPT Optimization Core provides a multi-modal developer toolkit spanning unified command-line utilities, interactive full-screen terminal user interfaces (TUI), and real-time observability dashboards.

---

## 🧭 Command Line Interfaces Summary

| Command / Script | Subsystem | Primary Purpose | Example Usage |
| :--- | :--- | :--- | :--- |
| `truthgpt` / `truth_cli.py` | Core CLI | Primary entrypoint for model compilation, training, and benchmarking. | `truthgpt train --config configs/presets/lora_fast.yaml` |
| `openclaw` / `openclaw.py` | Agent Swarm | CLI for autonomous multi-agent swarms and SOTA research paper discovery. | `openclaw swarm ask "Explain FlashAttention-3 tiling"` |
| `train_llm.py` | Training Engine | Direct launcher for single-node and multi-GPU distributed training runs. | `torchrun --nproc_per_node=4 train_llm.py --config configs/ddp.yaml` |
| `init_project.py` | Scaffolding | Initializes new experimental workspaces with pre-configured YAML presets. | `python init_project.py my_project --preset performance_max` |
| `validate_config.py` | Configuration | Pre-flight validation schema checker for training configurations. | `python validate_config.py --config configs/my_run.yaml` |
| `latency_optimizations.py` | Benchmarks | Comprehensive latency and memory bandwidth profiler across kernels. | `python latency_optimizations.py --benchmark-all` |
| `utils/health_check.py` | Diagnostics | System auditor checking Python, CUDA, drivers, and polyglot native libraries. | `python utils/health_check.py` |

---

## 🚀 `truthgpt` CLI

```bash
# Display help and available commands
truthgpt --help

# Launch full-screen interactive TUI terminal
truthgpt terminal

# Benchmark model inference speed and memory footprint
truthgpt benchmark --model meta-llama/Llama-2-7b --batch-size 8

# Compile a PyTorch model into an optimized TorchInductor / TensorRT graph
truthgpt compile --checkpoint runs/llama2_run/checkpoint-step-1000.pt --mode max-autotune

# Validate training YAML configuration
truthgpt validate --config configs/presets/transformer_1b_sota.yaml
```

---

## 🐝 `openclaw` Agent Swarm CLI

```bash
# Query the autonomous agent swarm with semantic role routing
openclaw swarm ask "What are the latest breakthroughs in multi-modal KV caching?" --user researcher_1

# Search SOTA research papers registry
openclaw papers list --category attention
openclaw papers info focusllm_2024

# Launch the OpenClaw REST, WebSocket & Webhooks daemon
openclaw serve --port 8080 --webhooks telegram,discord,slack
```

---

## 🖥️ Enhanced Dynamic Terminal (`enhanced_dynamic_terminal.py`)

Launch the interactive text user interface (TUI):

```bash
python enhanced_dynamic_terminal.py
```

### Key Capabilities
- **Live Hardware Gauges**: Real-time meters for CPU utilization, GPU VRAM allocation, CUDA tensor core saturation, Loss, and token throughput (tokens/sec).
- **Interactive Prompt REPL**: Dispatch instructions directly to active OpenClaw agents without leaving the terminal.
- **Log Stream Window**: Filterable, color-coded logging feed (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
- **Active Job Control**: Pause, resume, or abort ongoing training and compilation runs on demand.

---

## 📈 Real-Time Training Monitor (`utils/monitor_training.py`)

A lightweight terminal utility that attaches to any active training run directory:

```bash
python utils/monitor_training.py runs/llama2_lora_experiment
```

- Tails training logs with sub-second latency.
- Calculates moving averages for learning rate, step duration, and remaining time to completion (ETA).
- Renders an ASCII loss progression sparkline directly in your terminal.

---

## 🌐 Telemetry Web Dashboard (`dashboard.py`)

Launch the browser-based visualization dashboard:

```bash
python dashboard.py --port 8501
```

Access the UI at `http://localhost:8501`:
- Compare loss curves and validation perplexity across multiple training experiments.
- Inspect parameter histograms, gradient norms, and learning rate schedules.
- Browse saved checkpoint metadata, LoRA configurations, and evaluation metrics.
