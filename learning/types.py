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


SamplingStrategy = QueryStrategy


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


class OptimizationMetric(str, Enum):
    """Metrics to optimize."""
    ACCURACY = "accuracy"
    LOSS = "loss"
    F1 = "f1"
    ROUGE = "rouge"
    BLEU = "bleu"
    LATENCY = "latency"
    MEMORY = "memory"
    CUSTOM = "custom"


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
SSLPretextTaskType = SSLMethod
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


@dataclass
class LearningMetrics:
    """Aggregated learning telemetry and history metrics."""
    total_steps: int = 0
    total_epochs: int = 0
    total_duration_sec: float = 0.0
    best_metric_value: Optional[float] = None
    best_metric_name: str = "val_loss"
    history: List[StepState] = field(default_factory=list)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

    def add_step(self, step_state: StepState) -> None:
        self.history.append(step_state)
        self.total_steps = step_state.step
        self.total_epochs = step_state.epoch
        if self.best_metric_name in step_state.metrics:
            val = step_state.metrics[self.best_metric_name]
            if self.best_metric_value is None or val < self.best_metric_value:
                self.best_metric_value = val


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
# Base and Domain Configurations
# ==========================================

@dataclass
class LearningConfig:
    """Base configuration for all learning modules."""
    name: str = "default_learner"
    paradigm: LearningParadigm = LearningParadigm.ACTIVE
    learning_rate: float = 1e-3
    device: str = "cpu"
    seed: int = 42
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActiveLearningConfig(LearningConfig):
    """Configuration for Active Learning."""
    active_learning_strategy: ActiveLearningStrategy = ActiveLearningStrategy.UNCERTAINTY_SAMPLING
    uncertainty_measure: UncertaintyMeasure = UncertaintyMeasure.ENTROPY
    query_strategy: QueryStrategy = QueryStrategy.UNCERTAINTY_BASED
    n_initial_samples: int = 100
    n_query_samples: int = 10
    n_total_samples: int = 1000
    max_iterations: int = 50
    uncertainty_threshold: float = 0.5
    entropy_threshold: float = 0.8
    margin_threshold: float = 0.1
    diversity_method: str = "kmeans"
    n_clusters: int = 10
    diversity_weight: float = 0.5
    n_committee_members: int = 5
    disagreement_threshold: float = 0.3
    batch_size: int = 20
    batch_diversity_weight: float = 0.3
    enable_adaptive_sampling: bool = True
    enable_cost_sensitive_sampling: bool = False
    enable_online_learning: bool = True
    enable_model_uncertainty: bool = True


@dataclass
class AdaptiveLearningConfig(LearningConfig):
    """Configuration for Adaptive Learning and Concept Drift."""
    adaptation_rate: float = 0.01
    exploration_rate: float = 0.1
    exploitation_rate: float = 0.9
    enable_meta_learning: bool = True
    meta_learning_steps: int = 100
    meta_batch_size: int = 32
    meta_learning_rate: float = 0.0001
    enable_self_improvement: bool = True
    improvement_threshold: float = 0.05
    improvement_patience: int = 10
    improvement_memory_size: int = 1000
    enable_adaptive_lr: bool = True
    enable_adaptive_architecture: bool = True
    enable_adaptive_optimization: bool = True
    enable_performance_tracking: bool = True
    enable_learning_curves: bool = True
    enable_adaptation_logging: bool = True


@dataclass
class AdversarialConfig(LearningConfig):
    """Configuration for Adversarial Robustness and GANs."""
    attack_type: AdversarialAttackType = AdversarialAttackType.FGSM
    gan_type: GANType = GANType.VANILLA_GAN
    defense_strategy: DefenseStrategy = DefenseStrategy.ADVERSARIAL_TRAINING
    attack_epsilon: float = 0.1
    attack_alpha: float = 0.01
    attack_iterations: int = 10
    attack_norm: str = "inf"
    attack_targeted: bool = False
    generator_lr: float = 0.0002
    discriminator_lr: float = 0.0002
    gan_beta1: float = 0.5
    gan_beta2: float = 0.999
    gan_latent_dim: int = 100
    defense_epsilon: float = 0.1
    defense_alpha: float = 0.01
    defense_iterations: int = 10
    defense_norm: str = "inf"
    batch_size: int = 64
    num_epochs: int = 100
    enable_robustness_analysis: bool = True
    enable_attack_generation: bool = True
    enable_defense_training: bool = True
    enable_adversarial_training: bool = True


@dataclass
class BayesianOptimizationConfig(LearningConfig):
    """Configuration for Bayesian Optimization."""
    acquisition_function: AcquisitionFunction = AcquisitionFunction.EXPECTED_IMPROVEMENT
    kernel_type: KernelType = KernelType.MATERN52
    optimization_strategy: OptimizationStrategy = OptimizationStrategy.LBFGS
    n_initial_points: int = 5
    n_iterations: int = 25
    xi: float = 0.01
    kappa: float = 1.96
    noise_level: float = 1e-6
    normalize_y: bool = True
    random_state: int = 42


BayesianConfig = BayesianOptimizationConfig


@dataclass
class CausalConfig(LearningConfig):
    """Configuration for Causal Inference."""
    method: CausalMethod = CausalMethod.PROPENSITY_SCORE
    effect_type: CausalEffectType = CausalEffectType.ATE
    alpha: float = 0.05
    n_bootstrap: int = 100
    refutation_methods: List[str] = field(default_factory=lambda: ["random_common_cause", "placebo_treatment"])


@dataclass
class ContinualLearningConfig(LearningConfig):
    """Configuration for Continual / Lifelong Learning."""
    strategy: CLStrategy = CLStrategy.EWC
    replay_strategy: ReplayStrategy = ReplayStrategy.RESERVOIR
    memory_type: MemoryType = MemoryType.EPISODIC
    memory_size: int = 1000
    ewc_lambda: float = 5000.0
    gem_gamma: float = 0.5
    batch_size: int = 32
    n_tasks: int = 5


ContinualConfig = ContinualLearningConfig


@dataclass
class EnsembleConfig(LearningConfig):
    """Configuration for Ensemble Learning."""
    strategy: EnsembleStrategy = EnsembleStrategy.VOTING
    voting_strategy: VotingStrategy = VotingStrategy.SOFT
    boosting_method: BoostingMethod = BoostingMethod.GRADIENT_BOOST
    n_estimators: int = 10
    weights: Optional[List[float]] = None
    stacking_final_estimator: str = "logistic_regression"


@dataclass
class EvolutionaryConfig(LearningConfig):
    """Configuration for Evolutionary Optimization."""
    population_size: int = 100
    elite_size: int = 10
    tournament_size: int = 3
    crossover_rate: float = 0.8
    mutation_rate: float = 0.1
    mutation_strength: float = 0.1
    max_generations: int = 100
    convergence_threshold: float = 1e-6
    stagnation_limit: int = 20
    enable_multi_objective: bool = False
    n_objectives: int = 2
    pareto_front_size: int = 20
    enable_adaptive_parameters: bool = True
    enable_diversity_maintenance: bool = True


@dataclass
class FederatedLearningConfig(LearningConfig):
    """Configuration for Federated Learning."""
    aggregation_method: AggregationMethod = AggregationMethod.FEDAVG
    client_selection: ClientSelectionStrategy = ClientSelectionStrategy.RANDOM
    privacy_level: PrivacyLevel = PrivacyLevel.NONE
    n_clients: int = 10
    clients_per_round: int = 5
    n_rounds: int = 20
    local_epochs: int = 3
    local_lr: float = 0.01
    dp_epsilon: float = 1.0
    dp_delta: float = 1e-5


FederatedConfig = FederatedLearningConfig


@dataclass
class HpoConfig(LearningConfig):
    """Configuration for Hyperparameter Optimization."""
    algorithm: HpoAlgorithm = HpoAlgorithm.TPE
    sampler: SamplerType = SamplerType.TPESAMPLER
    pruner: PrunerType = PrunerType.HYPERBAND
    n_trials: int = 50
    timeout_seconds: Optional[float] = None
    n_jobs: int = 1
    direction: str = "minimize"


HPOConfig = HpoConfig


@dataclass
class MetaLearningConfig(LearningConfig):
    """Configuration for Meta-Learning."""
    algorithm: MetaLearningAlgorithm = MetaLearningAlgorithm.MAML
    task_distribution: TaskDistribution = TaskDistribution.FEW_SHOT
    n_ways: int = 5
    k_shots: int = 1
    q_queries: int = 15
    inner_lr: float = 0.01
    meta_lr: float = 0.001
    inner_steps: int = 5
    meta_epochs: int = 50


@dataclass
class MultiTaskConfig(LearningConfig):
    """Configuration for Multi-Task Learning."""
    task_type: TaskType = TaskType.CLASSIFICATION
    task_relationship: TaskRelationship = TaskRelationship.COOPERATIVE
    sharing_strategy: SharingStrategy = SharingStrategy.HARD_SHARING
    task_weights: Dict[str, float] = field(default_factory=dict)
    enable_gradient_surgery: bool = True
    loss_balancing_method: str = "uncertainty_weighting"


@dataclass
class NASConfig(LearningConfig):
    """Configuration for Neural Architecture Search."""
    search_strategy: SearchStrategy = SearchStrategy.EVOLUTIONARY
    max_layers: int = 12
    min_layers: int = 2
    population_size: int = 30
    generations: int = 20
    mutation_rate: float = 0.15
    crossover_rate: float = 0.7
    hardware_constraint_latency_ms: Optional[float] = None


@dataclass
class RLConfig(LearningConfig):
    """Configuration for Reinforcement Learning."""
    algorithm: RLAlgorithm = RLAlgorithm.PPO
    environment_type: EnvironmentType = EnvironmentType.SINGLE_AGENT
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_range: float = 0.2
    value_coef: float = 0.5
    entropy_coef: float = 0.01
    buffer_size: int = 10000
    batch_size: int = 64
    max_episodes: int = 500


@dataclass
class SSLConfig(LearningConfig):
    """Configuration for Self-Supervised Learning."""
    method: SSLMethod = SSLMethod.CONTRASTIVE
    pretext_task: PretextTaskType = PretextTaskType.ROTATION
    contrastive_loss: ContrastiveLossType = ContrastiveLossType.NT_XENT
    temperature: float = 0.07
    projection_dim: int = 128
    momentum: float = 0.999
    queue_size: int = 65536


@dataclass
class TransferLearningConfig(LearningConfig):
    """Configuration for Transfer Learning."""
    strategy: TransferStrategy = TransferStrategy.FINE_TUNING
    domain_adaptation: DomainAdaptationMethod = DomainAdaptationMethod.CORAL
    distillation_type: KnowledgeDistillationType = KnowledgeDistillationType.RESPONSE_BASED
    temperature: float = 2.0
    alpha_distillation: float = 0.5
    frozen_layers: List[str] = field(default_factory=list)
    unfreeze_schedule: Optional[Dict[int, List[str]]] = None


@dataclass
class LearningPipelineConfig:
    """Configuration for multi-stage LearningPipeline orchestration."""
    name: str = "learning_pipeline"
    fail_fast: bool = True
    log_level: str = "INFO"
    timeout_sec: Optional[float] = None
    save_stage_artifacts: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


# Type Aliases for Compatibility
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


__all__ = [
    'LearningParadigm',
    'LearningStrategyType',
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

    'LearningStatus',
    'ActiveLearningStrategy',
    'UncertaintyMeasure',
    'QueryStrategy',
    'SamplingStrategy',
    'LearningMode',
    'AdaptiveLearningStrategy',
    'AdversarialAttackType',
    'AdversarialMethod',
    'GANType',
    'DefenseStrategy',
    'AcquisitionFunction',
    'KernelType',
    'OptimizationStrategy',
    'OptimizationMetric',
    'CausalMethod',
    'CausalEffectType',
    'CLStrategy',
    'ContinualStrategy',
    'ReplayStrategy',
    'MemoryType',
    'EnsembleStrategy',
    'VotingStrategy',
    'BoostingMethod',
    'AggregationMethod',
    'FederatedAggregationMethod',
    'ClientSelectionStrategy',
    'PrivacyLevel',
    'HpoAlgorithm',
    'SamplerType',
    'PrunerType',
    'MetaLearningAlgorithm',
    'TaskDistribution',
    'TaskType',
    'TaskRelationship',
    'SharingStrategy',
    'SearchStrategy',
    'RLAlgorithm',
    'EnvironmentType',
    'SSLMethod',
    'PretextTaskType',
    'ContrastiveLossType',
    'TransferStrategy',
    'DomainAdaptationMethod',
    'KnowledgeDistillationType',
    'DistillationMethod',
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
    'LearningConfig',
    'ActiveLearningConfig',
    'AdaptiveLearningConfig',
    'AdversarialConfig',
    'BayesianOptimizationConfig',
    'BayesianConfig',
    'CausalConfig',
    'ContinualLearningConfig',
    'ContinualConfig',
    'EnsembleConfig',
    'EvolutionaryConfig',
    'FederatedLearningConfig',
    'FederatedConfig',
    'HpoConfig',
    'HPOConfig',
    'MetaLearningConfig',
    'MultiTaskConfig',
    'NASConfig',
    'RLConfig',
    'SSLConfig',
    'TransferLearningConfig',
    'LearningPipelineConfig',
]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.learning."):
        sys.modules["learning." + __name__[len("optimization_core.learning."):]] = _mod
    elif __name__.startswith("learning."):
        sys.modules["optimization_core.learning." + __name__[len("learning."):]] = _mod
