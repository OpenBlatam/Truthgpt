# Speculative Decoding & Verification

Autoregressive language model generation is memory-bandwidth bound: each token generation step requires reading billions of model parameters from GPU HBM to compute a single token vector.

**Speculative Decoding** accelerates inference by utilizing a small, fast draft model (e.g. 1B params) to propose $K$ candidate tokens in parallel, which are then verified simultaneously by the large target model (e.g. 70B params) in a **single forward pass**.

---

## 🏎️ How Speculative Decoding Works

```mermaid
sequenceDiagram
    autonumber
    participant Draft as Fast Draft Model (1B)
    participant Target as Large Target Model (70B)
    participant Sampler as Modified Rejection Sampler

    Note over Draft: Propose K candidate tokens
    Draft->>Draft: Token 1 -> Token 2 -> Token 3 -> Token 4 (4 quick steps)
    Draft->>Target: Pass sequence [x, t1, t2, t3, t4]

    Note over Target: Single Batched Forward Pass
    Target->>Sampler: Compute Target Logits for all positions simultaneously
    Sampler->>Sampler: Accept t1, t2, t3; Reject t4 & sample replacement t4'
    Sampler-->>Draft: Output accepted [t1, t2, t3, t4'] (3.2x speedup)
```

---

## ⚡ Mathematical Guarantees

Speculative decoding preserves the exact output probability distribution of the large target model. Using modified rejection sampling:

$$P(\text{accept } x_i) = \min\left(1, \frac{P_{\text{target}}(x_i \mid x_{<i})}{P_{\text{draft}}(x_i \mid x_{<i})}\right)$$

If a candidate token is rejected at position $i$, a replacement token is sampled from:

$$P_{\text{resample}}(x) = \frac{\max(0, P_{\text{target}}(x) - P_{\text{draft}}(x))}{\sum_y \max(0, P_{\text{target}}(y) - P_{\text{draft}}(y))}$$

- **Zero Quality Loss**: The output distribution is mathematically identical to running the large model alone.
- **2x–3.5x End-to-End Speedup**: Achieved whenever draft model proposals have high acceptance rates (e.g. 70%–85%).

---

## 🛠️ Configuration Example

```yaml
inference:
  speculative:
    enabled: true
    draft_model_name: "meta-llama/Llama-2-7b-chat-hf"
    target_model_name: "meta-llama/Llama-2-70b-chat-hf"
    num_speculative_tokens: 5
    acceptance_threshold: 0.85
```
