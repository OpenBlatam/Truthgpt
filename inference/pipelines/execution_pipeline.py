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
    def __init__(self, engine: Any, middlewares: List[MiddlewareProtocol] = None):
        self.engine = engine
        self.middlewares = middlewares or []
        
    async def _engine_handler(self, request_payload: Any) -> Any:
        """
        The terminal handler in the chain. Calls the actual engine.
        """
        prompt = ""
        gen_kwargs = {}
        stream = False

        if hasattr(request_payload, "prompt"):
            prompt = request_payload.prompt
            raw_kwargs = getattr(request_payload, 'generation_kwargs', None) or getattr(request_payload, 'params', None) or {}
            gen_kwargs = dict(raw_kwargs) if isinstance(raw_kwargs, dict) else {}
            for attr in ("max_tokens", "max_new_tokens", "temperature", "top_p"):
                if hasattr(request_payload, attr) and attr not in gen_kwargs:
                    val = getattr(request_payload, attr)
                    if val is not None:
                        gen_kwargs[attr] = val
            stream = getattr(request_payload, 'stream', False)
        elif isinstance(request_payload, dict):
            prompt = request_payload.get("prompt", "")
            gen_kwargs = dict(request_payload.get("generation_kwargs", request_payload.get("params", {})))
            for attr in ("max_tokens", "max_new_tokens", "temperature", "top_p"):
                if attr in request_payload and attr not in gen_kwargs:
                    gen_kwargs[attr] = request_payload[attr]
            stream = request_payload.get("stream", False)
        elif isinstance(request_payload, str):
            prompt = request_payload
        else:
            raise ValueError(f"Unsupported payload type for Engine Handler: {type(request_payload)}")


        if stream and hasattr(self.engine, "generate_stream"):
            return self.engine.generate_stream(prompt=prompt, **gen_kwargs)
        
        if hasattr(self.engine, "async_generate"):
            return await self.engine.async_generate(prompt, **gen_kwargs)
        elif hasattr(self.engine, "generate_async"):
            return await self.engine.generate_async(prompt, **gen_kwargs)
        elif hasattr(self.engine, "generate_stream"):
            chunks = []
            async for chunk in self.engine.generate_stream(prompt=prompt, **gen_kwargs):
                chunks.append(str(chunk))
            return "".join(chunks)
        elif hasattr(self.engine, "generate"):
            return self.engine.generate(prompt, **gen_kwargs)
        else:
            raise AttributeError(f"Engine {type(self.engine)} has no generation methods")

    async def execute(self, request_payload: Any) -> Any:
        """
        Executes the request through the middleware pipeline.
        """
        try:
            current_handler: NextHandler = self._engine_handler
            
            for middleware in reversed(self.middlewares):
                def make_handler(mw: MiddlewareProtocol, nxt: NextHandler):
                    async def handler(payload: Any) -> Any:
                        return await mw.process(payload, nxt)
                    return handler
                current_handler = make_handler(middleware, current_handler)
                
            return await current_handler(request_payload)
        except Exception as e:
            logger.error(f"ExecutionPipeline failed during request processing: {e}", exc_info=True)
            raise

