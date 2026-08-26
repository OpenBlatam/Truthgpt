# Advanced Optimizers & Schedulers

TruthGPT Optimization Core integrates a rich suite of SOTA first-order, second-order, and adaptive learning rate optimizers (`optimizers/`) designed to accelerate convergence and reduce optimizer memory footprints.

---

## 🏎️ Optimizer Comparison & Selection Guide

| Optimizer | Best Use Case | Memory per Param | Key Advantages |
| :--- | :--- | :--- | :--- |
| **Fused AdamW** | General Pre-training & Fine-tuning | 8 bytes (FP32 $m, v$) | Single-kernel GPU execution, rock-solid stability |
| **Lion (EvoLved Sign Momentum)** | Large-scale LLM Training | 4 bytes (FP32 $m$) | **50% lower optimizer VRAM**, faster step times, higher generalization |
| **Sophia-G (Second-Order)** | Pre-training Transformer Models | 8 bytes (Hessian diag) | 2x faster convergence than AdamW by scaling with curvature |
| **Prodigy (D-Adaptation)** | Zero-Tuning Experiments | 8 bytes | Automatic learning rate adaptation; no manual LR tuning needed |
| **8-Bit BitsAndBytes AdamW** | Consumer GPU Fine-tuning | 2 bytes (INT8 $m, v$) | **75% lower optimizer VRAM** with dynamic block-wise quantization |

---

## 🔬 Mathematical Formulations

### 1. Lion (EvoLved Sign Momentum)
Lion tracks only the first momentum vector and uses the sign function for parameter updates:

$$c_t = \beta_1 m_{t-1} + (1 - \beta_1) g_t$$

$$\theta_t = \theta_{t-1} - \eta_t (\text{sign}(c_t) + \lambda \theta_{t-1})$$

$$m_t = \beta_2 m_{t-1} + (1 - \beta_2) g_t$$

*Advantage*: Eliminates second momentum $v_t$, cutting optimizer state memory in half while performing uniform-magnitude coordinate updates.

### 2. Sophia-G (Second-order Clipped Stochastic Diagonal Hessian)
Sophia uses periodic lightweight Hutchinson stochastic estimators to approximate the diagonal of the Hessian matrix $h_t$, clipping extreme curvature updates:

$$m_t = \beta_1 m_{t-1} + (1 - \beta_1) g_t$$

$$\theta_t = \theta_{t-1} - \eta_t \cdot \text{clip}\left(\frac{m_t}{\max(h_t, \epsilon)}, \rho\right) - \eta_t \lambda \theta_{t-1}$$

*Advantage*: Navigates sharp valleys and non-convex loss surfaces 2x faster than standard AdamW.

---

## 📈 Learning Rate Schedulers

TruthGPT provides built-in schedules with warmup and minimum decay bounds:
- **Cosine Annealing with Warmup (`cosine`)**: Standard for LLM pre-training; smooth decay to $\eta_{\text{min}}$.
- **Linear Decay with Warmup (`linear`)**: Linear descent popular in instruction tuning and classification.
- **OneCycleLR (`one_cycle`)**: Fast super-convergence scheduling for quick domain adaptation.
- **Constant with Warmup (`constant`)**: Stabilizes early warmup without post-warmup decay.

---

## 🛠️ Usage in Python API & Config

```python
from factories.registry import OPTIMIZER_REGISTRY

# Build Lion optimizer directly from registry
optimizer = OPTIMIZER_REGISTRY.build(
    "lion",
    model.parameters(),
    lr=1e-4,
    betas=(0.9, 0.99),
    weight_decay=0.01
)
```

```yaml
training:
  optimizer_type: "lion"
  learning_rate: 0.0001
  weight_decay: 0.01
  scheduler: "cosine"
  warmup_ratio: 0.03
```
