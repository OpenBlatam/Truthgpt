# Practical Guide: KV-Cache Memory Optimization

This guide explains how to configure and tune Paged KV-Cache, Grouped Query Attention (GQA), and SnapKV eviction for long-context generation.

---

## ⚡ 1. Grouped Query Attention (GQA) & Multi-Query Attention (MQA)

Standard Multi-Head Attention (MHA) maintains independent Key ($K$) and Value ($V$) heads for every Query ($Q$) head.
- In GQA, multiple query heads share a single key/value head (e.g. 32 query heads sharing 8 key/value heads).
- **VRAM Savings**: Reduces KV-cache memory usage by **$4\times$**.

```yaml
model:
  n_heads: 32
  n_kv_heads: 8  # Grouped Query Attention ratio = 4:1
```

---

## 💾 2. Enabling SnapKV Dynamic Eviction

For ultra-long context documents (32k+ tokens), enable SnapKV:

```python
from optimization_core.inference.kv_cache import SnapKVCacheManager

kv_manager = SnapKVCacheManager(
    window_size=32,      # Retain initial attention window tokens
    kernel_size=5,       # Pooling kernel size
    max_capacity_prompt=2048  # Target compressed KV length
)
```

SnapKV dynamically filters out uninformative tokens while retaining exact reasoning and recall accuracy.
