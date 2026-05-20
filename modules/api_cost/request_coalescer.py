"""
Request Coalescing & Deduplication (System 5.9).
"""

import asyncio
import hashlib
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("optimization.api_cost.coalescer")

class RequestCoalescer:
    """
    Coalesces identical in-flight requests.
    
    If multiple agents request the same prompt/model combo simultaneously,
    only one API call is made, and the result is shared.
    """
    
    def __init__(self):
        self._in_flight: Dict[str, asyncio.Future] = {}

    async def execute(self, key: str, coro_func, *args, **kwargs) -> Any:
        # Create a unique key for the request
        request_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if request_hash in self._in_flight:
            logger.info("🔗 Coalescing: Request already in flight, waiting for result.")
            return await self._in_flight[request_hash]
            
        # Register new in-flight request
        future = asyncio.get_event_loop().create_future()
        self._in_flight[request_hash] = future
        
        try:
            result = await coro_func(*args, **kwargs)
            future.set_result(result)
            return result
        except Exception as e:
            future.set_exception(e)
            raise e
        finally:
            # Clean up after all waiters are done
            self._in_flight.pop(request_hash, None)
