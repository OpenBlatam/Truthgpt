# Tutorial: Fine-Tuning LLMs with LoRA & QLoRA

In this end-to-end tutorial, you will fine-tune a LLaMA or GPT-style language model on an instruction dataset using Low-Rank Adaptation (LoRA), Mixed Precision (BF16), and Dynamic Bucketing.

---

## 🎯 What You Will Learn
1. How LoRA decomposes weight updates into low-rank matrices.
2. How to configure a YAML experiment file for peak GPU memory efficiency.
3. How to train and evaluate the model using `train_llm.py`.
4. How to export merged adapter weights to `safetensors`.

---

## 🔬 Understanding LoRA

During traditional full fine-tuning, all model parameters $W_0 \in \mathbb{R}^{d \times k}$ are updated:

$$W = W_0 + \Delta W$$

**LoRA** freezes $W_0$ and parameterizes the update $\Delta W$ as the product of two low-rank matrices $B \in \mathbb{R}^{d \times r}$ and $A \in \mathbb{R}^{r \times k}$, where rank $r \ll \min(d, k)$:

$$h = W_0 x + \frac{\alpha}{r} (B A) x$$

- **VRAM Savings**: Reduces trainable parameters by **99%**, drastically cutting optimizer memory.
- **Zero Inference Latency**: At inference time, weights can be merged into $W_0 = W_0 + \frac{\alpha}{r} BA$ with zero architectural overhead.

---

## 📝 Step 1: Create Configuration YAML

Create `configs/my_lora_experiment.yaml`:

```yaml
model:
  name_or_path: "meta-llama/Llama-2-7b-hf"
  gradient_checkpointing: true
  save_safetensors: true
  lora:
    enabled: true
    r: 16
    alpha: 32
    dropout: 0.05
    target_modules:
      - "q_proj"
      - "k_proj"
      - "v_proj"
      - "o_proj"

training:
  epochs: 3
  train_batch_size: 4
  grad_accum_steps: 8
  learning_rate: 2e-4
  weight_decay: 0.01
  mixed_precision: "bf16"
  allow_tf32: true
  fused_adamw: true
  scheduler: "cosine"
  warmup_ratio: 0.03

data:
  dataset_name: "wikitext"
  text_field_max_len: 2048
  bucket_by_length: true
  num_workers: 4

logging:
  output_dir: "runs/llama2_lora_demo"
  log_interval: 20
  eval_interval: 200
  ckpt_interval_steps: 500
  ckpt_keep_last: 2
  ema_enabled: true
```

---

## 🚀 Step 2: Launch Training

```bash
# Single GPU Execution
python train_llm.py --config configs/my_lora_experiment.yaml

# Or Multi-GPU DDP (e.g. 4 GPUs)
torchrun --nproc_per_node=4 train_llm.py --config configs/my_lora_experiment.yaml
```

---

## 📊 Step 3: Monitor Live Progress

Open a separate terminal window:
```bash
python utils/monitor_training.py runs/llama2_lora_demo
```

---

## 💾 Step 4: Exporting Merged Weights

To merge adapter weights back into the base model for deployment:

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-hf")
lora_model = PeftModel.from_pretrained(base_model, "runs/llama2_lora_demo/final_checkpoint")

# Merge LoRA weights into base model
merged_model = lora_model.merge_and_unload()

# Save final standalone model
merged_model.save_pretrained("runs/llama2_merged_standalone", safe_serialization=True)
```
