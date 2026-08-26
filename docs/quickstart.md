# TruthGPT Optimization Core - Quick Start Guide

Get up and running with training, optimizing, and evaluating your first language model in under 5 minutes.

---

## ⚡ 1. Train Your First Model in 3 Commands

### Step 1: Health Check
Verify your environment and GPU acceleration:
```bash
python utils/health_check.py
```

### Step 2: Launch Training with a Preset
Run a fast fine-tuning experiment using the `lora_fast` configuration:
```bash
python train_llm.py --config configs/presets/lora_fast.yaml
```

This will automatically:
1. Initialize the tokenizer and base transformer model (e.g., GPT-2 or TinyLlama).
2. Inject Low-Rank Adaptation (LoRA) matrices into attention projections.
3. Stream length-bucketed batches to minimize padding waste.
4. Execute mixed-precision (BF16/FP16) training with fused AdamW.
5. Save model weights and training logs to `runs/lora_fast_run/`.

---

## 🐍 2. Python SDK Training Example

You can instantiate and execute the trainer programmatically within your own scripts or notebooks:

```python
from trainers.trainer import GenericTrainer, TrainerConfig

# 1. Define configuration
config = TrainerConfig(
    model_name="gpt2",
    output_dir="runs/my_first_run",
    epochs=2,
    train_batch_size=8,
    grad_accum_steps=2,
    learning_rate=1e-4,
    mixed_precision="bf16",  # "bf16", "fp16", or "none"
    lora_enabled=True,
    lora_r=16,
    lora_alpha=32,
    torch_compile=True,      # PyTorch 2.x JIT compilation
    fused_adamw=True,        # Ultra-fast CUDA AdamW
    log_interval=10,
    eval_interval=50,
)

# 2. Prepare sample dataset
train_data = [
    "TruthGPT Optimization Core provides zero-overhead LLM training.",
    "FlashAttention-2 accelerates self-attention with O(N) memory complexity.",
    "Dynamic length bucketing eliminates unnecessary padding computation.",
] * 200

val_data = [
    "Continuous batching improves inference serving throughput.",
    "Paged KV-Cache manages attention memory dynamically without fragmentation.",
] * 20

# 3. Instantiate and train
trainer = GenericTrainer(
    cfg=config,
    train_texts=train_data,
    val_texts=val_data,
    text_field_max_len=256,
)

trainer.train()
```

---

## 🛠️ 3. Creating Custom Training Configurations

Generate boilerplate project configs tailored to your specific hardware and model requirements:

```bash
python init_project.py custom_llama_finetune \
  --preset performance_max \
  --model meta-llama/Llama-2-7b-hf
```

This generates `configs/custom_llama_finetune.yaml`:

```yaml
model:
  name_or_path: "meta-llama/Llama-2-7b-hf"
  gradient_checkpointing: true
  lora:
    enabled: true
    r: 32
    alpha: 64
    dropout: 0.05
    target_modules: ["q_proj", "v_proj", "k_proj", "o_proj"]

training:
  epochs: 3
  batch_size: 4
  grad_accum_steps: 8       # Effective batch size = 32
  learning_rate: 2.0e-4
  scheduler: "cosine"
  warmup_ratio: 0.05
  mixed_precision: "bf16"
  torch_compile: true
  compile_mode: "reduce-overhead"

data:
  dataset_name: "wikitext"
  dataset_config_name: "wikitext-2-raw-v1"
  max_seq_length: 2048
  bucket_by_length: true

logging:
  output_dir: "runs/llama_finetune"
  log_interval: 25
  eval_interval: 200
  save_safetensors: true
```

Execute training using your custom configuration:
```bash
python train_llm.py --config configs/custom_llama_finetune.yaml
```

---

## 📊 4. Live Monitoring & Observability

### Real-Time Terminal Monitor
Watch loss trajectories, tokens/sec, and GPU memory in your terminal:
```bash
python utils/monitor_training.py runs/my_first_run
```

### TensorBoard Visualizer
```bash
tensorboard --logdir runs/
```

### Post-Training Summary & Loss Plots
```bash
python utils/visualize_training.py runs/my_first_run --summary --plot
```

---

## ⏭️ Next Steps

- **[System Architecture](architecture.md)**: Explore the decoupled registry and compiler layers.
- **[Optimization Guide](optimization.md)**: Learn how to scale sequence lengths and maximize TFLOPS.
- **[Distributed Training Guide](guides/distributed_training.md)**: Scale across multi-GPU nodes with DDP and FSDP.
