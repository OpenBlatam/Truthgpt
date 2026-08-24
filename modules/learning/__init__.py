"""
Learning Module for TruthGPT Optimization Core
==============================================
Provides lazy imports for all modular learning packages and components.
"""
from optimization_core.utils.dependency_manager import resolve_lazy_import

_LAZY_IMPORTS = {
    # 1. Evolutionary
    'EvolutionaryOptimizer': '.evolutionary',
    'EvolutionaryConfig': '.evolutionary',
    'evolutionary_computing': '.evolutionary',
    
    # 2. Causal
    'CausalInferenceSystem': '.causal',
    'CausalInferenceEngine': '.causal',
    'CausalConfig': '.causal',
    'causal_inference': '.causal',
    
    # 3. Active
    'ActiveLearningSystem': '.active',
    'ActiveLearner': '.active',
    'ActiveLearningConfig': '.active',
    'ActiveLearningStrategy': '.active',
    'UncertaintyMeasure': '.active',
    'active_learning': '.active',
    
    # 4. Adaptive
    'AdaptiveLearningSystem': '.adaptive',
    'AdaptiveLearner': '.adaptive',
    'AdaptiveLearningConfig': '.adaptive',
    'AdaptiveLearningStrategy': '.adaptive',
    'adaptive_learning': '.adaptive',
    
    # 5. Adversarial
    'AdversarialLearningSystem': '.adversarial',
    'AdversarialLearner': '.adversarial',
    'AdversarialConfig': '.adversarial',
    'adversarial_learning': '.adversarial',
    
    # 6. Bayesian
    'BayesianOptimizer': '.bayesian',
    'BayesianConfig': '.bayesian',
    'BayesianOptimizationConfig': '.bayesian',
    'bayesian_optimization': '.bayesian',
    
    # 7. Continual
    'ContinualLearner': '.continual',
    'ContinualConfig': '.continual',
    'continual_learning': '.continual',
    
    # 8. Ensemble
    'EnsembleManager': '.ensemble',
    'EnsembleLearner': '.ensemble',
    'EnsembleConfig': '.ensemble',
    'ensemble_learning': '.ensemble',
    
    # 9. Federated
    'FederatedServer': '.federated',
    'FederatedLearner': '.federated',
    'FederatedConfig': '.federated',
    'federated_learning': '.federated',
    
    # 10. HPO
    'HyperparameterOptimizer': '.hpo',
    'HPOConfig': '.hpo',
    'hyperparameter_optimization': '.hpo',
    
    # 11. Meta
    'MetaLearner': '.meta',
    'MetaConfig': '.meta',
    'meta_learning': '.meta',
    
    # 12. Multitask
    'MultitaskModel': '.multitask',
    'MultitaskLearner': '.multitask',
    'MultitaskConfig': '.multitask',
    'multitask_learning': '.multitask',
    
    # 13. NAS
    'NeuralArchitectureSearch': '.nas',
    'NASOptimizer': '.nas',
    'NASConfig': '.nas',
    'nas': '.nas',
    
    # 14. Reinforcement
    'RLSystem': '.reinforcement',
    'ReinforcementLearner': '.reinforcement',
    'RLConfig': '.reinforcement',
    'reinforcement_learning': '.reinforcement',
    
    # 15. Self-Supervised
    'SelfSupervisedTrainer': '.self_supervised',
    'SelfSupervisedLearner': '.self_supervised',
    'SelfSupervisedConfig': '.self_supervised',
    'self_supervised_learning': '.self_supervised',
    
    # 16. Transfer
    'TransferLearningManager': '.transfer',
    'TransferLearner': '.transfer',
    'TransferLearningConfig': '.transfer',
    'transfer_learning': '.transfer',
}

def __getattr__(name: str):
    return resolve_lazy_import(name, __package__ or 'learning', _LAZY_IMPORTS)

def __dir__():
    return list(_LAZY_IMPORTS.keys())

__all__ = list(_LAZY_IMPORTS.keys())
