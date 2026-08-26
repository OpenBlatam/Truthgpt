# 🛠️ Utilities API Reference

The `utils` module contains developer tools for health checks, environment diagnostics, live training monitoring, performance profiling, and dataset processing.

---

## 🔍 System Health Check (`utils/health_check.py`)

Performs an automated multi-point verification of the execution environment:

```bash
python utils/health_check.py
```

### Audited Components:
- **Python Version**: Validates Python 3.8+ compatibility.
- **PyTorch & CUDA**: Checks CUDA availability, compute capability, cuDNN version, and VRAM capacity.
- **Accelerator Backends**: Validates FlashAttention, Triton, xFormers, and TensorRT runtime libraries.
- **Polyglot Modules**: Verifies native Rust and C++ shared object linkage.

---

## 📊 Live Terminal Monitor (`utils/monitor_training.py`)

A curses/rich-based live dashboard that monitors training runs in real time:

```bash
python utils/monitor_training.py runs/my_experiment
```

### Displays:
- **Loss Progression**: Step-by-step moving average loss and validation loss curves.
- **Hardware Telemetry**: GPU utilization %, VRAM consumption, temperature, and power draw.
- **Throughput**: Real-time Tokens/sec and TFLOPs efficiency metrics.

---

## 📈 Post-Training Visualizer (`utils/visualize_training.py`)

Generates statistical reports and high-resolution plots of completed runs:

```bash
python utils/visualize_training.py runs/my_experiment --plot --summary
```

### Arguments:
- `--summary`: Prints total token count, best validation checkpoint, and training wall-clock time.
- `--plot`: Generates `loss_curve.png` and `lr_schedule.png` in the run directory.
- `--export-json`: Exports all step metrics into structured JSON format for external BI tools.
