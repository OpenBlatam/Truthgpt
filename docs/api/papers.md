# 🔬 Research Papers API Reference & Catalog

TruthGPT contains a native registry of State-Of-The-Art (SOTA) research paper implementations covering attention optimizations, context scaling, reasoning architectures, test-time reinforcement learning, and adaptive quantization.

All paper implementations are modular, typed, and registered within `papers`.

---

## 🏛️ `PaperRegistry`

**Location**: `papers.registry`

```python
from papers.registry import (
    PaperRegistry,
    PaperMetadata,
    PaperCategory,
    PaperResult,
    default_registry,
    create_algorithm,
    list_papers,
    get_paper
)
```

### Core Methods:

#### `list_papers(category: Optional[PaperCategory] = None) -> List[PaperMetadata]`
Returns all registered research paper specifications. Optional filtering by `PaperCategory` enum (`ATTENTION`, `CONTEXT`, `REASONING`, `QUANTIZATION`, `AGENTS`, `TTRL`, `EFFICIENCY`, `STABILITY`).

#### `get_paper(paper_id: str) -> Optional[PaperMetadata]`
Retrieves paper metadata, mathematical formulation, venue, year, and default hyperparameters.

#### `create_algorithm(paper_id: str, config: Optional[Any] = None) -> BasePaperModule`
Instantiates a research paper module with optional strongly-typed configuration.

---

## 📚 Complete Implemented Research Papers Catalog

| Paper ID | Class Name | Category | Mathematical / Algorithmic Mechanism |
| :--- | :--- | :--- | :--- |
| **`snap_kv`** | `SnapKVCacheCompressor` | Context / Memory | Identifies observation window and critical feature clusters to compress prompt KV-cache by up to $16\times$. |
| **`chain_of_draft`** | `ChainOfDraft` | Reasoning / Efficiency | Minimalist step-wise reasoning tokens reducing token generation length by $70\%$ while preserving answer accuracy. |
| **`confspec_reasoning`** | `ConfSpecReasoner` | Speculative / Reasoning | Confidence-guided speculative drafting that dynamically throttles draft tree width based on token entropy. |
| **`moqae_quant`** | `MoQAEQuantizer` | Quantization | Mixture of Quantization Auto-Encoders routing tensor blocks to specialized non-linear codebooks. |
| **`adaptive_kv_quant`** | `AdaptiveKVQuantizer` | Quantization | Per-head dynamic bitwidth allocation ($2\text{--}8\text{ bits}$) allocating higher precision to outlier-sensitive attention heads. |
| **`elastic_reasoning`** | `ElasticReasoning` | Test-Time Compute | Dynamically modulates reasoning compute budgets per question difficulty without human intervention. |
| **`intuitor_self_certainty`**| `IntuitorReward` | Self-Certainty / RL | Test-time reward modeling using token predictive entropy and self-certainty margin scoring. |
| **`echo_ttrl`** | `EchoOptimizer` | Test-Time RL | Echo Test-Time Reinforcement Learning updating transient adapter weights during live inference sessions. |
| **`atomic_agentic_memory`** | `AtomicAgenticMemory` | Swarms / Memory | Graph-structured episodic memory with hierarchical vector compression and sub-millisecond retrieval. |
| **`dynamic_topology_routing`**| `DynamicTopologyRouter` | Swarms / Routing | Dynamic message routing for multi-agent swarms using Bayesian communication cost minimization. |
| **`discriminative_verification`**| `DiscriminativeVerifier` | Step Verification | Multi-step mathematical proof verification assigning calibrated validity probabilities to intermediate thoughts. |
| **`distinct_leaf_decoding`**| `DistinctLeafEnumerator` | Tree Search | Tree-search decoding algorithm maximizing diversity across output branches to avoid repetitive mode collapse. |
| **`entropy_guided_inference`**| `EntropyGuidedInference` | Decoding | Real-time token entropy tracking that automatically switches between greedy decoding and nucleus sampling. |
| **`fp16_stability`** | `FP16Stability` | Numerical Stability | Dynamic loss scaling, gradient norm thresholding, and underflow mitigation for mixed precision training. |
| **`progressive_thought_encoding`**| `ProgressiveThoughtEncoder`| Thought Compression | Recursive latent thought encoding for recurrent reasoning transformers. |
| **`reinforced_attention`**| `ReinforcedAttentionLearner` | Attention | Policy gradient attention weighting that rewards focus on salient evidence tokens in long context prompts. |
| **`speculative_decoding`**| `SpeculativeDrafter` | Inference Acceleration | Dual-model speculative drafting verifying $K$ draft tokens in a single target model forward pass. |
| **`speculative_prefill`**| `SpeculativePrefillCompressor` | KV Prefill | Early-layer attention truncation accelerating prompt prefill latency by $2.8\times$. |

---

## 💻 Python Usage Examples

### Example 1: Applying SnapKV to an Active Inference Engine

```python
import torch
from papers.snap_kv import SnapKVCacheCompressor
from papers.config import SnapKVConfig

# Initialize compressor
config = SnapKVConfig(window_size=32, kernel_size=5, max_capacity_prompt=2048)
compressor = SnapKVCacheCompressor(config=config)

# Compress KV Cache during prompt prefill
compressed_k, compressed_v = compressor.compress(
    attn_weights=attention_probabilities,
    key_states=key_tensor,
    value_states=value_tensor
)
print(f"Compressed KV-Cache shape: {compressed_k.shape}")
```

---

### Example 2: Enabling Chain-of-Draft Token-Efficient Reasoning

```python
from papers.chain_of_draft import ChainOfDraft
from papers.config import ChainOfDraftConfig

config = ChainOfDraftConfig(max_draft_tokens=128, draft_delimiter="->")
cod = ChainOfDraft(config=config)

result = cod.process({"prompt": "Calculate the derivative of f(x) = x^3 * ln(x) at x = 2"})
print("Result:", result.output_data)
```
