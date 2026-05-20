TruthGPT has been refactored into the unified module `/workspace/truthgpt_unified.py`. This module integrates the following SOTA hallucination mitigation techniques, each backed by an arXiv paper:
- **DoLA** (arXiv:2309.03883): Decoding by Contrasting Layers.
- **Constitutional AI** (arXiv:2212.08073): Self-correction guided by a constitution.
- **ORPO** (arXiv:2403.07691): Odds Ratio Preference Optimization.
- **Self-Rewarding Language Models** (arXiv:2401.10020): Self-play with LLM-as-judge.
- **Self-Consistency** (arXiv:2203.11171): Multiple reasoning paths with majority voting.
- **Semantic Entropy** (arXiv:2306.04786): Uncertainty measurement via semantic equivalence.
- **FS-RAG** (arXiv:2406.16167): Frame Semantics for factual grounding.

The module provides a unified `TruthGPT` class with methods `mitigate()`, `list_techniques()`, and `get_technique_info()`. It also includes fallback utilities for hallucination detection and consistency teaming. The duckduckgo_search runtime warning has been handled by a conditional import (preferring the `ddgs` package).

**How to use:**
```python
from truthgpt_unified import TruthGPT
agent = TruthGPT()
safe_response, metadata = agent.mitigate(
    technique='semantic_entropy',
    prompt='What is the capital of France?',
    response='Paris is the capital city.'
)
print(safe_response)
```

References:
- DoLA: arXiv:2309.03883
- Constitutional AI: arXiv:2212.08073
- ORPO: arXiv:2403.07691
- Self-Rewarding: arXiv:2401.10020
- Self-Consistency: arXiv:2203.11171
- Semantic Entropy: arXiv:2306.04786
- FS-RAG: arXiv:2406.16167