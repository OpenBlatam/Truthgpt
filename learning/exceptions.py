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


LearningConfigError = LearnerConfigurationError


class OptimizationFailedError(LearningBaseException):
    """Raised when an optimization process fails to find a viable solution."""
    pass


class ConvergenceError(LearningBaseException):
    """Raised when an algorithm fails to converge within the allotted step/epoch budget."""
    pass


class StrategyNotSupportedError(LearningError):
    """Raised when an unsupported algorithm or combination of strategies is specified."""
    pass


class SamplingError(LearningError):
    """Raised when active learning sampling fails due to invalid pool or metric NaN."""
    pass


# Domain Specific Exceptions & Aliases
class ActiveLearningError(LearningError):
    """Raised during active learning sampling or cycle execution."""
    pass


class AdaptiveLearningError(LearningError):
    """Raised during adaptive drift detection or online adjustment."""
    pass


class AdversarialAttackError(LearningError):
    """Raised when an adversarial attack generation fails."""
    pass


class AdversarialDefenseError(LearningError):
    """Raised when an adversarial defense or certified radius calculation fails."""
    pass


class AdversarialError(LearningError):
    """General adversarial learning error."""
    pass


class BayesianOptimizationError(LearningError):
    """Raised during Bayesian optimization acquisition or surrogate fitting."""
    pass


class BayesianError(LearningError):
    """General Bayesian error."""
    pass


class CausalInferenceError(LearningError):
    """Raised during causal treatment effect estimation or refutation."""
    pass


class CausalDiscoveryError(LearningError):
    """Raised when causal DAG discovery fails."""
    pass


class ContinualLearningError(LearningError):
    """Raised during continual learning task adaptation or EWC regularization."""
    pass


class ContinualError(LearningError):
    """General continual learning error."""
    pass


class EnsembleLearningError(LearningError):
    """Raised during ensemble weighting, bagging, or voting aggregation."""
    pass


class EnsembleError(LearningError):
    """General ensemble error."""
    pass


class EvolutionaryOptimizationError(LearningError):
    """Raised during evolutionary genetic selection or crossover."""
    pass


class EvolutionaryError(LearningError):
    """General evolutionary error."""
    pass


class FederatedLearningError(LearningError):
    """Raised during federated round execution or client synchronization."""
    pass


class FederatedAggregationError(LearningError):
    """Raised when federated parameter aggregation or secure weight averaging fails."""
    pass


class HyperparameterOptimizationError(LearningError):
    """Raised during hyperparameter trial search or pruning."""
    pass


class HPOError(LearningError):
    """General HPO error."""
    pass


class MetaLearningError(LearningError):
    """Raised during meta-parameter adaptation or inner-loop task updates."""
    pass


class MultitaskLearningError(LearningError):
    """Raised during multi-task loss balancing or gradient surgery."""
    pass


class MultiTaskError(LearningError):
    """General multi-task learning error."""
    pass


MultiTaskLearningError = MultitaskLearningError


class ArchitectureSearchError(LearningError):
    """Raised when neural architecture generation or evaluation fails."""
    pass


class NASError(LearningError):
    """General neural architecture search error."""
    pass


class ReinforcementLearningError(LearningError):
    """Raised during RL policy updates, action selection, or trajectory collection."""
    pass


class RLError(LearningError):
    """General RL error."""
    pass


class SelfSupervisedLearningError(LearningError):
    """Raised during self-supervised contrastive pretraining."""
    pass


class SSLError(LearningError):
    """General self-supervised error."""
    pass


SelfSupervisedError = SelfSupervisedLearningError


class TransferLearningError(LearningError):
    """Raised during transfer fine-tuning, domain adaptation, or distillation."""
    pass


class PipelineError(LearningError):
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
    'LearningConfigError',
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
    'LearningConfigError',
]

from ._compat import register_dual_namespace as _register_ns
_register_ns(module_name=__name__)
