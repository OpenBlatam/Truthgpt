"""
Main API Cost Optimizer (System 5.9 Orchestrator).
"""

import logging
from typing import List, Dict, Any, Optional, Union

from .config import APICostConfig
from .semantic_cache import SemanticCache
from .prompt_compressor import LLMLinguaCompressor
from .model_cascade import ModelCascade, CascadeRouter
from .budget_tracker import BudgetTracker, CostCalculator, TokenCounter
from .request_coalescer import RequestCoalescer

logger = logging.getLogger("optimization.api_cost.optimizer")

class APICostOptimizer:
    """
    Industrial-grade API Cost Optimizer.
    
    Orchestrates Semantic Caching, Prompt Compression, Model Cascading,
    and Budget Tracking to minimize costs while maintaining peak performance.
    """
    
    def __init__(self, config: Optional[APICostConfig] = None):
        self.config = config or APICostConfig()
        
        # Initialize components
        self.cache = SemanticCache(
            similarity_threshold=self.config.semantic_cache.similarity_threshold,
            max_entries=self.config.semantic_cache.max_entries,
            ttl_seconds=self.config.semantic_cache.ttl_seconds
        )
        
        self.compressor = LLMLinguaCompressor(
            target_ratio=self.config.prompt_compression.target_ratio
        )
        
        self.budget = BudgetTracker(
            daily_limit=self.config.budget.daily_budget_usd,
            persistence_path=self.config.budget.persistence_path
        )
        
        self.coalescer = RequestCoalescer()
        self.calculator = CostCalculator(self.config.model_pricing)

    async def call(self, prompt: str, llm_func, models: Optional[List[str]] = None, **kwargs) -> Any:
        """
        Execute an optimized LLM call with full SOTA pipeline.
        """
        # 0. Early Abstention (System 5.9)
        from .abstention import EarlyAbstention
        abstention = EarlyAbstention()
        should_abstain, reason = abstention.check(prompt)
        if should_abstain:
            logger.warning("🛡️ Abstaining from request: %s", reason)
            return f"I cannot process this request: {reason}"

        # 1. Budget Circuit Breaker
        if not self.budget.is_within_budget():
            logger.error("🛑 Budget Exceeded! Blocking API call.")
            raise RuntimeError("API Budget Exceeded")

        # 2. Semantic Cache Lookup
        if self.config.enable_semantic_cache:
            cached = self.cache.get(prompt)
            if cached:
                logger.info("🎯 Cache Hit: Returning semantically similar response.")
                return cached

        # 3. Prompt Compression
        final_prompt = prompt
        if self.config.enable_prompt_compression:
            final_prompt = self.compressor.compress(prompt)

        # 4. Model Cascade Execution
        cascade_models = models or self.config.model_cascade.cascade_order
        cascade = ModelCascade(
            models=cascade_models, 
            threshold=self.config.model_cascade.confidence_threshold
        )

        async def _cascade_step_wrapper(p: str, model: str, **inner_kwargs):
            """Internal wrapper to track costs per step if needed."""
            return await llm_func(p, model=model, **inner_kwargs)

        # Use unique key for coalescing
        coalesce_key = f"{hash(prompt)}_{'_'.join(cascade_models)}"
        
        async def _run_optimized_pipeline():
            result = await cascade.execute_cascade(final_prompt, _cascade_step_wrapper, **kwargs)
            
            response = result.get("response")
            model_used = result.get("model")
            
            # Update budget if successful
            if not result.get("error"):
                in_tokens = TokenCounter.count(final_prompt)
                out_tokens = TokenCounter.count(response)
                cost = self.calculator.calculate(model_used, in_tokens, out_tokens)
                
                # Calculate Raw Cost (unoptimized: original prompt, most expensive model)
                orig_in_tokens = TokenCounter.count(prompt)
                frontier_model = cascade_models[-1]
                raw_cost = self.calculator.calculate(frontier_model, orig_in_tokens, out_tokens)
                
                self.budget.update(cost, in_tokens, out_tokens, raw_cost_usd=raw_cost)
                
                # Store in cache
                if self.config.enable_semantic_cache:
                    self.cache.put(prompt, response)
            
            return response

        return await self.coalescer.execute(coalesce_key, _run_optimized_pipeline)

def create_api_cost_optimizer(config: Optional[APICostConfig] = None) -> APICostOptimizer:
    """Factory function for the optimizer."""
    return APICostOptimizer(config)
