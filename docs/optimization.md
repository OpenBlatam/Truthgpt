# TruthGPT Optimization & Acceleration Bible

The TruthGPT Optimization Core integrates state-of-the-art computational and architectural optimizations to maximize hardware utilization (TFLOPS), minimize memory footprint (VRAM), and accelerate both training and inference workloads.

---

## ⚡ 1. Graph Compilation & Kernel Fusion

### TorchInductor & Dynamo (PyTorch 2.x+)

Standard PyTorch eager mode launches independent CUDA kernels for every elementary operation (e.g., `matmul`, `bias_add`, `layer_norm`, `gelu`), incurring severe CPU-GPU synchronization and high Global Memory (HBM) bandwidth pressure.

`torch.compile` captures the computation graph via TorchDynamo and generates fused C++/Triton kernels via TorchInductor.

| Compile Mode | Characteristics | Ideal Workload |
| :--- | :--- | :--- |
| `default` | Fast compilation time; standard operator fusion. | Development, rapid prototyping, medium batches. |
| `reduce-overhead` | Captures CUDA Graphs to eliminate CPU kernel launch latency. | Small batch inference, latency-critical serving. |
| `max-autotune` | Exhaustively benchmarks multiple Triton tile configurations. | Long-running production training and large-scale serving. |

#### Configuration in YAML:
```yaml
training:
  torch_compile: true
  compile_mode: "max-autotune"
```

---

### Custom Triton Kernels & Operator Fusion

The core provides optimized Triton kernels for operations that are bottlenecks in vanilla PyTorch:
- **Fused RoPE + Attention**: Fuses Rotary Positional Embedding directly into Query/Key projections.
- **Fused SwiGLU**: Combines gating linear projections and SiLU activations into a single SRAM kernel.
- **Fused LayerNorm / RMSNorm**: Fuses mean/variance reduction and elementwise affine scaling.

---

## 🚀 2. Hardware-Aware Attention Mechanisms

Self-attention computes $O(N^2)$ interactions across sequence length $N$. TruthGPT dynamically selects the fastest hardware-aware attention backend:

```mermaid
graph TD
    SeqIn["Input Sequence Q, K, V"] --> CheckHw{"Hardware & Kernel Check"}
    CheckHw -->|NVIDIA Ampere/Hopper| Flash2["FlashAttention-2 (SRAM Tiling, Zero IO Overhead)"]
    CheckHw -->|PyTorch 2.0 Native| SDPA["F.scaled_dot_product_attention (Auto-Backend)"]
    CheckHw -->|Very Long Context (32k+)| FocusLLM["FocusLLM / LongRoPE (Chunked Attention)"]
    CheckHw -->|Inference Serving| PagedAttn["PagedAttention (Virtual Memory Pages)"]
```

### 1. FlashAttention-2
- **Mechanism**: Splits Q, K, V matrices into blocks that fit within fast on-chip GPU SRAM (L1/Shared Memory), computing softmax incrementally without materializing the $N \times N$ attention matrix in High Bandwidth Memory (HBM).
- **Speedup**: 2x–4x faster than eager attention; memory complexity drops from $O(N^2)$ to $O(N)$.

### 2. PagedAttention (Inference Serving)
- **Problem**: Standard KV-caching pre-allocates contiguous memory for the maximum possible sequence length, wasting 60%–80% of VRAM due to internal and external fragmentation.
- **Solution**: Allocates KV-cache blocks dynamically in non-contiguous physical memory pages, enabling up to 4x higher serving concurrency.

---

## 🎯 3. Precision Modes & Tensor Cores

| Precision Mode | Bits | Dynamic Range | Hardware Support | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **TF32** | 19-bit | Same as FP32 (8-bit exp) | NVIDIA Ampere (A100, RTX 30/40) & Hopper | Default on Ampere+. 8x faster matmuls with zero code changes. |
| **BF16 (BFloat16)** | 16-bit | Same as FP32 (8-bit exp) | NVIDIA Ampere, Hopper, newer CPUs | **Recommended**. High numerical stability, no loss scaler required. |
| **FP16** | 16-bit | Narrow (5-bit exp) | NVIDIA Volta (V100), Turing (T4) | Legacy fallback. Requires dynamic `GradScaler` to prevent underflow. |
| **FP8 (E4M3 / E5M2)** | 8-bit | Extreme compression | NVIDIA Hopper (H100/H200/B200) | Ultra-large model pretraining and ultra-fast inference. |
| **INT8 / INT4 (AWQ)** | 8/4-bit | Quantized integer weights | All modern CUDA GPUs | Low-VRAM fine-tuning (QLoRA) and memory-constrained serving. |

#### Configuration in YAML:
```yaml
training:
  mixed_precision: "bf16"
  allow_tf32: true
```

---

## 💾 4. Memory Optimization & Scaling Strategies

### Gradient Checkpointing (Activation Recomputation)
- **Mechanism**: During the forward pass, intermediate layer activations are discarded from memory. During the backward pass, activations are recomputed on-the-fly from boundary checkpoints.
- **Trade-off**: Incurs ~20% additional compute overhead, but reduces activation memory by **up to 75%**, allowing significantly larger batch sizes.

```yaml
model:
  gradient_checkpointing: true
```

---

### Dynamic Length Bucketing & Smart Padding

Standard data loaders pad all sequences in a dataset to a fixed global max length (e.g., 2048 tokens). If the average sample is only 300 tokens, 85% of matrix operations compute zeroes.

TruthGPT groups samples of similar length into discrete cluster bins before batching, reducing redundant computation by up to **3x**:

```yaml
data:
  bucket_by_length: true
  bucket_bins: [64, 128, 256, 512, 1024, 2048]
```

---

### Distributed Memory Reduction (ZeRO / FSDP)

When training large models across multiple GPUs:

- **ZeRO-Stage 1**: Partitions optimizer states across GPUs (4x memory reduction).
- **ZeRO-Stage 2**: Partitions optimizer states + gradients across GPUs (8x memory reduction).
- **ZeRO-Stage 3 / FSDP**: Fully shards optimizer states, gradients, and model parameters across nodes, allowing 70B+ parameter models to fit on consumer/enterprise GPU clusters.

---

## 🛠️ 5. Advanced Optimizers Comparison

| Optimizer | Memory per Param | Update Characteristic | Recommended For |
| :--- | :--- | :--- | :--- |
| **Fused AdamW** | 8 bytes (fp32 moments) | Standard adaptive momentum with fused CUDA kernel | Baseline for small/medium models. |
| **Lion** | 4 bytes (sign-based momentum) | Uses `sign()` of gradient momentum; faster convergence | Pre-training and large-scale fine-tuning. |
| **Sophia-G** | 4 bytes (Hessian diagonal) | Curvature-aware second-order optimizer | Fast convergence with non-convex loss surfaces. |
| **8-Bit AdamW (bitsandbytes)** | 2 bytes (quantized moments) | Block-wise dynamic quantization of optimizer states | Fine-tuning on 8GB-24GB GPUs without accuracy loss. |

---

## 🕵️ 6. Performance Troubleshooting Matrix

| Symptom | Primary Root Cause | Recommended Remedy |
| :--- | :--- | :--- |
| **Low GPU Compute Utilization (<40%)** | CPU bottleneck or dataloader starvation | 1. Increase `num_workers` and `prefetch_factor`.<br>2. Enable `torch_compile: true` with `mode: "reduce-overhead"`.<br>3. Increase `train_batch_size`. |
| **CUDA Out of Memory (OOM)** | Activation memory explosion or optimizer overhead | 1. Enable `gradient_checkpointing: true`.<br>2. Switch to `mixed_precision: "bf16"`.<br>3. Enable 8-bit AdamW (`optimizer.type: "adamw_8bit"`).<br>4. Reduce batch size and increase `grad_accum_steps`. |
| **Training Throughput is Low** | Excessive padding in variable-length batches | Enable `data.bucket_by_length: true`. |
| **Loss is NaN / Diverging** | Gradient underflow/overflow in FP16 | 1. Switch to `mixed_precision: "bf16"`.<br>2. Lower `learning_rate` and enable gradient clipping (`max_grad_norm: 1.0`). |
