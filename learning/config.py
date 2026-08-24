"""
Configuration Dataclasses for Learning Subsystem
================================================
Defines composable, validated, serializable configuration dataclasses
for all 16 learning strategies, pipelines, and unified optimization.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from .exceptions import LearnerConfigurationError
from .types import (
    AcquisitionFunction,
    AcquisitionFunctionType,
    ActiveLearningStrategy,
    AdaptiveLearningStrategy,
    AdaptiveMode,
    AdversarialAttackType,
    AggregationMethod,
    AggregationMethodType,
    AttackType,
    CLStrategy,
    ContinualMethodType,
    DefenseStrategy,
    DefenseType,
    DomainAdaptationMethod,
    EnsembleMethodType,
    EnsembleStrategy,
    FederatedAggregationMethod,
    HpoAlgorithm,
    HPOSearchStrategyType,
    KernelType,
    KnowledgeDistillationType,
    LearningMode,
    LearningStrategyType,
    MetaAlgorithmType,
    MetaLearningAlgorithm,
    MultitaskLossBalancingType,
    NASStrategyType,
    PretextTaskType,
    QueryStrategy,
    QueryStrategyType,
    RLAlgorithm,
    RLAlgorithmType,
    SearchStrategy,
    SharingStrategy,
    SSLMethod,
    SSLPretextTaskType,
    TransferMethodType,
    TransferStrategy,
    UncertaintyMeasure,
    UncertaintyMeasureType,
)


# =====================================================================
# Base Config Mixin
# =====================================================================

class BaseConfigMixin:
    """Base mixin providing serialization, validation, and dict conversion."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration dataclass into a JSON-serializable dictionary."""
        def _convert(val: Any) -> Any:
            if hasattr(val, "value"):
                return val.value
            if isinstance(val, dict):
                return {k: _convert(v) for k, v in val.items()}
            if isinstance(val, (list, tuple)):
                return [_convert(v) for v in val]
            return val

        raw = asdict(self)  # type: ignore[call-overload]
        return {k: _convert(v) for k, v in raw.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Any:
        """Create configuration instance from dictionary, ignoring extraneous fields."""
        if not isinstance(data, dict):
            raise LearnerConfigurationError(f"Expected dict for config, got {type(data)}")
        valid_fields = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

    def validate(self) -> None:
        """Validate parameter ranges and logical consistency."""
        pass


# =====================================================================
# Strategy Configurations
# =====================================================================

@dataclass
class ActiveLearningConfig(BaseConfigMixin):
    """Configuration for Active Learning strategies."""
    strategy: QueryStrategy = QueryStrategy.UNCERTAINTY_BASED
    uncertainty_measure: UncertaintyMeasure = UncertaintyMeasure.ENTROPY
    n_initial_samples: int = 100
    n_query_samples: int = 10
    n_total_budget: int = 1000
    max_iterations: int = 50
    uncertainty_threshold: float = 0.5
    diversity_weight: float = 0.5
    n_clusters: int = 10
    n_committee_members: int = 5
    batch_size: int = 20
    enable_adaptive_sampling: bool = True
    enable_cost_sensitive: bool = False

    def validate(self) -> None:
        if self.n_query_samples <= 0:
            raise LearnerConfigurationError("n_query_samples must be positive")
        if self.n_initial_samples < 0:
            raise LearnerConfigurationError("n_initial_samples cannot be negative")
        if not (0.0 <= self.diversity_weight <= 1.0):
            raise LearnerConfigurationError("diversity_weight must be in [0.0, 1.0]")


@dataclass
class AdaptiveLearningConfig(BaseConfigMixin):
    """Configuration for Concept Drift and Self-Improving systems."""
    learning_rate: float = 0.001
    adaptation_rate: float = 0.01
    exploration_rate: float = 0.1
    exploitation_rate: float = 0.9
    mode: LearningMode = LearningMode.SELF_IMPROVING
    drift_detection_threshold: float = 0.05
    drift_window_size: int = 200
    enable_meta_learning: bool = True
    meta_batch_size: int = 32
    enable_self_improvement: bool = True
    improvement_threshold: float = 0.05
    improvement_patience: int = 10
    memory_capacity: int = 1000

    def validate(self) -> None:
        if self.learning_rate <= 0.0:
            raise LearnerConfigurationError("learning_rate must be positive")
        if self.drift_window_size < 10:
            raise LearnerConfigurationError("drift_window_size must be >= 10")


@dataclass
class AdversarialConfig(BaseConfigMixin):
    """Configuration for Adversarial attacks, defense, and robust training."""
    attack_type: AdversarialAttackType = AdversarialAttackType.PGD
    defense_type: DefenseStrategy = DefenseStrategy.ADVERSARIAL_TRAINING
    epsilon: float = 0.0314  # 8/255
    alpha: float = 0.0078    # 2/255
    num_steps: int = 10
    random_start: bool = True
    target_metric: str = "robust_accuracy"
    trades_beta: float = 6.0
    smoothing_sigma: float = 0.25

    def validate(self) -> None:
        if self.epsilon <= 0.0:
            raise LearnerConfigurationError("epsilon must be positive")
        if self.num_steps <= 0:
            raise LearnerConfigurationError("num_steps must be >= 1")


@dataclass
class BayesianConfig(BaseConfigMixin):
    """Configuration for Bayesian Optimization with Gaussian Processes."""
    acquisition_function: AcquisitionFunction = AcquisitionFunction.EXPECTED_IMPROVEMENT
    kernel_type: KernelType = KernelType.RBF
    n_initial_points: int = 10
    n_iterations: int = 50
    exploration_weight: float = 2.576  # UCB kappa
    xi: float = 0.01                   # EI / PI trade-off
    noise_level: float = 1e-4
    random_seed: int = 42

    def validate(self) -> None:
        if self.n_initial_points <= 0:
            raise LearnerConfigurationError("n_initial_points must be >= 1")
        if self.n_iterations <= 0:
            raise LearnerConfigurationError("n_iterations must be >= 1")


@dataclass
class CausalConfig(BaseConfigMixin):
    """Configuration for Causal Discovery and Effect Estimation."""
    alpha: float = 0.05
    estimator_method: str = "backdoor.linear_regression"
    discovery_algorithm: str = "pc"  # PC, GES, NOTEARS
    max_conditioning_set_size: int = 3
    num_bootstrap_refutations: int = 50
    placebo_test_fraction: float = 0.5
    confidence_level: float = 0.95

    def validate(self) -> None:
        if not (0.0 < self.alpha < 1.0):
            raise LearnerConfigurationError("alpha must be in (0, 1)")
        if self.num_bootstrap_refutations < 1:
            raise LearnerConfigurationError("num_bootstrap_refutations must be >= 1")


@dataclass
class ContinualConfig(BaseConfigMixin):
    """Configuration for Lifelong and Continual Learning."""
    method: CLStrategy = CLStrategy.EWC
    ewc_lambda: float = 400.0
    fisher_sample_size: int = 200
    replay_buffer_size: int = 1000
    replay_batch_size: int = 32
    temperature_distillation: float = 2.0
    si_c: float = 0.1

    def validate(self) -> None:
        if self.ewc_lambda < 0.0:
            raise LearnerConfigurationError("ewc_lambda cannot be negative")
        if self.replay_buffer_size <= 0:
            raise LearnerConfigurationError("replay_buffer_size must be positive")


@dataclass
class EnsembleConfig(BaseConfigMixin):
    """Configuration for Ensemble Learning (Voting, Stacking, Boosting)."""
    method: EnsembleStrategy = EnsembleStrategy.VOTING
    n_estimators: int = 5
    voting_strategy: str = "soft"  # soft, hard, weighted
    weights: Optional[List[float]] = None
    stacking_meta_learner: str = "ridge"
    bagging_sample_fraction: float = 0.8
    boosting_learning_rate: float = 0.1

    def validate(self) -> None:
        if self.n_estimators <= 0:
            raise LearnerConfigurationError("n_estimators must be positive")
        if not (0.0 < self.bagging_sample_fraction <= 1.0):
            raise LearnerConfigurationError("bagging_sample_fraction must be in (0, 1]")


@dataclass
class EvolutionaryConfig(BaseConfigMixin):
    """Configuration for Evolutionary Algorithms and CMA-ES."""
    population_size: int = 50
    generations: int = 100
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    elitism_count: int = 2
    selection_strategy: str = "tournament"
    tournament_size: int = 3
    mutation_sigma: float = 0.1

    def validate(self) -> None:
        if self.population_size <= 0:
            raise LearnerConfigurationError("population_size must be >= 1")
        if not (0.0 <= self.mutation_rate <= 1.0):
            raise LearnerConfigurationError("mutation_rate must be in [0, 1]")


@dataclass
class FederatedConfig(BaseConfigMixin):
    """Configuration for Federated Learning and secure aggregation."""
    aggregation_method: AggregationMethod = AggregationMethod.FEDAVG
    num_rounds: int = 50
    num_clients: int = 10
    clients_per_round: int = 5
    client_local_epochs: int = 3
    client_lr: float = 0.01
    fedprox_mu: float = 0.01
    clip_threshold: float = 10.0

    def validate(self) -> None:
        if self.num_clients < self.clients_per_round:
            raise LearnerConfigurationError("num_clients must be >= clients_per_round")
        if self.num_rounds <= 0:
            raise LearnerConfigurationError("num_rounds must be >= 1")


@dataclass
class HPOConfig(BaseConfigMixin):
    """Configuration for Hyperparameter Optimization."""
    strategy: HpoAlgorithm = HpoAlgorithm.TPE
    n_trials: int = 50
    timeout_seconds: Optional[float] = None
    pruning_enabled: bool = True
    min_resource: int = 1
    max_resource: int = 27
    reduction_factor: int = 3

    def validate(self) -> None:
        if self.n_trials <= 0:
            raise LearnerConfigurationError("n_trials must be >= 1")


@dataclass
class MetaConfig(BaseConfigMixin):
    """Configuration for Meta-Learning (MAML, Reptile)."""
    algorithm: MetaLearningAlgorithm = MetaLearningAlgorithm.MAML
    inner_lr: float = 0.01
    meta_lr: float = 0.001
    inner_steps: int = 5
    tasks_per_batch: int = 4
    meta_epochs: int = 100
    first_order: bool = False

    def validate(self) -> None:
        if self.inner_steps < 1:
            raise LearnerConfigurationError("inner_steps must be >= 1")
        if self.inner_lr <= 0.0 or self.meta_lr <= 0.0:
            raise LearnerConfigurationError("Learning rates must be positive")


@dataclass
class MultitaskConfig(BaseConfigMixin):
    """Configuration for Multi-Task Learning and loss balancing."""
    loss_balancing: SharingStrategy = SharingStrategy.HARD_SHARING
    task_weights: Dict[str, float] = field(default_factory=dict)
    gradnorm_alpha: float = 1.5
    temperature: float = 2.0
    shared_backbone_frozen: bool = False

    def validate(self) -> None:
        if self.gradnorm_alpha <= 0.0:
            raise LearnerConfigurationError("gradnorm_alpha must be positive")


@dataclass
class NASConfig(BaseConfigMixin):
    """Configuration for Neural Architecture Search."""
    strategy: SearchStrategy = SearchStrategy.EVOLUTIONARY
    search_epochs: int = 50
    arch_learning_rate: float = 3e-4
    arch_weight_decay: float = 1e-3
    n_candidate_blocks: int = 8
    max_macs_budget: Optional[float] = None

    def validate(self) -> None:
        if self.search_epochs < 1:
            raise LearnerConfigurationError("search_epochs must be >= 1")


@dataclass
class RLConfig(BaseConfigMixin):
    """Configuration for Reinforcement Learning agents."""
    algorithm: RLAlgorithm = RLAlgorithm.PPO
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_epsilon: float = 0.2
    actor_lr: float = 3e-4
    critic_lr: float = 1e-3
    buffer_size: int = 10000
    batch_size: int = 64
    target_update_tau: float = 0.005

    def validate(self) -> None:
        if not (0.0 < self.gamma <= 1.0):
            raise LearnerConfigurationError("gamma must be in (0, 1]")
        if self.batch_size <= 0:
            raise LearnerConfigurationError("batch_size must be positive")


@dataclass
class SelfSupervisedConfig(BaseConfigMixin):
    """Configuration for Self-Supervised Pretraining."""
    pretext_task: PretextTaskType = PretextTaskType.ROTATION
    temperature: float = 0.07
    projection_dim: int = 128
    hidden_dim: int = 512
    momentum_decay: float = 0.996
    mask_ratio: float = 0.15

    def validate(self) -> None:
        if self.temperature <= 0.0:
            raise LearnerConfigurationError("temperature must be positive")
        if not (0.0 < self.mask_ratio < 1.0):
            raise LearnerConfigurationError("mask_ratio must be in (0, 1)")


@dataclass
class TransferLearningConfig(BaseConfigMixin):
    """Configuration for Transfer Learning and Distillation."""
    method: TransferStrategy = TransferStrategy.FINE_TUNING
    head_learning_rate: float = 1e-3
    backbone_learning_rate: float = 1e-5
    gradual_unfreeze_epochs: int = 3
    distillation_temperature: float = 4.0
    distillation_alpha: float = 0.5

    def validate(self) -> None:
        if self.head_learning_rate <= 0.0:
            raise LearnerConfigurationError("head_learning_rate must be positive")
        if not (0.0 <= self.distillation_alpha <= 1.0):
            raise LearnerConfigurationError("distillation_alpha must be in [0, 1]")


@dataclass
class PipelineConfig(BaseConfigMixin):
    """Configuration for multi-stage learning pipelines."""
    pipeline_name: str = "truthgpt_learning_pipeline"
    stop_on_stage_failure: bool = True
    save_intermediate_checkpoints: bool = False
    checkpoint_dir: str = "./checkpoints/pipeline"
    timeout_seconds_per_stage: Optional[float] = None
    enable_telemetry: bool = True


# =====================================================================
# Master Composable Learning Configuration
# =====================================================================

@dataclass
class LearningConfig(BaseConfigMixin):
    """
    Master unified configuration containing sub-configurations for all
    learning strategies, with property delegation and dictionary validation.
    """
    strategy: LearningStrategyType = LearningStrategyType.ACTIVE
    active: ActiveLearningConfig = field(default_factory=ActiveLearningConfig)
    adaptive: AdaptiveLearningConfig = field(default_factory=AdaptiveLearningConfig)
    adversarial: AdversarialConfig = field(default_factory=AdversarialConfig)
    bayesian: BayesianConfig = field(default_factory=BayesianConfig)
    causal: CausalConfig = field(default_factory=CausalConfig)
    continual: ContinualConfig = field(default_factory=ContinualConfig)
    ensemble: EnsembleConfig = field(default_factory=EnsembleConfig)
    evolutionary: EvolutionaryConfig = field(default_factory=EvolutionaryConfig)
    federated: FederatedConfig = field(default_factory=FederatedConfig)
    hpo: HPOConfig = field(default_factory=HPOConfig)
    meta: MetaConfig = field(default_factory=MetaConfig)
    multitask: MultitaskConfig = field(default_factory=MultitaskConfig)
    nas: NASConfig = field(default_factory=NASConfig)
    reinforcement: RLConfig = field(default_factory=RLConfig)
    self_supervised: SelfSupervisedConfig = field(default_factory=SelfSupervisedConfig)
    transfer: TransferLearningConfig = field(default_factory=TransferLearningConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)

    # General metadata
    device: str = "cpu"
    seed: int = 42
    verbose: bool = False

    def validate(self) -> None:
        """Validate all sub-configurations."""
        self.active.validate()
        self.adaptive.validate()
        self.adversarial.validate()
        self.bayesian.validate()
        self.causal.validate()
        self.continual.validate()
        self.ensemble.validate()
        self.evolutionary.validate()
        self.federated.validate()
        self.hpo.validate()
        self.meta.validate()
        self.multitask.validate()
        self.nas.validate()
        self.reinforcement.validate()
        self.self_supervised.validate()
        self.transfer.validate()
        self.pipeline.validate()

    # Backward compatibility properties
    @property
    def learning_rate(self) -> float:
        return self.adaptive.learning_rate

    @learning_rate.setter
    def learning_rate(self, value: float) -> None:
        self.adaptive.learning_rate = value
        self.transfer.head_learning_rate = value


__all__ = [
    'BaseConfigMixin',
    'ActiveLearningConfig',
    'AdaptiveLearningConfig',
    'AdversarialConfig',
    'BayesianConfig',
    'CausalConfig',
    'ContinualConfig',
    'EnsembleConfig',
    'EvolutionaryConfig',
    'FederatedConfig',
    'HPOConfig',
    'MetaConfig',
    'MultitaskConfig',
    'NASConfig',
    'RLConfig',
    'SelfSupervisedConfig',
    'TransferLearningConfig',
    'PipelineConfig',
    'LearningConfig',
]
