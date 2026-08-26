# Troubleshooting Matrix & FAQ

This guide resolves common issues encountered during distributed training, inference serving, JIT compilation, and multi-agent execution.

---

## 🛑 Common Issues & Solutions

### 1. CUDA Out of Memory (`CUDA OOM`)
**Symptom**: `RuntimeError: CUDA out of memory. Tried to allocate 2.40 GiB`

**Solutions**:
1. **Enable Gradient Checkpointing**: Set `gradient_checkpointing: true` in your YAML config. Discards forward activations and reduces VRAM by up to 75%.
2. **Reduce Micro-Batch Size & Increase Accumulation**: Lower `train_batch_size: 2` and increase `grad_accum_steps: 16` to preserve effective batch size.
3. **Switch to 8-Bit Optimizers**: Use `optimizer_type: "adamw_8bit"` or `optimizer_type: "lion"` to save 50%–75% of optimizer state VRAM.
4. **Use BF16 / FP16 Precision**: Pure FP32 requires double the tensor memory footprint.

---

### 2. Loss is `NaN` or Exploding
**Symptom**: `Step 140 | Loss: nan | Grad Norm: 1420.5`

**Solutions**:
1. **Switch FP16 to BF16**: FP16 has limited exponent dynamic range ($10^{-5}$ to $65504$), easily overflowing to `NaN`. BF16 matches FP32 dynamic range ($10^{-38}$ to $10^{38}$) and eliminates gradient underflow.
2. **Enable Gradient Clipping**: Set `max_grad_norm: 1.0` in training settings.
3. **Add Learning Rate Warmup**: Set `warmup_ratio: 0.03` (or 300 warmup steps) to prevent destabilizing weight updates during initial iterations.
4. **Check for Corrupted Data**: Run `python utils/health_check.py` or inspect dataset tokens for non-finite values.

---

### 3. Low GPU Utilization (<50% MFU)
**Symptom**: `nvidia-smi` shows 25%–40% GPU utilization during training.

**Solutions**:
1. **Enable Dynamic Length Bucketing**: Set `bucket_by_length: true` to stop computing padding zeroes.
2. **Increase Dataloader Workers**: Set `num_workers: 4`, `prefetch_factor: 2`, and `persistent_workers: true`.
3. **Enable `torch.compile`**: Eliminates Python interpreter loop overhead with `torch_compile: true` and `compile_mode: "reduce-overhead"`.

---

### 4. `torch.compile` Compilation Errors
**Symptom**: `torch._dynamo.exc.Unsupported: ...` or C++ compiler missing.

**Solutions**:
1. **Install C++ Build Tools**:
   - On Linux: `sudo apt-get install build-essential`
   - On Windows: Install Visual Studio C++ Build Tools.
2. **Use Dynamic Shapes**: In inference, ensure `dynamic=True` is passed to avoid re-compiling for each new prompt token length.

---

## ❓ Frequently Asked Questions (FAQ)

#### Q: How does TruthGPT compare to vanilla HuggingFace Trainer?
**A**: TruthGPT provides higher MFU out of the box through integrated dynamic length bucketing, fused optimizers (Lion, Sophia), paged memory managers, polyglot C-FFI extensions, and autonomous agent swarms.

#### Q: Can I run TruthGPT without an NVIDIA GPU?
**A**: Yes. TruthGPT runs natively on Apple Silicon (via Metal Performance Shaders - MPS) and CPU modes for testing and agent workflows.

#### Q: Where are checkpoints saved and how do I resume training?
**A**: Checkpoints are stored in `runs/<output_dir>/`. Set `resume_enabled: true` in your configuration to automatically pick up from the latest saved checkpoint.
