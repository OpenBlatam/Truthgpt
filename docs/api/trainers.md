# 🚅 Trainers API Reference

The `trainers` module houses the execution engine of TruthGPT, orchestrating training loops, distributed synchronization, mixed-precision loss scaling, evaluation, and fault-tolerant checkpointing.

---

## 🏛️ `GenericTrainer`

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

### Core Methods

#### `train()`
```python
def train(self) -> None
```
Executes the full training loop over `cfg.epochs`. Manages gradient accumulation, mixed precision (`torch.cuda.amp`), gradient clipping, learning rate schedule steps, logging, and automatic checkpointing.

#### `evaluate()`
```python
def evaluate(self) -> float
```
Performs a validation pass over `val_texts`, calculating and returning the mean cross-entropy evaluation loss.

#### `save_checkpoint(step: int, is_best: bool = False)`
```python
def save_checkpoint(self, step: int, is_best: bool = False) -> str
```
Serializes model weights (using `safetensors`), optimizer states, scheduler steps, and RNG seeds. Returns the absolute file path of the saved checkpoint.

#### `load_checkpoint(path: str)`
```python
def load_checkpoint(self, path: str) -> None
```
Restores model weights, optimizer buffers, and training state from disk for seamless recovery.

---

## ⚡ Callback Interface

```python
class Callback:
    def on_train_begin(self, state: TrainingState) -> None: ...
    def on_step_begin(self, step: int, state: TrainingState) -> None: ...
    def on_step_end(self, step: int, loss: float, state: TrainingState) -> None: ...
    def on_epoch_end(self, epoch: int, state: TrainingState) -> None: ...
    def on_train_end(self, state: TrainingState) -> None: ...
```

### Available Built-in Callbacks:
- `WandbCallback`: Automatic Weights & Biases metric streaming.
- `TensorBoardCallback`: Local TensorBoard event logging.
- `ProgressCallback`: Real-time console progress bar with tokens/sec throughput tracking.
- `EarlyStoppingCallback`: Halts training when validation loss stops improving.
