"""
Ultra-Advanced TruthGPT Optimization Modules
Following deep learning best practices for maximum performance
"""

from .quantum_optimization import QuantumOptimizer, QuantumAttention, QuantumLayerNorm
from .neural_architecture_search import NASOptimizer, ArchitectureSearch, EfficientNetSearch
from .meta_learning import MetaLearner, MAML, Reptile, MetaOptimizer
from .reinforcement_learning import RLOptimizer, PolicyGradient, ActorCritic, PPO
from .evolutionary_optimization import EvolutionaryOptimizer, GeneticAlgorithm, DifferentialEvolution
from .bayesian_optimization import BayesianOptimizer, GaussianProcess, AcquisitionFunction
from .distributed_training import DistributedTrainer, HorovodTrainer, RayTrainer
from .model_compression import ModelCompressor, PruningOptimizer, KnowledgeDistillation
from .advanced_attention import SparseAttention, LinearAttention, PerformerAttention
from .memory_efficient import MemoryEfficientOptimizer, GradientCheckpointing, ActivationCheckpointing
from .hardware_optimization import HardwareOptimizer, TPUOptimizer, NPUOptimizer
from .profiling import AdvancedProfiler, MemoryProfiler, SpeedProfiler, EnergyProfiler

__all__ = [
    # Quantum optimization
    'QuantumOptimizer', 'QuantumAttention', 'QuantumLayerNorm',
    
    # Neural Architecture Search
    'NASOptimizer', 'ArchitectureSearch', 'EfficientNetSearch',
    
    # Meta learning
    'MetaLearner', 'MAML', 'Reptile', 'MetaOptimizer',
    
    # Reinforcement learning
    'RLOptimizer', 'PolicyGradient', 'ActorCritic', 'PPO',
    
    # Evolutionary optimization
    'EvolutionaryOptimizer', 'GeneticAlgorithm', 'DifferentialEvolution',
    
    # Bayesian optimization
    'BayesianOptimizer', 'GaussianProcess', 'AcquisitionFunction',
    
    # Distributed training
    'DistributedTrainer', 'HorovodTrainer', 'RayTrainer',
    
    # Model compression
    'ModelCompressor', 'PruningOptimizer', 'KnowledgeDistillation',
    
    # Advanced attention
    'SparseAttention', 'LinearAttention', 'PerformerAttention',
    
    # Memory efficient
    'MemoryEfficientOptimizer', 'GradientCheckpointing', 'ActivationCheckpointing',
    
    # Hardware optimization
    'HardwareOptimizer', 'TPUOptimizer', 'NPUOptimizer',
    
    # Profiling
    'AdvancedProfiler', 'MemoryProfiler', 'SpeedProfiler', 'EnergyProfiler'
]


