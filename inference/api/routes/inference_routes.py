"""
Inference API Routes
"""
import time
import asyncio
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator

from ...middleware.rate_limiter import rate_limiter
from ...middleware.circuit_breaker import circuit_breaker_manager, CircuitBreakerOpenError
from ...api_state import get_global_state

router = APIRouter()

class InferRequest(BaseModel):
    model: str = Field(..., description="Model identifier")
    prompt: str = Field(..., min_length=1, max_length=8192)
    params: Dict[str, Any] = Field(default_factory=dict)
    
    @validator("params")
    def validate_params(cls, v):
        max_tokens = v.get("max_new_tokens", 512)
        if max_tokens > 4096:
            raise ValueError("max_new_tokens cannot exceed 4096")
        return v

class InferResponse(BaseModel):
    id: str
    model: str
    output: str
    usage: Dict[str, int]
    latency_ms: float
    cached: bool = False

def get_request_id(req: Request) -> str:
    return req.headers.get("X-Request-ID", str(time.time()))

@router.post("/v1/infer", response_model=InferResponse)
async def infer(request: InferRequest, req: Request):
    request_id = get_request_id(req)
    client_id = req.client.host if req.client else "unknown"
    
    allowed, retry_after = rate_limiter.check_rate_limit(client_id)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
    cb = circuit_breaker_manager.get_breaker(request.model)
    if cb.get_stats().state.value == "OPEN":
        raise HTTPException(status_code=503, detail="Circuit breaker open")
        
    state = get_global_state()
    start_time = time.time()
    
    try:
        cached_result = state.cache.get(request.prompt, **request.params) if state.cache else None
        if cached_result:
            return InferResponse(
                id=request_id, model=request.model, output=cached_result["output"],
                usage=cached_result["usage"], latency_ms=(time.time() - start_time) * 1000, cached=True
            )
            
        async def _run_inference():
            if state.batch_processor:
                return await state.batch_processor.submit_async(
                    item={"prompt": request.prompt, "params": request.params}
                )
            return await state.model.generate_async(request.prompt, **request.params)
            
        result = await cb.call(_run_inference)
        latency_ms = (time.time() - start_time) * 1000
        
        text = result.text if hasattr(result, "text") else str(result)
        usage = result.usage if hasattr(result, "usage") else {}
        
        if state.cache:
            state.cache.set(request.prompt, {"output": text, "usage": usage}, **request.params)
            
        return InferResponse(
            id=request_id, model=request.model, output=text,
            usage=usage, latency_ms=latency_ms
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/v1/infer/stream")
async def infer_stream(request: InferRequest, req: Request):
    client_id = req.client.host if req.client else "unknown"
    
    allowed, retry_after = rate_limiter.check_rate_limit(client_id)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
    cb = circuit_breaker_manager.get_breaker(request.model)
    if cb.get_stats().state.value == "OPEN":
        raise HTTPException(status_code=503, detail="Circuit breaker open")
        
    state = get_global_state()
    
    async def generate_stream():
        try:
            async for chunk in state.model.stream_async(request.prompt, **request.params):
                yield f"event: token\\ndata: {{\"text\": \"{chunk}\"}}\\n\\n"
            yield "event: done\\ndata: {}\\n\\n"
        except Exception as e:
            yield f"event: error\\ndata: {{\"error\": \"{str(e)}\"}}\\n\\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )
