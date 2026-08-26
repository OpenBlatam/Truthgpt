# ⚙️ Configuration Schema Reference

TruthGPT uses a strictly validated, dataclass-backed YAML configuration architecture.

---

## 🏛️ `TrainerConfig`

```python
from trainers.trainer import TrainerConfig
```

### Complete Field Specification

```yaml
# configs/my_experiment.yaml

model:
  model_name: "gpt2"                      # HuggingFace ID or local filesystem path
  gradient_checkpointing: true            # Save up to 75% VRAM during backward pass
  save_safetensors: true                  # Fast zero-copy safe weight serialization
  lora_enabled: true                      # Low-Rank Adaptation for PEFT
  lora_r: 16                              # LoRA rank dimension
  lora_alpha: 32                          # Scaling factor (rule: alpha = 2 * r)
  lora_dropout: 0.05                      # Dropout probability on adapter layers
  lora_target_modules:                    # Modules to inject LoRA adapters into
    - "q_proj"
    - "v_proj"

training:
  epochs: 3                               # Number of full training epochs
  train_batch_size: 8                     # Per-device batch size
  grad_accum_steps: 4                     # Effective batch size = batch_size * accum_steps * GPUs
  learning_rate: 1.0e-4                   # Peak learning rate
  weight_decay: 0.01                      # L2 weight regularization
  optimizer: "lion"                       # 'lion', 'sophia', 'adamw', 'adamw_8bit', 'muon'
  scheduler: "cosine"                     # 'cosine', 'linear', 'wsd', 'constant'
  warmup_steps: 100                       # Steps for linear LR warmup
  max_grad_norm: 1.0                      # Gradient clipping threshold

precision:
  mixed_precision: "bf16"                 # 'bf16' (recommended for Ampere+), 'fp16', 'none'
  allow_tf32: true                        # TensorFloat-32 acceleration on Ampere/Ada/Hopper
  torch_compile: true                     # Enable PyTorch 2.0 Graph Mode
  compile_mode: "max-autotune"            # 'default', 'reduce-overhead', 'max-autotune'

data:
  dataset: "wikitext"                     # Dataset name or custom file path
  text_field_max_len: 512                 # Maximum sequence length in tokens
  num_workers: 4                          # DataLoader worker processes
  prefetch_factor: 2                      # Batches to prefetch per worker
  persistent_workers: true                # Keep workers alive across epoch boundaries
  bucket_by_length: true                  # Dynamic padding bucketing

checkpointing:
  output_dir: "runs/my_experiment"        # Path where checkpoints and logs are saved
  ckpt_interval_steps: 500                # Save checkpoint frequency
  ckpt_keep_last: 3                       # Retain N most recent checkpoints
  eval_interval: 250                      # Evaluation frequency
  ema_enabled: true                       # Exponential Moving Average of weights
  ema_decay: 0.999                        # EMA decay coefficient

logging:
  log_interval: 25                        # Metrics print interval
  use_wandb: false                        # Weights & Biases telemetry
  wandb_project: "truthgpt-runs"
```

---

## 🛠️ Programmatic Configuration API

```python
from optimization_core.config import ConfigManager

manager = ConfigManager()

# Load and validate YAML configuration file
config = manager.load_config("configs/presets/performance_max.yaml")

# Override parameters dynamically
config.training.learning_rate = 2e-4
config.training.train_batch_size = 16

# Validate consistency rules
manager.validate(config)
```
