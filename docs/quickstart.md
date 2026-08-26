# Quick Start Guide

> [!NOTE]
> This guide has been moved and enhanced in our structured portal at **[Getting Started: Quickstart](getting-started/quickstart.md)**.

Get up and running with training, high-throughput inference, and autonomous agent swarms in under 5 minutes using TruthGPT Optimization Core.

---

## 🏁 Train Your First Model

### 1. From the Command Line
```bash
# Verify installation health
python utils/health_check.py

# Run a quick training job using the 'lora_fast' preset
python train_llm.py --config configs/presets/lora_fast.yaml
```

### 2. Using Python API
```python
from trainers.trainer import GenericTrainer, TrainerConfig

# Define configuration
config = TrainerConfig(
    model_name="gpt2",
    output_dir="runs/my_first_run",
    epochs=1,
    train_batch_size=4,
    mixed_precision="bf16",
    allow_tf32=True,
    lora_enabled=True
)

train_texts = ["TruthGPT optimizes GPU compute through kernel fusion and paged memory."] * 100
val_texts = ["Validation sample for tracking perplexity."] * 10

trainer = GenericTrainer(cfg=config, train_texts=train_texts, val_texts=val_texts)
trainer.train()
```

---

## 📚 Explore the Full Documentation

- **[Installation Matrix](getting-started/installation.md)**
- **[Configuration System](getting-started/configuration.md)**
- **[System Architecture](core-architecture/overview.md)**
- **[Hardware Acceleration Guide](optimization/acceleration_guide.md)**
- **[High-Throughput Inference Engine](inference/inference_engine.md)**
- **[OpenClaw Agents SDK](agents-and-swarm/openclaw_sdk.md)**
- **[Full API Reference](api-reference/trainer_api.md)**
