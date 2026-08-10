from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Any, Dict

class InferenceRequest(BaseModel):
    model: str = Field(default="default", description="Model identifier")
    prompt: str = Field(..., min_length=1, description="Input prompt")
    params: Dict[str, Any] = Field(default_factory=dict, description="Generation parameters")
    idempotency_key: Optional[str] = Field(default=None, description="Idempotency key for deduplication")
    request_id: Optional[str] = Field(default=None, description="Unique identifier for tracing.")
    stream: bool = Field(default=False, description="Whether to stream the output.")
    generation_kwargs: Dict[str, Any] = Field(default_factory=dict, description="Additional generation parameters.")

    @field_validator("params")
    @classmethod
    def validate_params(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize params"""
        max_tokens = v.get("max_new_tokens", 512)
        if isinstance(max_tokens, int) and max_tokens > 4096:
            raise ValueError("max_new_tokens cannot exceed 4096")
        return v

    @property
    def id(self) -> Optional[str]:
        return self.request_id

    def to_dataclass(self) -> Any:
        """Convert to dataclass InferenceRequest."""
        from ..core.base_engine import InferenceRequest as DataclassInferenceRequest
        return DataclassInferenceRequest.from_pydantic(self)

    @classmethod
    def from_dataclass(cls, dataclass_obj: Any) -> "InferenceRequest":
        """Create from dataclass InferenceRequest."""
        if hasattr(dataclass_obj, "to_pydantic"):
            return dataclass_obj.to_pydantic()
        params = {"max_tokens": getattr(dataclass_obj, "max_tokens", 128),
                  "temperature": getattr(dataclass_obj, "temperature", 0.7),
                  "top_p": getattr(dataclass_obj, "top_p", 0.95)}
        params.update(getattr(dataclass_obj, "extra_params", {}) or {})
        return cls(
            prompt=getattr(dataclass_obj, "prompt", ""),
            request_id=getattr(dataclass_obj, "request_id", None),
            stream=getattr(dataclass_obj, "stream", False),
            params=params,
            generation_kwargs=getattr(dataclass_obj, "extra_params", {}) or {}
        )

class BatchInferenceRequest(BaseModel):
    prompts: List[str] = Field(..., min_length=1, description="List of input prompts.")
    request_id: Optional[str] = Field(default=None, description="Unique identifier for tracing.")
    generation_kwargs: Dict[str, Any] = Field(default_factory=dict, description="Additional generation parameters.")

class InferenceResponse(BaseModel):
    id: Optional[str] = Field(default=None, description="Request ID")
    model: str = Field(default="default", description="Model used")
    output: str = Field(default="", description="Generated text")
    usage: Dict[str, int] = Field(default_factory=dict, description="Token usage")
    latency_ms: float = Field(default=0.0, description="Inference latency in milliseconds")
    cached: bool = Field(default=False, description="Whether result was cached")
    text: str = Field(default="", description="Generated text (alias for output).")
    request_id: Optional[str] = Field(default=None, description="Unique identifier.")
    model_name: str = Field(default="default", description="Name of the model used.")

    def __init__(self, **data: Any):
        # Handle field aliases for backwards compatibility
        if "text" in data and ("output" not in data or not data["output"]):
            data["output"] = data["text"]
        elif "output" in data and ("text" not in data or not data["text"]):
            data["text"] = data["output"]
            
        if "id" in data and ("request_id" not in data or not data["request_id"]):
            data["request_id"] = data["id"]
        elif "request_id" in data and ("id" not in data or not data["id"]):
            data["id"] = data["request_id"]
            
        if "model_name" in data and ("model" not in data or data["model"] == "default"):
            data["model"] = data["model_name"]
        elif "model" in data and ("model_name" not in data or data["model_name"] == "default"):
            data["model_name"] = data["model"]
            
        super().__init__(**data)

    def to_dataclass(self) -> Any:
        """Convert to dataclass InferenceResponse."""
        from ..core.base_engine import InferenceResponse as DataclassInferenceResponse
        return DataclassInferenceResponse.from_pydantic(self)

    @classmethod
    def from_dataclass(cls, dataclass_obj: Any) -> "InferenceResponse":
        """Create from dataclass InferenceResponse."""
        if hasattr(dataclass_obj, "to_pydantic"):
            return dataclass_obj.to_pydantic()
        text = getattr(dataclass_obj, "text", "")
        model_name = getattr(dataclass_obj, "model_name", "")
        latency_ms = getattr(dataclass_obj, "latency_ms", 0.0)
        request_id = getattr(dataclass_obj, "request_id", None)
        tokens = getattr(dataclass_obj, "tokens_generated", None)
        return cls(
            text=text,
            output=text,
            model=model_name,
            model_name=model_name,
            latency_ms=latency_ms,
            request_id=request_id,
            usage={"total_tokens": tokens} if tokens is not None else {}
        )

class BatchInferenceResponse(BaseModel):
    responses: List[InferenceResponse] = Field(..., description="List of responses.")
    request_id: Optional[str] = Field(default=None, description="Unique identifier.")
    total_latency_ms: float = Field(..., description="Total batch generation latency.")

InferRequest = InferenceRequest
InferResponse = InferenceResponse


# Backward & cross-module compatibility aliases
InferRequest = InferenceRequest
InferResponse = InferenceResponse


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


