import sys
import logging
from typing import Any

_mod = sys.modules.get(__name__)
if _mod:
    sys.modules["inference.middleware.cache_interceptor"] = _mod
    sys.modules["optimization_core.inference.middleware.cache_interceptor"] = _mod

try:
    from optimization_core.inference.interfaces.middleware_protocol import MiddlewareProtocol, NextHandler
    from optimization_core.inference.schemas.requests import InferenceRequest
    from optimization_core.inference.interfaces.cache_protocol import KVCacheInterface
except ImportError:
    from ..interfaces.middleware_protocol import MiddlewareProtocol, NextHandler
    from ..schemas.requests import InferenceRequest
    from ..interfaces.cache_protocol import KVCacheInterface


logger = logging.getLogger(__name__)


class CacheInterceptor(MiddlewareProtocol):
    """
    Middleware that intercepts requests and attempts to serve them from the cache.
    Follows Chain of Responsibility pattern.
    """
    def __init__(self, cache: KVCacheInterface):
        self.cache = cache
        
    async def process(self, request_payload: Any, next_handler: NextHandler) -> Any:
        prompt = None
        if hasattr(request_payload, "prompt"):
            prompt = request_payload.prompt
        elif isinstance(request_payload, dict) and "prompt" in request_payload:
            prompt = request_payload["prompt"]

        if not prompt or not isinstance(prompt, str):
            # Pass through if it's not a payload with a prompt
            return await next_handler(request_payload)

        cache_key = str(hash(prompt))
        
        # 1. Check cache
        try:
            cached_result = self.cache.get(0, 0, cache_key)
            if cached_result:
                logger.info(f"Cache HIT for prompt: {prompt[:20]}...")
                if isinstance(cached_result, bytes):
                    return cached_result.decode('utf-8')
                return str(cached_result)
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")
            
        logger.debug(f"Cache MISS for prompt: {prompt[:20]}...")
        
        # 2. Proceed to next handler (which will eventually hit the Engine)
        response = await next_handler(request_payload)
        
        # 3. Cache the response (Assuming response is text for simplicity)
        if isinstance(response, str):
            try:
                self.cache.put(0, 0, response.encode('utf-8'), cache_key)
            except Exception as e:
                logger.error(f"Failed to write to cache: {e}")
        elif hasattr(response, "text") and isinstance(response.text, str):
            try:
                self.cache.put(0, 0, response.text.encode('utf-8'), cache_key)
            except Exception as e:
                logger.error(f"Failed to write to cache: {e}")
                
        return response
