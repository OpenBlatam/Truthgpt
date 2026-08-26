# Optimization Techniques & Acceleration

> [!NOTE]
> The full optimization manual has been expanded in our structured documentation portal at **[Optimization: Hardware Acceleration Guide](optimization/acceleration_guide.md)**.

TruthGPT leverages cutting-edge optimization techniques to maximize GPU compute efficiency (MFU) and minimize VRAM consumption:

1. **TorchInductor Graph Compilation**: JIT graph fusion and kernel generation.
2. **TF32 & Mixed Precision (BF16 / FP16)**: Multi-precision matrix math on Tensor Cores.
3. **Flash Attention 2 & 3**: IO-aware SRAM tiling for $O(N)$ linear memory scaling.
4. **Paged KV-Cache**: Virtual memory paging for autoregressive decoding.
5. **Fused & Advanced Optimizers**: Lion, Sophia, Prodigy, and 8-bit BitsAndBytes.

---

## 📚 Optimization Documentation

- **[Hardware Acceleration Guide](optimization/acceleration_guide.md)**
- **[Optimizers & Schedulers](optimization/optimizers.md)**
- **[KV-Cache Acceleration](optimization/kv_cache.md)**
- **[Custom Triton & CUDA Kernels](optimization/custom_kernels.md)**
