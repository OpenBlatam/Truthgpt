"""
Marketing AI Engine Package v5.0 Enterprise-SOTA
Full-funnel, multi-channel, persona-driven marketing system.
"""

from .knowledge import PERSONAS, CHANNEL_SPECS, FUNNEL_STAGES, CIALDINI_PRINCIPLES
from .models import ConsumerFatigueModel, CausalForestAttributor
from .generators import ContentGenerators
from .publisher import ProductionPublisher
from .connectors import AdPlatformManager
from .agents import (
    PersuasionCopywriterAgent,
    CausalForestAnalystAgent,
    BudgetOptimizerAgent
)
from .engine import IntegratedMarketingAITerminal

__all__ = [
    "PERSONAS",
    "CHANNEL_SPECS",
    "FUNNEL_STAGES",
    "CIALDINI_PRINCIPLES",
    "ConsumerFatigueModel",
    "CausalForestAttributor",
    "ContentGenerators",
    "ProductionPublisher",
    "AdPlatformManager",
    "PersuasionCopywriterAgent",
    "CausalForestAnalystAgent",
    "BudgetOptimizerAgent",
    "IntegratedMarketingAITerminal",
]
