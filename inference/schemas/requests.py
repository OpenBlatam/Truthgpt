from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class InferenceRequest(BaseModel):
    prompt: str = Field(..., description="The input prompt string.")
    request_id: Optional[str] = Field(default=None, description="Unique identifier for tracing.")
    stream: bool = Field(default=False, description="Whether to stream the output.")
    generation_kwargs: Dict[str, Any] = Field(default_factory=dict, description="Additional generation parameters.")

class BatchInferenceRequest(BaseModel):
    prompts: List[str] = Field(..., min_items=1, description="List of input prompts.")
    request_id: Optional[str] = Field(default=None, description="Unique identifier for tracing.")
    generation_kwargs: Dict[str, Any] = Field(default_factory=dict, description="Additional generation parameters.")

class InferenceResponse(BaseModel):
    text: str = Field(..., description="Generated text.")
    request_id: Optional[str] = Field(default=None, description="Unique identifier.")
    latency_ms: float = Field(..., description="Generation latency in milliseconds.")
    model_name: str = Field(..., description="Name of the model used.")

class BatchInferenceResponse(BaseModel):
    responses: List[InferenceResponse] = Field(..., description="List of responses.")
    request_id: Optional[str] = Field(default=None, description="Unique identifier.")
    total_latency_ms: float = Field(..., description="Total batch generation latency.")
