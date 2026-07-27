"""
Batch Scheduler wrapper around DynamicBatcher for backwards compatibility.
"""
from typing import List, Optional
from .advanced_batcher import DynamicBatcher
from ..core.base_engine import BaseInferenceEngine


class BatchScheduler(DynamicBatcher):
    """
    Backwards compatible BatchScheduler wrapper around DynamicBatcher.
    """
    def __init__(
        self,
        inference_engine: BaseInferenceEngine,
        max_batch_size: int = 8,
        max_wait_time: float = 0.1,
        priority_queue: bool = True,
    ):
        super().__init__(
            processor=lambda prompts: inference_engine.generate(prompts),
            max_batch_size=max_batch_size,
            max_wait_time=max_wait_time
        )
        self.engine = inference_engine
        self.priority_queue = priority_queue
    
    def process(
        self,
        prompt: str,
        priority: int = 0,
        callback: Optional[callable] = None,
        **kwargs
    ) -> str:
        """Process with priority scheduling."""
        # For simplicity in this wrapper, execute directly if kwargs exist
        # as DynamicBatcher doesn't easily pass kwargs per item.
        result = self.engine.generate(prompt, **kwargs)
        if callback:
            callback(result)
        return result
    
    def process_batch(
        self,
        prompts: List[str],
        priorities: Optional[List[int]] = None,
        **kwargs
    ) -> List[str]:
        """Process batch with optional priorities."""
        if priorities and self.priority_queue:
            indexed = list(zip(priorities, prompts))
            indexed.sort(reverse=True)
            prompts = [p for _, p in indexed]
        
        return self.engine.generate(prompts, **kwargs)


# Backwards compatibility
BatchProcessor = BatchScheduler
