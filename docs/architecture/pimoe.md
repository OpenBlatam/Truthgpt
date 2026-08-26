# 🌌 PiMoE: Physics-Informed Mixture of Experts

**PiMoE** (Physics-Informed Mixture of Experts) is TruthGPT's proprietary architecture that fuses deep learning transformer scaling with physical domain inductive biases and adaptive dynamic routing.

---

## 🌟 Conceptual Overview

Standard Mixture of Experts (MoE) models route tokens purely based on learned statistical softmax distributions, which frequently leads to:
1. **Expert Routing Collapse**: A small subset of experts receives all tokens while others remain idle.
2. **High Memory Overhead**: Inefficient loading and synchronization of unutilized expert weights.
3. **Lack of Physical Invariance**: Poor generalization on scientific, causal, and structured reasoning tasks.

**PiMoE solves this by introducing physical conservation laws and dynamical systems equations into the routing gate:**

```
                  ┌───────────────────────────────┐
                  │          Input Token          │
                  └──────────────┬────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       ┌────────────────────┐          ┌────────────────────┐
       │ Statistical Gating │          │ Physics-Informed   │
       │ Network (Softmax)  │          │ Hamiltonian Gate   │
       └─────────┬──────────┘          └─────────┬──────────┘
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
                   ┌───────────────────────────┐
                   │ Regularized Routing Matrix│
                   │ (Conservation Constrained)│
                   └─────────────┬─────────────┘
             ┌───────────────────┼───────────────────┐
             ▼                   ▼                   ▼
      ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
      │   Expert 1   │    │   Expert 2   │    │   Expert N   │
      │ (Kinematics) │    │  (Thermodyn) │    │   (General)  │
      └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
             └───────────────────┼───────────────────┘
                                 ▼
                  ┌──────────────────────────────┐
                  │ Weighted Fused Representation│
                  └──────────────────────────────┘
```

---

## ⚙️ Mathematical Formulation

### 1. Hamiltonian Conservation Constraint
The routing logits $H_i(x)$ incorporate an energy conservation penalty:

$$\mathcal{L}_{\text{balance}} = \alpha \sum_{i=1}^E \left( \frac{1}{B} \sum_{b=1}^B P_i(x_b) - \frac{1}{E} \right)^2 + \beta \sum_{i=1}^E \nabla_x \mathcal{H}_i(x)$$

Where $\mathcal{H}_i(x)$ represents the dynamic expert state Hamiltonian, enforcing smooth trajectory distributions across expert activations.

### 2. Sparsity & Expert Capacity Factor
To ensure deterministic execution times on GPU hardware, PiMoE uses a fixed **Expert Capacity Factor ($C$)**:

$$\text{Capacity} = \text{ceil}\left( \frac{\text{Tokens Per Batch} \times \text{Top-K}}{\text{Number of Experts}} \times C \right)$$

Tokens exceeding capacity are routed via a lightweight residual bypass without crashing the tensor kernels.

---

## 🛠️ Usage in Transformer Blocks

```python
from optimization_core.modules.feed_forward.mixture_of_experts import PiMoEFeedForward

pimoe_layer = PiMoEFeedForward(
    d_model=1024,
    d_ff=4096,
    num_experts=8,
    top_k=2,
    capacity_factor=1.25,
    physics_regularizer=0.05
)

x = torch.randn(16, 128, 1024, device="cuda")
out, aux_loss = pimoe_layer(x)
```
