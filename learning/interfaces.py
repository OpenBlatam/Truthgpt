"""
Interfaces and Abstract Base Classes for Learning Subsystem
============================================================
Defines core abstract contracts and protocols for all 16 learning strategies,
optimizers, samplers, callbacks, adapters, and fluent pipelines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
import torch
import torch.nn as nn
import numpy as np


# =====================================================================
# 1. Base Contracts
# =====================================================================

class BaseLearner(ABC):
    """
    Abstract Base Class for all learning algorithms and models.
    
    Provides standardized lifecycle methods for training/fitting,
    evaluating, predicting, state serialization, and metric reporting.
    """

    @abstractmethod
    def fit(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Fit or train the learning system on the provided data or environment.
        
        Returns:
            Dict[str, Any]: Training execution summary and metrics.
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, *args: Any, **kwargs: Any) -> Dict[str, float]:
        """
        Evaluate the current model or learning state on validation/test data.
        
        Returns:
            Dict[str, float]: Computed evaluation metrics.
        """
        raise NotImplementedError

    def predict(self, *args: Any, **kwargs: Any) -> Any:
        """
        Generate predictions using the trained model or policy.
        
        Returns:
            Any: Predicted outputs or actions.
        """
        raise NotImplementedError("Predict method is not implemented for this learner.")

    def get_metrics(self) -> Dict[str, Any]:
        """Retrieve accumulated training and operational metrics."""
        return {}

    def reset(self) -> None:
        """Reset the internal state, history, and buffers of the learner."""
        pass

    def state_dict(self) -> Dict[str, Any]:
        """Serialize learner state for checkpointing."""
        return {}

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore learner state from a checkpoint."""
        pass

    def save_state(self, path: str) -> None:
        """Serialize learner state to disk."""
        pass

    def load_state(self, path: str) -> None:
        """Restore learner state from disk."""
        pass


class BaseLearningOptimizer(ABC):
    """Abstract base class for search and optimization algorithms (HPO, NAS, Evolutionary, Bayesian)."""

    @abstractmethod
    def optimize(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the optimization loop and return optimal configuration or parameters."""
        raise NotImplementedError

    @abstractmethod
    def step(self, *args: Any, **kwargs: Any) -> Any:
        """Execute a single optimization step."""
        raise NotImplementedError

    @abstractmethod
    def get_best(self) -> Any:
        """Retrieve the best discovered solution and metric score."""
        raise NotImplementedError


class BaseSampler(ABC):
    """Abstract base class for data sampling and query selection."""

    @abstractmethod
    def sample(self, pool: Any, n_samples: int, **kwargs: Any) -> List[int]:
        """Select n_samples from the candidate pool."""
        raise NotImplementedError


# =====================================================================
# 2. Modality-Specific Strategy ABCs
# =====================================================================

class BaseActiveLearner(BaseLearner):
    """Abstract contract for Active Learning systems."""

    @abstractmethod
    def query_samples(self, unlabeled_pool: Any, n_samples: int = 10, **kwargs: Any) -> List[int]:
        """Query most informative samples from unlabeled data."""
        raise NotImplementedError

    @abstractmethod
    def update_model(self, new_labeled_data: Any, **kwargs: Any) -> Dict[str, float]:
        """Incorporate newly labeled samples into model state."""
        raise NotImplementedError

    @abstractmethod
    def get_uncertainty(self, data: Any) -> Any:
        """Compute uncertainty scores over data points."""
        raise NotImplementedError


class BaseAdaptiveLearner(BaseLearner):
    """Abstract contract for Adaptive and Concept Drift aware learning."""

    @abstractmethod
    def adapt(self, new_data: Any, **kwargs: Any) -> Any:
        """Adapt model parameters or representation to distribution shifts."""
        raise NotImplementedError

    @abstractmethod
    def detect_drift(self, incoming_stream: Any) -> bool:
        """Detect concept or covariate drift in data stream."""
        raise NotImplementedError


class BaseAdversarialLearner(BaseLearner):
    """Abstract contract for Adversarial Robustness and attacks/defenses."""

    @abstractmethod
    def generate_adversarial_examples(self, model: Any, inputs: Any, targets: Any, **kwargs: Any) -> Any:
        """Generate adversarial perturbations."""
        raise NotImplementedError

    @abstractmethod
    def train_robust(self, *args: Any, **kwargs: Any) -> Any:
        """Perform adversarial or robust training."""
        raise NotImplementedError

    @abstractmethod
    def evaluate_robustness(self, model: Any, test_loader: Any, **kwargs: Any) -> Dict[str, float]:
        """Assess model vulnerability against attacks."""
        raise NotImplementedError


class BaseBayesianOptimizer(BaseLearningOptimizer):
    """Abstract contract for Bayesian Optimization with Gaussian Processes / surrogates."""

    @abstractmethod
    def suggest(self) -> Dict[str, Any]:
        """Suggest next candidate hyperparameter configuration to evaluate."""
        raise NotImplementedError

    @abstractmethod
    def register_observation(self, params: Dict[str, Any], target_value: float) -> None:
        """Record evaluation outcome for suggested parameters."""
        raise NotImplementedError


class BaseCausalInference(ABC):
    """Abstract contract for Causal Inference and Effect Estimation."""

    @abstractmethod
    def estimate_ate(self, treatment: str, outcome: str, data: Any, **kwargs: Any) -> Any:
        """Estimate Average Treatment Effect (ATE)."""
        raise NotImplementedError

    @abstractmethod
    def discover_graph(self, data: Any, **kwargs: Any) -> Any:
        """Discover causal DAG topology from observational data."""
        raise NotImplementedError

    @abstractmethod
    def refute_estimate(self, estimate: Any, method: str = "random_common_cause", **kwargs: Any) -> Any:
        """Refute estimated causal effect using sensitivity tests."""
        raise NotImplementedError


class BaseContinualLearner(BaseLearner):
    """Abstract contract for Lifelong / Continual Learning."""

    @abstractmethod
    def learn_task(self, task_id: int, task_data: Any, **kwargs: Any) -> Any:
        """Train model on a new discrete task while mitigating catastrophic forgetting."""
        raise NotImplementedError

    @abstractmethod
    def evaluate_all_tasks(self, test_tasks: Dict[int, Any]) -> Dict[int, Dict[str, float]]:
        """Evaluate retention and performance across all previous tasks."""
        raise NotImplementedError


class BaseEnsembleLearner(BaseLearner):
    """Abstract contract for Ensemble strategies (Voting, Stacking, Boosting)."""

    @abstractmethod
    def add_learner(self, learner: Any, weight: float = 1.0) -> None:
        """Add a base estimator into the ensemble."""
        raise NotImplementedError

    @abstractmethod
    def predict_ensemble(self, inputs: Any, **kwargs: Any) -> Any:
        """Aggregate predictions across all base learners."""
        raise NotImplementedError


class BaseEvolutionaryOptimizer(BaseLearningOptimizer):
    """Abstract contract for Evolutionary Algorithms (GA, ES, CMA-ES)."""

    @abstractmethod
    def initialize_population(self, population_size: int) -> Any:
        """Initialize candidate population."""
        raise NotImplementedError

    @abstractmethod
    def evolve(self, generations: int = 10, **kwargs: Any) -> Any:
        """Run evolutionary generations."""
        raise NotImplementedError


class BaseFederatedLearner(ABC):
    """Abstract contract for Federated Learning coordination and client training."""

    @abstractmethod
    def broadcast_model(self) -> Any:
        """Broadcast global parameters to clients."""
        raise NotImplementedError

    @abstractmethod
    def aggregate_updates(self, client_updates: List[Any], **kwargs: Any) -> Any:
        """Aggregate client parameter updates into global model."""
        raise NotImplementedError

    @abstractmethod
    def train_round(self, round_num: int) -> Dict[str, Any]:
        """Execute a full federated round."""
        raise NotImplementedError


class BaseHyperparameterOptimizer(BaseLearningOptimizer):
    """Abstract contract for Hyperparameter Search algorithms."""

    @abstractmethod
    def search(self, objective_func: Any, n_trials: int = 50, **kwargs: Any) -> Any:
        """Run hyperparameter search space exploration."""
        raise NotImplementedError

    @abstractmethod
    def get_best_config(self) -> Dict[str, Any]:
        """Retrieve optimal discovered hyperparameters."""
        raise NotImplementedError


class BaseMetaLearner(BaseLearner):
    """Abstract contract for Meta-Learning (MAML, Reptile, Meta-SGD)."""

    @abstractmethod
    def meta_train(self, task_distribution: Any, meta_epochs: int = 100, **kwargs: Any) -> Any:
        """Optimize meta-parameters across task distributions."""
        raise NotImplementedError

    @abstractmethod
    def adapt_to_task(self, task_support: Any, inner_steps: int = 5, **kwargs: Any) -> Any:
        """Perform rapid inner-loop adaptation on task support set."""
        raise NotImplementedError


class BaseMultitaskLearner(BaseLearner):
    """Abstract contract for Multi-Task Learning."""

    @abstractmethod
    def compute_multitask_loss(self, task_losses: Dict[str, torch.Tensor], **kwargs: Any) -> torch.Tensor:
        """Combine and balance losses across concurrent tasks."""
        raise NotImplementedError

    @abstractmethod
    def train_multitask_step(self, batch_data: Dict[str, Any]) -> Dict[str, float]:
        """Execute single gradient step across multiple task heads."""
        raise NotImplementedError


class BaseNASOptimizer(BaseLearningOptimizer):
    """Abstract contract for Neural Architecture Search."""

    @abstractmethod
    def search_architecture(self, search_space: Any, dataset: Any, **kwargs: Any) -> Any:
        """Search for optimal neural network topology."""
        raise NotImplementedError

    @abstractmethod
    def evaluate_candidate(self, candidate_arch: Any, **kwargs: Any) -> float:
        """Score candidate architecture."""
        raise NotImplementedError


class BaseReinforcementLearner(BaseLearner):
    """Abstract contract for Reinforcement Learning (DQN, PPO, SAC)."""

    @abstractmethod
    def select_action(self, state: Any, explore: bool = True) -> Any:
        """Select action given environment state."""
        raise NotImplementedError

    @abstractmethod
    def update_policy(self, transitions: Any) -> Dict[str, float]:
        """Update policy / value functions using collected experience."""
        raise NotImplementedError


class BaseSelfSupervisedLearner(BaseLearner):
    """Abstract contract for Self-Supervised Learning and Pretraining."""

    @abstractmethod
    def pretrain_step(self, batch: Any) -> Dict[str, float]:
        """Execute single self-supervised pre-training step."""
        raise NotImplementedError

    @abstractmethod
    def extract_representations(self, data: Any) -> torch.Tensor:
        """Extract learned representations / embeddings."""
        raise NotImplementedError


class BaseTransferLearner(BaseLearner):
    """Abstract contract for Transfer Learning and Distillation."""

    @abstractmethod
    def transfer(self, target_model: Any, source_model: Any, **kwargs: Any) -> Any:
        """Transfer weights or representations between models."""
        raise NotImplementedError

    @abstractmethod
    def fine_tune(self, data_loader: Any, epochs: int = 5, **kwargs: Any) -> Dict[str, float]:
        """Fine-tune adapted model on downstream dataset."""
        raise NotImplementedError


# =====================================================================
# 3. Pipelines, Callbacks, and Auxiliaries
# =====================================================================

class BaseLearningPipeline(ABC):
    """Abstract contract for Fluent Multi-Stage Learning Pipelines."""

    @abstractmethod
    def add_stage(self, stage_name: str, module: Any, config: Optional[Dict[str, Any]] = None) -> BaseLearningPipeline:
        """Append a learning stage to the pipeline."""
        raise NotImplementedError

    @abstractmethod
    def execute(self, initial_data: Any = None, **kwargs: Any) -> Dict[str, Any]:
        """Execute all stages sequentially and return consolidated results."""
        raise NotImplementedError


class BaseCallback(ABC):
    """Abstract Base Class for lifecycle events during learning execution."""

    def on_learning_begin(self, learner: Any, state: Dict[str, Any]) -> None:
        """Triggered before learning/training begins."""
        pass

    def on_step_begin(self, learner: Any, step: int, state: Dict[str, Any]) -> None:
        """Triggered at the beginning of each iteration or step."""
        pass

    def on_step_end(self, learner: Any, step: int, metrics: Dict[str, Any]) -> None:
        """Triggered at the end of each iteration or step."""
        pass

    def on_evaluate(self, learner: Any, metrics: Dict[str, float]) -> None:
        """Triggered during evaluation phases."""
        pass

    def on_learning_end(self, learner: Any, state: Dict[str, Any]) -> None:
        """Triggered upon successful completion of learning."""
        pass

    def on_error(self, learner: Any, error: Exception, state: Dict[str, Any]) -> None:
        """Triggered when an unhandled exception occurs during learning."""
        pass


class BaseQuerySampler(BaseSampler):
    """Abstract Base Class for active learning query and uncertainty samplers."""

    @abstractmethod
    def sample(
        self,
        model: nn.Module,
        unlabeled_data: Union[np.ndarray, torch.Tensor, List[Any]],
        n_samples: int,
        *args: Any,
        **kwargs: Any
    ) -> Union[np.ndarray, torch.Tensor, List[int]]:
        """Sample informative or diverse data points for querying."""
        raise NotImplementedError


class BaseDefense(ABC):
    """Abstract Base Class for adversarial defenses and robustness hardening."""

    @abstractmethod
    def defend(
        self,
        model: nn.Module,
        inputs: torch.Tensor,
        targets: Optional[torch.Tensor] = None,
        *args: Any,
        **kwargs: Any
    ) -> torch.Tensor:
        """Apply defense transformations or purification to inputs."""
        raise NotImplementedError


class BaseDomainAdapter(ABC):
    """Abstract Base Class for transfer learning domain adaptation."""

    @abstractmethod
    def adapt(
        self,
        source_data: Any,
        target_data: Any,
        model: nn.Module,
        *args: Any,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Perform domain alignment and transfer adaptation."""
        raise NotImplementedError


class BaseAggregationStrategy(ABC):
    """Abstract Base Class for federated learning weight aggregation algorithms."""

    @abstractmethod
    def aggregate(
        self,
        client_updates: List[Dict[str, torch.Tensor]],
        client_weights: Optional[List[float]] = None,
        *args: Any,
        **kwargs: Any
    ) -> Dict[str, torch.Tensor]:
        """Aggregate model updates from distributed clients."""
        raise NotImplementedError


__all__ = [
    'BaseLearner',
    'BaseLearningOptimizer',
    'BaseSampler',
    'BaseActiveLearner',
    'BaseAdaptiveLearner',
    'BaseAdversarialLearner',
    'BaseBayesianOptimizer',
    'BaseCausalInference',
    'BaseContinualLearner',
    'BaseEnsembleLearner',
    'BaseEvolutionaryOptimizer',
    'BaseFederatedLearner',
    'BaseHyperparameterOptimizer',
    'BaseMetaLearner',
    'BaseMultitaskLearner',
    'BaseNASOptimizer',
    'BaseReinforcementLearner',
    'BaseSelfSupervisedLearner',
    'BaseTransferLearner',
    'BaseLearningPipeline',
    'BaseCallback',
    'BaseQuerySampler',
    'BaseDefense',
    'BaseDomainAdapter',
    'BaseAggregationStrategy',
]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.learning."):
        sys.modules["learning." + __name__[len("optimization_core.learning."):]] = _mod
    elif __name__.startswith("learning."):
        sys.modules["optimization_core.learning." + __name__[len("learning."):]] = _mod

