# Training Configuration Reference

The TruthGPT Training Subsystem uses a unified configuration engine powered by `TrainerConfig` (`trainers/config.py`). Configurations can be supplied as YAML files, JSON dictionaries, or Python dataclass instances.

---

## 📄 Complete YAML Configuration Template

```yaml
# configs/custom_training.yaml

model:
  name: "meta-llama/Llama-2-7b"
  vocab_size: 32000
  gradient_checkpointing: true
  save_safetensors: true
  torch_dtype: "bfloat16"

lora:
  enabled: true
  r: 16
  alpha: 32
  dropout: 0.05
  target_modules: ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

optimization:
  optimizer: "lion"             # lion, muon, sophia, fused_adamw, schedule_free, galore
  learning_rate: 1.0e-4
  weight_decay: 0.01
  adam_beta1: 0.9
  adam_beta2: 0.99
  max_grad_norm: 1.0
  mixed_precision: "bf16"       # bf16, fp16, none
  allow_tf32: true
  torch_compile: true
  compile_mode: "max-autotune"  # default, reduce-overhead, max-autotune

scheduler:
  type: "cosine"                # cosine, linear, wsd, constant, polynomial
  warmup_ratio: 0.05
  min_lr_ratio: 0.01

training:
  epochs: 3
  train_batch_size: 4
  grad_accum_steps: 8           # Effective batch size = 4 * 8 * num_gpus
  eval_batch_size: 4
  seed: 42

data:
  dataset_name: "wikitext"
  dataset_config_name: "wikitext-103-raw-v1"
  text_field_max_len: 2048
  bucket_by_length: true
  num_workers: 4
  prefetch_factor: 2
  persistent_workers: true

checkpointing:
  output_dir: "runs/llama2_finetune"
  ckpt_interval_steps: 500
  ckpt_keep_last: 3
  resume_enabled: true
  ema_enabled: true
  ema_decay: 0.999

logging:
  log_interval: 25
  eval_interval: 250
  callbacks:
    - "tensorboard"
    - "wandb"
  wandb_project: "truthgpt-training"
  wandb_run_name: "llama2-lion-opt"
```

---

## 🎛️ Pre-Built Presets

TruthGPT includes pre-tuned YAML configuration files located in `configs/presets/`:

| Preset Name | Path | Best For | Typical Hardware |
| :--- | :--- | :--- | :--- |
| `lora_fast.yaml` | `configs/presets/lora_fast.yaml` | Rapid verification & experimentation. | Single GPU (RTX 3080/4090, 8GB+ VRAM) |
| `performance_max.yaml` | `configs/presets/performance_max.yaml` | Maximum training throughput (TorchCompile + FlashAttention + Fused Lion). | NVIDIA A100 / H100 (80GB VRAM) |
| `memory_efficient.yaml` | `configs/presets/memory_efficient.yaml` | Fine-tuning large models on budget GPUs (QLoRA 4-bit + Checkpointing). | RTX 3060 / 4060 (12GB VRAM) |
| `multi_node_fsdp.yaml` | `configs/presets/multi_node_fsdp.yaml` | Multi-GPU / Multi-Node cluster scale training. | 8x A100/H100 Node Cluster |

---

## 💻 Python Instantiation

```python
from trainers.config import TrainerConfig

# Load directly from YAML file
config = TrainerConfig.from_yaml("configs/presets/lora_fast.yaml")

# Override specific parameters
config.learning_rate = 5e-5
config.epochs = 5
```
