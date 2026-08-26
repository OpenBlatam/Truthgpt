# Advanced Optimizers & Schedulers

TruthGPT Optimization Core integrates a rich suite of SOTA first-order, second-order, and adaptive learning rate optimizers, each registered in `factories/optimizer_factory.py`.

---

## 📊 Optimizer Comparison & Selection Guide

| Optimizer | Type / Order | Memory per Param | Best Use Case | Key Advantages |
| :--- | :--- | :--- | :--- | :--- |
| **SOAP** | 2nd-Order Preconditioned | ~16 bytes | LLM Pretraining & SFT | Faster convergence than AdamW via curvature preconditioning |
| **Muon** | Matrix Orthogonalized | ~8 bytes | Large Transformer Layers | Updates 2D matrices via Newton-Schulz orthogonalization |
| **AdamW** | 1st-Order Adaptive | 16 bytes | Standard Finetuning & General NLP | Extremely robust baseline, decoupled weight decay |
| **Sophia** | 2nd-Order Hessian-Estimated | 12 bytes | Large Pretraining | 2x faster wall-clock pretraining via diagonal Hessian estimates |
| **Lion** | Sign Momentum | 8 bytes | Vision Transformers & Diffusion | 50% less optimizer memory than AdamW |
| **Adafactor** | Factored 2nd Moment | 4 bytes | Extreme Memory-Constrained Runs | Factorizes optimizer state matrices, near-zero overhead |

---

## ⚡ Mathematical Overview of SOTA Optimizers

### 1. SOAP (Second-Order Algorithm with Preconditioning)
SOAP computes structured preconditioning matrices $L$ and $R$ for each weight tensor $W \in \mathbb{R}^{m \times n}$:

$$P = L^{-1/2} G R^{-1/2}$$

where $G$ is the gradient tensor, applying eigen-basis transformations without inverting full $mn \times mn$ Hessians.

### 2. Muon (Momentum Orthogonalized by Newton-Schulz)
Muon treats weight updates as orthogonal matrix operations:

$$O_{k+1} = \frac{1}{2} O_k (3I - O_k^T O_k)$$

Iterative Newton-Schulz polynomial iterations constrain spectral norms, drastically stabilizing deep Transformer activations.

---

## 💻 Instantiation via OptimizerFactory

```python
from factories.optimizer_factory import OptimizerFactory

# Create SOTA SOAP optimizer
optimizer = OptimizerFactory.create(
    optimizer_type="soap",
    model_params=model.parameters(),
    lr=3e-4,
    weight_decay=0.01,
    precondition_frequency=10
)

# Create Muon optimizer
muon_opt = OptimizerFactory.create(
    optimizer_type="muon",
    model_params=model.parameters(),
    lr=0.02,
    momentum=0.95
)
```

---

## 📈 Learning Rate Schedulers

TruthGPT provides built-in schedulers via `factories/scheduler_factory.py`:
- **CosineAnnealingWithWarmup**: Smooth cosine decay down to minimum LR.
- **WSD (Warmup-Stable-Decay)**: Extended flat learning rate phase followed by rapid polynomial decay (optimal for dataset scaling).
- **LinearDecayWithWarmup**: Standard linear ramp and decay.
