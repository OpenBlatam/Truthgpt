"""
Cost Intelligence & Performance Optimization (System 5.9).

Industrial-grade orchestration layer leveraging SOTA modules:
- Semantic Caching (GPTCache)
- Prompt Compression (LLMLingua-2)
- Model Cascading (FrugalGPT)
- Self-Verification (AutoMix)
- Early Abstention
- Token Budget Tracking
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

from truthgpt.modules.api_cost import (
    APICostOptimizer,
    APICostConfig,
    EarlyAbstention,
    MoASynthesis,
    PromptCompressor,
    LLMLinguaCompressor
)

# Conditional import for Claude Code capabilities
_has_claude = False
_claude_modules = {}
try:
    from truthgpt.modules.claude_capabilities import SandboxExecutor, TestRunner, CommandExecutor
    _has_claude = True
    _claude_modules['sandbox'] = SandboxExecutor
    _claude_modules['test_runner'] = TestRunner
    _claude_modules['command_executor'] = CommandExecutor
    claude_logger = logging.getLogger("agents.cost.claude")
    claude_logger.info("Claude Code capabilities loaded.")
except ImportError:
    pass

logger = logging.getLogger("agents.cost")

class CostIntelligence:
    """
    Industrialized Cost Intelligence Agent.
    
    Orchestrates the full optimization pipeline to ensure TruthGPT 
    operates at peak cost-efficiency without quality degradation.
    """

    def __init__(self, config: Optional[APICostConfig] = None):
        self.config = config or APICostConfig()
        self.optimizer = APICostOptimizer(self.config)
        self.abstention = EarlyAbstention()
        self.moa = MoASynthesis()
        self.compressor = LLMLinguaCompressor()
        
        # Stats tracking
        self._stats = {
            "total_calls": 0,
            "abstentions": 0,
            "cache_hits": 0,
            "compressions": 0,
            "moa_syntheses": 0
        }

    async def optimize_call(self, prompt: str, llm_func, models: Optional[List[str]] = None, **kwargs) -> str:
        """
        Execute an optimized LLM call through the full pipeline.
        """
        self._stats["total_calls"] += 1
        
        # 1. Early Abstention check
        abstain, reason = self.abstention.check(prompt)
        if abstain:
            self._stats["abstentions"] += 1
            return f"[ABSTENCIÓN]: {reason}"

        # 2. Pipeline Execution (Cache -> Compression -> Cascade -> Budget)
        try:
            response = await self.optimizer.call(prompt, llm_func, models=models, **kwargs)
            return response
        except Exception as e:
            logger.error("Optimization pipeline error: %s", e)
            # Fallback to basic call if optimizer fails
            return await llm_func(prompt, model=models[0] if models else None, **kwargs)

    def moa_synthesize(self, responses: List[str], prompt: str) -> str:
        """Mixture-of-Agents synthesis."""
        self._stats["moa_syntheses"] += 1
        return self.moa.synthesize(responses, prompt)

    def compress(self, prompt: str, ratio: float = 0.5) -> str:
        """Compress prompt using LLMLingua logic."""
        self._stats["compressions"] += 1
        return self.compressor.compress(prompt, target_ratio=ratio)

    def get_stats(self) -> Dict[str, Any]:
        """Return operational stats."""
        stats = self._stats.copy()
        stats.update(self.optimizer.cache.get_stats())
        return stats

# Lazy loading singleton
_cost_instance: Optional[CostIntelligence] = None

def get_cost_intelligence() -> CostIntelligence:
    global _cost_instance
    if _cost_instance is None:
        _cost_instance = CostIntelligence()
    return _cost_instance
