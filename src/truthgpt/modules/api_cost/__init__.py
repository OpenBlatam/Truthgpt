"""
API Cost Optimization Module for TruthGPT
==========================================

Industrial-grade cost reduction for LLM API calls without quality loss.

SOTA Techniques Implemented:
----------------------------
1. **Semantic Caching** (GPTCache - Bang, 2023)
   - Embedding-based cache hits for semantically similar prompts
   - Reduces redundant calls by 30-70%

2. **Prompt Compression** (LLMLingua - Jiang et al., 2023, EMNLP)
   - Token-level compression preserving semantic content
   - 2x-20x compression with <1% quality loss
   - Paper: https://arxiv.org/abs/2310.05736

3. **Model Cascading** (FrugalGPT - Chen et al., 2023)
   - Route to cheap model first; escalate only if confidence low
   - Up to 98% cost reduction matching GPT-4 quality
   - Paper: https://arxiv.org/abs/2305.05176

4. **Response Deduplication & Batching**
   - Coalesce identical/near-identical in-flight requests

5. **Token Budget Tracking**
   - Per-user/per-task budgets with circuit breakers
   - Real-time spend monitoring with hard caps

6. **Adaptive Context Pruning** (LongLLMLingua principles)
   - Question-aware context selection

Usage:
------
    from optimization_core.modules.api_cost import APICostOptimizer, APICostConfig
    
    config = APICostConfig(
        enable_semantic_cache=True,
        enable_prompt_compression=True,
        enable_model_cascade=True,
        daily_budget_usd=2.0,
    )
    optimizer = APICostOptimizer(config)
    response = await optimizer.call(prompt, models=['gpt-3.5', 'gpt-4'])
"""

from .config import APICostConfig, ModelTier, CacheBackend
from .semantic_cache import SemanticCache, EmbeddingCache
from .prompt_compressor import PromptCompressor, LLMLinguaCompressor
from .model_cascade import ModelCascade, CascadeRouter, ConfidenceScorer
from .budget_tracker import BudgetTracker, TokenCounter, CostCalculator
from .request_coalescer import RequestCoalescer
from .optimizer import APICostOptimizer, create_api_cost_optimizer
from .abstention import EarlyAbstention
from .moa import MoASynthesis

__all__ = [
    'APICostConfig',
    'ModelTier',
    'CacheBackend',
    'SemanticCache',
    'EmbeddingCache',
    'PromptCompressor',
    'LLMLinguaCompressor',
    'ModelCascade',
    'CascadeRouter',
    'ConfidenceScorer',
    'BudgetTracker',
    'TokenCounter',
    'CostCalculator',
    'RequestCoalescer',
    'APICostOptimizer',
    'create_api_cost_optimizer',
    'EarlyAbstention',
    'MoASynthesis',
]

__version__ = '1.0.0'
__author__ = 'TruthGPT Optimization Core Team'