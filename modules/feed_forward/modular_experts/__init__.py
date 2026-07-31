"""
Modular Expert Management System
Specialized modules for expert creation, management, and optimization.
"""

from .base_expert import BaseExpert, ExpertConfig, ExpertResult, ExpertType
from .reasoning_expert import ReasoningExpert, ReasoningExpertConfig

ComputationExpert = None
ComputationExpertConfig = None
MathematicalExpert = None
MathematicalExpertConfig = None
LanguageExpert = None
LanguageExpertConfig = None
CreativeExpert = None
CreativeExpertConfig = None
AnalyticalExpert = None
AnalyticalExpertConfig = None
SpecializedExpert = None
SpecializedExpertConfig = None
ExpertPool = None
ExpertPoolConfig = None
ExpertOptimizer = None
ExpertOptimizerConfig = None
ExpertFactory = None
create_expert = None
create_expert_pool = None
ExpertRegistry = None
register_expert = None
get_expert = None

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




