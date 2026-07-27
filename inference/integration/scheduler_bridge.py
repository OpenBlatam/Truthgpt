"""
Integration module to connect Inference Engines with the Orchestration layer.

This module provides the InferenceSchedulerBridge which elegantly routes
inference tasks to the SmartAgentScheduler, taking advantage of its adaptive timeouts
and circuit breaker resilience patterns.
"""

import asyncio
import logging
from typing import Optional, Any, Callable, Awaitable, List
import uuid

# Import the orchestration scheduler
try:
    from optimization_core.agents.orchestration.scheduler.smart_scheduler import SmartAgentScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    SmartAgentScheduler = Any

from optimization_core.inference.core.base_engine import BaseInferenceEngine

logger = logging.getLogger(__name__)


class InferenceSchedulerBridge:
    """
    Bridge to route inference requests to the SmartAgentScheduler.
    """
    def __init__(self, engine: BaseInferenceEngine, scheduler: Optional[SmartAgentScheduler] = None):
        """
        Initialize the bridge.
        
        Args:
            engine: The underlying Async inference engine (e.g. AsyncTensorRTLLMEngine)
            scheduler: An optional SmartAgentScheduler instance. If None, a new one is created.
        """
        self.engine = engine
        if not SCHEDULER_AVAILABLE:
            logger.warning("SmartAgentScheduler is not available. The bridge will fallback to direct execution.")
            self.scheduler = None
        else:
            self.scheduler = scheduler or SmartAgentScheduler()
            
    async def submit_prompt(
        self, 
        prompt: str, 
        priority: int = 0, 
        dependencies: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Submit a prompt to the scheduler for async execution.
        
        Args:
            prompt: The prompt to infer.
            priority: Task priority.
            dependencies: Task dependencies.
            kwargs: Additional engine kwargs.
            
        Returns:
            The generated text result.
        """
        if not self.scheduler:
            # Fallback when scheduler is missing
            return await self._fallback_direct_execute(prompt, **kwargs)
            
        task_id = f"inference_{uuid.uuid4().hex[:8]}"
        
        # We need a resilient fallback in case TensorRT fails or times out
        async def fallback():
            logger.warning(f"Executing fallback for task {task_id} due to timeout/failure.")
            # In a real scenario, this could switch to an AsyncVLLMEngine or simpler PyTorch model
            # For now, we will retry the same engine without scheduler constraints
            return await self._fallback_direct_execute(prompt, **kwargs)

        try:
            self.scheduler.create_inference_task(
                engine=self.engine,
                prompt=prompt,
                task_id=task_id,
                priority=priority,
                dependencies=dependencies,
                **kwargs
            )
            
            # Start execution graph
            await self.scheduler.execute_task_graph()
            
            # Retrieve result from the scheduler tasks map
            completed_task = self.scheduler.tasks.get(task_id)
            if completed_task and completed_task.status == "COMPLETED":
                return completed_task.result
            elif completed_task and completed_task.status == "FAILED":
                logger.error(f"Inference task {task_id} failed in scheduler. Using fallback.")
                return await fallback()
            else:
                logger.error(f"Inference task {task_id} did not complete normally. Status: {completed_task.status if completed_task else 'UNKNOWN'}")
                return await fallback()
                
        except Exception as e:
            logger.error(f"Error submitting to scheduler bridge: {e}")
            return await fallback()

    async def _fallback_direct_execute(self, prompt: str, **kwargs) -> str:
        """Fallback to direct execution without scheduler overhead."""
        if hasattr(self.engine, 'generate_async'):
            return await self.engine.generate_async(prompt, **kwargs)
        else:
            # Wrap sync generate in async
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: self.engine.generate(prompt, **kwargs))
            if isinstance(result, list):
                return result[0].text if hasattr(result[0], 'text') else str(result[0])
            return result.text if hasattr(result, 'text') else str(result)
