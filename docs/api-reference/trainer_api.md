# Trainer API Reference

The `GenericTrainer` class (`trainers/trainer.py`) is the primary interface for distributed model training, evaluation, and checkpoint management.

---

## 🏛️ `GenericTrainer` Class

```python
class GenericTrainer:
    def __init__(
        self,
        cfg: TrainerConfig,
        train_texts: Union[List[str], Iterable[str]],
        val_texts: Optional[Union[List[str], Iterable[str]]] = None,
        text_field_max_len: int = 512,
        callbacks: Optional[List[Callback]] = None,
        data_options: Optional[Dict[str, Any]] = None,
    ) -> None: ...
```

### Constructor Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `cfg` | `TrainerConfig` | *Required* | Strongly typed configuration dataclass containing model, training, and logging settings. |
| `train_texts` | `Iterable[str]` | *Required* | Training text samples for tokenization and dataset creation. |
| `val_texts` | `Iterable[str]` | `None` | Validation text samples for evaluation passes. |
| `text_field_max_len` | `int` | `512` | Token truncation limit for sequence inputs. |
| `callbacks` | `List[Callback]` | `None` | Custom lifecycle hooks (e.g. `WandbCallback`, `TensorBoardCallback`). |
| `data_options` | `Dict[str, Any]` | `None` | Advanced data loading options (bucketing thresholds, custom collators). |

---

## 🛠️ Public Methods

### `train() -> Dict[str, float]`
Executes the primary training loop for `cfg.epochs`.
- **Returns**: Dictionary containing final training metrics (final loss, best validation loss, total step count).
- **Exceptions**: Handles `KeyboardInterrupt` with safe checkpoint flush.

### `evaluate() -> float`
Performs a full evaluation pass on the validation dataset.
- **Returns**: Floating point average validation loss (and perplexity).
- **Behavior**: Uses EMA averaged weights if `cfg.ema_enabled=True`.

### `save_checkpoint(path: Optional[str] = None) -> str`
Saves an atomic `safetensors` model checkpoint and optimizer state.
- **Returns**: Absolute path to written checkpoint file.

---

## 📄 `TrainerConfig` Dataclass Reference

```python
@dataclass
class TrainerConfig:
    model_name: str = "gpt2"
    output_dir: str = "runs/run"
    epochs: int = 3
    train_batch_size: int = 8
    eval_batch_size: int = 8
    grad_accum_steps: int = 2
    learning_rate: float = 5e-5
    weight_decay: float = 0.01
    mixed_precision: str = "bf16"        # "bf16", "fp16", "none"
    allow_tf32: bool = True
    torch_compile: bool = False
    compile_mode: str = "default"        # "default", "reduce-overhead", "max-autotune"
    lora_enabled: bool = False
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    ema_enabled: bool = True
    ema_decay: float = 0.999
    fused_adamw: bool = True
    ckpt_interval_steps: int = 1000
    ckpt_keep_last: int = 3
```
