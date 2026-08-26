# Tutorial: Fine-Tuning LLaMA with LoRA & FlashAttention

In this tutorial, you will fine-tune a LLaMA-2 7B model on a custom instruction dataset using Low-Rank Adaptation (LoRA), FlashAttention-2, and the Lion optimizer.

---

## 📋 Prerequisites
- 1x NVIDIA GPU with 16GB+ VRAM (RTX 3090, 4090, A10, A100).
- TruthGPT installed with CUDA support (`python utils/health_check.py`).

---

## 🛠️ Step 1: Create Configuration YAML

Save the following file as `configs/finetune_llama.yaml`:

```yaml
model:
  name: "meta-llama/Llama-2-7b"
  gradient_checkpointing: true
  save_safetensors: true

lora:
  enabled: true
  r: 16
  alpha: 32
  dropout: 0.05
  target_modules: ["q_proj", "v_proj", "k_proj", "o_proj"]

optimization:
  optimizer: "lion"
  learning_rate: 1.0e-4
  mixed_precision: "bf16"
  allow_tf32: true
  torch_compile: true

training:
  epochs: 3
  train_batch_size: 4
  grad_accum_steps: 8
  eval_batch_size: 4

data:
  dataset_name: "wikitext"
  dataset_config_name: "wikitext-2-raw-v1"
  text_field_max_len: 1024
  bucket_by_length: true

checkpointing:
  output_dir: "runs/llama2_lora_finetuned"
  ckpt_interval_steps: 200
  ckpt_keep_last: 2
  ema_enabled: true
```

---

## 🚀 Step 2: Start Training

Run the training job:

```bash
python train_llm.py --config configs/finetune_llama.yaml
```

You can watch real-time metrics in a separate terminal:

```bash
python utils/monitor_training.py runs/llama2_lora_finetuned
```

---

## 🔍 Step 3: Test Model Generation

After training completes, run inference with your fine-tuned LoRA weights:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b", torch_dtype="auto", device_map="cuda")
model = PeftModel.from_pretrained(base_model, "runs/llama2_lora_finetuned")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b")

inputs = tokenizer("Translate this code into Python: ...", return_tensors="pt").to("cuda")
outputs = model.generate(**inputs, max_new_tokens=100)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```
