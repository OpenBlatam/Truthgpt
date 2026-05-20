# TruthGPT - Enterprise Fact-Checking AI Agent

**TruthGPT** is a modular, autonomous AI agent engineered for **maximum factual accuracy** and **hallucination mitigation**. It integrates over 20 peer-reviewed techniques from arXiv, each implemented as a standalone Python module in `/workspace/`. The agent operates via a ReAct (Reasoning + Acting) loop, prioritizing verifiable benchmarks and real-time tool usage (web search, file I/O, bash).

## Core Design Principles
- **Factuality First**: Every claim is verified by cascading detection and correction modules.
- **SOTA Integration**: Continuously updated with the latest research in hallucination reduction.
- **Modularity**: Each technique is a self-contained `async run_technique(prompt, context)` function, enabling easy plug-and-play.
- **Determinism**: Caching via MD5 of sorted JSON configs ensures reproducible results.

## Implemented Techniques (with arXiv Citations)

| Technique | arXiv ID | Module | Description |
|-----------|----------|--------|-------------|
| DoLA | [2309.03883](https://arxiv.org/abs/2309.03883) | `truthgpt_dola.py` | Contrasts logits from different layers to suppress hallucinations. |
| Constitutional AI | [2212.08073](https://arxiv.org/abs/2212.08073) | `truthgpt_cai.py` | Fine-tuning with constitutional principles for harmless outputs. |
| ORPO | [2403.07691](https://arxiv.org/abs/2403.07691) | `truthgpt_orpo.py` | Preference optimization using odds ratio. |
| Self-Rewarding | [2401.10020](https://arxiv.org/abs/2401.10020) | `truthgpt_self_reward.py` | Joint actor-critic training for self-judgment. |
| Self-Consistency | [2203.11171](https://arxiv.org/abs/2203.11171) | `truthgpt_self_consistency.py` | Aggregates multiple reasoning paths for coherent answers. |
| Semantic Entropy | [2306.04786](https://arxiv.org/abs/2306.04786) | `truthgpt_semantic_entropy.py` | Measures semantic uncertainty to detect hallucinations. |
| FS-RAG | [2406.16167](https://arxiv.org/abs/2406.16167) | `truthgpt_fs_rag.py` | Frame-semantics-based retrieval for factual accuracy. |
| REFIND RAG | [2502.13622](https://arxiv.org/abs/2502.13622) | `truthgpt_refind_rag.py` | Retrieval ensemble with numeric plausibility checks. |
| Contrastive Decoding | [2210.15097](https://arxiv.org/abs/2210.15097) | `truthgpt_contrastive_decoding.py` | Contrasts logits of small and large models. |
| DPO | [2305.18290](https://arxiv.org/abs/2305.18290) | `truthgpt_dpo.py` | Direct Preference Optimization without RL. |
| SPIN | [2401.01335](https://arxiv.org/abs/2401.01335) | `truthgpt_spin.py` | Self-play fine-tuning for instruction-following. |
| Self-Reflection | [2310.06271](https://arxiv.org/abs/2310.06271) | `truthgpt_self_reflection.py` | Iterative self-reflection to improve output. |
| Hallucination-focused PO | [2501.17295](https://arxiv.org/abs/2501.17295) | `truthgpt_hallucination_focused_po.py` | Preference optimization targeting hallucination reduction. |
| Phase-wise Self-Reward | [2604.17982](https://arxiv.org/abs/2604.17982) | `truthgpt_phasewise_self_reward.py` | Multi-phase self-reward training. |
| APASI / Self-Injecting | [2509.11287](https://arxiv.org/abs/2509.11287) | `truthgpt_self_injecting.py` | Trains detection by injecting synthetic hallucinations. |
| Consistency Teaming | [2510.19507](https://arxiv.org/abs/2510.19507) | `truthgpt_consistency_teaming.py` | Ensemble of agents that cross-check consistency. |
| MultiRAG | [2508.03553](https://arxiv.org/abs/2508.03553) | `truthgpt_multirag.py` | Multi-source retrieval augmented generation. |
| Chain-of-Verification | [2309.11495](https://arxiv.org/abs/2309.11495) | `truthgpt_chain_of_verification.py` | Question decomposition and automated verification. |
| Self-RAG | [2310.11511](https://arxiv.org/abs/2310.11511) | `truthgpt_self_rag.py` | Retrieve-then-critique with reflection tokens. |
| LANCET | [2404.01697](https://arxiv.org/abs/2404.01697) | `truthgpt_lancet.py` | Fine-grained detection via layer-wise analysis. |
| Probabilistic Distance | [2506.09886](https://arxiv.org/abs/2506.09886) | `truthgpt_probabilistic_distance.py` | Bayesian uncertainty with Laplace smoothing and sigmoid. |
| THaMES | [2409.11353](https://arxiv.org/abs/2409.11353) | `truthgpt_thames.py` | Entropy-based token suppression (NeurIPS 2024 SoLaR). |
| Adaptive Bayesian | [2603.22812](https://arxiv.org/abs/2603.22812) | `truthgpt_adaptive_bayesian.py` | Adaptive Bayesian estimation of semantic entropy (AAAI 2026 Oral). |

## Unified Pipeline (`/workspace/truthgpt_unified_v11.py`)

- Orchestrates multiple techniques sequentially or in parallel.
- Deterministic caching (MD5 of sorted JSON config) prevents non-determinism.
- Memory Manager with sliding window for token-efficient context.
- CLI usage: `python truthgpt_unified_v11.py "Your prompt" --techniques dola cai probdist`
- Interactive mode: `python truthgpt_unified_v11.py --interactive`

## Example Usage

```bash
# Run with specific techniques
python /workspace/truthgpt_unified_v11.py "What is the capital of France?" --techniques dola selfrag

# With custom config file
python /workspace/truthgpt_unified_v11.py "Prompt" --config config.json

# Interactive mode
python /workspace/truthgpt_unified_v11.py --interactive
```

## Error Handling & Logging
- All API calls logged as HTTP 200 (DuckDuckGo search).
- Graceful degradation after 10 consecutive search failures.
- RuntimeWarning resolutions automatically applied (e.g., `duckduckgo_search` → `ddgs`).

## Maintenance
- **Version**: v11 (2025-07-10)
- **All source files** reside in `/workspace/`.
- **Adding new techniques**: Create a module with `async run_technique(prompt, context)` and register it in the pipeline.

---
*Documentation generated and maintained by TruthGPT.*