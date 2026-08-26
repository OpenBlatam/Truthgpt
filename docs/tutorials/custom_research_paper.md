# Tutorial: Implementing & Registering a Custom Research Paper

In this tutorial, you will implement a new research paper innovation (e.g., a custom sliding-window attention mechanism) and register it into the TruthGPT SOTA Papers Registry.

---

## 🛠️ Step 1: Implement the Layer

Create `papers/implementations/sliding_window_2025.py`:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class SlidingWindowAttention2025(nn.Module):
    def __init__(self, d_model: int, n_heads: int, window_size: int = 512):
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.window_size = window_size
        self.qkv_proj = nn.Linear(d_model, 3 * d_model)
        self.out_proj = nn.Linear(d_model, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, S, D = x.shape
        # Compute sliding window attention mask
        # ... custom sliding window logic ...
        return self.out_proj(x)
```

---

## 📝 Step 2: Register Paper Metadata

Add the paper descriptor to `papers/registry.py`:

```python
from papers.registry import register_paper

register_paper(
    paper_id="sliding_window_2025",
    title="Sliding Window Attention for Infinite Sequences",
    authors=["Research Team"],
    year=2025,
    category="attention",
    implementation_class=SlidingWindowAttention2025,
    default_config={"window_size": 512}
)
```

---

## 🔍 Step 3: Verify Discovery

```bash
openclaw papers info sliding_window_2025
```
