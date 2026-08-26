# 🔬 Research Papers API Reference

TruthGPT contains a curated registry of 48+ State-Of-The-Art (SOTA) research paper implementations covering attention optimizations, context scaling, sparse architectures, and adaptive optimizers.

---

## 🏛️ `PaperRegistry`

```python
from optimization_core.papers import PaperRegistry
```

### Methods

#### `list_papers(category: Optional[str] = None) -> List[PaperSpec]`
Returns a list of all registered SOTA paper specifications.
- **Categories**: `"attention"`, `"context_extension"`, `"optimizers"`, `"moe"`, `"quantization"`.

#### `get_paper(paper_id: str) -> PaperSpec`
Retrieves detailed metadata, citations, and model factory hooks for a specific paper.

#### `apply_paper_to_model(paper_id: str, model: torch.nn.Module, **kwargs) -> torch.nn.Module`
Transforms an existing model using the architectural enhancements introduced in the specified paper.

---

## 📚 Selected Implemented Papers

| Paper ID | Title | Key Mechanism |
| :--- | :--- | :--- |
| **`flash_attn_v2`** | *FlashAttention-2: Faster Attention with Better Parallelism* | SRAM tiled matrix multiplication with online softmax reduction. |
| **`longrope_2024`** | *LongRoPE: Extending Context Windows Beyond 2 Million Tokens* | Non-uniform positional interpolation with evolutionary search. |
| **`focus_llm`** | *FocusLLM: Scaling Context to Infinite Lengths via Focus Tokens* | Local-global chunked memory compression for extreme sequence lengths. |
| **`lion_opt_2023`** | *Symbolic Discovery of Optimization Algorithms* | Sign-momentum update rule reducing optimizer memory footprint by 50%. |
| **`sophia_2023`** | *Sophia: A Second-Order Stochastic Optimizer for LLMs* | Diagonal Hessian estimation preventing catastrophic gradient spikes. |
| **`swiglu_2020`** | *GLU Variants Improve Transformer* | Swish-Gated Linear Units improving transformer feed-forward expressive capacity. |

---

## 💻 CLI Paper Discovery

```bash
# List all registered papers
openclaw papers list

# Get deep breakdown of LongRoPE implementation
openclaw papers info longrope_2024
```
