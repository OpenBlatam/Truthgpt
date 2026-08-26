# Models & Modular Components API Reference

The `modules` and `models` packages contain decoupled, composable neural building blocks for architecting state-of-the-art transformer models and foundation architectures.

---

## 🏛️ Modular Hierarchy

```
modules/
├── embeddings/                # Positional & semantic embedding mechanisms
│   ├── positional_encoding.py # Standard sinusoidal encodings
│   ├── rotary_embeddings.py   # Rotary Positional Embeddings (RoPE)
│   ├── alibi_embeddings.py    # Attention with Linear Biases (ALiBi)
│   └── relative_embeddings.py # Relative position matrices
├── attention/                 # High-performance attention mechanisms
│   ├── flash_attention.py     # FlashAttention-2 & SDPA backends
│   ├── multi_head_attention.py# Scaled Dot-Product Multi-Head Attention
│   ├── sparse_attention.py    # Block-sparse & sliding window attention
│   └── cross_attention.py     # Multi-modal cross-attention
├── feed_forward/              # Non-linear projection layers
│   ├── feed_forward.py        # SwiGLU, GeGLU, and standard MLP
│   └── mixture_of_experts.py  # MoE / PiMoE Sparse Routing Layers
├── transformer_block/         # Pre-LayerNorm Transformer Block assemblies
└── model/                     # Complete Decoder-only & Encoder-Decoder models
```

---

## 🎯 1. Attention Mechanisms (`modules.attention`)

### `FlashAttention2`
Hardware-accelerated self-attention utilizing on-chip SRAM tiling.

```python
from modules.attention import create_flash_attention

attention = create_flash_attention(
    d_model=4096,
    n_heads=32,
    head_dim=128,
    dropout=0.0,
    causal=True,
    use_flash_attention=True
)

# Input shape: [batch_size, seq_len, d_model]
context_output = attention(hidden_states)
```

---

## 🧭 2. Positional Encodings (`modules.embeddings`)

### `RotaryEmbedding` (RoPE)
Rotates Query and Key representations in complex 2D planes according to token sequence positions:

$$\mathbf{R}_{\Theta, m}^d = \text{diag}\left(\mathbf{R}_{\theta_1, m}, \mathbf{R}_{\theta_2, m}, \dots, \mathbf{R}_{\theta_{d/2}, m}\right)$$

```python
from modules.embeddings import RotaryEmbedding

rope = RotaryEmbedding(
    dim=128,
    max_position_embeddings=32768,
    base=10000.0,
    scaling_factor=1.0  # Supports YaRN / LongRoPE scaling
)

# Apply rotation to Q and K
q_rot, k_rot = rope(q_tensor, k_tensor, position_ids)
```

---

## ⚡ 3. Feed-Forward Networks & SwiGLU (`modules.feed_forward`)

### `SwiGLUFeedForward`
Gated linear activation unit shown to significantly improve linguistic representations:

$$\text{SwiGLU}(x) = \left(\text{Swish}(x W_{\text{gate}}) \otimes x W_{\text{up}}\right) W_{\text{down}}$$

```python
from modules.feed_forward import create_swiglu

ffn = create_swiglu(
    d_model=4096,
    d_ff=11008,          # Typically (8/3) * d_model
    bias=False
)

ffn_out = ffn(hidden_states)
```

---

## 🔮 4. Mixture of Experts (MoE / PiMoE) (`modules.feed_forward.mixture_of_experts`)

Implements sparse expert routing, activating only top-$k$ experts per token:

```python
from modules.feed_forward import MixtureOfExperts

moe = MixtureOfExperts(
    d_model=4096,
    d_ff=4096,
    num_experts=8,
    top_k=2,                     # Route each token to top-2 experts
    router_jitter_noise=0.01,
    load_balancing_loss_weight=0.01
)

moe_out, auxiliary_loss = moe(hidden_states)
```

---

## 🏗️ 5. Complete Model Assembly (`modules.model`)

Construct a production-ready decoder-only language model using factory methods:

```python
from modules.model import create_transformer_model

model = create_transformer_model(
    vocab_size=32000,
    d_model=4096,
    n_heads=32,
    n_layers=32,
    d_ff=11008,
    max_seq_length=4096,
    attention_type="flash",
    activation_type="swiglu",
    norm_type="rmsnorm",
    use_gradient_checkpointing=True
)

# Forward pass
logits = model(input_ids)  # Shape: [batch_size, seq_len, vocab_size]
```
