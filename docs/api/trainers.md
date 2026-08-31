# 🚅 Trainers & Checkpointing API Reference

The `trainers` module houses the execution engine of TruthGPT, orchestrating training loops, distributed synchronization, mixed-precision loss scaling, evaluation, Exponential Moving Average (EMA), and fault-tolerant checkpointing.

---

## 🏛️ `GenericTrainer`

**Location**: `trainers.trainer`

```python
from trainers.trainer import GenericTrainer
```

### Signature
```python
class GenericTrainer:
    def __init__(
        self,
        cfg: TrainerConfig,
        train_texts: List[str] | Iterable[str],
        val_texts: Optional[List[str] | Iterable[str]] = None,
        text_field_max_len: int = 512,
        callbacks: Optional[List[Callback]] = None,
        data_options: Optional[Dict[str, Any]] = None,
        tokenizer: Optional[PreTrainedTokenizerBase] = None,
        model: Optional[nn.Module] = None,
    )
```

### Constructor Parameters
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `cfg` | `TrainerConfig` | *Required* | Complete training and model hyperparameters configuration object. |
| `train_texts` | `Iterable[str]` | *Required* | Raw text data or tokens for model training. |
| `val_texts` | `Iterable[str]` | `None` | Validation dataset for periodic evaluation and loss tracking. |
| `text_field_max_len`| `int` | `512` | Token length limit for tokenization and dynamic padding. |
| `callbacks` | `List[Callback]`| `None` | Custom callbacks (e.g. `WandbCallback`, `TensorBoardCallback`, `EarlyStoppingCallback`). |
| `data_options` | `Dict[str, Any]`| `None` | Advanced dataloader options (e.g. `bucket_by_length`, `dynamic_pad`). |
| `tokenizer` | `PreTrainedTokenizer` | `None` | Pre-initialized tokenizer (auto-loaded from `cfg.model_name` if omitted). |
| `model` | `nn.Module` | `None` | Pre-instantiated PyTorch model (auto-loaded from `cfg.model_name` if omitted). |

---

### Core Execution Methods

#### `train()`
```python
def train(self) -> None
```
Executes the primary training loop across `cfg.epochs`.
- **Execution Flow**:
  1. Initializes distributed environment and seeds.
  2. Injects LoRA adapters / quantizations if configured.
  3. Compiles computation graph via `torch.compile` if enabled.
  4. Manages micro-batch forward passes under AMP (`torch.autocast`).
  5. Scales losses via `GradScaler` and performs gradient accumulation.
  6. Clips gradients to `max_grad_norm` and updates weights via fused optimizer.
  7. Updates EMA shadow weights.
  8. Triggers periodic validation passes and asynchronous checkpoint serialization.

#### `evaluate() -> Dict[str, float]`
```python
def evaluate(self) -> Dict[str, float]
```
Performs an exhaustive evaluation pass across the validation dataset.
- **Returns**: Dictionary containing `eval_loss`, `perplexity`, and `eval_runtime_sec`.
- **Behavior**: Temporarily replaces model weights with EMA shadow parameters if EMA is active, disables gradient computation, and aggregates distributed metrics.

#### `save_checkpoint(epoch: int, step: int, metrics: Dict[str, float]) -> str`
```python
def save_checkpoint(self, epoch: int, step: int, metrics: Dict[str, float]) -> str
```
Delegates to `CheckpointManager` to safely write `safetensors` model weights, optimizer states, scheduler steps, and metadata JSON. Returns the checkpoint file path.

#### `resume_from_checkpoint(checkpoint_path: str)`
```python
def resume_from_checkpoint(self, checkpoint_path: str) -> None
```
Restores model weights, optimizer states, dynamic loss scaler, and scheduler step counter from a previous snapshot.

---

## 🧩 Subsystem Managers

### 1. `CheckpointManager` (`trainers.checkpoint_manager`)
Manages safe atomic saving, rotation, and disk cleanup of training checkpoints:
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

## ⚡ Callback Interface

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
- `WandbCallback`: Automatic Weights & Biases metric streaming.
- `TensorBoardCallback`: Local TensorBoard event logging.
- `ProgressCallback`: Real-time console progress bar with tokens/sec throughput tracking.
- `EarlyStoppingCallback`: Halts training when validation loss stops improving.
- `ProfilerCallback`: Captures PyTorch Chrome trace timelines for CUDA kernel profiling.
