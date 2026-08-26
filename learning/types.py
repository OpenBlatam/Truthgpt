"""
Unified Types, Data Structures, and Enums for the Learning Subsystem.
=====================================================================
Comprehensive dataclasses, configurations, telemetry, results, and
strategy enums covering all 16 learning domains and multi-stage pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
import time
import numpy as np


class LearningParadigm(str, Enum):
    """Supported learning paradigms in the subsystem."""
    ACTIVE = "active"
    ADAPTIVE = "adaptive"
    ADVERSARIAL = "adversarial"
    BAYESIAN = "bayesian"
    CAUSAL = "causal"
    CONTINUAL = "continual"
    ENSEMBLE = "ensemble"
    EVOLUTIONARY = "evolutionary"
    FEDERATED = "federated"
    HPO = "hpo"
    META = "meta"
    MULTITASK = "multitask"
    NAS = "nas"
    REINFORCEMENT = "reinforcement"
    SELF_SUPERVISED = "self_supervised"
    TRANSFER = "transfer"
    PIPELINE = "pipeline"


LearningStrategyType = LearningParadigm


class LearningStatus(str, Enum):
    """Lifecycle status of a learning run."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ==========================================
# Paradigm-Specific Enums
# ==========================================

class ActiveLearningStrategy(str, Enum):
    """Active learning query selection strategies."""
    UNCERTAINTY_SAMPLING = "uncertainty_sampling"
    DIVERSITY_SAMPLING = "diversity_sampling"
    QUERY_BY_COMMITTEE = "query_by_committee"
    EXPECTED_MODEL_CHANGE = "expected_model_change"
    BATCH_ACTIVE_LEARNING = "batch_active_learning"
    HYBRID_SAMPLING = "hybrid_sampling"
    ADAPTIVE_SAMPLING = "adaptive_sampling"
    COST_SENSITIVE_SAMPLING = "cost_sensitive_sampling"


class UncertaintyMeasure(str, Enum):
    """Uncertainty metrics for active learning."""
    ENTROPY = "entropy"
    MARGIN = "margin"
    LEAST_CONFIDENT = "least_confident"
    VARIANCE = "variance"
    BALD = "bald"
    MAXIMUM_ENTROPY = "maximum_entropy"
    VARIANCE_REDUCTION = "variance_reduction"


class QueryStrategy(str, Enum):
    """Query mode for active learning."""
    RANDOM_SAMPLING = "random_sampling"
    UNCERTAINTY_BASED = "uncertainty_based"
    DIVERSITY_BASED = "diversity_based"
    HYBRID_STRATEGY = "hybrid_strategy"
    ADAPTIVE_STRATEGY = "adaptive_strategy"
    COST_AWARE_STRATEGY = "cost_aware_strategy"
    # Aliases
    RANDOM = "random_sampling"
    UNCERTAINTY = "uncertainty_based"
    DIVERSITY = "diversity_based"
    HYBRID = "hybrid_strategy"


class SamplingStrategy(str, Enum):
    """Data sampling strategies for active and adaptive learning."""
    RANDOM = "random"
    UNCERTAINTY = "uncertainty"
    DIVERSITY = "diversity"
    HYBRID = "hybrid"
    CORESET = "coreset"
    BADGE = "badge"
    RANDOM_SAMPLING = "random_sampling"
    UNCERTAINTY_BASED = "uncertainty_based"
    DIVERSITY_BASED = "diversity_based"
    HYBRID_STRATEGY = "hybrid_strategy"
    ADAPTIVE_STRATEGY = "adaptive_strategy"
    COST_AWARE_STRATEGY = "cost_aware_strategy"


class OptimizationMetric(str, Enum):
    """Optimization objectives and evaluation metrics."""
    LOSS = "loss"
    ACCURACY = "accuracy"
    F1 = "f1"
    PRECISION = "precision"
    RECALL = "recall"
    REWARD = "reward"
    AUC = "auc"
    PERPLEXITY = "perplexity"
    MSE = "mse"
    MAE = "mae"
    ROUGE = "rouge"
    BLEU = "bleu"
    LATENCY = "latency"
    MEMORY = "memory"
    CUSTOM = "custom"


@dataclass
class LearningMetrics:
    """Unified metrics container for learning processes.
    
    Combines per-step tracking with aggregated training telemetry and history.
    """
    loss: float = 0.0
    val_loss: Optional[float] = None
    accuracy: Optional[float] = None
    val_accuracy: Optional[float] = None
    step: int = 0
    epoch: int = 0
    total_steps: int = 0
    total_epochs: int = 0
    duration_seconds: float = 0.0
    total_duration_sec: float = 0.0
    best_metric_value: Optional[float] = None
    best_metric_name: str = "val_loss"
    history: List['StepState'] = field(default_factory=list)
    extra_metrics: Dict[str, Any] = field(default_factory=dict)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "loss": self.loss,
            "step": self.step,
            "epoch": self.epoch,
            "total_steps": self.total_steps,
            "total_epochs": self.total_epochs,
            "duration_seconds": self.duration_seconds,
            "total_duration_sec": self.total_duration_sec,
            "timestamp": self.timestamp,
        }
        if self.accuracy is not None:
            data["accuracy"] = self.accuracy
        if self.val_loss is not None:
            data["val_loss"] = self.val_loss
        if self.val_accuracy is not None:
            data["val_accuracy"] = self.val_accuracy
        if self.best_metric_value is not None:
            data["best_metric_value"] = self.best_metric_value
            data["best_metric_name"] = self.best_metric_name
        data.update(self.extra_metrics)
        data.update(self.custom_metrics)
        return data

    def add_step(self, step_state: 'StepState') -> None:
        """Record a training step and track best metric."""
        self.history.append(step_state)
        self.total_steps = step_state.step
        self.total_epochs = step_state.epoch
        if self.best_metric_name in step_state.metrics:
            val = step_state.metrics[self.best_metric_name]
            if self.best_metric_value is None or val < self.best_metric_value:
                self.best_metric_value = val


class LearningMode(str, Enum):
    """Adaptive learning modes."""
    CONTINUOUS = "continuous"
    EPISODIC = "episodic"
    META = "meta"
    SELF_IMPROVING = "self_improving"
    EXPLORATION = "exploration"
    EXPLOITATION = "exploitation"


AdaptiveLearningStrategy = LearningMode


class AdversarialAttackType(str, Enum):
    """Adversarial attack techniques."""
    FGSM = "fgsm"
    PGD = "pgd"
    CW = "cw"
    DEEPFOOL = "deepfool"
    AUTOATTACK = "autoattack"
    BOUNDARY = "boundary"


AdversarialMethod = AdversarialAttackType


class GANType(str, Enum):
    """Generative Adversarial Network variants."""
    VANILLA = "vanilla"
    VANILLA_GAN = "vanilla_gan"
    WGAN = "wgan"
    WGAN_GP = "wgan_gp"
    CONDITIONAL = "conditional"
    CYCLE = "cycle"


class DefenseStrategy(str, Enum):
    """Adversarial defense methodologies."""
    ADVERSARIAL_TRAINING = "adversarial_training"
    RANDOMIZATION = "randomization"
    DEFENSIVE_DISTILLATION = "defensive_distillation"
    FEATURE_SQUEEZING = "feature_squeezing"
    PURIFICATION = "purification"


class AcquisitionFunction(str, Enum):
    """Bayesian optimization acquisition functions."""
    EXPECTED_IMPROVEMENT = "expected_improvement"
    PROBABILITY_OF_IMPROVEMENT = "probability_of_improvement"
    UPPER_CONFIDENCE_BOUND = "upper_confidence_bound"
    THOMPSON_SAMPLING = "thompson_sampling"
    KNOWLEDGE_GRADIENT = "knowledge_gradient"
    ENTROPY_SEARCH = "entropy_search"


class KernelType(str, Enum):
    """Gaussian Process kernel types."""
    RBF = "rbf"
    MATERN32 = "matern32"
    MATERN52 = "matern52"
    EXPONENTIAL = "exponential"
    RATIONAL_QUADRATIC = "rational_quadratic"


class OptimizationStrategy(str, Enum):
    """Acquisition optimization methods."""
    LBFGS = "lbfgs"
    RANDOM = "random"
    GENETIC = "genetic"
    DIRECT = "direct"
    CMAES = "cmaes"


# NOTE: OptimizationMetric is defined above with all members consolidated.
# This duplicate definition has been removed during refactoring.


class CausalMethod(str, Enum):
    """Causal inference methods."""
    PC_ALGORITHM = "pc_algorithm"
    FCI = "fci"
    GES = "ges"
    PROPENSITY_SCORE = "propensity_score"
    INSTRUMENTAL_VARIABLES = "instrumental_variables"
    REGRESSION_DISCONTINUITY = "regression_discontinuity"
    SYNTHETIC_CONTROL = "synthetic_control"


class CausalEffectType(str, Enum):
    """Types of causal effects."""
    ATE = "ate"
    ATT = "att"
    CATE = "cate"
    ITE = "ite"


class CLStrategy(str, Enum):
    """Continual learning strategies."""
    EWC = "ewc"
    REPLAY = "replay"
    GEM = "gem"
    PROGRESSIVE_NETWORKS = "progressive_networks"
    PACKNET = "packnet"
    LWF = "lwf"


ContinualStrategy = CLStrategy


class ReplayStrategy(str, Enum):
    """Memory replay strategies."""
    RANDOM = "random"
    RESERVOIR = "reservoir"
    HERDING = "herding"
    UNCERTAINTY = "uncertainty"
    BALANCED = "balanced"


class MemoryType(str, Enum):
    """Continual learning memory architectures."""
    EPISODIC = "episodic"
    GENERATIVE = "generative"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class EnsembleStrategy(str, Enum):
    """Ensemble aggregation strategies."""
    VOTING = "voting"
    BAGGING = "bagging"
    BOOSTING = "boosting"
    STACKING = "stacking"
    DYNAMIC = "dynamic"


class VotingStrategy(str, Enum):
    """Ensemble voting methods."""
    HARD = "hard"
    SOFT = "soft"
    WEIGHTED = "weighted"


class BoostingMethod(str, Enum):
    """Boosting algorithms."""
    ADABOOST = "adaboost"
    GRADIENT_BOOST = "gradient_boost"
    XGBOOST = "xgboost"


class AggregationMethod(str, Enum):
    """Federated learning aggregation algorithms."""
    FEDAVG = "fedavg"
    FEDPROX = "fedprox"
    FEDOPT = "fedopt"
    SCAFFOLD = "scaffold"
    FEDNOVA = "fednova"


FederatedAggregationMethod = AggregationMethod


class ClientSelectionStrategy(str, Enum):
    """Federated client selection mechanisms."""
    RANDOM = "random"
    LOSS_BASED = "loss_based"
    RESOURCE_AWARE = "resource_aware"
    ACTIVE = "active"


class PrivacyLevel(str, Enum):
    """Differential privacy levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class HpoAlgorithm(str, Enum):
    """Hyperparameter optimization algorithms."""
    BAYESIAN = "bayesian"
    EVOLUTIONARY = "evolutionary"
    TPE = "tpe"
    CMAES = "cmaes"
    OPTUNA = "optuna"
    RANDOM = "random"
    GRID = "grid"


class SamplerType(str, Enum):
    """HPO parameter samplers."""
    TPESAMPLER = "tpesampler"
    CMAESSAMPLER = "cmaessampler"
    RANDOMSAMPLER = "randomsampler"
    GRIDSAMPLER = "gridsampler"
    NSGAIISAMPLER = "nsgaiisampler"


class PrunerType(str, Enum):
    """HPO early stopping trial pruners."""
    MEDIANPRUNER = "medianpruner"
    HYPERBAND = "hyperband"
    PERCENTILEPRUNER = "percentilepruner"
    NOPRUNER = "nopruner"


class MetaLearningAlgorithm(str, Enum):
    """Meta-learning algorithms."""
    MAML = "maml"
    REPTILE = "reptile"
    FOMAML = "fomaml"
    ANIL = "anil"
    META_SGD = "meta_sgd"


class TaskDistribution(str, Enum):
    """Meta-learning task distributions."""
    FEW_SHOT = "few_shot"
    CROSS_DOMAIN = "cross_domain"
    MULTI_MODAL = "multi_modal"


class TaskType(str, Enum):
    """Multi-task learning task types."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    SEGMENTATION = "segmentation"
    DETECTION = "detection"
    GENERATION = "generation"


class TaskRelationship(str, Enum):
    """Task relationship definitions."""
    INDEPENDENT = "independent"
    HIERARCHICAL = "hierarchical"
    COMPETITIVE = "competitive"
    COOPERATIVE = "cooperative"


class SharingStrategy(str, Enum):
    """Multi-task parameter sharing schemes."""
    HARD_SHARING = "hard_sharing"
    SOFT_SHARING = "soft_sharing"
    CROSS_STITCH = "cross_stitch"
    SLUICE = "sluice"


class SearchStrategy(str, Enum):
    """Neural architecture search strategies."""
    EVOLUTIONARY = "evolutionary"
    DIFFERENTIABLE = "differentiable"
    REINFORCEMENT = "reinforcement"
    BAYESIAN = "bayesian"
    RANDOM = "random"


class RLAlgorithm(str, Enum):
    """Reinforcement learning algorithms."""
    DQN = "dqn"
    DUELING_DQN = "dueling_dqn"
    PPO = "ppo"
    A2C = "a2c"
    SAC = "sac"
    DDPG = "ddpg"


class EnvironmentType(str, Enum):
    """RL environment interaction modes."""
    SINGLE_AGENT = "single_agent"
    MULTI_AGENT = "multi_agent"
    CONTINUOUS = "continuous"
    DISCRETE = "discrete"


class SSLMethod(str, Enum):
    """Self-supervised learning methods."""
    CONTRASTIVE = "contrastive"
    PRETEXT = "pretext"
    MOMENTUM = "momentum"
    MASKED_AUTOENCODER = "masked_autoencoder"
    BYOL = "byol"
    SIMCLR = "simclr"


class PretextTaskType(str, Enum):
    """SSL pretext task types."""
    ROTATION = "rotation"
    JIGSAW = "jigsaw"
    COLORIZATION = "colorization"
    INPAINTING = "inpainting"
    MASKING = "masking"


class ContrastiveLossType(str, Enum):
    """Contrastive loss functions."""
    NT_XENT = "nt_xent"
    INFO_NCE = "info_nce"
    TRIPLET = "triplet"
    BARLOW_TWINS = "barlow_twins"


class TransferStrategy(str, Enum):
    """Transfer learning strategies."""
    FINE_TUNING = "fine_tuning"
    FEATURE_EXTRACTION = "feature_extraction"
    DOMAIN_ADAPTATION = "domain_adaptation"
    KNOWLEDGE_DISTILLATION = "knowledge_distillation"
    MULTI_TASK_TRANSFER = "multi_task_transfer"


class DomainAdaptationMethod(str, Enum):
    """Domain adaptation alignment algorithms."""
    CORAL = "coral"
    MMD = "mmd"
    DANN = "dann"
    ADDA = "adda"
    MCD = "mcd"


class KnowledgeDistillationType(str, Enum):
    """Knowledge distillation schemes."""
    RESPONSE_BASED = "response_based"
    FEATURE_BASED = "feature_based"
    RELATION_BASED = "relation_based"


DistillationMethod = KnowledgeDistillationType

# Aliases for Configuration Schemas
UncertaintyMeasureType = UncertaintyMeasure
QueryStrategyType = QueryStrategy
AdaptiveMode = LearningMode
AttackType = AdversarialAttackType
DefenseType = DefenseStrategy
AcquisitionFunctionType = AcquisitionFunction
ContinualMethodType = CLStrategy
EnsembleMethodType = EnsembleStrategy
AggregationMethodType = AggregationMethod
HPOSearchStrategyType = HpoAlgorithm
MetaAlgorithmType = MetaLearningAlgorithm
MultitaskLossBalancingType = SharingStrategy
NASStrategyType = SearchStrategy
RLAlgorithmType = RLAlgorithm
SSLPretextTaskType = PretextTaskType
TransferMethodType = TransferStrategy


@dataclass
class StepState:
    """Snapshot of a learning step's state and metrics."""
    step: int
    epoch: int = 0
    loss: float = 0.0
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    info: Dict[str, Any] = field(default_factory=dict)


# NOTE: LearningMetrics is defined above as a unified dataclass combining
# per-step tracking with aggregated telemetry. This duplicate has been removed.


@dataclass
class OptimizationResult:
    """General result of an optimization run."""
    best_params: Dict[str, Any] = field(default_factory=dict)
    best_score: float = 0.0
    n_iterations: int = 0
    total_iterations: int = 0
    best_parameters: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    duration_seconds: float = 0.0
    converged: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.best_params and self.best_parameters:
            self.best_params = self.best_parameters
        if not self.best_parameters and self.best_params:
            self.best_parameters = self.best_params
        if self.n_iterations == 0 and self.total_iterations != 0:
            self.n_iterations = self.total_iterations
        if self.total_iterations == 0 and self.n_iterations != 0:
            self.total_iterations = self.n_iterations


@dataclass
class QueryResult:
    """Result of an active learning query."""
    queried_indices: List[int]
    uncertainty_scores: Optional[np.ndarray] = None
    diversity_scores: Optional[np.ndarray] = None
    query_time_sec: float = 0.0


@dataclass
class ActiveLearningResult:
    """Result summary of an active learning cycle."""
    queried_indices: List[int] = field(default_factory=list)
    labeled_pool_size: int = 0
    unlabeled_pool_size: int = 0
    iteration: int = 0
    metrics: Dict[str, float] = field(default_factory=dict)
    query_duration_sec: float = 0.0


@dataclass
class CausalEffectResult:
    """Estimated causal effect and sensitivity metrics."""
    ate: float = 0.0
    att: Optional[float] = None
    ci_lower: float = 0.0
    ci_upper: float = 0.0
    p_value: float = 0.0
    refutation_passed: bool = True
    discovered_edges: List[Tuple[str, str]] = field(default_factory=list)


@dataclass
class FederatedRoundResult:
    """Result summary of a federated training round."""
    round_number: int = 0
    participating_clients: int = 0
    global_loss: float = 0.0
    client_losses: Dict[str, float] = field(default_factory=dict)
    duration_seconds: float = 0.0
    aggregation_status: str = "success"


@dataclass
class DefenseResult:
    """Result of an adversarial defense or attack evaluation."""
    clean_accuracy: float = 0.0
    robust_accuracy: float = 0.0
    attack_success_rate: float = 0.0
    perturbation_norm: float = 0.0
    defense_duration_sec: float = 0.0


@dataclass
class NASResult:
    """Result of a Neural Architecture Search run."""
    best_architecture: Any = None
    best_fitness: float = 0.0
    generations_completed: int = 0
    search_history: List[Dict[str, Any]] = field(default_factory=list)
    search_duration_sec: float = 0.0


@dataclass
class HPOExperimentResult:
    """Result of a hyperparameter optimization experiment."""
    best_params: Dict[str, Any] = field(default_factory=dict)
    best_value: float = 0.0
    total_trials: int = 0
    pruned_trials: int = 0
    duration_sec: float = 0.0
    trial_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PipelineStageResult:
    """Execution summary of an individual stage in a LearningPipeline."""
    stage_name: str
    paradigm: Union[LearningParadigm, str] = LearningParadigm.PIPELINE
    status: Union[LearningStatus, str] = LearningStatus.COMPLETED
    metrics: Dict[str, Any] = field(default_factory=dict)
    duration_sec: float = 0.0
    duration_seconds: float = 0.0
    strategy_type: Optional[str] = None
    output_data: Any = None
    error: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class EvaluationResult:
    """Standardized evaluation metric mapping."""
    metrics: Dict[str, float] = field(default_factory=dict)
    loss: float = 0.0
    accuracy: Optional[float] = None
    num_samples: int = 0
    duration_seconds: float = 0.0
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.metrics.get(key, default)


@dataclass
class LearningStepResult:
    """Telemetry data emitted from a single training or adaptation step."""
    step: int
    loss: float
    metrics: Dict[str, float] = field(default_factory=dict)
    learning_rate: float = 0.0
    grad_norm: Optional[float] = None
    step_duration_seconds: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class SampleQuery:
    """Active learning query recommendation."""
    indices: List[int] = field(default_factory=list)
    uncertainty_scores: List[float] = field(default_factory=list)
    diversity_scores: Optional[List[float]] = None
    query_strategy: Optional[Any] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class TaskMetrics:
    """Performance metrics for a specific multi-task or continual task ID."""
    task_id: Union[int, str]
    metrics: Dict[str, float] = field(default_factory=dict)
    loss: float = 0.0
    sample_count: int = 0


@dataclass
class LearnerState:
    """Comprehensive snapshot of a learner's internal state."""
    strategy: Any = None
    stage: Any = None
    step_count: int = 0
    epoch_count: int = 0
    best_score: Optional[float] = None
    metrics_history: List[Dict[str, float]] = field(default_factory=list)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ModelSnapshot:
    """Lightweight reference to a model state or weight checkpoint."""
    model_name: str
    iteration: int
    score: float
    state_dict_ref: Optional[Any] = None
    file_path: Optional[str] = None
    created_at: float = field(default_factory=time.time)


class LearningStage(str, Enum):
    """Lifecycle stage of a learning process or pipeline."""
    INITIALIZATION = "initialization"
    PRETRAINING = "pretraining"
    EXPLORATION = "exploration"
    EXPLOITATION = "exploitation"
    ADAPTATION = "adaptation"
    FINE_TUNING = "fine_tuning"
    ROBUSTIFICATION = "robustification"
    EVALUATION = "evaluation"
    COMPLETE = "complete"
    FAILED = "failed"


# ==========================================
# Configuration Dataclasses
# ==========================================
# NOTE: Authoritative Config definitions live in their respective module files
# (e.g., meta_learning.py, adversarial_learning.py, etc.) and are aggregated
# via config.py. The redundant copies that were here have been removed.
# Import configs from .config or from the individual module files.
#
# Backward-compat re-exports for code that imported configs from types.py:
try:
    from .config import (
        BaseLearningConfig as _BaseLearningConfig,
        LearningPipelineConfig,
        ActiveLearningConfig,
        AdaptiveLearningConfig,
        AdversarialConfig,
        BayesianOptimizationConfig,
        CausalConfig,
        ContinualLearningConfig,
        EnsembleConfig,
        EvolutionaryConfig,
        FederatedLearningConfig,
        HpoConfig,
        MetaLearningConfig,
        MultiTaskConfig,
        NASConfig,
        RLConfig,
        SSLConfig,
        TransferLearningConfig,
    )
    # Convenience aliases
    LearningConfig = _BaseLearningConfig
    BayesianConfig = BayesianOptimizationConfig
    ContinualConfig = ContinualLearningConfig
    FederatedConfig = FederatedLearningConfig
    HPOConfig = HpoConfig
except ImportError:
    # Graceful degradation if config module has circular imports during init
    pass


__all__ = [
    # Paradigm & Status Enums
    'LearningParadigm',
    'LearningStrategyType',
    'LearningStatus',

    # Active Learning
    'ActiveLearningStrategy',
    'UncertaintyMeasure',
    'QueryStrategy',
    'SamplingStrategy',

    # Adaptive Learning
    'LearningMode',
    'AdaptiveLearningStrategy',

    # Adversarial
    'AdversarialAttackType',
    'AdversarialMethod',
    'GANType',
    'DefenseStrategy',

    # Bayesian
    'AcquisitionFunction',
    'KernelType',
    'OptimizationStrategy',
    'OptimizationMetric',

    # Causal
    'CausalMethod',
    'CausalEffectType',

    # Continual
    'CLStrategy',
    'ContinualStrategy',
    'ReplayStrategy',
    'MemoryType',

    # Ensemble
    'EnsembleStrategy',
    'VotingStrategy',
    'BoostingMethod',

    # Federated
    'AggregationMethod',
    'FederatedAggregationMethod',
    'ClientSelectionStrategy',
    'PrivacyLevel',

    # HPO
    'HpoAlgorithm',
    'SamplerType',
    'PrunerType',

    # Meta-Learning
    'MetaLearningAlgorithm',
    'TaskDistribution',

    # Multitask
    'TaskType',
    'TaskRelationship',
    'SharingStrategy',

    # NAS
    'SearchStrategy',

    # RL
    'RLAlgorithm',
    'EnvironmentType',

    # SSL
    'SSLMethod',
    'PretextTaskType',
    'ContrastiveLossType',

    # Transfer
    'TransferStrategy',
    'DomainAdaptationMethod',
    'KnowledgeDistillationType',
    'DistillationMethod',

    # Type Aliases
    'UncertaintyMeasureType',
    'QueryStrategyType',
    'AdaptiveMode',
    'AttackType',
    'DefenseType',
    'AcquisitionFunctionType',
    'ContinualMethodType',
    'EnsembleMethodType',
    'AggregationMethodType',
    'HPOSearchStrategyType',
    'MetaAlgorithmType',
    'MultitaskLossBalancingType',
    'NASStrategyType',
    'RLAlgorithmType',
    'SSLPretextTaskType',
    'TransferMethodType',

    # Dataclass Results & State
    'StepState',
    'LearningMetrics',
    'OptimizationResult',
    'EvaluationResult',
    'LearningStepResult',
    'SampleQuery',
    'TaskMetrics',
    'LearnerState',
    'ModelSnapshot',
    'LearningStage',
    'QueryResult',
    'ActiveLearningResult',
    'CausalEffectResult',
    'FederatedRoundResult',
    'DefenseResult',
    'NASResult',
    'HPOExperimentResult',
    'PipelineStageResult',
]
