## TruthGPT v19 – Enterprise Fact-Checking AI Agent

**A modular, extensible framework integrating 28 state-of-the-art hallucination mitigation techniques from peer-reviewed arXiv papers.**

TruthGPT is designed to detect and reduce hallucinations in large language model outputs. It combines diverse strategies—contrastive decoding, preference optimization, self-consistency, retrieval-augmented generation, and more—into an adaptive ensemble voting system. The result is factually accurate responses with quantified confidence scores.

All techniques are backed by arXiv papers. See the [Techniques](#techniques) table below for direct links.

---

## Features
- **28 SOTA Techniques** – Parallel execution of methods like DoLA, Constitutional AI, ORPO, Self-RAG, and 24 more.
- **Adaptive Ensemble Voting** – Weighted aggregation based on historical confidence per technique.
- **Real API Integration** – Optionally use OpenAI GPT-4 via `OPENAI_API_KEY`; falls back to simulation if not set.
- **Efficient Caching** – LRU + TTL cache avoids recomputation for repeated queries.
- **Async Architecture** – Semaphore‑limited concurrency for fast processing.
- **Configurable** – JSON configuration file for ordering, temperature, sample count, and more.
- **Comprehensive Error Handling** – Individual technique failures do not crash the pipeline.

---

## Quick Start

### Installation
```bash
git clone https://github.com/your-org/truthgpt.git
cd truthgpt
pip install -r requirements.txt
```

Set your API key (optional):
```bash
export OPENAI_API_KEY="sk-..."
```

### Run a Query
```bash
python /workspace/truthgpt_unified_v19.py "What is the capital of France?"
```

### Interactive Mode
```bash
python /workspace/truthgpt_unified_v19.py --interactive
```

### Use Specific Techniques
```bash
python /workspace/truthgpt_unified_v19.py --techniques dola self_rag consistency "Explain gravity"
```

---

## Techniques (28 Total)

Each technique is implemented as an async module. The table below includes the exact arXiv identifier linked to the paper.

| # | Technique | arXiv ID | Category |
|---|-----------|----------|----------|
| 1 | DoLA | [2309.03883](https://arxiv.org/abs/2309.03883) | Contrastive Decoding |
| 2 | Constitutional AI | [2212.08073](https://arxiv.org/abs/2212.08073) | Safety Training |
| 3 | ORPO | [2403.07691](https://arxiv.org/abs/2403.07691) | Preference Optimization |
| 4 | Self-Rewarding | [2401.10020](https://arxiv.org/abs/2401.10020) | Self-Supervision |
| 5 | Self-Consistency | [2203.11171](https://arxiv.org/abs/2203.11171) | Sampling Ensemble |
| 6 | Semantic Entropy | [2306.04786](https://arxiv.org/abs/2306.04786) | Uncertainty |
| 7 | FS-RAG | [2406.16167](https://arxiv.org/abs/2406.16167) | Retrieval-Augmented |
| 8 | REFIND RAG | [2502.13622](https://arxiv.org/abs/2502.13622) | Reranking |
| 9 | Contrastive Decoding | [2210.15097](https://arxiv.org/abs/2210.15097) | Decoding |
|10 | DPO | [2305.18290](https://arxiv.org/abs/2305.18290) | Human Preference |
|11 | SPIN | [2401.01335](https://arxiv.org/abs/2401.01335) | Self-Play |
|12 | Self-Reflection | [2310.06271](https://arxiv.org/abs/2310.06271) | Reflection |
|13 | Hallucination-focused PO | [2501.17295](https://arxiv.org/abs/2501.17295) | Preference Optimization |
|14 | Phase-wise Self-Reward | [2604.17982](https://arxiv.org/abs/2604.17982) | Multi-step RL |
|15 | Self-Injecting Hallucinations | [2509.11287](https://arxiv.org/abs/2509.11287) | Robustness |
|16 | Consistency Teaming | [2510.19507](https://arxiv.org/abs/2510.19507) | Multi-agent |
|17 | MultiRAG | [2508.03553](https://arxiv.org/abs/2508.03553) | Multi-source RAG |
|18 | Chain-of-Verification | [2309.11495](https://arxiv.org/abs/2309.11495) | Verification |
|19 | Self-RAG | [2310.11511](https://arxiv.org/abs/2310.11511) | Self-Retrieval |
|20 | LANCET | [2404.01697](https://arxiv.org/abs/2404.01697) | Local Assessment |
|21 | Probabilistic Distance | [2506.09886](https://arxiv.org/abs/2506.09886) | Detection |
|22 | THaMES | [2409.11353](https://arxiv.org/abs/2409.11353) | Verification |
|23 | Adaptive Bayesian Estimation | [2603.22812](https://arxiv.org/abs/2603.22812) | Bayesian Inference |
|24 | TUM-MiKaNi | [2507.00579](https://arxiv.org/abs/2507.00579) | Multilingual Detection |
|25 | HIDE & Seek | [2506.17748](https://arxiv.org/abs/2506.17748) | Decoupled Representation |
|26 | AggTruth | [2506.18628](https://arxiv.org/abs/2506.18628) | Aggregated Attention |
|27 | First Hallucination Token | [2507.20836](https://arxiv.org/abs/2507.20836) | Early Detection |
|28 | Dynamic Contrastive Decoding | [2402.06705](https://arxiv.org/abs/2402.06705) | Decoding |

---

## Configuration

You can customize the pipeline via a JSON file:

```json
{
  "techniques_order": ["dola", "cai", "orpo", "self_rag"],
  "cache_enabled": true,
  "max_context_tokens": 4096,
  "num_samples": 5,
  "temperature": 0.7,
  "api_key": "",
  "use_real_model": false
}
```

Pass it with:
```bash
python truthgpt_unified_v19.py --config config.json "Your question"
```

---

## Architecture Overview

1. **Input** → **Memory Manager** (sliding window) → **Ensemble Voter** → **28 parallel techniques** → **Weighted aggregation** → **Output + Confidence**.
2. Caching (LRU+TTL) avoids recomputation.
3. Async execution with semaphore limits concurrency.

---

## Programmatic API

```python
from truthgpt_unified_v19 import TruthGPT
import asyncio

async def main():
    gpt = TruthGPT()
    result = await gpt.process("What is the capital of France?")
    print(result["output"], "Confidence:", result["confidence"])

asyncio.run(main())
```

---

## Testing

```bash
pytest tests/
```

Unit tests are included in the repository.

---

## Dependencies

- Python 3.10+
- aiohttp
- openai (optional)
- numpy
- (See `requirements.txt` for full list)

---

## License

MIT License – see `LICENSE` file.

---

## Citation

If you use TruthGPT in your research, please cite the relevant arXiv papers listed in the [Techniques](#techniques) table.

---

## Contact

For questions or contributions, open an issue on GitHub.