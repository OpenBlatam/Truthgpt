from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, validator

class InferRequest(BaseModel):
    """Inference request model"""
    model: str = Field(..., description="Model identifier")
    prompt: str = Field(..., min_length=1, max_length=8192, description="Input prompt")
    params: Dict[str, Any] = Field(default_factory=dict, description="Generation parameters")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key for deduplication")
    
    @validator("params")
    def validate_params(cls, v):
        """Validate and normalize params"""
        max_tokens = v.get("max_new_tokens", 512)
        if max_tokens > 4096:
            raise ValueError("max_new_tokens cannot exceed 4096")
        return v

class InferResponse(BaseModel):
    """Inference response model"""
    id: str = Field(..., description="Request ID")
    model: str = Field(..., description="Model used")
    output: str = Field(..., description="Generated text")
    usage: Dict[str, int] = Field(..., description="Token usage")
    latency_ms: float = Field(..., description="Inference latency in milliseconds")
    cached: bool = Field(default=False, description="Whether result was cached")

class TokenChunk(BaseModel):
    """Streaming token chunk"""
    text: str = Field(..., description="Token text")
    finish_reason: Optional[str] = Field(None, description="Finish reason if done")

class WebhookPayload(BaseModel):
    """Webhook payload"""
    id: str
    type: str
    payload: Dict[str, Any]
    timestamp: int
