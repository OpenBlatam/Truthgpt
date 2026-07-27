import logging
from typing import Any
from ..interfaces.middleware_protocol import MiddlewareProtocol, NextHandler
from ..schemas.requests import InferenceRequest
from ..interfaces.cache_protocol import KVCacheInterface

logger = logging.getLogger(__name__)

class CacheInterceptor(MiddlewareProtocol):
    """
    Middleware that intercepts requests and attempts to serve them from the cache.
    Follows Chain of Responsibility.
    """
    def __init__(self, cache: KVCacheInterface):
        self.cache = cache
        
    async def process(self, request_payload: Any, next_handler: NextHandler) -> Any:
        if not isinstance(request_payload, InferenceRequest):
            # Pass through if it's not a standard request
            return await next_handler(request_payload)

        prompt = request_payload.prompt
        cache_key = str(hash(prompt))
        
        # 1. Check cache
        cached_result = self.cache.get(0, 0, cache_key)
        if cached_result:
            logger.info(f"Cache HIT for prompt: {prompt[:20]}...")
            return cached_result.decode('utf-8')
            
        logger.debug(f"Cache MISS for prompt: {prompt[:20]}...")
        
        # 2. Proceed to next handler (which will eventually hit the Engine)
        response = await next_handler(request_payload)
        
        # 3. Cache the response (Assuming response is text for simplicity in this mock)
        if isinstance(response, str):
            try:
                self.cache.put(0, 0, response.encode('utf-8'), cache_key)
            except Exception as e:
                logger.error(f"Failed to write to cache: {e}")
                
        return response
