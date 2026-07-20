"""
Configuration for API Cost Optimization.

Based on SOTA research:
- FrugalGPT (Chen et al., 2023): https://arxiv.org/abs/2305.05176
- LLMLingua (Jiang et al., 2023): https://arxiv.org/abs/2310.05736
- GPTCache (Bang, 2023): https://arxiv.org/abs/2306.11516
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict


class CacheBackend(str, Enum):
    """Cache backend types."""
    MEMORY = 'memory'           # In-process LRU
    SQLITE = 'sqlite'           # Persistent local
    REDIS = 'redis'             # Distributed
    FAISS = 'faiss'             # Vector similarity (semantic)
    CHROMA = 'chroma'           # Vector DB


class ModelTier(str, Enum):
    """Model tiers ordered by cost (cheapest first). FrugalGPT cascade order."""
    NANO = 'nano'               # e.g., gpt-4o-mini, haiku, gemini-flash-8b
    SMALL = 'small'              # e.g., gpt-4o-mini, claude-haiku
    MEDIUM = 'medium'           # e.g., gpt-4o, sonnet
    LARGE = 'large'             # e.g., gpt-4-turbo, opus
    FRONTIER = 'frontier'        # e.g., o1, gpt-5


# Per-1M-token pricing in USD (approx Q4 2024). Update as needed.
DEFAULT_MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # OpenAI
    'gpt-4o-mini':       {'input': 0.150,  'output': 0.600,  'tier': ModelTier.NANO},
    'gpt-4o':            {'input': 2.500,  'output': 10.000, 'tier': ModelTier.MEDIUM},
    'gpt-4-turbo':       {'input': 10.000, 'output': 30.000, 'tier': ModelTier.LARGE},
    'o1-mini':           {'input': 3.000,  'output': 12.000, 'tier': ModelTier.MEDIUM},
    'o1':                {'input': 15.000, 'output': 60.000, 'tier': ModelTier.FRONTIER},
    # Anthropic
    'claude-3-haiku':    {'input': 0.250,  'output': 1.250,  'tier': ModelTier.NANO},
    'claude-3-5-haiku':  {'input': 1.000,  'output': 5.000,  'tier': ModelTier.SMALL},
    'claude-3-5-sonnet': {'input': 3.000,  'output': 15.000, 'tier': ModelTier.MEDIUM},
    'claude-3-opus':     {'input': 15.000, 'output': 75.000, 'tier': ModelTier.LARGE},
    # Google
    'gemini-1.5-flash-8b': {'input': 0.0375, 'output': 0.150, 'tier': ModelTier.NANO},
    'gemini-1.5-flash':  {'input': 0.075,  'output': 0.300,  'tier': ModelTier.SMALL},
    'gemini-1.5-pro':    {'input': 1.250,  'output': 5.000,  'tier': ModelTier.MEDIUM},
    # DeepSeek (extremely cheap)
    'deepseek-chat':     {'input': 0.140,  'output': 0.280,  'tier': ModelTier.NANO},
    'deepseek-reasoner': {'input': 0.550,  'output': 2.190,  'tier': ModelTier.SMALL},
}


@dataclass
class SemanticCacheConfig:
    """GPTCache-style semantic caching."""
    enabled: bool = True
    backend: CacheBackend = CacheBackend.SQLITE
    similarity_threshold: float = 0.92  # Cosine sim threshold for cache hit
    embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2'  # Local, free
    max_entries: int = 100_000
    ttl_seconds: int = 7 * 24 * 3600  # 1 week
    cache_dir: str = './.api_cost_cache'
    exact_match_first: bool = True  # Try hash match before embedding


@dataclass
class PromptCompressionConfig:
    """LLMLingua prompt compression."""
    enabled: bool = True
    target_ratio: float = 0.5  # Compress to 50% of original tokens
    min_tokens_to_compress: int = 500  # Only compress long prompts
    preserve_questions: bool = True  # Question-aware (LongLLMLingua)
    preserve_format: bool = True  # Keep JSON/markdown structure
    compressor_model: str = 'microsoft/llmlingua-2-xlm-roberta-large-meetingbank'
    use_local_compressor: bool = True  # Avoid API call for compression itself
    force_tokens: List[str] = field(default_factory=lambda: ['\n', '?', '.', ':'])


@dataclass
class ModelCascadeConfig:
    """FrugalGPT cascade configuration."""
    enabled: bool = True
    cascade_order: List[str] = field(default_factory=lambda: [
        'gemini-1.5-flash-8b',  # Cheapest first
        'gpt-4o-mini',
        'claude-3-5-sonnet',
        'gpt-4o',
    ])
    confidence_threshold: float = 0.85  # Accept if scorer >= this
    confidence_method: str = 'self_consistency'  # 'logprobs'|'self_consistency'|'judge'
    max_escalations: int = 2
    judge_model: Optional[str] = 'gpt-4o-mini'  # Cheap judge for quality


@dataclass
class BudgetConfig:
    """Hard budget caps with circuit breakers."""
    enabled: bool = True
    daily_budget_usd: float = 2.0  # User specified ~$10/day, target $2
    hourly_budget_usd: float = 0.25
    per_request_max_usd: float = 0.10
    alert_threshold_pct: float = 0.80  # Alert at 80% spend
    hard_stop_on_exceed: bool = True
    persistence_path: str = './.api_cost_budget.json'
    track_per_user: bool = True
    track_per_task: bool = True


@dataclass
class CoalescingConfig:
    """Request deduplication for in-flight identical calls."""
    enabled: bool = True
    window_ms: int = 100  # Coalesce requests within this window
    max_batch_size: int = 16


@dataclass
class APICostConfig:
    """Master config combining all SOTA cost-reduction techniques."""
    # Sub-configs
    semantic_cache: SemanticCacheConfig = field(default_factory=SemanticCacheConfig)
    prompt_compression: PromptCompressionConfig = field(default_factory=PromptCompressionConfig)
    model_cascade: ModelCascadeConfig = field(default_factory=ModelCascadeConfig)
    budget: BudgetConfig = field(default_factory=BudgetConfig)
    coalescing: CoalescingConfig = field(default_factory=CoalescingConfig)

    # Convenience flags
    enable_semantic_cache: bool = True
    enable_prompt_compression: bool = True
    enable_model_cascade: bool = True
    enable_budget_tracking: bool = True
    enable_request_coalescing: bool = True

    # Pricing table (override per deployment)
    model_pricing: Dict[str, Dict] = field(default_factory=lambda: dict(DEFAULT_MODEL_PRICING))

    # Observability
    log_savings: bool = True
    metrics_path: str = './.api_cost_metrics.jsonl'

    daily_budget_usd: float = 2.0  # Convenience accessor

    def __post_init__(self):
        # Sync convenience flags to sub-configs
        self.semantic_cache.enabled = self.enable_semantic_cache
        self.prompt_compression.enabled = self.enable_prompt_compression
        self.model_cascade.enabled = self.enable_model_cascade
        self.budget.enabled = self.enable_budget_tracking
        self.coalescing.enabled = self.enable_request_coalescing
        self.budget.daily_budget_usd = self.daily_budget_usd

    @classmethod
    def aggressive_savings(cls) -> 'APICostConfig':
        """Maximum cost reduction preset (~80-95% savings)."""
        cfg = cls(daily_budget_usd=1.0)
        cfg.semantic_cache.similarity_threshold = 0.88  # More cache hits
        cfg.prompt_compression.target_ratio = 0.35  # Aggressive compression
        cfg.model_cascade.confidence_threshold = 0.75  # Accept cheap more often
        return cfg

    @classmethod
    def quality_first(cls) -> 'APICostConfig':
        """Conservative savings preserving quality (~40-60% savings)."""
        cfg = cls(daily_budget_usd=3.0)
        cfg.semantic_cache.similarity_threshold = 0.96  # Only near-identical
        cfg.prompt_compression.target_ratio = 0.7
        cfg.model_cascade.confidence_threshold = 0.92
        return cfg