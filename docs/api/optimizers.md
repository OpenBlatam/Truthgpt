# ⚡ Optimizers & Schedulers API Reference

The `optimizers` and `factories.optimizer` modules provide a unified optimization architecture for TruthGPT, featuring parameter decay grouping, automated kernel fusion fallbacks, 8-bit quantized optimizers, advanced schedulers, and enterprise-grade multi-level optimizer wrappers.

---

## 🏛️ TruthGPT Optimizer System

**Location**: `optimizers.__init__` & `optimizers.core.base_truthgpt_optimizer`

```python
from optimizers import (
    create_truthgpt_optimizer,
    create_production_optimizer,
    UnifiedTruthGPTOptimizer,
    ProductionOptimizer,
    OptimizationLevel
)

# Initialize multi-level enterprise optimizer
optimizer = create_truthgpt_optimizer(
    level="enterprise",
    config={
        "learning_rate": 1e-4,
        "weight_decay": 0.01,
        "enable_quantization": True,
        "enable_cuda_graphs": True
    }
)
```

### Optimization Levels

| Level | Enum Value | Features Enabled |
| :--- | :--- | :--- |
| `"basic"` | `OptimizationLevel.BASIC` | Parameter decay grouping, baseline AdamW / SGD |
| `"advanced"` | `OptimizationLevel.ADVANCED` | Fused CUDA kernels, mixed precision AMP scaling, cosine LR schedule |
| `"expert"` | `OptimizationLevel.EXPERT` | 8-bit quantization, gradient checkpointing, FlashAttention fusion |
| `"enterprise"` | `OptimizationLevel.ENTERPRISE` | Multi-GPU ZeRO sharding, JIT graph compilation, adaptive memory management |

---

## 🏭 Parameter Groups & Factory Registry

**Location**: `factories.optimizer`

```python
from factories.optimizer import (
    create_optimizer,
    create_param_groups,
    create_scheduler,
    OptimizerConfig,
    LRSchedulerConfig,
    OPTIMIZERS,
    SCHEDULERS
)

# 1. Separate model parameters into decay and no-decay groups (biases & LayerNorm excluded)
param_groups = create_param_groups(model, weight_decay=0.01)

# 2. Build optimizer from configuration
opt_config = OptimizerConfig(
    name="adamw",
    lr=1e-4,
    weight_decay=0.01,
    fused=True
)
optimizer = create_optimizer(opt_config, model)

# 3. Build learning rate scheduler
sched_config = LRSchedulerConfig(
    name="cosine",
    warmup_steps=500,
    total_steps=10000,
    min_lr=1e-6
)
scheduler = create_scheduler(sched_config, optimizer)
```

---

## 🏎️ Built-in Optimizer Algorithms

The `OPTIMIZERS` registry includes built-in implementations and dynamic dispatch:

### 1. `adamw` (Fused AdamW)
Standard decoupled weight decay optimizer with automated PyTorch fused CUDA kernel acceleration:

```python
optimizer = OPTIMIZERS.build("adamw", param_groups, lr=1e-4, weight_decay=0.01, fused=True)
```

### 2. `adamw_8bit` (BitsAndBytes 8-Bit Quantized)
Saves up to $75\%$ of optimizer VRAM by compressing first and second momentum tensors into non-linear 8-bit representations:

```python
optimizer = OPTIMIZERS.build("adamw_8bit", param_groups, lr=1e-4, weight_decay=0.01)
```

### 3. `lion` (EvoLved Sign Momentum)
Uses sign-based momentum updates with $50\%$ less memory than AdamW:

```python
optimizer = OPTIMIZERS.build("lion", param_groups, lr=1e-4, weight_decay=0.01)
```

### 4. `adafactor` (Sub-Linear Memory Optimizer)
Low-rank factorization of second-moment statistics for massive model pretraining:

```python
optimizer = OPTIMIZERS.build("adafactor", param_groups, lr=1e-3)
```

---

## 📈 Learning Rate Schedulers

The `SCHEDULERS` registry supports:

| Scheduler | Identifier | Arguments | Description |
| :--- | :--- | :--- | :--- |
| **Cosine with Warmup** | `"cosine"` | `warmup_steps`, `total_steps`, `min_lr` | Linear warmup followed by cosine annealing decay. |
| **Linear Warmup** | `"linear"` | `warmup_steps`, `total_steps` | Linear warmup followed by linear decay to 0. |
| **Warmup-Stable-Decay** | `"wsd"` | `warmup_steps`, `stable_steps`, `decay_steps` | Constant learning rate for bulk training, rapid power-law decay. |
| **One Cycle LR** | `"one_cycle"` | `total_steps`, `max_lr`, `pct_start` | Super-convergence 1cycle policy. |
| **Polynomial Decay** | `"polynomial"` | `warmup_steps`, `total_steps`, `power` | Polynomial exponent decay. |
| **Constant with Warmup** | `"constant"` | `warmup_steps` | Linear warmup followed by fixed learning rate. |

---

## 🏢 `ProductionOptimizer`

**Location**: `optimizers.production.production_optimizer`

```python
from optimizers.production.production_optimizer import ProductionOptimizer

prod_opt = ProductionOptimizer(config={"target": "latency", "precision": "fp16"})
optimized_model = prod_opt.optimize(model)
```
