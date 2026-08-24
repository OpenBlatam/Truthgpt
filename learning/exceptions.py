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

    def __init__(self, message: str = "", details: Optional[Dict[str, Any]] = None) -> None:
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


class SamplingError(LearningBaseException):
    """Raised when active learning sampling fails due to invalid pool or metric NaN."""
    pass


# Domain Specific Exceptions & Aliases
class ActiveLearningError(LearningBaseException):
    """Raised during active learning sampling or cycle execution."""
    pass


class AdaptiveLearningError(LearningBaseException):
    """Raised during adaptive drift detection or online adjustment."""
    pass


class AdversarialAttackError(LearningBaseException):
    """Raised when an adversarial attack generation fails."""
    pass


class AdversarialDefenseError(LearningBaseException):
    """Raised when an adversarial defense or certified radius calculation fails."""
    pass


class AdversarialError(LearningBaseException):
    """General adversarial learning error."""
    pass


class BayesianOptimizationError(LearningBaseException):
    """Raised during Bayesian optimization acquisition or surrogate fitting."""
    pass


class BayesianError(LearningBaseException):
    """General Bayesian error."""
    pass


class CausalInferenceError(LearningBaseException):
    """Raised during causal treatment effect estimation or refutation."""
    pass


class CausalDiscoveryError(LearningBaseException):
    """Raised when causal DAG discovery fails."""
    pass


class ContinualLearningError(LearningBaseException):
    """Raised during continual learning task adaptation or EWC regularization."""
    pass


class ContinualError(LearningBaseException):
    """General continual learning error."""
    pass


class EnsembleLearningError(LearningBaseException):
    """Raised during ensemble weighting, bagging, or voting aggregation."""
    pass


class EnsembleError(LearningBaseException):
    """General ensemble error."""
    pass


class EvolutionaryOptimizationError(LearningBaseException):
    """Raised during evolutionary genetic selection or crossover."""
    pass


class EvolutionaryError(LearningBaseException):
    """General evolutionary error."""
    pass


class FederatedLearningError(LearningBaseException):
    """Raised during federated round execution or client synchronization."""
    pass


class FederatedAggregationError(LearningBaseException):
    """Raised when federated parameter aggregation or secure weight averaging fails."""
    pass


class HyperparameterOptimizationError(LearningBaseException):
    """Raised during hyperparameter trial search or pruning."""
    pass


class HPOError(LearningBaseException):
    """General HPO error."""
    pass


class MetaLearningError(LearningBaseException):
    """Raised during meta-parameter adaptation or inner-loop task updates."""
    pass


class MultitaskLearningError(LearningBaseException):
    """Raised during multi-task loss balancing or gradient surgery."""
    pass


class MultiTaskError(LearningBaseException):
    """General multi-task learning error."""
    pass


MultiTaskLearningError = MultitaskLearningError


class ArchitectureSearchError(LearningBaseException):
    """Raised when neural architecture generation or evaluation fails."""
    pass


class NASError(LearningBaseException):
    """General neural architecture search error."""
    pass


class ReinforcementLearningError(LearningBaseException):
    """Raised during RL policy updates, action selection, or trajectory collection."""
    pass


class RLError(LearningBaseException):
    """General RL error."""
    pass


class SelfSupervisedLearningError(LearningBaseException):
    """Raised during self-supervised contrastive pretraining."""
    pass


class SSLError(LearningBaseException):
    """General self-supervised error."""
    pass


SelfSupervisedError = SelfSupervisedLearningError


class TransferLearningError(LearningBaseException):
    """Raised during transfer fine-tuning, domain adaptation, or distillation."""
    pass


class PipelineError(LearningBaseException):
    """Raised when execution of a multi-stage learning pipeline encounters an error."""
    pass


class PipelineExecutionError(PipelineError):
    """Raised when a specific pipeline stage execution fails."""
    pass


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
    'ActiveLearningError',
    'AdaptiveLearningError',
    'AdversarialAttackError',
    'AdversarialDefenseError',
    'AdversarialError',
    'BayesianOptimizationError',
    'BayesianError',
    'CausalInferenceError',
    'CausalDiscoveryError',
    'ContinualLearningError',
    'ContinualError',
    'EnsembleLearningError',
    'EnsembleError',
    'EvolutionaryOptimizationError',
    'EvolutionaryError',
    'FederatedLearningError',
    'FederatedAggregationError',
    'HyperparameterOptimizationError',
    'HPOError',
    'MetaLearningError',
    'MultitaskLearningError',
    'MultiTaskLearningError',
    'MultiTaskError',
    'ArchitectureSearchError',
    'NASError',
    'ReinforcementLearningError',
    'RLError',
    'SelfSupervisedLearningError',
    'SelfSupervisedError',
    'SSLError',
    'TransferLearningError',
    'PipelineError',
    'PipelineExecutionError',
]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.learning."):
        sys.modules["learning." + __name__[len("optimization_core.learning."):]] = _mod
    elif __name__.startswith("learning."):
        sys.modules["optimization_core.learning." + __name__[len("learning."):]] = _mod

