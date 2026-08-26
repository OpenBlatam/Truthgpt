# Callbacks, Monitoring & Profiling

The **TruthGPT Callbacks & Monitoring Subsystem** (`trainers/callbacks.py`, `trainers/metrics_tracker.py`, `trainers/profiler.py`) provides real-time telemetry, experiment tracking, and custom event hooks.

---

## 📊 Supported Observability Backends

### 1. Weights & Biases (WandB)

Logs live train loss, validation loss, tokens-per-second, learning rate, GPU memory allocation, and gradient norm histograms.

```yaml
logging:
  callbacks: ["wandb"]
  wandb_project: "truthgpt-frontier"
  wandb_run_name: "llama3-muon-finetune"
  wandb_entity: "my-team"
```

### 2. TensorBoard

Outputs event logs readable by TensorBoard.

```bash
tensorboard --logdir runs/
```

---

## 🛠️ Building Custom Callbacks

Inherit from `Callback` in `trainers.callbacks`:

```python
from trainers.callbacks import Callback
from trainers.trainer import GenericTrainer

class SlackAlertCallback(Callback):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def on_train_begin(self, trainer: GenericTrainer):
        print("Training has initiated...")

    def on_epoch_end(self, trainer: GenericTrainer, epoch: int, metrics: dict):
        val_loss = metrics.get("val_loss", 0.0)
        print(f"Epoch {epoch} finished with Validation Loss: {val_loss:.4f}")

    def on_train_end(self, trainer: GenericTrainer):
        print("Training completed successfully!")
```

Pass the callback to `GenericTrainer`:

```python
trainer = GenericTrainer(
    cfg=config,
    train_texts=train_texts,
    val_texts=val_texts,
    callbacks=[SlackAlertCallback("https://hooks.slack.com/...")]
)
```

---

## ⚡ PyTorch Profiler Integration

Profile CPU/CUDA kernel execution, memory allocations, and compute bottlenecks:

```yaml
profiler:
  enabled: true
  wait_steps: 5
  warmup_steps: 5
  active_steps: 10
  repeat: 1
  export_chrome_trace: true
  export_tensorboard: true
```

Chrome traces (`.json`) can be viewed directly in `chrome://tracing` or [Speedscope](https://www.speedscope.app/).
