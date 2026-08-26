# CLI & Command Reference

TruthGPT provides comprehensive command-line interfaces for training, autonomous agent interaction, project scaffolding, and dependency management.

---

## 🧭 CLI Summary

| Command / Script | Primary Purpose | Example Usage |
| :--- | :--- | :--- |
| `truthgpt` / `truth_cli.py` | Primary CLI entrypoint for optimization, training, and system control. | `truthgpt train --config configs/presets/lora_fast.yaml` |
| `openclaw` / `openclaw.py` | Autonomous Agent Swarm & Paper Discovery CLI. | `openclaw swarm ask "Summarize LongRoPE"` |
| `train_llm.py` | Direct distributed training launcher. | `python train_llm.py --config configs/my_run.yaml` |
| `init_project.py` | Scaffolds new training experiments and YAML configs. | `python init_project.py my_project --preset performance_max` |
| `install_extras.py` | Manages optional dependency groups. | `python install_extras.py wandb` |
| `utils/health_check.py` | Audits CUDA, PyTorch, and system hardware. | `python utils/health_check.py` |

---

## 🚀 `truthgpt` CLI

```bash
# Display help and commands
truthgpt --help

# Start interactive TUI terminal
truthgpt terminal

# Run model benchmark
truthgpt benchmark --model meta-llama/Llama-2-7b --batch-size 8

# Compile a model checkpoint
truthgpt compile --checkpoint runs/run/checkpoint-step-1000.pt --mode max-autotune
```

---

## 🐝 `openclaw` CLI

```bash
# Swarm interaction
openclaw swarm ask "What are the latest breakthroughs in multi-modal LLMs?" --user alice

# Paper discovery
openclaw papers list --category attention
openclaw papers info focusllm_2024

# Launch OpenClaw REST & Webhook server
openclaw serve --port 8000
```
