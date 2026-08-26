# Tutorial: Fine-Tuning LLaMA with LoRA, FlashAttention-2, & BF16

In this hands-on tutorial, you will fine-tune a 7-Billion parameter LLaMA model on a custom instruction dataset using **Low-Rank Adaptation (LoRA)**, **FlashAttention-2**, and **BFloat16 mixed precision** on a single 24GB GPU.

---

## 🎯 Tutorial Objectives
1. Prepare a custom JSONL instruction-tuning dataset.
2. Configure LoRA hyperparameters with FlashAttention-2.
3. Launch distributed mixed-precision training.
4. Export the merged weights to `safetensors`.

---

## 📝 Step 1: Prepare Dataset

Create `data/alpaca_sample.jsonl`:
```json
{"instruction": "Explain the role of gradient checkpointing.", "output": "Gradient checkpointing trades additional compute for memory by recomputing activations during backprop."}
{"instruction": "What is FlashAttention-2?", "output": "FlashAttention-2 is an IO-aware exact attention algorithm that tiles computation within GPU SRAM."}
```

---

## ⚙️ Step 2: Create YAML Configuration

Create `configs/llama_lora_tutorial.yaml`:

```yaml
model:
  name_or_path: "meta-llama/Llama-2-7b-hf"
  gradient_checkpointing: true
  lora:
    enabled: true
    r: 16
    alpha: 32
    dropout: 0.05
    target_modules: ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

training:
  epochs: 3
  batch_size: 4
  grad_accum_steps: 4          # Effective batch size = 16
  learning_rate: 2.0e-4
  scheduler: "cosine"
  warmup_ratio: 0.03
  mixed_precision: "bf16"
  allow_tf32: true
  fused_adamw: true
  torch_compile: true
  compile_mode: "reduce-overhead"

data:
  dataset_path: "data/alpaca_sample.jsonl"
  max_seq_length: 2048
  bucket_by_length: true

logging:
  output_dir: "runs/llama_lora_run"
  log_interval: 10
  eval_interval: 50
  save_safetensors: true
```

---

## 🚀 Step 3: Run Training

Launch the training run:

```bash
python train_llm.py --config configs/llama_lora_tutorial.yaml
```

Monitor live metrics in real-time in a separate terminal:
```bash
python utils/monitor_training.py runs/llama_lora_run
```

---

## 💾 Step 4: Export & Merge LoRA Weights

After training completes, merge the LoRA adapter weights back into the base model for zero-overhead inference:

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-hf")
lora_model = PeftModel.from_pretrained(base_model, "runs/llama_lora_run/best_checkpoint")

# Merge LoRA weights into base weights
merged_model = lora_model.merge_and_unload()
merged_model.save_pretrained("runs/llama_lora_merged", safe_serialization=True)

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")
tokenizer.save_pretrained("runs/llama_lora_merged")
print("✅ Successfully exported merged model to runs/llama_lora_merged")
```
