"""
Neural Compiler Module for TruthGPT
Advanced neural-guided compilation with machine learning optimization
"""

from .neural_compiler import (
    NeuralCompiler, NeuralCompilationConfig, NeuralCompilationResult,
    NeuralCompilationMode, NeuralOptimizationStrategy, NeuralCompilationTarget,
    create_neural_compiler, neural_compilation_context
)
from .architecture_search import NeuralAttentionMechanism, NeuralMemoryNetwork, QuantumNeuralLayer
from .rl_optimizer import RLOptimizer
from .meta_learning import MetaLearningEngine

__all__ = [
    'NeuralCompiler',
    'NeuralCompilationConfig',
    'NeuralCompilationResult',
    'NeuralCompilationMode',
    'NeuralOptimizationStrategy',
    'NeuralCompilationTarget',
    'NeuralAttentionMechanism',
    'NeuralMemoryNetwork',
    'QuantumNeuralLayer',
    'RLOptimizer',
    'MetaLearningEngine',
    'create_neural_compiler',
    'neural_compilation_context'
]

__version__ = "1.0.0"


