"""
Unified Learning Strategies & Autonomous Optimization Subsystem
===============================================================
Provides centralized access to 16 state-of-the-art machine learning paradigms:
- Active Learning (Uncertainty & Diversity Sampling, Query by Committee)
- Adaptive Learning (Concept Drift Detection, Self-Improving Meta-Loops)
- Adversarial Learning (FGSM, PGD, GANs, Certified Defenses)
- Bayesian Optimization (Gaussian Process Surrogates, Acquisition Functions)
- Causal Inference (DAG Discovery, Propensity Matching, Instrumental Variables)
- Continual Learning (EWC, Experience Replay, Progressive Networks)
- Ensemble Learning (Voting, Stacking, Bagging, Dynamic Weighting)
- Evolutionary Computing (Genetic Algorithms, ES, CMA-ES)
- Federated Learning (FedAvg, Secure Aggregation, Privacy Preservation)
- Hyperparameter Optimization (TPE, Hyperband, Optuna, Multi-Objective)
- Meta-Learning (MAML, Reptile, Few-Shot Task Adaptation)
- Multi-Task Learning (Task Balancers, Gradient Surgery, Shared Heads)
- Neural Architecture Search (Evolutionary & Differentiable NAS)
- Reinforcement Learning (DQN, Dueling DQN, PPO, Multi-Agent)
- Self-Supervised Learning (SimCLR, InfoNCE, Momentum Encoders, Pretext)
- Transfer Learning (Fine-Tuning, Feature Extraction, Distillation, Domain Adaptation)

Also provides:
- Abstract Interfaces & Base Classes (`interfaces.py`)
- Hierarchical Typed Exceptions (`exceptions.py`)
- Dataclasses, Schemas & Enums (`types.py`)
- Thread-Safe Component Discovery & Factory (`registry.py`)
- Declarative Fluent Pipeline Orchestrator (`pipeline.py`)
"""

from __future__ import annotations

import sys
import threading
import importlib
from typing import Any, Dict, List, Optional, Union

__version__ = "2.5.0"

# Thread-safe cache and synchronization lock
_import_cache: Dict[str, Any] = {}
_cache_lock = threading.RLock()

# Central lazy-loading mapping table
_LAZY_IMPORTS: Dict[str, str] = {
    # ── Core Infrastructure ───────────────────────────────────────────
    # Interfaces
    "BaseLearner": ".interfaces",
    "BaseLearningOptimizer": ".interfaces",
    "BaseSampler": ".interfaces",
    "BaseActiveLearner": ".interfaces",
    "BaseAdaptiveLearner": ".interfaces",
    "BaseAdversarialLearner": ".interfaces",
    "BaseBayesianOptimizer": ".interfaces",
    "BaseCausalInference": ".interfaces",
    "BaseContinualLearner": ".interfaces",
    "BaseEnsembleLearner": ".interfaces",
    "BaseEvolutionaryOptimizer": ".interfaces",
    "BaseFederatedLearner": ".interfaces",
    "BaseHyperparameterOptimizer": ".interfaces",
    "BaseMetaLearner": ".interfaces",
    "BaseMultitaskLearner": ".interfaces",
    "BaseNASOptimizer": ".interfaces",
    "BaseReinforcementLearner": ".interfaces",
    "BaseSelfSupervisedLearner": ".interfaces",
    "BaseTransferLearner": ".interfaces",
    "BaseLearningPipeline": ".interfaces",

    # Exceptions
    "LearningBaseException": ".exceptions",
    "LearningError": ".exceptions",
    "LearnerNotFoundError": ".exceptions",
    "LearnerInitializationError": ".exceptions",
    "LearnerConfigurationError": ".exceptions",
    "OptimizationFailedError": ".exceptions",
    "ConvergenceError": ".exceptions",
    "StrategyNotSupportedError": ".exceptions",
    "SamplingError": ".exceptions",
    "AdversarialAttackError": ".exceptions",
    "CausalDiscoveryError": ".exceptions",
    "FederatedAggregationError": ".exceptions",
    "ArchitectureSearchError": ".exceptions",
    "PipelineError": ".exceptions",

    # Types & Dataclasses
    "LearningStrategyType": ".types",
    "UncertaintyMeasure": ".types",
    "SamplingStrategy": ".types",
    "AdversarialMethod": ".types",
    "OptimizationMetric": ".types",
    "TaskType": ".types",
    "FederatedAggregationMethod": ".types",
    "DistillationMethod": ".types",
    "ContinualStrategy": ".types",
    "LearningMetrics": ".types",
    "OptimizationResult": ".types",
    "ActiveLearningResult": ".types",
    "CausalEffectResult": ".types",
    "FederatedRoundResult": ".types",
    "NASResult": ".types",
    "LearningConfig": ".types",
    "ActiveLearningConfig": ".types",
    "AdaptiveLearningConfig": ".types",
    "AdversarialConfig": ".types",
    "BayesianConfig": ".types",
    "CausalConfig": ".types",
    "ContinualConfig": ".types",
    "EnsembleConfig": ".types",
    "EvolutionaryConfig": ".types",
    "FederatedConfig": ".types",
    "HPOConfig": ".types",
    "MetaLearningConfig": ".types",
    "MultiTaskConfig": ".types",
    "NASConfig": ".types",
    "RLConfig": ".types",
    "SSLConfig": ".types",
    "TransferLearningConfig": ".types",
    "LearningPipelineConfig": ".types",

    # Registry & Factories
    "LearningRegistry": ".registry",
    "learning_registry": ".registry",
    "LEARNING_REGISTRY": ".registry",
    "LearningModuleEntry": ".registry",
    "register_learning_module": ".registry",
    "list_available_learning_modules": ".registry",
    "get_learning_module_info": ".registry",
    "create_learning_module": ".factory",
    "create_learner": ".factory",
    "create_learning_optimizer": ".factory",
    "create_learning_config": ".factory",

    # Pipeline Builder
    "LearningPipeline": ".pipeline",
    "CompositeLearningPipeline": ".pipeline",
    "PipelineStage": ".pipeline",
    "PipelineResult": ".pipeline",
    "PipelineConfig": ".config",
    "LearningPipelineBuilder": ".pipeline",
    "create_pipeline_builder": ".pipeline",
    "create_learning_pipeline": ".pipeline",

    # ── 1. Active Learning ───────────────────────────────────────────
    "ActiveLearner": ".active_learning",
    "ActiveLearningStrategy": ".active_learning",
    "ActiveLearningSystem": ".active_learning",
    "UncertaintySampler": ".active_learning",
    "DiversitySampler": ".active_learning",
    "QueryByCommittee": ".active_learning",
    "create_active_learning_system": ".active_learning",

    # ── 2. Adaptive Learning ─────────────────────────────────────────
    "AdaptiveLearner": ".adaptive_learning",
    "AdaptiveLearningStrategy": ".adaptive_learning",
    "AdaptiveLearningSystem": ".adaptive_learning",
    "PerformanceTracker": ".adaptive_learning",
    "SelfImprovementEngine": ".adaptive_learning",
    "create_adaptive_learning_system": ".adaptive_learning",

    # ── 3. Adversarial Learning ──────────────────────────────────────
    "AdversarialLearner": ".adversarial_learning",
    "AdversarialLearningSystem": ".adversarial_learning",
    "AdversarialAttacker": ".adversarial_learning",
    "AdversarialDefense": ".adversarial_learning",
    "RobustnessAnalyzer": ".adversarial_learning",
    "create_adversarial_learning_system": ".adversarial_learning",

    # ── 4. Bayesian Optimization ─────────────────────────────────────
    "BayesianOptimizer": ".bayesian_optimization",
    "GaussianProcessModel": ".bayesian_optimization",
    "AcquisitionFunctionOptimizer": ".bayesian_optimization",
    "create_bayesian_optimizer": ".bayesian_optimization",

    # ── 5. Causal Inference ──────────────────────────────────────────
    "CausalInference": ".causal_inference",
    "CausalInferenceEngine": ".causal_inference",
    "CausalInferenceSystem": ".causal_inference",
    "CausalDiscovery": ".causal_inference",
    "CausalEffectEstimator": ".causal_inference",
    "create_causal_inference_system": ".causal_inference",

    # ── 6. Continual Learning ────────────────────────────────────────
    "ContinualLearner": ".continual_learning",
    "CLTrainer": ".continual_learning",
    "EWC": ".continual_learning",
    "ReplayBuffer": ".continual_learning",
    "ProgressiveNetwork": ".continual_learning",
    "create_cl_trainer": ".continual_learning",

    # ── 7. Ensemble Learning ─────────────────────────────────────────
    "EnsembleLearner": ".ensemble_learning",
    "EnsembleManager": ".ensemble_learning",
    "EnsembleTrainer": ".ensemble_learning",
    "VotingEnsemble": ".ensemble_learning",
    "StackingEnsemble": ".ensemble_learning",
    "DynamicEnsemble": ".ensemble_learning",
    "create_ensemble_trainer": ".ensemble_learning",

    # ── 8. Evolutionary Computing ────────────────────────────────────
    "EvolutionaryOptimizer": ".evolutionary_computing",
    "Individual": ".evolutionary_computing",
    "Population": ".evolutionary_computing",
    "create_evolutionary_optimizer": ".evolutionary_computing",

    # ── 9. Federated Learning ────────────────────────────────────────
    "FederatedLearner": ".federated_learning",
    "FederatedLearningSystem": ".federated_learning",
    "FederatedServer": ".federated_learning",
    "FederatedClient": ".federated_learning",
    "create_federated_learning_system": ".federated_learning",

    # ── 10. Hyperparameter Optimization ──────────────────────────────
    "HyperparameterOptimizer": ".hyperparameter_optimization",
    "HpoManager": ".hyperparameter_optimization",
    "TPEOptimizer": ".hyperparameter_optimization",
    "OptunaOptimizer": ".hyperparameter_optimization",
    "create_hpo_manager": ".hyperparameter_optimization",

    # ── 11. Meta Learning ────────────────────────────────────────────
    "MetaLearner": ".meta_learning",
    "MAML": ".meta_learning",
    "Reptile": ".meta_learning",
    "create_meta_learner": ".meta_learning",

    # ── 12. Multi-Task Learning ──────────────────────────────────────
    "MultitaskLearner": ".multitask_learning",
    "MultitaskModel": ".multitask_learning",
    "MultiTaskNetwork": ".multitask_learning",
    "MultiTaskTrainer": ".multitask_learning",
    "create_multitask_trainer": ".multitask_learning",

    # ── 13. Neural Architecture Search ───────────────────────────────
    "NASOptimizer": ".nas",
    "NeuralArchitectureSearch": ".nas",
    "EvolutionaryNAS": ".nas",
    "DifferentiableNAS": ".nas",
    "create_evolutionary_nas": ".nas",

    # ── 14. Reinforcement Learning ───────────────────────────────────
    "ReinforcementLearner": ".reinforcement_learning",
    "RLSystem": ".reinforcement_learning",
    "RLTrainingManager": ".reinforcement_learning",
    "DQNAgent": ".reinforcement_learning",
    "PPOAgent": ".reinforcement_learning",
    "create_rl_training_manager": ".reinforcement_learning",

    # ── 15. Self-Supervised Learning ─────────────────────────────────
    "SelfSupervisedLearner": ".self_supervised_learning",
    "SelfSupervisedTrainer": ".self_supervised_learning",
    "SSLTrainer": ".self_supervised_learning",
    "create_ssl_trainer": ".self_supervised_learning",

    # ── 16. Transfer Learning ────────────────────────────────────────
    "TransferLearner": ".transfer_learning",
    "TransferLearningManager": ".transfer_learning",
    "TransferTrainer": ".transfer_learning",
    "FineTuner": ".transfer_learning",
    "FeatureExtractor": ".transfer_learning",
    "KnowledgeDistiller": ".transfer_learning",
    "DomainAdapter": ".transfer_learning",
    "create_transfer_trainer": ".transfer_learning",
}


def _register_builtin_modules() -> None:
    """Pre-populate the learning registry with all 16 domains."""
    from .registry import LEARNING_REGISTRY
    
    domain_factories = {
        "active": lambda config=None, **kw: _lazy_load_symbol("create_active_learning_system")(config, **kw) if config else _lazy_load_symbol("ActiveLearner")(**kw),
        "adaptive": lambda config=None, **kw: _lazy_load_symbol("create_adaptive_learning_system")(config, **kw) if config else _lazy_load_symbol("AdaptiveLearner")(**kw),
        "adversarial": lambda config=None, **kw: _lazy_load_symbol("create_adversarial_learning_system")(config, **kw) if config else _lazy_load_symbol("AdversarialLearner")(**kw),
        "bayesian": lambda config=None, **kw: _lazy_load_symbol("create_bayesian_optimizer")(config, **kw) if config else _lazy_load_symbol("BayesianOptimizer")(**kw),
        "causal": lambda config=None, **kw: _lazy_load_symbol("create_causal_inference_system")(config, **kw) if config else _lazy_load_symbol("CausalInference")(**kw),
        "continual": lambda config=None, **kw: _lazy_load_symbol("create_cl_trainer")(config, **kw) if config else _lazy_load_symbol("ContinualLearner")(**kw),
        "ensemble": lambda config=None, **kw: _lazy_load_symbol("create_ensemble_trainer")(config, **kw) if config else _lazy_load_symbol("EnsembleLearner")(**kw),
        "evolutionary": lambda config=None, **kw: _lazy_load_symbol("create_evolutionary_optimizer")(config, **kw) if config else _lazy_load_symbol("EvolutionaryOptimizer")(**kw),
        "federated": lambda config=None, **kw: _lazy_load_symbol("create_federated_learning_system")(config, **kw) if config else _lazy_load_symbol("FederatedLearner")(**kw),
        "hpo": lambda config=None, **kw: _lazy_load_symbol("create_hpo_manager")(config, **kw) if config else _lazy_load_symbol("HyperparameterOptimizer")(**kw),
        "meta": lambda model=None, config=None, **kw: _lazy_load_symbol("create_meta_learner")(model, config, **kw) if (model and config) else _lazy_load_symbol("MetaLearner")(model, config, **kw),
        "multitask": lambda config=None, **kw: _lazy_load_symbol("create_multitask_trainer")(config, **kw) if config else _lazy_load_symbol("MultitaskLearner")(**kw),
        "nas": lambda config=None, **kw: _lazy_load_symbol("create_evolutionary_nas")(config, **kw) if config else _lazy_load_symbol("NASOptimizer")(**kw),
        "reinforcement": lambda config=None, **kw: _lazy_load_symbol("create_rl_training_manager")(config, **kw) if config else _lazy_load_symbol("ReinforcementLearner")(**kw),
        "self_supervised": lambda config=None, **kw: _lazy_load_symbol("create_ssl_trainer")(config, **kw) if config else _lazy_load_symbol("SelfSupervisedLearner")(**kw),
        "transfer": lambda config=None, **kw: _lazy_load_symbol("create_transfer_trainer")(config, **kw) if config else _lazy_load_symbol("TransferLearner")(**kw),
    }
    
    for name, factory in domain_factories.items():
        LEARNING_REGISTRY.register(
            name=name,
            factory_or_cls=factory,
            description=f"Unified factory for {name} learning module."
        )


def _lazy_load_symbol(name: str) -> Any:
    """Helper to lazily load a specific symbol without triggering full imports."""
    if name in _import_cache:
        return _import_cache[name]
        
    if name not in _LAZY_IMPORTS:
        available = sorted(_LAZY_IMPORTS.keys())[:10]
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'. "
            f"Available: {', '.join(available)}..."
        )

    module_path = _LAZY_IMPORTS[name]
    package_name = __package__ or "optimization_core.learning"
    
    try:
        module = importlib.import_module(module_path, package=package_name)
        obj = getattr(module, name)
        _import_cache[name] = obj
        return obj
    except (ImportError, AttributeError) as e:
        # Fallback to direct relative import if package context differs
        try:
            rel = module_path.lstrip('.')
            module = importlib.import_module(f"optimization_core.learning.{rel}")
            obj = getattr(module, name)
            _import_cache[name] = obj
            return obj
        except Exception:
            raise AttributeError(
                f"module '{__name__}' failed to lazy-load '{name}' from '{module_path}': {e}"
            ) from e


def __getattr__(name: str) -> Any:
    """Lazy import system for learning modules."""
    if name == "__version__":
        return __version__
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    with _cache_lock:
        return _lazy_load_symbol(name)


def __dir__() -> List[str]:
    """Directory listing for autocomplete and IDE support."""
    return sorted(list(set(list(globals().keys()) + list(_LAZY_IMPORTS.keys()))))


# Populate default registry entries
_register_builtin_modules()

# Dual module registration for backward compatibility
_curr_mod = sys.modules.get(__name__)
if _curr_mod:
    if __name__ == "optimization_core.learning":
        sys.modules["learning"] = _curr_mod
    elif __name__ == "learning":
        sys.modules["optimization_core.learning"] = _curr_mod

__all__ = [
    "__version__",
] + list(_LAZY_IMPORTS.keys())
