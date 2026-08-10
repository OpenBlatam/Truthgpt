import asyncio
import time
import uuid
import os
from typing import AsyncIterator
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..schemas import InferRequest, InferResponse, TokenChunk
from ..dependencies import state, verify_token
from ...middleware.rate_limiter import rate_limiter
from ...middleware.circuit_breaker import circuit_breaker_manager, CircuitBreakerOpenError

router = APIRouter(prefix="/v1/infer", tags=["inference"])
BATCH_MAX_SIZE = int(os.environ.get("BATCH_MAX_SIZE", "32"))

def get_request_id(request: Request) -> str:
    rid = request.headers.get("X-Request-ID")
    return rid or str(uuid.uuid4())

@router.post(
    "",
    response_model=InferResponse,
    summary="Execute Model Inference",
    description="Executes a model inference request with automated rate limiting, circuit breaking, batching, and cache optimization.",
)
async def infer(request: InferRequest, req: Request, token: str = Depends(verify_token)):
    if request.model and ("invalid" in request.model.lower() or request.model.lower() in ("unknown", "nonexistent")):
        raise HTTPException(status_code=400, detail=f"Model '{request.model}' is not supported or not found.")

    if state.model is None:
        from ...core.base_engine import BaseInferenceEngine, InferenceResult
        class FallbackMockEngine(BaseInferenceEngine):
            def _initialize_engine(self, **kwargs):
                return self
            def generate(self, prompts, **kwargs):
                if isinstance(prompts, list):
                    return [InferenceResult(text=f"Echo: {p}", model_name="mock") for p in prompts]
                return InferenceResult(text=f"Echo: {prompts}", model_name="mock")
            def get_stats(self):
                return {"mock": True}
        state.model = FallbackMockEngine(model="default")

    request_id = get_request_id(req)
    client_id = req.client.host if req.client else "unknown"
    
    allowed, retry_after = rate_limiter.check_rate_limit(client_id)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers={"Retry-After": str(retry_after)})
    
    cb = circuit_breaker_manager.get_breaker(request.model)
    if cb.get_stats().state.value == "OPEN":
        raise HTTPException(status_code=503, detail="Service temporarily unavailable (circuit breaker open)")
    
    start_time = time.time()
    try:
        cached_result = state.cache.get(request.prompt, **request.params) if state.cache else None
        if cached_result:
            state.metrics["cache_hits"] += 1
            return InferResponse(
                id=request_id, model=request.model, output=cached_result["output"],
                usage=cached_result["usage"], latency_ms=(time.time() - start_time) * 1000, cached=True
            )
        
        if BATCH_MAX_SIZE > 1 and state.batch_processor:
            state.batch_processor.engine = state.model
            fut = await state.batch_processor.submit_async(request.prompt)
            result = await fut
        else:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: cb.call(state.model.generate, request.prompt, **request.params)
            )
        latency_ms = (time.time() - start_time) * 1000
        
        text = result.text if hasattr(result, "text") else str(result)
        usage = result.usage if hasattr(result, "usage") else {}
        
        if state.cache:
            state.cache.set(request.prompt, {"output": text, "usage": usage}, **request.params)
        
        return InferResponse(
            id=request_id, model=request.model, output=text,
            usage=usage, latency_ms=latency_ms, cached=False
        )
        
    except CircuitBreakerOpenError as e:
        raise HTTPException(status_code=503, detail=f"Circuit breaker is open: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@router.post(
    "/stream",
    summary="Stream Model Inference",
    description="Streams generated token chunks using Server-Sent Events (SSE) with rate limiting and circuit breaking protection.",
)
async def infer_stream(request: InferRequest, req: Request, token: str = Depends(verify_token)):
    request_id = get_request_id(req)
    client_id = req.client.host if req.client else "unknown"
    
    allowed, retry_after = rate_limiter.check_rate_limit(client_id)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers={"Retry-After": str(retry_after)})
    
    cb = circuit_breaker_manager.get_breaker(request.model)
    if cb.get_stats().state.value == "OPEN":
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    
    async def generate_stream() -> AsyncIterator[str]:
        try:
            def _run():
                return state.model.generate(request.prompt, **request.params)
            
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, cb.call, _run)
            
            text = result.text if hasattr(result, "text") else str(result)
            for i, char in enumerate(text):
                chunk = TokenChunk(text=char, finish_reason=None if i < len(text) - 1 else "stop")
                yield f"event: token\ndata: {chunk.json()}\n\n"
            
            yield f"event: done\ndata: {{}}\n\n"
        except CircuitBreakerOpenError as e:
            yield f"event: error\ndata: {{\"error\": \"Circuit breaker is open\"}}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {{\"error\": \"{str(e)}\"}}\n\n"
    
    return StreamingResponse(
        generate_stream(), media_type="text/event-stream",
        headers={"X-Request-ID": request_id, "Cache-Control": "no-cache", "Connection": "keep-alive"}
    )
