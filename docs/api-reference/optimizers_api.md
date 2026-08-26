# Optimizers API Reference

The `OPTIMIZER_REGISTRY` (`factories/registry.py` and `optimizers/`) provides the factory and lookup interface for all built-in and custom deep learning optimizers.

---

## 🏛️ `OPTIMIZER_REGISTRY` API

```python
from factories.registry import OPTIMIZER_REGISTRY

# Register a custom optimizer
@OPTIMIZER_REGISTRY.register("my_optimizer")
class MyCustomOptimizer(torch.optim.Optimizer):
    ...

# Instantiate via build factory
optimizer = OPTIMIZER_REGISTRY.build(
    "lion",
    model.parameters(),
    lr=1e-4,
    betas=(0.9, 0.99),
    weight_decay=0.01
)
```

---

## 📋 Available Optimizers in Registry

| Registry Key | Class | Module Path | Default Arguments |
| :--- | :--- | :--- | :--- |
| `"adamw"` | `torch.optim.AdamW` | `torch.optim` | `lr=1e-3, betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-2` |
| `"fused_adamw"` | `FusedAdamW` | `optimizers/pytorch/fused_adamw.py` | `lr=1e-3, betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-2` |
| `"lion"` | `LionOptimizer` | `optimizers/lion.py` | `lr=1e-4, betas=(0.9, 0.99), weight_decay=1e-2` |
| `"sophia"` | `SophiaG` | `optimizers/sophia.py` | `lr=2e-4, betas=(0.965, 0.99), rho=0.04, weight_decay=1e-1` |
| `"prodigy"` | `Prodigy` | `optimizers/prodigy.py` | `lr=1.0, d_coef=1.0, weight_decay=1e-2` |
| `"adamw_8bit"` | `AdamW8bit` | `bitsandbytes.optim` | `lr=1e-3, betas=(0.9, 0.999), is_paged=True` |
