"""
Modular Expert Management System
Specialized modules for expert creation, management, and optimization.
"""

from .base_expert import BaseExpert, ExpertConfig, ExpertResult
from .reasoning_expert import ReasoningExpert, ReasoningExpertConfig
from .computation_expert import ComputationExpert, ComputationExpertConfig
from .mathematical_expert import MathematicalExpert, MathematicalExpertConfig
from .language_expert import LanguageExpert, LanguageExpertConfig
from .creative_expert import CreativeExpert, CreativeExpertConfig
from .analytical_expert import AnalyticalExpert, AnalyticalExpertConfig
from .specialized_expert import SpecializedExpert, SpecializedExpertConfig
from .expert_pool import ExpertPool, ExpertPoolConfig
from .expert_optimizer import ExpertOptimizer, ExpertOptimizerConfig
from .expert_factory import ExpertFactory, create_expert, create_expert_pool
from .expert_registry import ExpertRegistry, register_expert, get_expert

__all__ = [
    # Base Expert
    'BaseExpert',
    'ExpertConfig',
    'ExpertResult',
    
    # Specialized Experts
    'ReasoningExpert',
    'ReasoningExpertConfig',
    'ComputationExpert',
    'ComputationExpertConfig',
    'MathematicalExpert',
    'MathematicalExpertConfig',
    'LanguageExpert',
    'LanguageExpertConfig',
    'CreativeExpert',
    'CreativeExpertConfig',
    'AnalyticalExpert',
    'AnalyticalExpertConfig',
    'SpecializedExpert',
    'SpecializedExpertConfig',
    
    # Expert Management
    'ExpertPool',
    'ExpertPoolConfig',
    'ExpertOptimizer',
    'ExpertOptimizerConfig',
    
    # Factory and Registry
    'ExpertFactory',
    'create_expert',
    'create_expert_pool',
    'ExpertRegistry',
    'register_expert',
    'get_expert'
]




