"""
Learning Strategies Subsystem for TruthGPT Optimization Core
=============================================================
Unified, enterprise-grade learning subsystem encompassing 16 learning paradigms,
multi-stage fluent pipelines, typed registry, and extensible optimization strategies:
- Active Learning
- Adaptive Learning & Concept Drift
- Adversarial Learning & Robustness
- Bayesian Optimization & Surrogate Models
- Causal Inference & Effect Estimation
- Continual & Lifelong Learning
- Ensemble Learning (Voting, Stacking, Boosting)
- Evolutionary Computing & Multi-Objective Search
- Federated Learning & Privacy Preservation
- Hyperparameter Optimization (Optuna, TPE, CMA-ES)
- Meta-Learning (MAML, Reptile, Few-Shot)
- Multitask Learning & Gradient Surgery
- Neural Architecture Search (NAS)
- Reinforcement Learning (DQN, PPO)
- Self-Supervised Learning & Contrastive Pretraining
- Transfer Learning, Domain Adaptation & Distillation
"""

from __future__ import annotations

import sys
import threading
import importlib
from typing import Any, Dict, List, Optional, Union

# Version
__version__ = "2.0.0"

# Module level aliasing for backward compatibility
_curr_mod = sys.modules.get(__name__)
if _curr_mod:
    if __name__.startswith("optimization_core.learning"):
        sys.modules["learning"] = _curr_mod
    elif __name__ == "learning":
        sys.modules["optimization_core.learning"] = _curr_mod

# Comprehensive lazy import mapping
_LAZY_IMPORTS: Dict[str, str] = {
    # Interfaces & Contracts
    'BaseLearner': '.interfaces',
    'BaseLearningOptimizer': '.interfaces',
    'BaseSampler': '.interfaces',
    'BaseActiveLearner': '.interfaces',
    'BaseAdaptiveLearner': '.interfaces',
    'BaseAdversarialLearner': '.interfaces',
    'BaseBayesianOptimizer': '.interfaces',
    'BaseCausalInference': '.interfaces',
    'BaseContinualLearner': '.interfaces',
    'BaseEnsembleLearner': '.interfaces',
    'BaseEvolutionaryOptimizer': '.interfaces',
    'BaseFederatedLearner': '.interfaces',
    'BaseHyperparameterOptimizer': '.interfaces',
    'BaseMetaLearner': '.interfaces',
    'BaseMultitaskLearner': '.interfaces',
    'BaseNASOptimizer': '.interfaces',
    'BaseReinforcementLearner': '.interfaces',
    'BaseSelfSupervisedLearner': '.interfaces',
    'BaseTransferLearner': '.interfaces',
    'BaseLearningPipeline': '.interfaces',
    'BaseCallback': '.interfaces',
    'BaseQuerySampler': '.interfaces',
    'BaseDefense': '.interfaces',
    'BaseDomainAdapter': '.interfaces',
    'BaseAggregationStrategy': '.interfaces',

    # Exceptions
    'LearningBaseException': '.exceptions',
    'LearningError': '.exceptions',
    'LearnerNotFoundError': '.exceptions',
    'LearnerInitializationError': '.exceptions',
    'LearnerConfigurationError': '.exceptions',
    'OptimizationFailedError': '.exceptions',
    'ConvergenceError': '.exceptions',
    'StrategyNotSupportedError': '.exceptions',
    'SamplingError': '.exceptions',
    'AdversarialAttackError': '.exceptions',
    'CausalDiscoveryError': '.exceptions',
    'ContinualLearningError': '.exceptions',
    'EnsembleError': '.exceptions',
    'EvolutionaryError': '.exceptions',
    'FederatedLearningError': '.exceptions',
    'FederatedAggregationError': '.exceptions',
    'HyperparameterOptimizationError': '.exceptions',
    'MetaLearningError': '.exceptions',
    'MultiTaskLearningError': '.exceptions',
    'NASError': '.exceptions',
    'ArchitectureSearchError': '.exceptions',
    'ReinforcementLearningError': '.exceptions',
    'SelfSupervisedError': '.exceptions',
    'TransferLearningError': '.exceptions',
    'PipelineExecutionError': '.exceptions',
    'PipelineError': '.exceptions',

    # Types & Enums
    'LearningParadigm': '.types',
    'LearningStrategyType': '.types',
    'LearningStatus': '.types',
    'ActiveLearningStrategy': '.types',
    'UncertaintyMeasure': '.types',
    'QueryStrategy': '.types',
    'SamplingStrategy': '.types',
    'LearningMode': '.types',
    'AdaptiveLearningStrategy': '.types',
    'AdversarialAttackType': '.types',
    'AdversarialMethod': '.types',
    'GANType': '.types',
    'DefenseStrategy': '.types',
    'AcquisitionFunction': '.types',
    'KernelType': '.types',
    'OptimizationStrategy': '.types',
    'OptimizationMetric': '.types',
    'CausalMethod': '.types',
    'CausalEffectType': '.types',
    'CLStrategy': '.types',
    'ContinualStrategy': '.types',
    'ReplayStrategy': '.types',
    'MemoryType': '.types',
    'EnsembleStrategy': '.types',
    'VotingStrategy': '.types',
    'BoostingMethod': '.types',
    'AggregationMethod': '.types',
    'FederatedAggregationMethod': '.types',
    'ClientSelectionStrategy': '.types',
    'PrivacyLevel': '.types',
    'HpoAlgorithm': '.types',
    'SamplerType': '.types',
    'PrunerType': '.types',
    'MetaLearningAlgorithm': '.types',
    'TaskDistribution': '.types',
    'TaskType': '.types',
    'TaskRelationship': '.types',
    'SharingStrategy': '.types',
    'SearchStrategy': '.types',
    'RLAlgorithm': '.types',
    'EnvironmentType': '.types',
    'SSLMethod': '.types',
    'PretextTaskType': '.types',
    'ContrastiveLossType': '.types',
    'TransferStrategy': '.types',
    'DomainAdaptationMethod': '.types',
    'KnowledgeDistillationType': '.types',
    'DistillationMethod': '.types',

    # Results & Telemetry
    'StepState': '.types',
    'LearningMetrics': '.types',
    'OptimizationResult': '.types',
    'QueryResult': '.types',
    'ActiveLearningResult': '.types',
    'CausalEffectResult': '.types',
    'FederatedRoundResult': '.types',
    'DefenseResult': '.types',
    'NASResult': '.types',
    'HPOExperimentResult': '.types',
    'PipelineStageResult': '.types',

    # Configs
    'LearningConfig': '.types',
    'ActiveLearningConfig': '.types',
    'AdaptiveLearningConfig': '.types',
    'AdversarialConfig': '.types',
    'BayesianOptimizationConfig': '.types',
    'BayesianConfig': '.types',
    'CausalConfig': '.types',
    'ContinualLearningConfig': '.types',
    'ContinualConfig': '.types',
    'EnsembleConfig': '.types',
    'EvolutionaryConfig': '.types',
    'FederatedLearningConfig': '.types',
    'FederatedConfig': '.types',
    'HpoConfig': '.types',
    'HPOConfig': '.types',
    'MetaLearningConfig': '.types',
    'MultiTaskConfig': '.types',
    'NASConfig': '.types',
    'RLConfig': '.types',
    'SSLConfig': '.types',
    'TransferLearningConfig': '.types',
    'LearningPipelineConfig': '.types',

    # Registry & Pipeline
    'LearningModuleEntry': '.registry',
    'LearningRegistry': '.registry',
    'LEARNING_REGISTRY': '.registry',
    'learning_registry': '.registry',
    'register_learning_module': '.registry',
    'list_available_learning_modules': '.registry',
    'get_learning_module_info': '.registry',
    'create_learning_module': '.registry',
    'create_learner': '.registry',
    'create_learning_optimizer': '.factory',
    'create_learning_config': '.factory',
    'LEARNING_MODULE_REGISTRY': '.registry',
    'PipelineStage': '.pipeline',
    'LearningPipeline': '.pipeline',
    'CompositeLearningPipeline': '.pipeline',
    'PipelineResult': '.pipeline',
    'PipelineConfig': '.config',
    'LearningPipelineBuilder': '.pipeline',
    'create_pipeline_builder': '.pipeline',
    'create_learning_pipeline': '.pipeline',

    # Submodules
    'active_learning': '.active_learning',
    'adaptive_learning': '.adaptive_learning',
    'adversarial_learning': '.adversarial_learning',
    'bayesian_optimization': '.bayesian_optimization',
    'causal_inference': '.causal_inference',
    'continual_learning': '.continual_learning',
    'ensemble_learning': '.ensemble_learning',
    'evolutionary_computing': '.evolutionary_computing',
    'federated_learning': '.federated_learning',
    'hyperparameter_optimization': '.hyperparameter_optimization',
    'meta_learning': '.meta_learning',
    'multitask_learning': '.multitask_learning',
    'reinforcement_learning': '.reinforcement_learning',
    'self_supervised_learning': '.self_supervised_learning',
    'transfer_learning': '.transfer_learning',

    # 1. Active Learning
    'ActiveLearner': '.active_learning',
    'ActiveLearningSystem': '.active_learning',
    'UncertaintySampler': '.active_learning',
    'DiversitySampler': '.active_learning',
    'QueryByCommittee': '.active_learning',
    'ExpectedModelChange': '.active_learning',
    'BatchActiveLearning': '.active_learning',
    'create_active_learning_system': '.active_learning',

    # 2. Adaptive Learning
    'AdaptiveLearner': '.adaptive_learning',
    'AdaptiveLearningSystem': '.adaptive_learning',
    'PerformanceTracker': '.adaptive_learning',
    'SelfImprovementEngine': '.adaptive_learning',
    'create_adaptive_learning_system': '.adaptive_learning',

    # 3. Adversarial Learning
    'AdversarialLearner': '.adversarial_learning',
    'AdversarialLearningSystem': '.adversarial_learning',
    'AdversarialAttacker': '.adversarial_learning',
    'AdversarialDefense': '.adversarial_learning',
    'GANGenerator': '.adversarial_learning',
    'GANDiscriminator': '.adversarial_learning',
    'GANTrainer': '.adversarial_learning',
    'RobustnessAnalyzer': '.adversarial_learning',
    'create_adversarial_learning_system': '.adversarial_learning',

    # 4. Bayesian Optimization
    'BayesianOptimizer': '.bayesian_optimization',
    'GaussianProcessModel': '.bayesian_optimization',
    'AcquisitionFunctionOptimizer': '.bayesian_optimization',
    'create_bayesian_optimizer': '.bayesian_optimization',

    # 5. Causal Inference
    'CausalInference': '.causal_inference',
    'CausalInferenceSystem': '.causal_inference',
    'CausalDiscovery': '.causal_inference',
    'CausalEffectEstimator': '.causal_inference',
    'SensitivityAnalyzer': '.causal_inference',
    'RobustnessChecker': '.causal_inference',
    'create_causal_inference_system': '.causal_inference',

    # 6. Continual Learning
    'ContinualLearner': '.continual_learning',
    'CLTrainer': '.continual_learning',
    'LifelongLearner': '.continual_learning',
    'EWC': '.continual_learning',
    'ReplayBuffer': '.continual_learning',
    'ProgressiveNetwork': '.continual_learning',
    'create_cl_trainer': '.continual_learning',

    # 7. Ensemble Learning
    'EnsembleLearner': '.ensemble_learning',
    'EnsembleTrainer': '.ensemble_learning',
    'VotingEnsemble': '.ensemble_learning',
    'StackingEnsemble': '.ensemble_learning',
    'BaggingEnsemble': '.ensemble_learning',
    'BoostingEnsemble': '.ensemble_learning',
    'DynamicEnsemble': '.ensemble_learning',
    'create_ensemble_trainer': '.ensemble_learning',

    # 8. Evolutionary Computing
    'EvolutionaryOptimizer': '.evolutionary_computing',
    'create_evolutionary_optimizer': '.evolutionary_computing',

    # 9. Federated Learning
    'FederatedLearner': '.federated_learning',
    'FederatedLearningSystem': '.federated_learning',
    'FederatedClient': '.federated_learning',
    'FederatedServer': '.federated_learning',
    'AsyncFederatedServer': '.federated_learning',
    'create_federated_learning_system': '.federated_learning',

    # 10. Hyperparameter Optimization
    'HyperparameterOptimizer': '.hyperparameter_optimization',
    'HpoManager': '.hyperparameter_optimization',
    'TPEOptimizer': '.hyperparameter_optimization',
    'CMAESOptimizer': '.hyperparameter_optimization',
    'OptunaOptimizer': '.hyperparameter_optimization',
    'create_hpo_manager': '.hyperparameter_optimization',

    # 11. Meta Learning
    'MetaLearner': '.meta_learning',
    'MAML': '.meta_learning',
    'Reptile': '.meta_learning',
    'TaskGenerator': '.meta_learning',
    'create_meta_learner': '.meta_learning',

    # 12. Multitask Learning
    'MultitaskLearner': '.multitask_learning',
    'MultiTaskTrainer': '.multitask_learning',
    'MultiTaskNetwork': '.multitask_learning',
    'TaskBalancer': '.multitask_learning',
    'GradientSurgery': '.multitask_learning',
    'create_multitask_trainer': '.multitask_learning',

    # 13. NAS
    'NASOptimizer': '.nas',
    'EvolutionaryNAS': '.nas',
    'DifferentiableNAS': '.nas',
    'create_evolutionary_nas': '.nas',

    # 14. Reinforcement Learning
    'ReinforcementLearner': '.reinforcement_learning',
    'RLTrainingManager': '.reinforcement_learning',
    'DQNAgent': '.reinforcement_learning',
    'PPOAgent': '.reinforcement_learning',
    'create_rl_training_manager': '.reinforcement_learning',

    # 15. Self-Supervised Learning
    'SelfSupervisedLearner': '.self_supervised_learning',
    'SSLTrainer': '.self_supervised_learning',
    'ContrastiveLearner': '.self_supervised_learning',
    'RepresentationLearner': '.self_supervised_learning',
    'create_ssl_trainer': '.self_supervised_learning',

    # 16. Transfer Learning
    'TransferLearner': '.transfer_learning',
    'TransferTrainer': '.transfer_learning',
    'FineTuner': '.transfer_learning',
    'FeatureExtractor': '.transfer_learning',
    'KnowledgeDistiller': '.transfer_learning',
    'DomainAdapter': '.transfer_learning',
    'create_transfer_trainer': '.transfer_learning',
}

_import_cache: Dict[str, Any] = {}
_cache_lock = threading.RLock()


def __getattr__(name: str) -> Any:
    """Lazy import system for learning modules."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    if name not in _LAZY_IMPORTS:
        available = sorted(list(_LAZY_IMPORTS.keys()))[:10]
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'. "
            f"Available: {', '.join(available)}..."
        )

    with _cache_lock:
        if name in _import_cache:
            return _import_cache[name]

        module_path = _LAZY_IMPORTS[name]
        pkg = __name__
        try:
            module = importlib.import_module(module_path, pkg)
            obj = getattr(module, name)
            _import_cache[name] = obj
            return obj
        except (ImportError, AttributeError) as e:
            # Fallback across alternate namespace root (learning vs optimization_core.learning)
            try:
                rel = module_path.lstrip('.')
                alt_mod = f"optimization_core.learning.{rel}" if "optimization_core" not in pkg else f"learning.{rel}"
                module = importlib.import_module(alt_mod)
                obj = getattr(module, name)
                _import_cache[name] = obj
                return obj
            except Exception:
                raise AttributeError(
                    f"module '{__name__}' has no attribute '{name}'. "
                    f"Failed to import from '{module_path}': {e}"
                ) from e


def __dir__() -> List[str]:
    """Directory listing for dynamic inspection and tab completion."""
    return sorted(list(globals().keys()) + list(_LAZY_IMPORTS.keys()))


__all__ = list(_LAZY_IMPORTS.keys()) + [
    '__version__',
    '__all__',
]
