"""
Service layer with clear interfaces for business logic and modular microservices.
"""
import sys

if "optimization_core.core.services" not in sys.modules:
    sys.modules["optimization_core.core.services"] = sys.modules[__name__]
if "core.services" not in sys.modules:
    sys.modules["core.services"] = sys.modules[__name__]

from .base_service import BaseService

from .model_service import ModelService
from .training_service import TrainingService
from .inference_service import InferenceService

try:
    from .modular_microservices import (
        MicroserviceComponent,
        ModularServiceLevel,
        ModularMicroserviceResult,
        QuantizationMicroservice,
        PruningMicroservice,
        EnhancementMicroservice,
        AccelerationMicroservice,
        AIMicroservice,
        ModularMicroserviceOrchestrator,
        ModularMicroserviceSystem,
        create_modular_microservice_system,
    )
except ImportError:
    MicroserviceComponent = None  # type: ignore
    ModularServiceLevel = None  # type: ignore
    ModularMicroserviceResult = None  # type: ignore
    QuantizationMicroservice = None  # type: ignore
    PruningMicroservice = None  # type: ignore
    EnhancementMicroservice = None  # type: ignore
    AccelerationMicroservice = None  # type: ignore
    AIMicroservice = None  # type: ignore
    ModularMicroserviceOrchestrator = None  # type: ignore
    ModularMicroserviceSystem = None  # type: ignore
    create_modular_microservice_system = None  # type: ignore

try:
    from ..kernel.services.agent_service import AgentService, AgentProcess, AgentScheduler
except ImportError:
    try:
        from ..kernels.services.agent_service import AgentService
        AgentProcess = None  # type: ignore
        AgentScheduler = None  # type: ignore
    except ImportError:
        AgentService = None  # type: ignore
        AgentProcess = None  # type: ignore
        AgentScheduler = None  # type: ignore

__all__ = [
    "BaseService",
    "ModelService",
    "TrainingService",
    "InferenceService",
    "AgentService",
    "AgentProcess",
    "AgentScheduler",
    "MicroserviceComponent",
    "ModularServiceLevel",
    "ModularMicroserviceResult",
    "QuantizationMicroservice",
    "PruningMicroservice",
    "EnhancementMicroservice",
    "AccelerationMicroservice",
    "AIMicroservice",
    "ModularMicroserviceOrchestrator",
    "ModularMicroserviceSystem",
    "create_modular_microservice_system",
]
