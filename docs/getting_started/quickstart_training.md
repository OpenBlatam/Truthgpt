# ⚡ Quickstart: Training LLMs in 5 Minutes

This guide walks you through launching your first Large Language Model training or fine-tuning run using the TruthGPT Optimization Core.

---

## 🏃 Method 1: CLI Training via Presets (Recommended)

TruthGPT provides pre-configured, production-validated YAML presets for common hardware and workload profiles.

```bash
# 1. Fast LoRA Fine-Tuning (runs on consumer GPU with ~6GB VRAM)
python train_llm.py --config configs/presets/lora_fast.yaml

# 2. High-Throughput Pretraining (FlashAttention, TF32, Torch.compile)
python train_llm.py --config configs/presets/performance_max.yaml

# 3. Memory-Optimized Training (Gradient Checkpointing, 8-bit AdamW)
python train_llm.py --config configs/presets/memory_saver.yaml
```

---

## 🐍 Method 2: Python Programmatic Training API

You can orchestrate training jobs programmatically using `GenericTrainer` and `TrainerConfig`:

```python
from trainers.trainer import GenericTrainer, TrainerConfig

# 1. Configure the training run
config = TrainerConfig(
    model_name="gpt2",                  # HuggingFace model or local path
    output_dir="runs/my_first_experiment",
    epochs=3,
    train_batch_size=8,
    grad_accum_steps=2,
    learning_rate=5e-5,
    mixed_precision="bf16",             # 'bf16', 'fp16', or 'none'
    allow_tf32=True,                    # Hardware acceleration for Ampere+
    torch_compile=False,                # Set True for graph fusion
    lora_enabled=True,                  # Parameter-Efficient Fine-Tuning
    lora_r=16,
    lora_alpha=32,
    gradient_checkpointing=True,        # Massive memory reduction
    ckpt_interval_steps=500
)

# 2. Prepare sample dataset
train_texts = [
    "TruthGPT is a high-performance optimization core for deep learning.",
    "FlashAttention enables linear memory scaling for transformer models.",
    "PiMoE introduces physics-informed sparse routing for mixture-of-experts."
] * 200

val_texts = [
    "Validation sample checking generalization performance."
] * 20

# 3. Instantiate and run trainer
trainer = GenericTrainer(
    cfg=config,
    train_texts=train_texts,
    val_texts=val_texts,
    text_field_max_len=512
)

# 4. Start execution
trainer.train()

# 5. Evaluate final model
eval_loss = trainer.evaluate()
print(f"Final Validation Loss: {eval_loss:.4f}")
```

---

## 🛠️ Method 3: Initializing a Custom Project

Generate customized YAML configurations using `init_project.py`:

```bash
# Initialize a new project tailored for Llama-2-7b
python init_project.py llama_finetune --preset performance_max --model meta-llama/Llama-2-7b

# This generates configs/llama_finetune.yaml. Now run:
python train_llm.py --config configs/llama_finetune.yaml
```

---

## 📊 Live Monitoring & Dashboard

Monitor loss curves, GPU memory, throughput, and hardware efficiency in real time:

```bash
# Terminal Live Dashboard
python utils/monitor_training.py runs/my_first_experiment

# Interactive Web Dashboard
python dashboard.py --port 8501

# TensorBoard
tensorboard --logdir runs
```

---

## ⏭️ What's Next?

- Explore [Optimization Techniques](../guides/optimization_tuning.md) to maximize tokens/sec.
- Learn how to scale to multi-GPU in [Distributed Training](../guides/distributed_training.md).
- Read the full [Trainer API Reference](../api/trainers.md).
