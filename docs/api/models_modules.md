# Models & Modular Components API Reference

The `models` and `modules` packages contain decoupled, composable neural building blocks and model builders for architecting state-of-the-art transformer models, diffusion pipelines, and PiMoE architectures.

---

## 🏛️ Modular Hierarchy

```
models/
├── model_manager.py           # Central lifecycle and model orchestration manager
├── model_builder.py           # Fluent builder pattern for transformer models
├── models.py                  # Native TruthGPT transformer architectures
├── attention_utils.py         # Rotary, ALiBi, and efficient attention modules
├── hf_transformers.py         # HuggingFace Transformers wrapper
└── hf_diffusers.py            # Diffusion pipeline integrations

modules/
├── attention/                 # High-performance attention mechanisms
├── embeddings/                # Positional & semantic embedding mechanisms
├── feed_forward/              # SwiGLU, GeGLU, and PiMoE routing networks
└── transformer_block/         # Transformer block assemblies
```

---

## 🎯 1. Model Builders & Managers (`models`)

### `ModelBuilder` & `ModelManager`

```python
from models import (
    ModelBuilder,
    ModelManager,
    TruthGPTModelConfig,
    create_model_builder,
    create_model_manager
)

# 1. Configure TruthGPT model
config = TruthGPTModelConfig(
    vocab_size=32000,
    d_model=4096,
    n_heads=32,
    n_layers=32,
    d_ff=11008,
    max_seq_len=8192
)

# 2. Build model instance
builder = create_model_builder()
model = builder.with_config(config).build()

# 3. Manage model lifecycle
manager = create_model_manager(model=model, config=config)
```

---

## 🧭 2. Positional Encodings & Attention (`models.attention_utils`)

### `RotaryPositionalEmbedding` & `ALiBiPositionalEmbedding`

```python
from models.attention_utils import (
    RotaryPositionalEmbedding,
    ALiBiPositionalEmbedding,
    create_attention
)

# Initialize RoPE embedding module
rope = RotaryPositionalEmbedding(dim=128, max_seq_len=32768)

# Initialize efficient scaled dot-product attention
attention = create_attention(
    d_model=4096,
    n_heads=32,
    attention_type="scaled_dot_product"
)
```

---

## ⚡ 3. Feed-Forward Networks & SwiGLU (`modules.feed_forward`)

### `SwiGLU` & `FeedForward`

$$\text{SwiGLU}(x) = \left(\text{Swish}(x W_{\text{gate}}) \otimes x W_{\text{up}}\right) W_{\text{down}}$$

```python
from modules.feed_forward import SwiGLU, FeedForward, create_feed_forward

# Create SwiGLU feed-forward network
ffn = create_feed_forward(
    d_model=4096,
    d_ff=11008,
    activation="swiglu"
)
```

---

## 🌌 4. Physics-Informed Mixture of Experts (PiMoE)

**Location**: `modules.feed_forward.pimoe_router`

```python
from modules.feed_forward.pimoe_router import (
    PiMoESystem,
    create_pimoe_system,
    ExpertType
)

pimoe = create_pimoe_system(
    d_model=4096,
    num_experts=8,
    top_k=2,
    router_type="token_level"
)

# Route input through physics-informed experts
output, routing_decisions = pimoe(hidden_states)
```

---

## 📦 5. HuggingFace Model Bridges (`models.hf_transformers`)

```python
from models.hf_transformers import HFTransformersModel, create_hf_transformers_model

hf_model = create_hf_transformers_model(
    model_name_or_path="meta-llama/Llama-3-8B",
    device_map="auto",
    torch_dtype="bfloat16"
)
```
