"""
Exception Hierarchy for Learning Subsystem
==========================================
Defines typed exceptions for error handling, validation,
and recovery across all learning modules and pipelines.
"""

from __future__ import annotations
from typing import Optional, Any, Dict


class LearningBaseException(Exception):
    """Base exception for all errors originating from the learning module."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class LearningError(LearningBaseException):
    """General error during learning strategy execution."""
    pass


class LearnerNotFoundError(LearningBaseException):
    """Raised when a requested learner or strategy is not registered."""
    pass


class LearnerInitializationError(LearningBaseException):
    """Raised when a learner fails to initialize its model, environment, or parameters."""
    pass


class LearnerConfigurationError(LearningBaseException):
    """Raised when provided hyperparameters or configurations are invalid."""
    pass


class OptimizationFailedError(LearningBaseException):
    """Raised when an optimization process fails to find a viable solution."""
    pass


class ConvergenceError(LearningBaseException):
    """Raised when an algorithm fails to converge within the allotted step/epoch budget."""
    pass


class StrategyNotSupportedError(LearningBaseException):
    """Raised when an unsupported algorithm or combination of strategies is specified."""
    pass


class SamplingError(LearningError):
    """Raised when active learning sampling fails due to invalid pool or metric NaN."""
    pass


class AdversarialAttackError(LearningError):
    """Raised when an adversarial attack generation fails."""
    pass


class CausalDiscoveryError(LearningError):
    """Raised when causal DAG discovery or effect estimation fails."""
    pass


class ContinualLearningError(LearningError):
    """Raised during task transitions, replay memory, or regularization."""
    pass


class EnsembleError(LearningError):
    """Raised during ensemble model aggregation, voting, or stacking."""
    pass


class EvolutionaryError(LearningError):
    """Raised during genetic selection, mutation, or population evaluation."""
    pass


class FederatedLearningError(LearningError):
    """Raised during federated aggregation, client training, or communication."""
    pass


class HyperparameterOptimizationError(LearningError):
    """Raised during hyperparameter search, trial pruning, or sampling."""
    pass


class MetaLearningError(LearningError):
    """Raised during inner-loop adaptation or meta-gradient computation."""
    pass


class MultiTaskLearningError(LearningError):
    """Raised during multi-task loss balancing, gradient surgery, or head routing."""
    pass


class NASError(LearningError):
    """Raised during neural architecture search, evaluation, or generation."""
    pass


class ReinforcementLearningError(LearningError):
    """Raised during policy updates, environment interactions, or replay storage."""
    pass


class SelfSupervisedError(LearningError):
    """Raised during pretext task computation, contrastive pairing, or representation learning."""
    pass


class TransferLearningError(LearningError):
    """Raised during domain adaptation, feature extraction, or fine-tuning."""
    pass


class PipelineExecutionError(LearningError):
    """Raised when a multi-stage learning pipeline encounters a fatal execution error."""
    pass


# Convenience Aliases
ArchitectureSearchError = NASError
FederatedAggregationError = FederatedLearningError
PipelineError = PipelineExecutionError


__all__ = [
    'LearningBaseException',
    'LearningError',
    'LearnerNotFoundError',
    'LearnerInitializationError',
    'LearnerConfigurationError',
    'OptimizationFailedError',
    'ConvergenceError',
    'StrategyNotSupportedError',
    'SamplingError',
    'AdversarialAttackError',
    'CausalDiscoveryError',
    'ContinualLearningError',
    'EnsembleError',
    'EvolutionaryError',
    'FederatedLearningError',
    'FederatedAggregationError',
    'HyperparameterOptimizationError',
    'MetaLearningError',
    'MultiTaskLearningError',
    'NASError',
    'ArchitectureSearchError',
    'ReinforcementLearningError',
    'SelfSupervisedError',
    'TransferLearningError',
    'PipelineExecutionError',
    'PipelineError',
]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.learning."):
        sys.modules["learning." + __name__[len("optimization_core.learning."):]] = _mod
    elif __name__.startswith("learning."):
        sys.modules["optimization_core.learning." + __name__[len("learning."):]] = _mod

