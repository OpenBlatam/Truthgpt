# ⚡ Optimizers & Schedulers API Reference

The `optimizers` module provides state-of-the-art optimization algorithms, 8-bit quantized optimizers, and adaptive learning rate schedulers for deep neural network training.

---

## 🏛️ Supported Optimizers

### 1. `Lion` (EvoLved Sign Momentum)
Lion tracks only momentum (not variance), using the sign operation to compute updates. It consumes **$50\%$ less optimizer memory** than AdamW and achieves faster empirical convergence on LLMs.

```python
from optimizers.lion import Lion

optimizer = Lion(
    model.parameters(),
    lr=1e-4,
    betas=(0.9, 0.99),
    weight_decay=0.01
)
```

---

### 2. `Sophia` (Second-Order Stochastic Optimization)
Sophia estimates the diagonal Hessian using stochastic Hutchinson traces, preventing catastrophic loss spikes and achieving $2\times$ faster pretraining than AdamW.

```python
from optimizers.sophia import SophiaG

optimizer = SophiaG(
    model.parameters(),
    lr=2e-4,
    betas=(0.965, 0.99),
    rho=0.04,
    weight_decay=0.1
)
```

---

### 3. `AdamW8Bit` (BitsAndBytes Quantized Optimizer)
Compresses optimizer first and second momentum states into 8-bit non-linear blockwise representations, saving up to **$75\%$ of optimizer VRAM**.

```python
from optimizers.quantized import AdamW8Bit

optimizer = AdamW8Bit(
    model.parameters(),
    lr=5e-5,
    betas=(0.9, 0.999),
    weight_decay=0.01
)
```

---

### 4. `Muon` (Momentum Orthogonalized Matrix Optimizer)
Designed for transformer matrix weights, applying orthogonal updates via Newton-Schulz iterations for maximum stability.

```python
from optimizers.muon import Muon

optimizer = Muon(
    model.parameters(),
    lr=0.02,
    momentum=0.95,
    nesterov=True,
    ns_steps=5
)
```

---

## 📈 Learning Rate Schedulers

| Scheduler | Class | Key Arguments | Description |
| :--- | :--- | :--- | :--- |
| **Cosine with Warmup** | `CosineAnnealingWithWarmup` | `warmup_steps`, `max_steps`, `min_lr` | Linear warmup followed by cosine decay down to `min_lr`. Standard for LLM training. |
| **Linear Decay with Warmup**| `LinearWarmupScheduler` | `warmup_steps`, `total_steps` | Linear ramp up then linear decay to zero. |
| **WSD (Warmup-Stable-Decay)**| `WSDScheduler` | `warmup_steps`, `stable_steps`, `decay_steps` | Constant maximum learning rate for the majority of training, with rapid power-law decay at the end. |
