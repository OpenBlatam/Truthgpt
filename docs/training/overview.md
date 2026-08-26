# Training Engine Overview

The **TruthGPT Training Engine** is an enterprise-ready, modular distributed training framework built for training and fine-tuning frontier foundation models.

---

## 🏗️ Engine Subsystems

```
optimization_core/trainers/
├── trainer.py              # GenericTrainer: Main training loop & state machine
├── config.py               # TrainerConfig dataclass and validation
├── model_manager.py        # Model initialization, LoRA/PEFT, TorchDynamo, AMP
├── data_manager.py         # Dynamic batching, length bucketing, dataset samplers
├── checkpoint_manager.py   # SafeTensors serialization, async I/O, auto-resume
├── dist_manager.py         # DDP, FSDP, DeepSpeed ZeRO 1/2/3 integration
├── ema_manager.py          # Exponential Moving Average (EMA) weight tracking
├── evaluator.py            # Validation loss, perplexity, and metrics calculation
├── callbacks.py            # Event hooks (WandB, TensorBoard, Profiler, EarlyStopping)
└── exceptions.py           # Self-healing runtime exceptions and fallback handlers
```

---

## 🔄 The `GenericTrainer` Lifecycle

The `GenericTrainer` class standardizes the training lifecycle into distinct phases:

```mermaid
sequenceDiagram
    autonumber
    participant CLI as CLI / Script (train_llm.py)
    participant TM as ModelManager
    participant DM as DataManager
    participant Dist as DistManager
    participant Loop as GenericTrainer Loop
    participant Ckpt as CheckpointManager

    CLI->>Dist: Initialize Distributed Backend (NCCL/Gloo)
    CLI->>TM: Load Base Model & Apply LoRA / Quantization
    CLI->>TM: Apply Torch.compile & Fused Kernels
    CLI->>DM: Build Bucketed DataLoader & Samplers
    CLI->>Loop: Execute train()
    
    loop Each Epoch
        loop Each Batch
            Loop->>Loop: Forward Pass (AMP Scaled: BF16/FP16)
            Loop->>Loop: Loss Calculation & Gradient Backward
            Loop->>Loop: Gradient Clipping (Norm)
            Loop->>TM: Optimizer Step & LR Schedule Step
            Loop->>Loop: EMA Weight Update
        end
        Loop->>Loop: Run Evaluation Pass (evaluator.py)
        Loop->>Ckpt: Save Checkpoint (SafeTensors / Async)
    end
```

---

## 🚀 Quick Training Example

```python
from trainers.trainer import GenericTrainer
from trainers.config import TrainerConfig

# 1. Define configuration
config = TrainerConfig(
    model_name="meta-llama/Llama-2-7b",
    output_dir="runs/llama2_finetune",
    epochs=3,
    train_batch_size=4,
    grad_accum_steps=8,
    learning_rate=2e-4,
    mixed_precision="bf16",
    lora_enabled=True,
    lora_r=16,
    lora_alpha=32,
    torch_compile=True,
    allow_tf32=True
)

# 2. Prepare sample dataset
train_texts = ["Training text sample #1", "Sample #2 with instruction"] * 500
val_texts = ["Validation sample #1", "Validation sample #2"] * 50

# 3. Instantiate & Train
trainer = GenericTrainer(
    cfg=config,
    train_texts=train_texts,
    val_texts=val_texts
)

trainer.train()
```

---

## 🛡️ Fault Tolerance & Automatic Recovery

The training engine is resilient against common training instabilities:

1. **Automatic NaN/Inf Loss Skipping**: When an exploding gradient generates a NaN loss, the trainer drops the gradient update, halves the learning rate temporarily, and logs a warning.
2. **Crash Auto-Resume**: Set `resume_enabled: true` in your YAML to automatically detect the latest valid checkpoint in `output_dir` and restore model weights, optimizer states, LR scheduler, and random number generator (RNG) states.
3. **Out-of-Memory (OOM) Fallback**: If an activation spike causes a CUDA OOM error, the `GenericTrainer` flushes the CUDA cache, enables activation checkpointing dynamically, and resumes execution.
