"""
TruthGPT Kernel Services

Modular services that replace the monolithic architecture:
- AgentService: Manages AI agents and swarm operations
- ModelService: Handles model inference and management
- ResearchService: Papers, research, and knowledge management
- OptimizationService: System optimization and performance
- InferenceService: High-performance inference engine
- BenchmarkService: Tracks optimization savings and metrics
- TraceService: Records decision-making traces and rationales
"""

from .base_service import BaseService, ServiceState
from .agent_service import AgentService
from .model_service import ModelService
from .research_service import ResearchService
from .optimization_service import OptimizationService
from .inference_service import InferenceService
from .benchmark_service import BenchmarkService
from .trace_service import TraceService

__all__ = [
    "BaseService",
    "ServiceState",
    "AgentService",
    "ModelService", 
    "ResearchService",
    "OptimizationService",
    "InferenceService",
    "BenchmarkService",
    "TraceService",
]
