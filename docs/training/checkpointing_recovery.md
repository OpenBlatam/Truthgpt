# Checkpointing, EMA & Fault Tolerance

The **TruthGPT Checkpoint & State Subsystem** (`trainers/checkpoint_manager.py`, `trainers/ema_manager.py`) manages safe model serialization, Exponential Moving Average (EMA) weight smoothing, and automated disaster recovery.

---

## 💾 SafeTensors & PyTorch Serialization

By default, TruthGPT serializes weights using HuggingFace `safetensors` format:
- **Zero-Copy Memory Mapping (`mmap`)**: Up to 10x faster model loading compared to standard `torch.save`.
- **Security**: Protects against arbitrary Python pickle code execution vulnerabilities.

```yaml
checkpointing:
  save_safetensors: true
  output_dir: "runs/my_model_checkpoints"
  ckpt_interval_steps: 1000
  ckpt_keep_last: 3
```

---

## 📈 Exponential Moving Average (EMA)

EMA maintains an exponentially smoothed shadow copy of model weights:
$$\theta_{\text{EMA}}^{(t)} = \beta \cdot \theta_{\text{EMA}}^{(t-1)} + (1 - \beta) \cdot \theta^{(t)}$$

- **Advantage**: EMA weights regularly achieve 0.5 - 1.5 lower perplexity on evaluation benchmarks than raw final step weights by smoothing out noisy gradient steps.
- **Evaluation Integration**: During validation passes, `GenericTrainer` automatically evaluates on the EMA weights without corrupting the active training gradients.

```yaml
checkpointing:
  ema_enabled: true
  ema_decay: 0.999
```

---

## 🔄 Crash Auto-Resume

To resume training without losing epoch or optimizer state:

```yaml
checkpointing:
  resume_enabled: true
```

When started, `CheckpointManager` scans `output_dir`:
1. Discovers the latest checkpoint step (e.g. `checkpoint-step-4000.pt` or `model.safetensors`).
2. Loads model weights and shadow EMA buffers.
3. Restores optimizer states, momentum tensors, and learning rate scheduler step count.
4. Restores CUDA RNG states for reproducible data sampling.
