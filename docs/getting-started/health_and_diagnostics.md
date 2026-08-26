# Health Checks & Environment Diagnostics

TruthGPT includes a comprehensive diagnostic suite to audit system readiness, verify CUDA driver compatibility, monitor GPU memory allocations, and diagnose bottlenecks before launching compute-intensive jobs.

---

## 🩺 Built-In Diagnostic Tools

### 1. Master Environment Health Check

Run the top-level audit tool:

```bash
python utils/health_check.py
```

#### What It Audits:
- **Python Runtime**: Verifies Python 3.8+ (recommends 3.10+).
- **Core ML Frameworks**: Checks `torch`, `transformers`, `accelerate`, `peft`, `safetensors`.
- **CUDA & GPU Architecture**:
  - Validates CUDA driver vs PyTorch runtime build.
  - Queries GPU Compute Capability (e.g. 8.0 for A100, 8.9 for RTX 4090, 9.0 for H100).
  - Tests TF32 and BF16 availability.
- **Module Resolution & Imports**: Audits internal factories, registries, and trainers.
- **Disk & VRAM Availability**: Checks writable cache and checkpoint directories.

---

## 📊 2. Real-Time Training Monitor

Monitor active training runs from a second terminal window or SSH session:

```bash
# Monitor directory for checkpoint writes, loss, and throughput
python utils/monitor_training.py runs/llama2_enterprise
```

### Metrics Displayed:
- Current Step & Epoch progress bar.
- Instantaneous and smoothed Loss.
- Tokens per Second (Throughput).
- GPU VRAM Utilization and Temperature.
- Checkpoint commit timestamps and disk sizes.

---

## 📈 3. Post-Training Visualization & Reporting

Analyze completed experiments and loss convergence:

```bash
# Print summary of best loss, training duration, and saved checkpoints
python utils/visualize_training.py runs/llama2_enterprise --summary

# Generate loss convergence plot image
python utils/visualize_training.py runs/llama2_enterprise --plot
```

---

## 🔍 4. Troubleshooting Diagnostic Matrix

| Health Check Diagnostic | Root Cause | Solution |
| :--- | :--- | :--- |
| `CUDA is available: False` | PyTorch CPU-only binary installed or CUDA driver mismatch | Reinstall PyTorch via `--index-url https://download.pytorch.org/whl/cu121` |
| `BFloat16 supported: False` | GPU is pre-Ampere architecture (e.g. GTX 1080, Tesla V100, T4) | Change `mixed_precision` to `"fp16"` in YAML config |
| `Flash Attention import failed` | `flash-attn` package not compiled for current CUDA version | Run `python install_extras.py flash_attn` or use PyTorch native SDPA |
| `Torch compile error: C++ compiler missing` | No MSVC on Windows or `build-essential` missing on Linux | Install GCC/Clang (`apt install build-essential`) or Visual Studio C++ Build Tools |
