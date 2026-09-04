"""
🧭 TruthGPT Cloud - Routing Data Models
Defines response envelopes and streaming chunk models for cloud inference routing.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional


@dataclass
class CloudInferenceResponse:
    response_id: str
    content: str
    tier_used: str
    model_name: str
    execution_time_ms: float
    tokens_consumed: int
    tokens_remaining_today: int
    time_to_first_token_ms: float = 0.0
    model_used: str = ""
    proof_certificate: Optional[Dict[str, Any]] = None
    swarm_trace: Optional[Dict[str, Any]] = None
    verification_passed: bool = True
    confidence_score: float = 0.99
    priority_routing: bool = False

    def __post_init__(self):
        if not self.model_used:
            self.model_used = self.model_name
        if self.time_to_first_token_ms == 0.0:
            self.time_to_first_token_ms = round(max(0.1, self.execution_time_ms * 0.15), 2)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StreamChunk:
    chunk_id: str
    delta_text: str
    is_final: bool
    proof_certificate: Optional[Dict[str, Any]] = None
    tokens_consumed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


__all__ = [
    "CloudInferenceResponse",
    "StreamChunk",
]
