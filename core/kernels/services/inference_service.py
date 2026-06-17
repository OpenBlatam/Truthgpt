"""
InferenceService - High-performance inference engine
"""

import asyncio
from typing import Dict, Any, Optional, List
from .base_service import BaseService


class InferenceService(BaseService):
    """Service for high-performance model inference with batching and caching"""

    def __init__(self, kernel, config: Optional[Dict[str, Any]] = None):
        super().__init__(kernel, config)
        self._request_queue: asyncio.Queue = asyncio.Queue()
        self._cache: Dict[str, Any] = {}
        self._worker_task: Optional[asyncio.Task] = None
        self._total_requests: int = 0
        self._cache_hits: int = 0

    async def _on_start(self) -> None:
        self._worker_task = asyncio.create_task(self._inference_worker())
        self.logger.info("InferenceService: worker started")

    async def _on_stop(self) -> None:
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        self._cache.clear()

    async def _get_health_info(self) -> Dict[str, Any]:
        return {
            "queue_size": self._request_queue.qsize(),
            "cache_size": len(self._cache),
            "total_requests": self._total_requests,
            "cache_hit_rate": (
                self._cache_hits / self._total_requests
                if self._total_requests > 0 else 0.0
            )
        }

    async def infer(self, prompt: str, model: str = "default", **kwargs) -> str:
        """Submit an inference request and await the result"""
        self._total_requests += 1
        cache_key = f"{model}:{hash(prompt)}"

        if cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key]

        future: asyncio.Future = asyncio.get_event_loop().create_future()
        await self._request_queue.put({
            "prompt": prompt,
            "model": model,
            "kwargs": kwargs,
            "future": future,
            "cache_key": cache_key
        })

        result = await future
        return result

    async def _inference_worker(self) -> None:
        """Background worker that processes inference requests"""
        while True:
            try:
                request = await self._request_queue.get()
                prompt = request["prompt"]
                model = request["model"]
                kwargs = request["kwargs"]
                future = request["future"]
                cache_key = request["cache_key"]

                try:
                    model_svc = self.kernel.get_service("models")
                    engine = model_svc.get_engine(model) if model_svc else None

                    if engine:
                        result = await asyncio.get_event_loop().run_in_executor(
                            None, lambda: engine.generate(prompt, **kwargs)
                        )
                    else:
                        result = f"[InferenceService] No engine available for model '{model}'"

                    self._cache[cache_key] = result
                    if not future.done():
                        future.set_result(result)

                except Exception as e:
                    if not future.done():
                        future.set_exception(e)

                self._request_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Inference worker error: {e}")
