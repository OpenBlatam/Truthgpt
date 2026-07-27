import asyncio
import logging
from typing import Optional, Dict
try:
    from ..pipelines.execution_pipeline import ExecutionPipeline
    from ..schemas.requests import InferenceRequest, InferenceResponse
except ImportError:
    from inference.pipelines.execution_pipeline import ExecutionPipeline
    from inference.schemas.requests import InferenceRequest, InferenceResponse

logger = logging.getLogger(__name__)

class SmartSchedulerAdapter:
    """
    Adapter bridging the external smart_scheduler.py to the ExecutionPipeline.
    Ensures non-blocking, queue-based request ingestion.
    """
    def __init__(self, pipeline: ExecutionPipeline, max_queue_size: int = 1000):
        self.pipeline = pipeline
        self.request_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.response_registry: Dict[str, asyncio.Future] = {}
        self._worker_task: Optional[asyncio.Task] = None

    async def start(self):
        """Starts the background worker consuming from the scheduler queue."""
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._process_queue())
            logger.info("SmartSchedulerAdapter started.")

    async def stop(self):
        """Stops the background worker."""
        if self._worker_task:
            self._worker_task.cancel()
            self._worker_task = None
            logger.info("SmartSchedulerAdapter stopped.")

    async def submit_request(self, request: InferenceRequest) -> asyncio.Future:
        """
        Submits a request from the smart_scheduler to the inference pipeline.
        Returns a Future that the scheduler can await.
        """
        req_id = request.request_id or "default_id"
        future = asyncio.Future()
        self.response_registry[req_id] = future
        
        try:
            await self.request_queue.put(request)
        except asyncio.QueueFull:
            logger.error("Inference request queue is full. Rejecting.")
            future.set_exception(RuntimeError("Queue Full"))
            
        return future

    async def _process_queue(self):
        """Background task processing requests continuously."""
        while True:
            try:
                request: InferenceRequest = await self.request_queue.get()
                req_id = request.request_id or "default_id"
                
                try:
                    # Execute through the middleware pipeline
                    response_text = await self.pipeline.execute(request)
                    
                    response = InferenceResponse(
                        text=str(response_text),
                        request_id=req_id,
                        latency_ms=0.0, # Handled by tracing in real implementation
                        model_name="tensorrt_model_dynamic"
                    )
                    
                    if req_id in self.response_registry:
                        self.response_registry[req_id].set_result(response)
                except Exception as e:
                    logger.error(f"Failed processing request {req_id}: {e}")
                    if req_id in self.response_registry:
                        self.response_registry[req_id].set_exception(e)
                finally:
                    self.request_queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Critical error in adapter worker: {e}")
