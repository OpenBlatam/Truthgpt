import logging
from typing import List, Any
from ..interfaces.middleware_protocol import MiddlewareProtocol, NextHandler
from ..interfaces.engine_protocol import AsyncInferenceEngine
from ..schemas.requests import InferenceRequest

logger = logging.getLogger(__name__)

class ExecutionPipeline:
    """
    Orchestrates the Chain of Responsibility.
    Wraps an InferenceEngine with a series of MiddlewareProtocols.
    """
    def __init__(self, engine: AsyncInferenceEngine, middlewares: List[MiddlewareProtocol]):
        self.engine = engine
        self.middlewares = middlewares
        
    async def _engine_handler(self, request_payload: Any) -> Any:
        """
        The terminal handler in the chain. Calls the actual engine.
        """
        if isinstance(request_payload, InferenceRequest):
            if request_payload.stream:
                return self.engine.generate_stream(
                    prompt=request_payload.prompt,
                    **request_payload.generation_kwargs
                )
            else:
                # Mock aggregation of stream for non-streaming requests
                stream = self.engine.generate_stream(
                    prompt=request_payload.prompt,
                    **request_payload.generation_kwargs
                )
                return "".join([chunk async for chunk in stream])
        raise ValueError("Unsupported payload type for Engine Handler")

    async def execute(self, request_payload: Any) -> Any:
        """
        Executes the request through the middleware pipeline.
        """
        # Build the chain backwards
        current_handler: NextHandler = self._engine_handler
        
        for middleware in reversed(self.middlewares):
            def make_handler(mw=middleware, nxt=current_handler):
                async def handler(payload):
                    return await mw.process(payload, nxt)
                return handler
            current_handler = make_handler()
            
        return await current_handler(request_payload)
