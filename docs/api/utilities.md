# 🛠️ Utilities API Reference

The `utils` subsystem provides developer tools for environment diagnostics, hardware telemetry, training visualization, checkpoint exporting, dataset profiling, and automated integrity validation.

---

## 🔍 System Health & Diagnostics (`utils/health_check.py`)

```python
from utils.health_check import HealthChecker, DiagnosticReport
```

### Methods:

#### `HealthChecker.run_full_diagnostic(strict: bool = False) -> DiagnosticReport`
Runs a multi-point audit of the execution host and runtime libraries.
- `strict` (*bool*): When `True`, raises `EnvironmentError` if recommended accelerator packages (e.g. FlashAttention, Triton) are missing.
- **Returns**: `DiagnosticReport` object containing hardware specs, installed versions, and pass/warn/fail status flags.

#### `DiagnosticReport.to_dict() -> dict`
Serializes audit metrics to a JSON-compatible dictionary.

#### `DiagnosticReport.print_rich_table()`
Renders a color-coded terminal summary table using Rich.

### CLI Usage:
```bash
python utils/health_check.py --strict --json-output report.json
```

---

## 📊 Live Training Telemetry (`utils/monitor_training.py`)

```python
from utils.monitor_training import LiveTrainingMonitor, TelemetryConfig
```

A curses/rich live dashboard that tracks GPU hardware metrics and training dynamics in real time.

```python
# Programmatic usage in custom training loops
monitor = LiveTrainingMonitor(
    log_dir="runs/experiment_llama_7b",
    refresh_rate_hz=2.0,
    track_gpu_telemetry=True
)

monitor.start()
# Inside training step:
monitor.log_step(step=step, loss=loss_val, lr=current_lr, tokens_per_sec=tok_sec)
monitor.stop()
```

### Monitored Metrics:
- **GPU Hardware**: Compute Utilization %, VRAM Used/Total (GB), Temperature (°C), Power Draw (Watts).
- **Training Progression**: Step, Moving Average Loss, Validation Loss, Perplexity, Learning Rate.
- **Throughput**: Instantaneous and cumulative Tokens/Second, Step Time (ms), Estimated Time of Arrival (ETA).

---

## 📈 Visualization & Reporting (`utils/visualize_training.py`)

```python
from utils.visualize_training import TrainingVisualizer
```

Generates publication-quality charts and summaries of completed training sessions.

```python
visualizer = TrainingVisualizer(run_directory="runs/experiment_llama_7b")

# Generate loss and learning rate curve plots
visualizer.plot_curves(
    output_path="runs/experiment_llama_7b/training_report.png",
    smooth_weight=0.6,
    include_validation=True
)

# Export summary JSON
summary = visualizer.generate_summary()
print(f"Total Trained Tokens: {summary['total_tokens']:,}")
print(f"Final Validation Loss: {summary['final_val_loss']:.4f}")
```

### CLI Usage:
```bash
python utils/visualize_training.py runs/experiment_llama_7b --plot --summary --export-json summary.json
```

---

## 📦 Checkpoint Exporting & Conversion (`utils/export_model.py`)

```python
from utils.export_model import export_checkpoint, ConversionTarget
```

Converts raw PyTorch `.pt` training checkpoints into optimized production formats:

```python
export_checkpoint(
    checkpoint_path="checkpoints/epoch_3.pt",
    output_directory="models/exported_llama/",
    target=ConversionTarget.SAFETENSORS,  # SAFETENSORS, ONNX, TENSORRT
    dtype="bfloat16",
    merge_lora_weights=True
)
```

### Supported Export Targets:
- **`SAFETENSORS`**: Zero-copy memory-mapped tensor format for Hugging Face and vLLM.
- **`ONNX`**: Open Neural Network Exchange graph with dynamic sequence length axes.
- **`TENSORRT`**: Compiled TensorRT execution engine optimized for target GPU architecture.

---

## 📑 Dataset Profiling & Tokenizer Metrics (`utils/dataset_profiler.py`)

```python
from utils.dataset_profiler import DatasetProfiler

profiler = DatasetProfiler(dataset_path="data/train.jsonl", tokenizer_name="meta-llama/Llama-2-7b-hf")
stats = profiler.analyze_length_distribution(num_buckets=16)

print(f"Min Tokens: {stats.min_len} | Max Tokens: {stats.max_len} | Median: {stats.median_len}")
profiler.recommend_bucket_edges(target_padding_efficiency=0.95)
```

---

## 🔗 Related Resources
- [Health & Diagnostics Getting Started Guide](../getting_started/health_and_diagnostics.md)
- [CLI Reference & Interactive Terminals](../guides/cli_and_terminals.md)
- [Trainers API Reference](trainers.md)
