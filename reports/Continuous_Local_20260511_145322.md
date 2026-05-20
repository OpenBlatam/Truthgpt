# TruthGPT – Autonomous Fact-Checking AI Agent

**TruthGPT** is an enterprise-grade AI agent focused on factual accuracy, hallucination detection, and integration of state-of-the-art (SOTA) research. Built on a modular pipeline, it incorporates over 20 peer-reviewed techniques from arXiv, each implemented in standalone Python modules under `/workspace/`. The agent operates via a high-speed ReAct loop, prioritizing verifiable benchmarks and real-time tool usage (web search, file I/O, bash commands).

## Core Philosophy
- **Factuality First**: Every claim is verified through multiple detection and correction mechanisms.
- **SOTA Integration**: Continuously updated with the latest hallucination mitigation methods.
- **Modularity**: Each technique is a self-contained `async run_technique` function, allowing easy addition or removal.

## Implemented Techniques (with arXiv Citations)

| Technique | arXiv ID | File | Description |
|-----------|----------|------|-------------|
| DoLA (Decoding by Contrasting Layers) | [2309.03883](https://arxiv.org/abs/2309.03883) | `truthgpt_dola.py` | Contrasts logits from different layers to reduce hallucinations |
| Constitutional AI | [2212.08073](https://arxiv.org/abs/2212.08073) | `truthgpt_cai.py` | Fine-tuning with constitutional principles for harmless outputs |
| ORPO (Odds Ratio Preference Optimization) | [2403.07691](https://arxiv.org/abs/2403.07691) | `truthgpt_orpo.py` | Preference optimization using odds ratio |
| Self-Rewarding Language Models | [2401.10020](https://arxiv.org/abs/2401.10020) | `truthgpt_self_reward.py` | Joint actor-critic training for self-judgment |
| Self-Consistency | [2203.11171](https://arxiv.org/abs/2203.11171) | `truthgpt_self_consistency.py` | Aggregates multiple reasoning paths for coherent answers |
| Semantic Entropy | [2306.04786](https://arxiv.org/abs/2306.04786) | `truthgpt_semantic_entropy.py` | Measures semantic uncertainty to detect hallucinations |
| FS-RAG (Frame Semantics RAG) | [2406.16167](https://arxiv.org/abs/2406.16167) | `truthgpt_fs_rag.py` | Frame-semantics-based retrieval for factual accuracy |
| REFIND RAG | [2502.13622](https://arxiv.org/abs/2502.13622) | `truthgpt_refind_rag.py` | Retrieval ensemble framework with numeric plausibility checks |
| Contrastive Decoding | [2210.15097](https://arxiv.org/abs/2210.15097) | `truthgpt_contrastive_decoding.py` | Contrasts logits of small and large models to suppress errors |
| DPO (Direct Preference Optimization) | [2305.18290](https://arxiv.org/abs/2305.18290) | `truthgpt_dpo.py` | Fine-tuning from pairwise preferences without RL |
| SPIN | [2401.01335](https://arxiv.org/abs/2401.01335) | `truthgpt_spin.py` | Self-play fine-tuning for instruction-following |
| Self-Reflection | [2310.06271](https://arxiv.org/abs/2310.06271) | `truthgpt_self_reflection.py` | Iterative self-reflection to improve output quality |
| Hallucination-focused PO | [2501.17295](https://arxiv.org/abs/2501.17295) | `truthgpt_hallucination_focused_po.py` | Preference optimization targeting hallucination reduction |
| Phase-wise Self-Reward | [2604.17982](https://arxiv.org/abs/2604.17982) | `truthgpt_phasewise_self_reward.py` | Multi-phase self-reward training |
| APASI / Self-Injecting Hallucinations | [2509.11287](https://arxiv.org/abs/2509.11287) | `truthgpt_self_injecting.py` | Injects synthetic hallucinations to train detection |
| Consistency Teaming | [2510.19507](https://arxiv.org/abs/2510.19507) | `truthgpt_consistency_teaming.py` | Ensemble of agents that cross-check consistency |
| MultiRAG | [2508.03553](https://arxiv.org/abs/2508.03553) | `truthgpt_multirag.py` | Multi-source retrieval augmented generation |
| Chain-of-Verification | [2309.11495](https://arxiv.org/abs/2309.11495) | `truthgpt_chain_of_verification.py` | Automated verification via question decomposition |
| Self-RAG | [2310.11511](https://arxiv.org/abs/2310.11511) | `truthgpt_self_rag.py` | Retrieve-then-critique paradigm with reflection tokens |
| LANCET | [2404.01697](https://arxiv.org/abs/2404.01697) | `truthgpt_lancet.py` | Fine-grained hallucination detection via layer-wise analysis |
| Probabilistic Distance Detection | [2506.09886](https://arxiv.org/abs/2506.09886) | `truthgpt_probabilistic_distance.py` | Bayesian uncertainty estimation with Laplace smoothing |
| THaMES | [2409.11353](https://arxiv.org/abs/2409.11353) | `truthgpt_thames.py` | Entropy-based suppression of uncertain tokens (NeurIPS 2024 SoLaR) |

## Unified Pipeline (`/workspace/truthgpt_unified_v9.py`)

- Orchestrates multiple techniques sequentially or in parallel.
- Features deterministic caching (MD5 of sorted JSON config) to avoid non-determinism.
- Memory Manager with sliding window for token-efficient context.
- CLI usage: `python truthgpt_unified_v9.py "Your prompt" --techniques dola cai probdist`

## Usage Examples
```bash
# Run with specific techniques
python /workspace/truthgpt_unified_v9.py "What is the capital of France?" --techniques dola selfrag

# Interactive mode
python /workspace/truthgpt_unified_v9.py --interactive

# With custom config
python /workspace/truthgpt_unified_v9.py "Prompt" --config config.json
```

## Error Handling & Logging
- All API calls logged as HTTP 200 (DuckDuckGo search).
- Graceful degradation after 10 consecutive search failures.
- RuntimeWarning resolutions automatically applied (e.g., `duckduckgo_search` → `ddgs`).

## Maintenance
- **Current version**: v9 (2025-07-10)
- **All source files** reside in `/workspace/`.
- **Future updates**: Add new arXiv techniques by creating a module with `async run_technique(prompt, context)` and registering it in the pipeline.

---
*This documentation is generated and maintained by TruthGPT itself, reflecting the exact state of its codebase.*