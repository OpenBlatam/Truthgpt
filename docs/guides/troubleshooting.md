# 🕵️ Troubleshooting & Diagnostics Guide

This guide provides diagnostics and proven resolutions for common training, compilation, CUDA, and agent issues.

---

## 🚨 Common Issues & Resolutions

### 1. `CUDA out of memory (OOM)`
**Symptoms**: PyTorch raises `torch.cuda.OutOfMemoryError` during forward or backward pass.

**Diagnostic Checklist & Solutions**:
1. **Enable Gradient Checkpointing**:
   ```yaml
   model:
     gradient_checkpointing: true
   ```
2. **Switch to BF16 Mixed Precision**:
   ```yaml
   precision:
     mixed_precision: "bf16"
   ```
3. **Use 8-bit Optimizer**:
   ```yaml
   training:
     optimizer: "adamw_8bit"
   ```
4. **Reduce Micro-Batch Size and Increase Gradient Accumulation**:
   ```yaml
   training:
     train_batch_size: 2
     grad_accum_steps: 16
   ```

---

### 2. `Loss is NaN / Inf` or Divergence
**Symptoms**: Loss drops to `nan` or spikes to infinity after several training steps.

**Diagnostic Checklist & Solutions**:
1. **FP16 Underflow**: Switch `mixed_precision` from `"fp16"` to `"bf16"`. BFloat16 preserves the full dynamic range of FP32.
2. **Gradient Explosion**: Lower `learning_rate` (e.g. from `1e-3` to `1e-4`) and enforce gradient clipping:
   ```yaml
   training:
     max_grad_norm: 1.0
   ```
3. **Bad Data Samples**: Check for empty or corrupted text samples in the dataset using `utils/health_check.py`.

---

### 3. Low GPU Utilization (< 40%)
**Symptoms**: `nvidia-smi` shows low GPU Compute Utilization while CPU utilization is high.

**Diagnostic Checklist & Solutions**:
1. **Dataloader Bottleneck (Data Starvation)**:
   - Increase `num_workers: 4` or `8`.
   - Set `persistent_workers: true` and `prefetch_factor: 2`.
2. **Dynamic Padding Waste**: Enable `bucket_by_length: true` so the dataloader does not compute excessive padding tokens.
3. **CPU Kernel Launch Overhead**: Enable `torch_compile: true` with `compile_mode: "reduce-overhead"`.

---

### 4. Distributed Multi-GPU Deadlock
**Symptoms**: Multi-GPU training freezes on Step 0 or epoch end without throwing an exception.

**Diagnostic Checklist & Solutions**:
1. **Unsynchronized Dataloader Lengths**: Ensure all distributed ranks process identical sample counts:
   ```yaml
   distributed:
     drop_last: true
   ```
2. **NCCL Communication Timeout**: Set environment variable before launching:
   ```bash
   export NCCL_DEBUG=INFO
   export TORCH_DISTRIBUTED_DEBUG=DETAIL
   export NCCL_TIMEOUT=1800
   ```

---

### 5. Swarm Routing or Tool Execution Errors
**Symptoms**: Agents return empty observations or fail to route queries.

**Diagnostic Checklist & Solutions**:
1. **Inspect Traces**: Query `/v1/traces/recent` to inspect the exact failing tool invocation.
2. **Check SQLite Memory Lock**: If running multiple concurrent processes, ensure SQLite connection timeouts are configured or switch to PostgreSQL.
