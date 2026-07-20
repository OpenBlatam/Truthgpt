"""
polyglot_core.domain
====================

Domain layer – pure business logic with zero infrastructure dependencies.

This package contains:
  - Value Objects  : immutable, self-validating data carriers
  - Entities       : identity-carrying domain objects
  - Aggregates     : consistency boundaries
  - Domain Events  : side-effect triggers across bounded contexts
  - Domain Services: stateless domain operations
  - Repositories   : abstract data-access contracts
  - Specifications : composable predicate objects

Dependency Rule: this package must NEVER import from infrastructure,
application, or presentation layers.
"""

from __future__ import annotations

from polyglot_core.domain.value_objects import (
    BackendCapability,
    BackendDescriptor,
    ComputeBudget,
    LatencyBound,
    MemoryBound,
    ModelDimensions,
    QoSPolicy,
    SamplingParameters,
    TensorShape,
    TokenizerSpec,
)
from polyglot_core.domain.entities import (
    BackendNode,
    CacheEntry,
    InferenceRequest,
    InferenceResponse,
    TokenSequence,
)
from polyglot_core.domain.events import (
    BackendDegradedEvent,
    BackendRecoveredEvent,
    CacheEvictionEvent,
    CacheHitEvent,
    CacheMissEvent,
    GenerationCompletedEvent,
    GenerationStartedEvent,
    InferenceFailedEvent,
    QuantizationAppliedEvent,
)
from polyglot_core.domain.exceptions import (
    BackendUnavailableError,
    BudgetExceededError,
    DimensionMismatchError,
    DomainValidationError,
    EmptyInputError,
    InvalidConfigurationError,
    LatencyBudgetExceededError,
    MemoryBudgetExceededError,
    ModelNotFoundError,
    QuantizationError,
    TokenLimitExceededError,
)

__all__ = [
    # Value Objects
    "BackendCapability",
    "BackendDescriptor",
    "ComputeBudget",
    "LatencyBound",
    "MemoryBound",
    "ModelDimensions",
    "QoSPolicy",
    "SamplingParameters",
    "TensorShape",
    "TokenizerSpec",
    # Entities
    "BackendNode",
    "CacheEntry",
    "InferenceRequest",
    "InferenceResponse",
    "TokenSequence",
    # Events
    "BackendDegradedEvent",
    "BackendRecoveredEvent",
    "CacheEvictionEvent",
    "CacheHitEvent",
    "CacheMissEvent",
    "GenerationCompletedEvent",
    "GenerationStartedEvent",
    "InferenceFailedEvent",
    "QuantizationAppliedEvent",
    # Exceptions
    "BackendUnavailableError",
    "BudgetExceededError",
    "DimensionMismatchError",
    "DomainValidationError",
    "EmptyInputError",
    "InvalidConfigurationError",
    "LatencyBudgetExceededError",
    "MemoryBudgetExceededError",
    "ModelNotFoundError",
    "QuantizationError",
    "TokenLimitExceededError",
]
