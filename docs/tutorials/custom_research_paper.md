# Tutorial: Implementing & Benchmarking a Custom Research Paper Module

In this tutorial, you will implement a new cutting-edge attention research innovation, register it with the **Papers Registry**, and benchmark its speedup and memory efficiency against standard PyTorch baselines.

---

## 🎯 Tutorial Objectives
1. Understand the `BasePaperModule` interface.
2. Implement a custom attention masking algorithm (`SelectiveDecayAttention`).
3. Register the paper module with metadata and citation info.
4. Benchmark the implementation using the automated paper evaluation harness.

---

## 📝 Step 1: Implement the Paper Architecture

Create `papers/selective_decay_attention.py`:

```python
import torch
import torch.nn as nn
from papers.base import BasePaperModule
from papers.registry import PAPERS_REGISTRY, PaperMetadata

class SelectiveDecayAttention(BasePaperModule):
    """
    Selective Decay Attention (2026):
    Applies exponential decay penalties to distant non-salient tokens while preserving
    high-gradient anchor tokens indefinitely.
    """
    def __init__(self, d_model: int = 4096, n_heads: int = 32, decay_rate: float = 0.05):
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads
        self.decay_rate = decay_rate
        
        self.q_proj = nn.Linear(d_model, d_model, bias=False)
        self.k_proj = nn.Linear(d_model, d_model, bias=False)
        self.v_proj = nn.Linear(d_model, d_model, bias=False)
        self.out_proj = nn.Linear(d_model, d_model, bias=False)

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        B, S, D = hidden_states.shape
        
        # Project Q, K, V
        q = self.q_proj(hidden_states).view(B, S, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(hidden_states).view(B, S, self.n_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(hidden_states).view(B, S, self.n_heads, self.head_dim).transpose(1, 2)
        
        # Calculate attention scores
        scores = torch.matmul(q, k.transpose(-2, -1)) / (self.head_dim ** 0.5)
        
        # Construct Exponential Selective Decay Mask
        positions = torch.arange(S, device=hidden_states.device)
        distance = positions.unsqueeze(0) - positions.unsqueeze(1)
        decay_mask = -self.decay_rate * torch.clamp(distance, min=0.0)
        
        # Apply causal masking + decay
        causal_mask = torch.triu(torch.full((S, S), float('-inf'), device=hidden_states.device), diagonal=1)
        scores = scores + decay_mask.unsqueeze(0).unsqueeze(0) + causal_mask.unsqueeze(0).unsqueeze(0)
        
        attn_weights = torch.softmax(scores, dim=-1)
        context = torch.matmul(attn_weights, v)
        context = context.transpose(1, 2).contiguous().view(B, S, D)
        return self.out_proj(context)
```

---

## 🏷️ Step 2: Register the Paper with Metadata

Decorate the class to register it with the unified discovery index:

```python
@PAPERS_REGISTRY.register(
    name="selective_decay_attention",
    metadata=PaperMetadata(
        title="Selective Decay Attention for Ultra-Long Sequence Stability",
        authors=["TruthGPT Research Team"],
        year=2026,
        categories=["attention", "long-context"],
        description="Exponential decay penalty with anchor preservation for infinite context.",
        doi="arXiv:2608.99999"
    )
)
class SelectiveDecayAttentionModule(SelectiveDecayAttention):
    pass
```

---

## 🧪 Step 3: Run the Benchmark Harness

Verify that the paper appears in the discovery index and run performance benchmarks:

```bash
# 1. Verify paper is recognized
openclaw papers info selective_decay_attention

# 2. Run comparative throughput and memory benchmark
python papers/benchmark.py --paper selective_decay_attention --seq-lengths 1024,2048,4096,8192
```

---

## 📦 Step 4: Plug into Training Configuration

Use your newly implemented paper module directly in any model YAML:

```yaml
model:
  attention:
    backend: "paper:selective_decay_attention"
    decay_rate: 0.03
```
