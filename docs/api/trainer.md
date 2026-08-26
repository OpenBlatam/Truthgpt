# Trainer Engine API Reference

The `GenericTrainer` class and its accompanying management subsystems constitute the core training engine of the TruthGPT Optimization Core.

---

## 🏎️ `GenericTrainer`

**Location**: `trainers.trainer`

```python
class GenericTrainer:
    def __init__(
        self,
        cfg: TrainerConfig,
        train_texts: List[str] | Iterable[str],
        val_texts: List[str] | Iterable[str],
        text_field_max_len: int = 512,
        callbacks: Optional[List[Callback]] = None,
        data_options: Optional[Dict[str, Any]] = None,
        tokenizer: Optional[PreTrainedTokenizerBase] = None,
        model: Optional[nn.Module] = None,
    )
```

### Initialization Arguments

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `cfg` | `TrainerConfig` | *Required* | Complete trainer configuration dataclass containing optimization, hardware, and logging parameters. |
| `train_texts` | `Iterable[str]` | *Required* | Raw or tokenized training sequence data. |
| `val_texts` | `Iterable[str]` | *Required* | Validation dataset used for periodic evaluation passes. |
| `text_field_max_len` | `int` | `512` | Token sequence truncation and dynamic bucketing upper boundary. |
| `callbacks` | `List[Callback]` | `None` | Optional list of event-driven lifecycle callbacks. |
| `data_options` | `Dict[str, Any]`| `None` | Advanced data ingestion flags (e.g., streaming buffers, custom collator settings). |
| `tokenizer` | `PreTrainedTokenizer` | `None` | Pre-initialized tokenizer (auto-loaded from `cfg.model_name` if omitted). |
| `model` | `nn.Module` | `None` | Pre-instantiated PyTorch model (auto-loaded from `cfg.model_name` if omitted). |

---

### Core Execution Methods

#### `train()`
Executes the primary training loop across `cfg.epochs`.
- **Flow**:
  1. Initializes distributed environment and seeds.
  2. Injects LoRA adapters / quantizations if configured.
  3. Compiles computation graph via `torch.compile` if enabled.
  4. Manages micro-batch forward passes under AMP (`torch.autocast`).
  5. Scales losses via `GradScaler` and performs gradient accumulation.
  6. Clips gradients to `max_grad_norm` and updates weights via fused optimizer.
  7. Updates EMA shadow weights.
  8. Triggers periodic validation passes and asynchronous checkpoint serialization.

#### `evaluate() -> Dict[str, float]`
Performs an exhaustive evaluation pass across the validation dataset.
- **Returns**: Dictionary containing `eval_loss`, `perplexity`, and `eval_runtime_sec`.
- **Behavior**: Temporarily replaces model weights with EMA shadow parameters if EMA is active, disables gradient computation, and aggregates distributed metrics.

#### `save_checkpoint(epoch: int, step: int, metrics: Dict[str, float]) -> str`
Delegates to `CheckpointManager` to safely write `safetensors` model weights, optimizer states, scheduler steps, and metadata JSON.

#### `resume_from_checkpoint(checkpoint_path: str)`
Restores model weights, optimizer states, dynamic loss scaler, and scheduler step counter from a previous snapshot.

---

## 🧩 Subsystem Managers

### 1. `CheckpointManager` (`trainers.checkpoint_manager`)
Manages safe atomic saving, rotation, and disk cleanup of training checkpoints.
- **Rotation**: Automatically retains only the top `ckpt_keep_last` checkpoints based on lowest validation loss.
- **Format**: Serializes tensor weights using `safetensors` for memory-mapped, zero-copy deserialization.

### 2. `EMAManager` (`trainers.ema_manager`)
Maintains an Exponential Moving Average of model parameters:
$$\theta_{\text{EMA}} \leftarrow \beta \cdot \theta_{\text{EMA}} + (1 - \beta) \cdot \theta_{\text{model}}$$
- Produces smoother evaluation metrics and prevents overfitting in late training stages.

### 3. `DistManager` (`trainers.dist_manager`)
Wraps distributed communication primitives:
- Initializes `torch.distributed` with NCCL (GPU) or Gloo (CPU) backends.
- Wraps models with `DistributedDataParallel` (DDP) or Fully Sharded Data Parallel (FSDP).
- Handles cross-rank tensor reductions and gradient barrier synchronizations.

---

## 🔔 Callbacks API

**Location**: `trainers.callbacks`

Implement custom training hooks by inheriting from `Callback`:

```python
from trainers.callbacks import Callback

class CustomMetricsCallback(Callback):
    def on_train_begin(self, trainer, cfg):
        print("Training starting...")

    def on_step_end(self, trainer, step: int, loss: float, lr: float):
        if step % 100 == 0:
            print(f"Step {step}: Loss = {loss:.4f}, LR = {lr:.6e}")

    def on_evaluate_end(self, trainer, metrics: dict):
        print(f"Validation complete: Eval Loss = {metrics['eval_loss']:.4f}")

    def on_train_end(self, trainer):
        print("Training completed successfully.")
```

### Built-in Callbacks
- `WandbCallback`: Automatic logging of gradients, learning rates, loss curves, and system telemetry to Weights & Biases.
- `TensorBoardCallback`: Writes event summaries to `runs/` for live TensorBoard dashboards.
- `ProfilerCallback`: Captures PyTorch Chrome trace timelines for CUDA kernel profiling.
