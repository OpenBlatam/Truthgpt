# 🔬 Tutorial: Implementing & Registering Custom Research Papers

TruthGPT includes a modular **SOTA Research Papers Registry** containing implementations of cutting-edge deep learning advancements.

In this tutorial, you will learn how to translate a research paper from mathematical equations into a high-performance PyTorch module, inherit from `BasePaperModule`, register it in `PaperRegistry`, expose it to the configuration system, and verify numerical correctness with unit tests.

---

## 🎯 What You Will Learn
1. How to structure a new paper implementation module under `papers/`.
2. How to register paper metadata, citations, and model hooks with `PaperMetadata`.
3. How to write a PyTest numerical validation suite.
4. How to benchmark your new implementation.

---

## 📐 The Target Paper: Elastic Reasoning (2026)

Suppose we want to implement **Elastic Reasoning**, which dynamically modulates reasoning compute budgets per token based on local entropy:

$$\text{Attention}(Q, K, V) = \text{Softmax}\left(\frac{Q K^T}{\sqrt{d_k}} \odot M_{\text{elastic}}(\mathcal{H})\right) V$$

Where $M_{\text{elastic}}(\mathcal{H})$ is an entropy-guided routing mask that skips redundant token interactions.

---

## 🛠️ Step 1: Implement the Paper Algorithm Module

Create `papers/elastic_reasoning.py`:

```python
import math
import torch
import torch.nn as nn
from typing import Any, Dict, Optional

from papers.base import BasePaperModule, PaperCategory, PaperMetadata, PaperResult
from papers.config import BasePaperConfig

class ElasticReasoningConfig(BasePaperConfig):
    entropy_threshold: float = 0.65
    max_iterations: int = 10

class ElasticReasoning(BasePaperModule):
    """Implementation of Elastic Reasoning algorithm."""

    @classmethod
    def get_metadata(cls) -> PaperMetadata:
        return PaperMetadata(
            paper_id="elastic_reasoning",
            title="Elastic Reasoning: Dynamic Compute Allocation via Entropy Gating",
            authors=["TruthGPT Research Team"],
            year=2026,
            category=PaperCategory.REASONING,
            tags=["reasoning", "dynamic_compute", "entropy_routing"]
        )

    def process(self, input_data: Any) -> PaperResult:
        # Processing logic here
        return PaperResult(
            paper_id="elastic_reasoning",
            output_data=input_data,
            metrics={"compute_savings_pct": 34.2}
        )
```

---

## 📝 Step 2: Register Paper into `PaperRegistry`

Register your module with metadata in `papers/registry.py`:

```python
from papers.registry import PaperRegistry, default_registry

# Register directly into the global catalog
default_registry.register(
    metadata=ElasticReasoning.get_metadata(),
    module_class=ElasticReasoning,
    config_class=ElasticReasoningConfig
)
```

---

## 🧪 Step 3: Write PyTest Unit Tests

Create `tests/papers/test_elastic_reasoning.py` to verify shape consistency and numerical stability:

```python
import pytest
import torch
from papers.elastic_reasoning import ElasticReasoning
from papers.config import ElasticReasoningConfig

def test_elastic_reasoning_processing():
    config = ElasticReasoningConfig(entropy_threshold=0.5)
    module = ElasticReasoning(config=config)
    
    result = module.process({"prompt": "Solve 2x + 5 = 15"})
    assert result.paper_id == "elastic_reasoning"
    assert "compute_savings_pct" in result.metrics
```
