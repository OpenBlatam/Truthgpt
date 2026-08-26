# Compiler Integration Guide

This guide explains how to integrate the **TruthGPT Compiler Subsystem** with standard PyTorch models, custom transformer architectures, and the `GenericTrainer`.

---

## 🚀 1. Quick Integration with `GenericTrainer`

The simplest way to use the compiler is by setting flags in your YAML configuration:

```yaml
training:
  torch_compile: true
  compile_mode: "max-autotune"  # "default", "reduce-overhead", "max-autotune"
  allow_tf32: true
```

When initialized, `ModelManager` will automatically wrap the model using `torch.compile(model, mode=cfg.compile_mode)`.

---

## 🐍 2. Direct Python Integration

You can compile standalone models or specific sub-modules:

```python
import torch
from optimization_core.compiler import compile_model
from transformers import AutoModelForCausalLM

# 1. Load model
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b",
    torch_dtype=torch.bfloat16,
    device_map="cuda"
)

# 2. Compile model
compiled_model = compile_model(
    model,
    mode="reduce-overhead",
    backend="inductor",
    enable_custom_triton_kernels=True
)

# 3. Fast inference
inputs = torch.randint(0, 32000, (1, 512), device="cuda")
with torch.inference_mode():
    outputs = compiled_model(inputs)
```

---

## 🛠️ 3. Handling Dynamic Shapes & Sequence Lengths

When training or serving on variable length sequences:

```python
import torch

# Mark dynamic dimensions (e.g. sequence length dim 1)
torch._dynamo.mark_dynamic(inputs, 1)

# Compile with dynamic shape support
compiled_model = torch.compile(model, dynamic=True)
```
