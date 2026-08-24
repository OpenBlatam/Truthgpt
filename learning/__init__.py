"""
Unified Learning Strategies Subsystem for TruthGPT Optimization Core.

Provides an enterprise-grade, highly modular, and extensible suite of 16 distinct
learning paradigms with thread-safe lazy imports, structured configuration
dataclasses, typed exceptions, component registries, lifecycle callbacks,
and multi-stage learning pipeline orchestration.

Paradigms Supported:
- Active Learning (Uncertainty, Diversity, Committee, Expected Model Change)
- Adaptive Learning (Exploration, Exploitation, Meta-Learning, Self-Improvement)
- Adversarial Robustness & GANs (FGSM, PGD, CW, Defensive Distillation, WGAN)
- Bayesian Optimization (Gaussian Processes, Acquisition Optimization, Multi-Objective)
- Causal Inference (Discovery, Effect Estimation, Sensitivity, DiD, Propensity Matching)
- Continual Learning (EWC, Replay Buffers, Progressive Networks, Lifelong Learning)
- Ensemble Learning (Voting, Stacking, Bagging, Boosting, Dynamic Weighting)
- Evolutionary Computing (Genetic Algorithms, Multi-Objective Pareto, Elitism)
- Federated Learning (FedAvg, FedProx, Differential Privacy, Secure Aggregation)
- Hyperparameter Optimization (TPE, CMA-ES, Bayesian HPO, Optuna, Pruning)
- Meta-Learning (MAML, Reptile, Few-Shot Task Generation)
- Multitask Learning (Hard/Soft Parameter Sharing, Gradient Surgery, PCGrad)
- Neural Architecture Search (Evolutionary NAS, Differentiable Supernets)
- Reinforcement Learning (DQN, Dueling DQN, PPO, Multi-Agent Environments)
- Self-Supervised Learning (SimCLR, MoCo, BYOL, Pretext Tasks, Memory Banks)
- Transfer Learning (Fine-Tuning, Feature Extraction, Domain Adaptation, Distillation)
- Learning Pipeline (Multi-stage composition & workflow execution)
"""

from __future__ import annotations

import importlib
import logging
import sys
import threading
from typing import Any, Dict, List, Optional, Type, Union

logger = logging.getLogger(__name__)

# ==========================================
# Lazy Import Resolution Map
# ==========================================

_LAZY_IMPORTS: Dict[str, str] = {
    # Core Infrastructure
    'BaseLearner': '.interfaces',
    'BaseLearningStrategy': '.interfaces',
    'BaseQuerySampler': '.interfaces',
    'BaseDefense': '.interfaces',
    'BaseDomainAdapter': '.interfaces',
    'BaseAggregationStrategy': '.interfaces',
    'BaseArchitectureSearch': '.interfaces',
    'BaseAcquisitionFunction': '.interfaces',
    'BaseCallback': '.interfaces',
    
    # Exceptions
    'LearningError': '.exceptions',
    'LearningConfigError': '.exceptions',
    'ActiveLearningError': '.exceptions',
    'AdaptiveLearningError': '.exceptions',
    'AdversarialAttackError': '.exceptions',
    'AdversarialDefenseError': '.exceptions',
    'BayesianOptimizationError': '.exceptions',
    'CausalInferenceError': '.exceptions',
    'ContinualLearningError': '.exceptions',
    'EnsembleError': '.exceptions',
    'EvolutionaryError': '.exceptions',
    'FederatedLearningError': '.exceptions',
    'HyperparameterOptimizationError': '.exceptions',
    'MetaLearningError': '.exceptions',
    'MultiTaskLearningError': '.exceptions',
    'NASError': '.exceptions',
    'ReinforcementLearningError': '.exceptions',
    'SelfSupervisedError': '.exceptions',
    'TransferLearningError': '.exceptions',
    'PipelineExecutionError': '.exceptions',
    
    # Configs
    'BaseLearningConfig': '.config',
    'ActiveLearningConfig': '.config',
    'AdaptiveLearningConfig': '.config',
    'AdversarialConfig': '.config',
    'BayesianOptimizationConfig': '.config',
    'CausalConfig': '.config',
    'ContinualLearningConfig': '.config',
    'EnsembleConfig': '.config',
    'EvolutionaryConfig': '.config',
    'FederatedLearningConfig': '.config',
    'HPOConfig': '.config',
    'MetaLearningConfig': '.config',
    'MultiTaskConfig': '.config',
    'NASConfig': '.config',
    'RLConfig': '.config',
    'SSLConfig': '.config',
    'TransferLearningConfig': '.config',
    'LearningPipelineConfig': '.config',
    
    # Types & Enums
    'LearningParadigm': '.types',
    'LearningStatus': '.types',
    'StepState': '.types',
    'LearningMetrics': '.types',
    'QueryResult': '.types',
    'DefenseResult': '.types',
    'NASResult': '.types',
    'HPOExperimentResult': '.types',
    'PipelineStageResult': '.types',
    
    # Registry, Callbacks & Pipeline
    'LearningRegistry': '.registry',
    'CallbackHandler': '.callbacks',
    'PrintLogger': '.callbacks',
    'TelemetryCallback': '.callbacks',
    'EarlyStoppingCallback': '.callbacks',
    'PipelineStage': '.pipeline',
    'LearningPipeline': '.pipeline',
    
    # Active Learning
    'ActiveLearningStrategy': '.active_learning',
    'UncertaintyMeasure': '.active_learning',
    'QueryStrategy': '.active_learning',
    'ActiveLearningSystem': '.active_learning',
    'ActiveLearner': '.active_learning',
    'UncertaintySampler': '.active_learning',
    'DiversitySampler': '.active_learning',
    'QueryByCommittee': '.active_learning',
    'ExpectedModelChange': '.active_learning',
    'BatchActiveLearning': '.active_learning',
    
    # Adaptive Learning
    'LearningMode': '.adaptive_learning',
    'AdaptiveLearningStrategy': '.adaptive_learning',
    'AdaptiveLearningSystem': '.adaptive_learning',
    'AdaptiveLearner': '.adaptive_learning',
    'PerformanceTracker': '.adaptive_learning',
    'SelfImprovementEngine': '.adaptive_learning',
    
    # Adversarial Learning
    'AdversarialAttackType': '.adversarial_learning',
    'GANType': '.adversarial_learning',
    'DefenseStrategy': '.adversarial_learning',
    'AdversarialLearningSystem': '.adversarial_learning',
    'AdversarialLearner': '.adversarial_learning',
    'AdversarialAttacker': '.adversarial_learning',
    'AdversarialDefense': '.adversarial_learning',
    'RobustnessAnalyzer': '.adversarial_learning',
    'GANTrainer': '.adversarial_learning',
    'GANGenerator': '.adversarial_learning',
    'GANDiscriminator': '.adversarial_learning',
    
    # Bayesian Optimization
    'AcquisitionFunction': '.bayesian_optimization',
    'KernelType': '.bayesian_optimization',
    'OptimizationStrategy': '.bayesian_optimization',
    'BayesianOptimizer': '.bayesian_optimization',
    'GaussianProcessModel': '.bayesian_optimization',
    'AcquisitionFunctionOptimizer': '.bayesian_optimization',
    
    # Causal Inference
    'CausalMethod': '.causal_inference',
    'CausalEffectType': '.causal_inference',
    'CausalInferenceSystem': '.causal_inference',
    'CausalInference': '.causal_inference',
    'CausalInferenceEngine': '.causal_inference',
    'CausalDiscovery': '.causal_inference',
    'CausalEffectEstimator': '.causal_inference',
    'SensitivityAnalyzer': '.causal_inference',
    'RobustnessChecker': '.causal_inference',
    
    # Continual Learning
    'CLStrategy': '.continual_learning',
    'ReplayStrategy': '.continual_learning',
    'MemoryType': '.continual_learning',
    'CLTrainer': '.continual_learning',
    'ContinualLearner': '.continual_learning',
    'EWC': '.continual_learning',
    'ReplayBuffer': '.continual_learning',
    'ProgressiveNetwork': '.continual_learning',
    'LifelongLearner': '.continual_learning',
    
    # Ensemble Learning
    'EnsembleStrategy': '.ensemble_learning',
    'VotingStrategy': '.ensemble_learning',
    'BoostingMethod': '.ensemble_learning',
    'EnsembleTrainer': '.ensemble_learning',
    'EnsembleLearner': '.ensemble_learning',
    'EnsembleManager': '.ensemble_learning',
    'VotingEnsemble': '.ensemble_learning',
    'StackingEnsemble': '.ensemble_learning',
    'BaggingEnsemble': '.ensemble_learning',
    'BoostingEnsemble': '.ensemble_learning',
    'DynamicEnsemble': '.ensemble_learning',
    
    # Evolutionary Computing
    'SelectionMethod': '.evolutionary_computing',
    'CrossoverMethod': '.evolutionary_computing',
    'MutationMethod': '.evolutionary_computing',
    'EvolutionaryAlgorithm': '.evolutionary_computing',
    'EvolutionaryOptimizer': '.evolutionary_computing',
    'Individual': '.evolutionary_computing',
    'Population': '.evolutionary_computing',
    
    # Federated Learning
    'AggregationMethod': '.federated_learning',
    'ClientSelectionStrategy': '.federated_learning',
    'PrivacyLevel': '.federated_learning',
    'FederatedLearningSystem': '.federated_learning',
    'FederatedLearner': '.federated_learning',
    'FederatedClient': '.federated_learning',
    'FederatedServer': '.federated_learning',
    'AsyncFederatedServer': '.federated_learning',
    'PrivacyPreservation': '.federated_learning',
    
    # Hyperparameter Optimization
    'HpoAlgorithm': '.hyperparameter_optimization',
    'SamplerType': '.hyperparameter_optimization',
    'PrunerType': '.hyperparameter_optimization',
    'HpoManager': '.hyperparameter_optimization',
    'HyperparameterOptimizer': '.hyperparameter_optimization',
    'TPEOptimizer': '.hyperparameter_optimization',
    'CMAESOptimizer': '.hyperparameter_optimization',
    'OptunaOptimizer': '.hyperparameter_optimization',
    
    # Meta Learning
    'MetaLearningAlgorithm': '.meta_learning',
    'TaskDistribution': '.meta_learning',
    'MetaLearner': '.meta_learning',
    'TaskGenerator': '.meta_learning',
    'MAML': '.meta_learning',
    'Reptile': '.meta_learning',
    
    # Multitask Learning
    'TaskType': '.multitask_learning',
    'TaskRelationship': '.multitask_learning',
    'SharingStrategy': '.multitask_learning',
    'MultiTaskTrainer': '.multitask_learning',
    'MultitaskLearner': '.multitask_learning',
    'MultitaskModel': '.multitask_learning',
    'TaskBalancer': '.multitask_learning',
    'GradientSurgery': '.multitask_learning',
    'SharedRepresentation': '.multitask_learning',
    'MultiTaskHead': '.multitask_learning',
    'MultiTaskNetwork': '.multitask_learning',
    
    # Neural Architecture Search
    'SearchStrategy': '.nas',
    'EvolutionaryNAS': '.nas',
    'NASOptimizer': '.nas',
    'NeuralArchitectureSearch': '.nas',
    'DifferentiableNAS': '.nas',
    'ArchitectureGene': '.nas',
    'NeuralArchitecture': '.nas',
    
    # Reinforcement Learning
    'RLAlgorithm': '.reinforcement_learning',
    'EnvironmentType': '.reinforcement_learning',
    'RLTrainingManager': '.reinforcement_learning',
    'ReinforcementLearner': '.reinforcement_learning',
    'RLSystem': '.reinforcement_learning',
    'DQNAgent': '.reinforcement_learning',
    'PPOAgent': '.reinforcement_learning',
    'ExperienceReplay': '.reinforcement_learning',
    'DQNNetwork': '.reinforcement_learning',
    'DuelingDQNNetwork': '.reinforcement_learning',
    'MultiAgentEnvironment': '.reinforcement_learning',
    
    # Self-Supervised Learning
    'SSLMethod': '.self_supervised_learning',
    'PretextTaskType': '.self_supervised_learning',
    'ContrastiveLossType': '.self_supervised_learning',
    'SSLTrainer': '.self_supervised_learning',
    'SelfSupervisedLearner': '.self_supervised_learning',
    'SelfSupervisedTrainer': '.self_supervised_learning',
    'ContrastiveLearner': '.self_supervised_learning',
    'PretextTaskModel': '.self_supervised_learning',
    'RepresentationLearner': '.self_supervised_learning',
    'MomentumEncoder': '.self_supervised_learning',
    'MemoryBank': '.self_supervised_learning',
    
    # Transfer Learning
    'TransferStrategy': '.transfer_learning',
    'DomainAdaptationMethod': '.transfer_learning',
    'KnowledgeDistillationType': '.transfer_learning',
    'TransferTrainer': '.transfer_learning',
    'TransferLearner': '.transfer_learning',
    'TransferLearningManager': '.transfer_learning',
    'FineTuner': '.transfer_learning',
    'FeatureExtractor': '.transfer_learning',
    'KnowledgeDistiller': '.transfer_learning',
    'DomainAdapter': '.transfer_learning',
    'MultiTaskAdapter': '.transfer_learning',
}

_import_cache: Dict[str, Any] = {}
_cache_lock = threading.RLock()


def __getattr__(name: str) -> Any:
    """
    Thread-safe lazy import resolution for the learning subsystem.
    """
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    with _cache_lock:
        if name in _import_cache:
            return _import_cache[name]
        
        if name not in _LAZY_IMPORTS:
            available = sorted(_LAZY_IMPORTS.keys())[:15]
            raise AttributeError(
                f"module '{__name__}' has no attribute '{name}'. "
                f"Available attributes: {', '.join(available)}..."
            )
        
        rel_module = _LAZY_IMPORTS[name]
        full_module = f"{__name__}{rel_module}"
        try:
            mod = importlib.import_module(full_module)
            obj = getattr(mod, name)
            _import_cache[name] = obj
            return obj
        except Exception as e:
            # Fallback direct relative import
            try:
                mod = importlib.import_module(rel_module, package=__name__)
                obj = getattr(mod, name)
                _import_cache[name] = obj
                return obj
            except Exception as inner_e:
                raise AttributeError(
                    f"module '{__name__}' failed to load '{name}' from '{full_module}': {e} | {inner_e}"
                ) from e


def __dir__() -> List[str]:
    """Provide complete autocomplete attribute listing."""
    return sorted(set(list(globals().keys()) + list(_LAZY_IMPORTS.keys()) + list(LEARNING_MODULE_REGISTRY.keys())))


# ==========================================
# Unified Factory & Module Registry
# ==========================================

LEARNING_MODULE_REGISTRY: Dict[str, Dict[str, str]] = {
    "active": {
        "module": ".active_learning",
        "class": "ActiveLearningSystem",
        "config_class": "ActiveLearningConfig",
        "description": "Active Learning with uncertainty and diversity sampling."
    },
    "adaptive": {
        "module": ".adaptive_learning",
        "class": "AdaptiveLearningSystem",
        "config_class": "AdaptiveLearningConfig",
        "description": "Adaptive and self-improving meta-optimization systems."
    },
    "adversarial": {
        "module": ".adversarial_learning",
        "class": "AdversarialLearningSystem",
        "config_class": "AdversarialConfig",
        "description": "Adversarial robustness, attack simulations, and GAN training."
    },
    "bayesian": {
        "module": ".bayesian_optimization",
        "class": "BayesianOptimizer",
        "config_class": "BayesianOptimizationConfig",
        "description": "Bayesian optimization with Gaussian Processes."
    },
    "causal": {
        "module": ".causal_inference",
        "class": "CausalInferenceSystem",
        "config_class": "CausalConfig",
        "description": "Causal discovery, effect estimation, and sensitivity analysis."
    },
    "continual": {
        "module": ".continual_learning",
        "class": "CLTrainer",
        "config_class": "ContinualLearningConfig",
        "description": "Continual and lifelong learning with catastrophic forgetting prevention."
    },
    "ensemble": {
        "module": ".ensemble_learning",
        "class": "EnsembleTrainer",
        "config_class": "EnsembleConfig",
        "description": "Ensemble model aggregation, voting, bagging, boosting, and stacking."
    },
    "evolutionary": {
        "module": ".evolutionary_computing",
        "class": "EvolutionaryOptimizer",
        "config_class": "EvolutionaryConfig",
        "description": "Evolutionary computing, genetic algorithms, and multi-objective optimization."
    },
    "federated": {
        "module": ".federated_learning",
        "class": "FederatedLearningSystem",
        "config_class": "FederatedLearningConfig",
        "description": "Federated learning with differential privacy and client aggregation."
    },
    "hpo": {
        "module": ".hyperparameter_optimization",
        "class": "HpoManager",
        "config_class": "HPOConfig",
        "description": "Hyperparameter optimization via TPE, CMA-ES, and Optuna."
    },
    "meta": {
        "module": ".meta_learning",
        "class": "MetaLearner",
        "config_class": "MetaLearningConfig",
        "description": "Meta-learning algorithms including MAML and Reptile."
    },
    "multitask": {
        "module": ".multitask_learning",
        "class": "MultiTaskTrainer",
        "config_class": "MultiTaskConfig",
        "description": "Multi-task learning with shared representation and gradient surgery."
    },
    "nas": {
        "module": ".nas",
        "class": "EvolutionaryNAS",
        "config_class": "NASConfig",
        "description": "Neural architecture search with evolutionary and differentiable strategies."
    },
    "reinforcement": {
        "module": ".reinforcement_learning",
        "class": "RLTrainingManager",
        "config_class": "RLConfig",
        "description": "Reinforcement learning training with DQN, PPO, and multi-agent systems."
    },
    "self_supervised": {
        "module": ".self_supervised_learning",
        "class": "SSLTrainer",
        "config_class": "SSLConfig",
        "description": "Self-supervised learning with contrastive learning and pretext tasks."
    },
    "transfer": {
        "module": ".transfer_learning",
        "class": "TransferTrainer",
        "config_class": "TransferLearningConfig",
        "description": "Transfer learning, domain adaptation, and knowledge distillation."
    },
    "pipeline": {
        "module": ".pipeline",
        "class": "LearningPipeline",
        "config_class": "LearningPipelineConfig",
        "description": "Multi-stage learning pipeline orchestrator."
    }
}


def create_learning_module(module_type: str, config: Optional[Union[Dict[str, Any], Any]] = None, **kwargs: Any) -> Any:
    """
    Unified factory function to instantiate any learning subsystem module.
    
    Args:
        module_type: Name of the paradigm (e.g., 'active', 'adversarial', 'evolutionary', etc.)
        config: Optional configuration dataclass instance or dictionary of options.
        **kwargs: Additional parameters passed to component initialization.
        
    Returns:
        Instantiated learner object adhering to BaseLearner protocol.
        
    Example:
        >>> from optimization_core.learning import create_learning_module
        >>> learner = create_learning_module("active")
        >>> hpo = create_learning_module("hpo", {"n_trials": 20})
    """
    key = module_type.lower().replace("-", "_").replace(" ", "_")
    
    # Handle common aliases
    alias_map = {
        "active_learning": "active",
        "adaptive_learning": "adaptive",
        "adversarial_learning": "adversarial",
        "bayesian_optimization": "bayesian",
        "causal_inference": "causal",
        "continual_learning": "continual",
        "lifelong_learning": "continual",
        "ensemble_learning": "ensemble",
        "evolutionary_computing": "evolutionary",
        "federated_learning": "federated",
        "hyperparameter_optimization": "hpo",
        "meta_learning": "meta",
        "multitask_learning": "multitask",
        "neural_architecture_search": "nas",
        "reinforcement_learning": "reinforcement",
        "rl": "reinforcement",
        "self_supervised_learning": "self_supervised",
        "ssl": "self_supervised",
        "transfer_learning": "transfer",
    }
    key = alias_map.get(key, key)
    
    if key not in LEARNING_MODULE_REGISTRY:
        available = ", ".join(sorted(LEARNING_MODULE_REGISTRY.keys()))
        raise ValueError(f"Unknown learning module type: '{module_type}'. Available: {available}")
    
    entry = LEARNING_MODULE_REGISTRY[key]
    mod_path = f"{__name__}{entry['module']}"
    cls_name = entry["class"]
    cfg_name = entry["config_class"]
    
    mod = importlib.import_module(mod_path)
    cls_obj = getattr(mod, cls_name)
    
    # Build config instance if dict is passed
    if isinstance(config, dict):
        try:
            cfg_mod = importlib.import_module(f"{__name__}.config")
            cfg_cls = getattr(cfg_mod, cfg_name)
            config_instance = cfg_cls.from_dict(config)
        except Exception:
            config_instance = config
    elif config is None:
        try:
            cfg_mod = importlib.import_module(f"{__name__}.config")
            cfg_cls = getattr(cfg_mod, cfg_name)
            config_instance = cfg_cls(**kwargs)
        except Exception:
            config_instance = None
    else:
        config_instance = config

    if config_instance is not None:
        return cls_obj(config_instance)
    return cls_obj()


def list_available_learning_modules() -> List[str]:
    """List all supported learning paradigms in the subsystem."""
    return sorted(list(LEARNING_MODULE_REGISTRY.keys()))


def get_learning_module_info(module_type: str) -> Dict[str, Any]:
    """Retrieve metadata and description for a learning module."""
    key = module_type.lower()
    if key not in LEARNING_MODULE_REGISTRY:
        raise ValueError(f"Module '{module_type}' not found.")
    return dict(LEARNING_MODULE_REGISTRY[key])


# ==========================================
# Module Exports
# ==========================================

__all__ = [
    # Factory & Utilities
    'create_learning_module',
    'list_available_learning_modules',
    'get_learning_module_info',
    'LEARNING_MODULE_REGISTRY',
    
    # Core Interfaces
    'BaseLearner',
    'BaseLearningStrategy',
    'BaseQuerySampler',
    'BaseDefense',
    'BaseDomainAdapter',
    'BaseAggregationStrategy',
    'BaseArchitectureSearch',
    'BaseAcquisitionFunction',
    'BaseCallback',
    
    # Exceptions
    'LearningError',
    'LearningConfigError',
    'ActiveLearningError',
    'AdaptiveLearningError',
    'AdversarialAttackError',
    'AdversarialDefenseError',
    'BayesianOptimizationError',
    'CausalInferenceError',
    'ContinualLearningError',
    'EnsembleError',
    'EvolutionaryError',
    'FederatedLearningError',
    'HyperparameterOptimizationError',
    'MetaLearningError',
    'MultiTaskLearningError',
    'NASError',
    'ReinforcementLearningError',
    'SelfSupervisedError',
    'TransferLearningError',
    'PipelineExecutionError',
    
    # Core Infrastructure
    'LearningRegistry',
    'LearningPipeline',
    'PipelineStage',
    'CallbackHandler',
    'PrintLogger',
    'TelemetryCallback',
    'EarlyStoppingCallback',
    
    # Configs
    'BaseLearningConfig',
    'ActiveLearningConfig',
    'AdaptiveLearningConfig',
    'AdversarialConfig',
    'BayesianOptimizationConfig',
    'CausalConfig',
    'ContinualLearningConfig',
    'EnsembleConfig',
    'EvolutionaryConfig',
    'FederatedLearningConfig',
    'HPOConfig',
    'MetaLearningConfig',
    'MultiTaskConfig',
    'NASConfig',
    'RLConfig',
    'SSLConfig',
    'TransferLearningConfig',
    'LearningPipelineConfig',
    
    # Primary Learners & Aliases
    'ActiveLearningSystem',
    'ActiveLearner',
    'AdaptiveLearningSystem',
    'AdaptiveLearner',
    'AdversarialLearningSystem',
    'AdversarialLearner',
    'BayesianOptimizer',
    'CausalInferenceSystem',
    'CausalInference',
    'CausalInferenceEngine',
    'CLTrainer',
    'ContinualLearner',
    'LifelongLearner',
    'EnsembleTrainer',
    'EnsembleLearner',
    'EnsembleManager',
    'EvolutionaryOptimizer',
    'FederatedLearningSystem',
    'FederatedLearner',
    'HpoManager',
    'HyperparameterOptimizer',
    'MetaLearner',
    'MultiTaskTrainer',
    'MultitaskLearner',
    'EvolutionaryNAS',
    'NASOptimizer',
    'NeuralArchitectureSearch',
    'RLTrainingManager',
    'ReinforcementLearner',
    'RLSystem',
    'SSLTrainer',
    'SelfSupervisedLearner',
    'SelfSupervisedTrainer',
    'TransferTrainer',
    'TransferLearner',
    'TransferLearningManager',
]

# Dual-namespace shim support
_curr_mod = sys.modules.get(__name__)
if _curr_mod:
    if __name__.startswith("optimization_core.learning"):
        sys.modules["learning"] = _curr_mod
    elif __name__ == "learning":
        sys.modules["optimization_core.learning"] = _curr_mod
