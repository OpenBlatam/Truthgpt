# 🟣 TruthGPT Julia Core (`TruthGPT.jl` / `TruthGPTCore.jl`)

High-performance scientific computing and machine learning core for TruthGPT.

## 🌟 Key Submodules

| Submodule | Description | Key Types / Functions |
|:---|:---|:---|
| **`Attention`** | Scaled dot-product, Flash Attention, RoPE | `flash_attention`, `AttentionConfig`, `RoPE` |
| **`Cache`** | Thread-safe KV Cache & Sharded Cache | `KVCache`, `ShardedKVCache`, `kv_cache_get`, `kv_cache_put` |
| **`Compression`**| High-speed LZ4 & Zstd compression | `compress_lz4`, `decompress_lz4`, `compress_zstd` |
| **`Quantization`** | INT8, INT4 packed, Grouped quantization | `quantize_int8`, `quantize_int4`, `quantize_grouped` |
| **`Optimization`** | Bayesian/Random/Grid optimization & Schedulers | `optimize_hyperparams`, `cosine_schedule`, `focal_loss` |
| **`JumpOptimization`** | LP, QP, MIP mathematical programming via HiGHS | `optimize_linear`, `optimize_quadratic`, `optimize_mip` |
| **`FluxML`** | Flux.jl deep learning & language models | `create_model`, `train_model`, `predict` |
| **`Transformer`** | Pre-norm Transformer with RoPE & SwiGLU | `Transformer`, `TransformerConfig`, `generate` |
| **`Inference`** | Greedy, Top-K, Top-P, and Nucleus sampling | `TokenSampler`, `sample_nucleus`, `sample_greedy` |
| **`GPU`** | CUDA GPU acceleration | `has_cuda`, `attention_cuda`, `batched_mul_cuda` |
| **`Utils`** | Precision conversion, Profiling, Parallelism | `to_float32`, `to_bfloat16`, `parallel_map`, `benchmark` |

---

## 🚀 Julia Usage Example

```julia
using TruthGPT

# 1. Hyperparameter Optimization
bounds = HyperparamBounds(
    lr_range = (1e-5, 1e-2),
    batch_range = (16, 128)
)

loss_fn(p) = (p[:lr] - 1e-3)^2 + (p[:batch_size] - 32)^2
result = optimize_hyperparams(loss_fn, bounds, method=:random, max_iters=50)

# 2. INT8 Quantization
tensor = randn(Float32, 128, 128)
q_tensor = quantize_int8(tensor)
restored = dequantize(q_tensor)

# 3. Transformer Generation
config = TransformerConfig(d_model=128, n_heads=4, n_layers=2, vocab_size=1000)
model = Transformer(config)
tokens = generate(model, [1, 2, 3], max_new_tokens=20)
```

---

## 🐍 Python Interoperability

```python
from julia import TruthGPTCore

# Create bounds and optimize
bounds = TruthGPTCore.HyperparamBounds(
    lr_range=(1e-5, 1e-2),
    batch_range=(16, 128)
)
```

---

## 🧪 Testing

```bash
julia --project=. test/runtests.jl
```
