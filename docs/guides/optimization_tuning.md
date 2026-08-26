# ⚡ Deep Dive: Optimization & Performance Tuning

Maximizing training throughput and memory efficiency requires orchestrating multiple hardware and software optimization layers. This guide outlines the key techniques supported by TruthGPT and how to tune them.

---

## 🏎️ Performance Optimization Matrix

| Technique | Hardware Target | Throughput Impact | Memory Reduction | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **FlashAttention-2** | NVIDIA Ampere / Ada / Hopper | $2\times - 4\times$ | $O(N^2) \rightarrow O(N)$ | Long sequences ($>1024$ tokens) |
| **Torch.compile** | NVIDIA / AMD / Intel | $1.3\times - 2.0\times$ | ~10% (kernel fusion) | Medium to large models |
| **TF32 Mode** | NVIDIA Ampere+ | $3\times - 8\times$ (GEMMs) | Zero change (FP32 storage) | Default for all Ampere+ runs |
| **Mixed Precision (BF16)** | Ampere / Hopper / TPU | $1.8\times - 2.5\times$ | **50%** | Stable training without loss scaler |
| **Gradient Checkpointing** | Any GPU / Accelerator | -20% compute overhead | **70% - 75%** | Models $>1\text{B}$ parameters |
| **Dynamic Padding & Bucketing**| Any | $1.5\times - 3\times$ | Up to 50% | Variable length text datasets |
| **KV-Cache Paged Attention** | Serving / Inference | $2\times - 5\times$ | **60%** | Multi-turn chat & long generations |

---

## 1. FlashAttention & Scaled Dot-Product Attention (SDPA)

Standard attention materializes an $N \times N$ attention weight matrix in high-latency GPU High-Bandwidth Memory (HBM). FlashAttention computes attention entirely within ultra-fast on-chip GPU SRAM.

```yaml
# In your YAML config
model:
  attention_type: "flash"
  use_flash_attention: true
```

---

## 2. Graph Compilation (`torch.compile`)

Graph compilation eliminates Python bytecode dispatch latency and fuses adjacent elementwise tensor operations into single CUDA kernel launches.

### Optimal Modes:
- **`default`**: Fast compilation time, ideal for rapid prototyping.
- **`reduce-overhead`**: Employs CUDA Graphs to pre-record kernel sequences, removing CPU overhead for small batch sizes.
- **`max-autotune`**: Profiles multiple Triton GEMM block dimensions. Best for long production runs.

```yaml
training:
  torch_compile: true
  compile_mode: "max-autotune"
```

---

## 3. Dynamic Length Bucketing

When training on heterogeneous text lengths, padding every sequence to the maximum global length wastes compute on dummy padding tokens.

### How TruthGPT Bucketing Works:
1. Sorts/clusters training examples into length buckets ($[128, 256, 512, 1024]$).
2. Mini-batches are drawn exclusively from homogeneous length buckets.
3. Dynamically pads each batch to the length of the *longest sample in that batch*, rather than the global maximum.

```yaml
data:
  bucket_by_length: true
  bucket_bins: [128, 256, 512, 1024, 2048]
```

---

## 4. KV-Cache Memory Optimizations

During autoregressive inference, TruthGPT uses chunked PagedAttention to prevent GPU memory fragmentation caused by dynamic sequence growth:

```python
from optimization_core.inference import KVCacheManager

cache_mgr = KVCacheManager(
    num_layers=32,
    num_heads=32,
    head_dim=128,
    page_size=16,
    device="cuda"
)
```
