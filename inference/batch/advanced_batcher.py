"""
Advanced Batch Processing for Inference
========================================

High-performance async-native batch processing with:
- Dynamic batching
- Priority queues
- Batch optimization
- Memory management
- Parallel processing
"""

import time
import asyncio
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Any, Dict, Generic, TypeVar, Awaitable
from enum import Enum

from ..exceptions import BatchProcessingError

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


class BatchPriority(Enum):
    """Batch priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class BatchItem(Generic[T]):
    """Item in a batch."""
    data: T
    priority: BatchPriority = BatchPriority.NORMAL
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """Compare by priority (higher priority first)."""
        if self.priority != other.priority:
            return self.priority.value > other.priority.value
        return self.created_at < other.created_at


@dataclass
class Batch(Generic[T]):
    """Batch of items."""
    items: List[BatchItem[T]]
    created_at: float = field(default_factory=time.time)
    max_size: int = 32
    
    @property
    def size(self) -> int:
        """Get batch size."""
        return len(self.items)
    
    @property
    def is_full(self) -> bool:
        """Check if batch is full."""
        return self.size >= self.max_size
    
    @property
    def age(self) -> float:
        """Get batch age in seconds."""
        return time.time() - self.created_at


class DynamicBatcher(Generic[T, R]):
    """
    Dynamic batcher with priority queue and optimization using native asyncio.
    """
    
    def __init__(
        self,
        processor: Callable[[List[T]], Awaitable[List[R]]],
        max_batch_size: int = 32,
        min_batch_size: int = 1,
        max_wait_time: float = 0.1,
        max_queue_size: int = 1000,
        optimize_batches: bool = True
    ):
        self.processor = processor
        self.max_batch_size = max_batch_size
        self.min_batch_size = min_batch_size
        self.max_wait_time = max_wait_time
        self.max_queue_size = max_queue_size
        self.optimize_batches = optimize_batches
        
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        self._stats = {
            "batches_processed": 0,
            "items_processed": 0,
            "total_wait_time": 0.0,
            "total_process_time": 0.0,
        }
        self._stats_lock = asyncio.Lock()
    
    def start(self):
        """Start the async batcher loop."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.info("Async Dynamic batcher started")
    
    async def stop(self):
        """Stop the async batcher loop."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Async Dynamic batcher stopped")
    
    async def submit(
        self,
        item: T,
        priority: BatchPriority = BatchPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Submit an item for batching."""
        batch_item = BatchItem(
            data=item,
            priority=priority,
            metadata=metadata or {}
        )
        
        try:
            self._queue.put_nowait(batch_item)
        except asyncio.QueueFull:
            raise BatchProcessingError("Batch queue is full")
    
    async def _process_loop(self):
        """Main processing loop."""
        current_batch: List[BatchItem[T]] = []
        batch_start_time = time.time()
        
        while self._running:
            try:
                try:
                    # Wait for an item with timeout
                    item = await asyncio.wait_for(self._queue.get(), timeout=self.max_wait_time)
                    current_batch.append(item)
                    self._queue.task_done()
                except asyncio.TimeoutError:
                    if current_batch:
                        await self._process_batch(current_batch)
                        current_batch = []
                        batch_start_time = time.time()
                    continue
                
                should_process = (
                    len(current_batch) >= self.max_batch_size or
                    (len(current_batch) >= self.min_batch_size and
                     time.time() - batch_start_time >= self.max_wait_time)
                )
                
                if should_process:
                    await self._process_batch(current_batch)
                    current_batch = []
                    batch_start_time = time.time()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in async batch processing loop: {e}", exc_info=True)
    
    async def _process_batch(self, items: List[BatchItem[T]]):
        """Process a batch of items."""
        if not items:
            return
        
        start_time = time.time()
        batch_data = [item.data for item in items]
        
        if self.optimize_batches:
            batch_data = self._optimize_batch(batch_data)
        
        try:
            results = await self.processor(batch_data)
            
            process_time = time.time() - start_time
            async with self._stats_lock:
                self._stats["batches_processed"] += 1
                self._stats["items_processed"] += len(items)
                self._stats["total_process_time"] += process_time
                self._stats["total_wait_time"] += sum(
                    time.time() - item.created_at for item in items
                )
            
            logger.debug(f"Processed batch of {len(items)} items in {process_time:.3f}s")
        except Exception as e:
            logger.error(f"Error processing batch: {e}", exc_info=True)
            raise BatchProcessingError(f"Batch processing failed: {e}") from e
    
    def _optimize_batch(self, batch: List[T]) -> List[T]:
        """Optimize batch order by prompt length to minimize padding overhead."""
        if not batch or not self.optimize_batches:
            return batch
        try:
            return sorted(
                batch,
                key=lambda x: len(getattr(x, "prompt", x)) if isinstance(getattr(x, "prompt", x), str) else 0
            )
        except Exception:
            return batch
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get batcher statistics."""
        async with self._stats_lock:
            avg_batch_size = (
                self._stats["items_processed"] / self._stats["batches_processed"]
                if self._stats["batches_processed"] > 0 else 0
            )
            avg_process_time = (
                self._stats["total_process_time"] / self._stats["batches_processed"]
                if self._stats["batches_processed"] > 0 else 0
            )
            avg_wait_time = (
                self._stats["total_wait_time"] / self._stats["items_processed"]
                if self._stats["items_processed"] > 0 else 0
            )
            
            return {
                **self._stats,
                "queue_size": self._queue.qsize(),
                "avg_batch_size": avg_batch_size,
                "avg_process_time": avg_process_time,
                "avg_wait_time": avg_wait_time,
            }


class ContinuousBatcher(DynamicBatcher[T, R]):
    """
    Continuous batcher that processes items as they arrive using asyncio.
    """
    
    def __init__(
        self,
        processor: Optional[Callable] = None,
        engine: Optional[Any] = None,
        latency_budget_ms: Optional[float] = None,
        max_wait_time: float = 0.02,
        **kwargs
    ):
        async def _dynamic_processor(batch):
            eng = getattr(self, "engine", engine)
            if eng is not None:
                if hasattr(eng, "generate_batch"):
                    return await eng.generate_batch(batch)
                elif hasattr(eng, "agenerate"):
                    return await eng.agenerate(batch)
                elif hasattr(eng, "generate"):
                    loop = asyncio.get_running_loop()
                    return await loop.run_in_executor(None, eng.generate, batch)
            if processor is not None:
                return await processor(batch)
            raise RuntimeError("No engine or processor configured for ContinuousBatcher")
        
        if latency_budget_ms is not None:
            max_wait_time = latency_budget_ms / 1000.0
            
        super().__init__(processor=_dynamic_processor, max_wait_time=max_wait_time, **kwargs)
        self.engine = engine
        self._pending_results: Dict[int, asyncio.Future] = {}
        self._result_counter = 0

    async def stop(self):
        """Stop batcher and set exception on any pending result futures."""
        await super().stop()
        for fut in self._pending_results.values():
            if not fut.done():
                fut.set_exception(BatchProcessingError("ContinuousBatcher stopped before request completion"))
        self._pending_results.clear()
    
    async def submit_async(
        self,
        item: T,
        priority: BatchPriority = BatchPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Awaitable[R]:
        """
        Submit item and return an asyncio.Future for the result.
        """
        self._result_counter += 1
        result_id = self._result_counter
        
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_results[result_id] = future
        
        if metadata is None:
            metadata = {}
        metadata["result_id"] = result_id
        
        await self.submit(item, priority, metadata)
        return future
            
    async def _process_batch(self, items: List[BatchItem[T]]):
        """Process batch and dispatch results back to pending futures."""
        if not items:
            return
            
        start_time = time.time()
        batch_data = [item.data for item in items]
        
        proc = None
        if self.engine is not None:
            if hasattr(self.engine, "agenerate"):
                proc = self.engine.agenerate
            elif hasattr(self.engine, "generate_batch"):
                proc = self.engine.generate_batch
            elif hasattr(self.engine, "generate"):
                proc = self.engine.generate
            else:
                proc = self.engine
        if proc is None:
            proc = self.processor
            
        if proc is None:
            raise BatchProcessingError("No engine or processor configured for ContinuousBatcher")
                
        try:
            import inspect
            if inspect.iscoroutinefunction(proc):
                results = await proc(batch_data)
            else:
                res = proc(batch_data)
                if asyncio.iscoroutine(res) or hasattr(res, "__await__"):
                    results = await res
                else:
                    results = res
            
            if not isinstance(results, list):
                results = [results] * len(items)
            elif len(results) != len(items):
                logger.warning(f"Batch results length ({len(results)}) doesn't match items ({len(items)}).")
                results = results[:len(items)]
                results.extend([None] * (len(items) - len(results)))
                
            for item, result in zip(items, results):
                result_id = item.metadata.get("result_id")
                if result_id is not None:
                    future = self._pending_results.pop(result_id, None)
                    if future and not future.done():
                        future.set_result(result)
                            
            process_time = time.time() - start_time
            async with self._stats_lock:
                self._stats["batches_processed"] += 1
                self._stats["items_processed"] += len(items)
                self._stats["total_process_time"] += process_time
                self._stats["total_wait_time"] += sum(
                    time.time() - item.created_at for item in items
                )
                
            logger.debug(f"Processed continuous batch of {len(items)} items in {process_time:.3f}s")
            
        except Exception as e:
            logger.error(f"Error processing batch in ContinuousBatcher: {e}", exc_info=True)
            for item in items:
                result_id = item.metadata.get("result_id")
                if result_id is not None:
                    future = self._pending_results.pop(result_id, None)
                    if future and not future.done():
                        future.set_exception(e)
