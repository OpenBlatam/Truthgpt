# Triton & CUDA Kernel Acceleration

The **TruthGPT Kernel Subsystem** (`compiler/kernels/`) provides custom high-throughput kernels implemented in OpenAI **Triton** and NVIDIA **CUDA C++** that out-perform naive PyTorch layer compositions by eliminating High-Bandwidth Memory (HBM) roundtrips.

---

## ⚡ Key Accelerated Kernels

### 1. Fused SwiGLU Kernel (Triton)

Standard PyTorch computes SwiGLU by launching three distinct CUDA kernels:
1. `gate = silu(x @ W_gate)`
2. `up = x @ W_up`
3. `out = gate * up`

The TruthGPT Fused SwiGLU kernel executes the elementwise multiplication and SiLU activation entirely inside GPU SRAM (Shared Memory):

- **Memory Bandwidth Reduction**: $2.8\times$ fewer memory load/store operations.
- **Speedup**: $1.65\times$ faster forward/backward pass.

---

### 2. FlashAttention-2 & Scaled Dot Product Attention (SDPA)

- **SRAM Tiling**: Divides Queries ($Q$), Keys ($K$), and Values ($V$) into discrete blocks (typically $64 \times 64$ or $128 \times 64$).
- **Online Softmax**: Computes softmax scaling factors dynamically without materializing the full $N \times N$ attention matrix in GPU RAM.
- **Linear Memory**: Reduces attention memory complexity from $O(N^2)$ to $O(N)$ with respect to sequence length $N$.

---

### 3. Fused Cross-Entropy Loss

Standard cross-entropy creates a full vocabulary logits tensor in GPU memory (e.g. $[B, S, V] = [4, 2048, 32000] = 1.05 \text{ GB}$ of FP32 memory).
The TruthGPT Fused Cross-Entropy kernel combines the final linear layer projection, log-softmax, and loss reduction into a streaming chunked kernel:

- **Peak VRAM Reduction**: Saves up to **4GB to 12GB of VRAM** per training step on large vocabularies ($V \ge 32k$).

---

## 🛠️ Inspecting & Benchmarking Kernels

Run the included kernel benchmark suite:

```bash
python -m compiler.kernels.benchmark_all --dtype bfloat16 --batch-size 8 --seq-len 2048
```
