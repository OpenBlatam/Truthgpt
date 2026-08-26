# 💡 Example: End-to-End LLM Fine-Tuning

This complete runnable example demonstrates fine-tuning a GPT-2/Llama architecture model on custom text data using LoRA, FlashAttention, and BFloat16 mixed precision.

---

## 🐍 Complete Python Script

```python
import os
import torch
from trainers.trainer import GenericTrainer, TrainerConfig

def run_experiment():
    # 1. Configure the training setup
    cfg = TrainerConfig(
        model_name="gpt2",
        output_dir="runs/finetune_example",
        epochs=2,
        train_batch_size=4,
        grad_accum_steps=4,
        learning_rate=1e-4,
        weight_decay=0.01,
        mixed_precision="bf16" if torch.cuda.is_bf16_supported() else "fp16",
        allow_tf32=True,
        lora_enabled=True,
        lora_r=16,
        lora_alpha=32,
        gradient_checkpointing=True,
        ckpt_interval_steps=200
    )

    # 2. Prepare sample dataset
    train_corpus = [
        "Physics-Informed Mixture of Experts dynamically gates experts using Hamiltonian physics.",
        "FlashAttention-2 computes attention directly in on-chip SRAM for linear memory scaling.",
        "Polyglot execution offloads intensive memory allocation and tensor ops to Rust and C++.",
        "The TruthGPT compiler optimizes computational graphs via MLIR and TorchInductor."
    ] * 250

    val_corpus = [
        "Evaluation sample measuring generalization loss on unseen optimization text."
    ] * 20

    # 3. Instantiate GenericTrainer
    print("Initializing GenericTrainer...")
    trainer = GenericTrainer(
        cfg=cfg,
        train_texts=train_corpus,
        val_texts=val_corpus,
        text_field_max_len=256
    )

    # 4. Execute training run
    print("Beginning training loop...")
    trainer.train()

    # 5. Evaluate and save checkpoint
    final_loss = trainer.evaluate()
    print(f"Training Complete! Final Validation Loss: {final_loss:.4f}")

if __name__ == "__main__":
    run_experiment()
```

---

## 🚀 Running the Script

```bash
python examples/basic_training.py
```
