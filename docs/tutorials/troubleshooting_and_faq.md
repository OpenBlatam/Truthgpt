# Troubleshooting & Frequently Asked Questions (FAQ)

Common issues, solutions, and architectural FAQs when training and serving models with TruthGPT.

---

## 🛑 Common Issues & Solutions

### 1. `CUDA Out of Memory (OOM)` During Training
- **Fix 1**: Enable activation checkpointing in YAML: `model.gradient_checkpointing: true`.
- **Fix 2**: Switch optimizer from standard FP32 AdamW to `optimizer: "lion"` or `optimizer: "galore"`.
- **Fix 3**: Reduce `train_batch_size` (e.g. from 8 to 2) and increase `grad_accum_steps` (e.g. from 2 to 8) to maintain the identical effective batch size.
- **Fix 4**: Enable mixed precision: `mixed_precision: "bf16"`.

---

### 2. Loss is `NaN` or `Inf`
- **Cause**: Exploding gradients during FP16 training or learning rate set too high.
- **Fix 1**: Use `mixed_precision: "bf16"` (Ampere/Hopper GPUs avoid FP16 underflow).
- **Fix 2**: Add gradient clipping: `optimization.max_grad_norm: 1.0`.
- **Fix 3**: Lower max learning rate by a factor of $2\times$ or $5\times$.

---

### 3. `torch.compile` is Slow on First Step
- **Explanation**: This is expected behavior. `TorchInductor` traces the computational graph and compiles Triton kernels during the initial 1-3 forward/backward passes. Subsequent iterations run significantly faster.
- **Tip**: Set `compile_mode: "default"` for rapid development and `"max-autotune"` only for long production runs.

---

## ❓ Frequently Asked Questions

#### Q: Does TruthGPT support Apple Silicon (M1/M2/M3)?
**A**: Yes! TruthGPT automatically selects PyTorch MPS (`Metal Performance Shaders`) when CUDA is not detected.

#### Q: How is TruthGPT different from HuggingFace Accelerate?
**A**: TruthGPT provides an integrated polyglot compiler subsystem (MLIR, TensorRT, Triton, C++, Rust), built-in 48+ SOTA paper algorithms, autonomous multi-agent swarm orchestration (OpenClaw), and continuous batching inference serving out-of-the-box.
