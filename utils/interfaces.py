"""
TruthGPT Optimization Core Utilities — Interfaces and Abstract Base Classes
===========================================================================
Defines abstract contracts and base models for optimization utilities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

try:
    from pydantic import BaseModel, ConfigDict
    _PYDANTIC_AVAILABLE = True
except ImportError:
    _PYDANTIC_AVAILABLE = False
    class BaseModel:  # type: ignore
        def __init__(self, **data: Any):
            for k, v in data.items():
                setattr(self, k, v)
        def dict(self) -> Dict[str, Any]:
            return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        def model_dump(self) -> Dict[str, Any]:
            return self.dict()


class BaseOptimizationModel(BaseModel):
    """
    Standard Base Model for all optimization configurations, payloads,
    and metadata models across the TruthGPT Optimization Core.
    """
    if _PYDANTIC_AVAILABLE:
        model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    def to_summary(self) -> Dict[str, Any]:
        """Return a summarized dictionary view of the model."""
        if hasattr(self, "model_dump"):
            return self.model_dump(exclude_none=True)
        return self.dict()

    def to_dict(self) -> Dict[str, Any]:
        """Convert model attributes to dictionary."""
        return self.to_summary()


class BaseUtility(ABC):
    """Abstract Base Class for all utility components in optimization_core."""

    @abstractmethod
    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Initialize utility resources."""
        raise NotImplementedError

    def shutdown(self) -> None:
        """Release allocated resources."""
        pass

    def cleanup(self) -> None:
        """Alias for shutdown."""
        self.shutdown()

    def health_check(self) -> Dict[str, Any]:
        """Perform a self-diagnostic health check."""
        return {"status": "healthy"}

    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata describing the utility."""
        return {"name": self.__class__.__name__}


class BaseOptimizer(ABC):
    """Abstract interface for optimization components."""

    @abstractmethod
    def optimize(self, target: Any, *args: Any, **kwargs: Any) -> Any:
        """Apply optimization transformation to target."""
        raise NotImplementedError

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Return runtime optimization statistics."""
        raise NotImplementedError


BaseOptimizerUtility = BaseOptimizer


class BaseManager(ABC):
    """Abstract interface for resource and hardware lifecycle managers."""

    def setup(self) -> None:
        """Setup management context."""
        pass

    def teardown(self) -> None:
        """Teardown management context."""
        pass

    def get_status(self) -> Dict[str, Any]:
        """Return current manager status."""
        return {"status": "active"}


BaseHardwareManager = BaseManager


class BaseTracker(ABC):
    """Abstract interface for experiment tracking and metric logging."""

    @abstractmethod
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        """Log numerical metrics at a given step."""
        raise NotImplementedError

    @abstractmethod
    def log_params(self, params: Dict[str, Any]) -> None:
        """Log hyperparameter configuration."""
        raise NotImplementedError

    def finish(self) -> None:
        """Finalize tracking session."""
        pass


class BaseMetricsCollector(ABC):
    """Abstract interface for hardware telemetry and metrics collectors."""

    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """Sample and return hardware and system metrics."""
        raise NotImplementedError


BaseTelemetryCollector = BaseMetricsCollector


class BaseResilienceHandler(BaseUtility):
    """Abstract base class for resilience primitives (circuit breakers, retries, rate limiters)."""

    @abstractmethod
    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute a callable with applied resilience policy."""
        pass

    def reset(self) -> None:
        """Reset resilience tracking state."""
        pass

    def get_state(self) -> Dict[str, Any]:
        """Return current status dictionary of the resilience handler."""
        return {}


class BaseConfigManager(BaseUtility):
    """Abstract base class for configuration loading, validation, and export."""

    def load(self, source: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        return {}

    def validate(self, config: Dict[str, Any]) -> bool:
        return True

    def export(self, config: Dict[str, Any], destination: str) -> None:
        pass


class BaseAdapter(ABC):
    """Abstract interface for inter-subsystem adapters and connectors."""

    @abstractmethod
    def adapt(self, target: Any, **kwargs: Any) -> Any:
        """Bridge or adapt the target for downstream execution."""
        raise NotImplementedError


BaseSerializationHandler = BaseAdapter


class BaseLogger(ABC):
    """Abstract interface for structured training and system loggers."""

    @abstractmethod
    def log_step(self, step: int, epoch: int, loss: float, **kwargs: Any) -> None:
        """Log training step progress."""
        raise NotImplementedError

    @abstractmethod
    def log_eval(self, step: int, val_loss: float, **kwargs: Any) -> None:
        """Log evaluation phase results."""
        raise NotImplementedError


class BaseTaskScheduler(BaseUtility):
    """Abstract base class for asynchronous and threaded task scheduling."""

    def submit(self, task_id: str, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        pass

    def cancel(self, task_id: str) -> bool:
        return False

    def get_task_status(self, task_id: str) -> Optional[str]:
        return None


__all__ = [
    "BaseOptimizationModel",
    "BaseUtility",
    "BaseOptimizer",
    "BaseOptimizerUtility",
    "BaseManager",
    "BaseHardwareManager",
    "BaseTracker",
    "BaseMetricsCollector",
    "BaseTelemetryCollector",
    "BaseResilienceHandler",
    "BaseConfigManager",
    "BaseAdapter",
    "BaseSerializationHandler",
    "BaseLogger",
    "BaseTaskScheduler",
]
