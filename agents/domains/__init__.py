"""
TruthGPT Domain Agents Subpackage.

Provides specialized domain agents for Blockchain, Code Execution, Data Analysis,
Embodied RL, Formal Verification, Marketing Intelligence, Messaging, System Intelligence,
and Google ADK (Gemini 2.5 Pro native agents via google-adk).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Submodules
from . import (
    blockchain,
    code_interpreter,
    data_analysis,
    embodied_rl,
    formal_verification,
    google_adk,
    intelligence,
    marketing_intelligence,
    messaging,
    system_intelligence,
)

# Re-export domain agent implementations directly
from .code_interpreter import CodeInterpreterAgent
from .data_analysis import DataAnalysisAgent
from .embodied_rl.rl_agent import RLAgent
from .formal_verification.math_agent import MathAgent
from .marketing_intelligence.marketing_agent import MarketingAgent
from .system_intelligence.research_agent import ResearchAgent
from .system_intelligence.system_agent import SystemAgent
from .blockchain.blockchain_agent import BlockchainAgent
from .google_adk import (
    ADKGeminiAgent,
    ADKResearchAgent,
    ADKCodeAgent,
    ADKOrchestratorAgent,
    adk_tool,
)

__all__ = [
    # Submodules
    "blockchain",
    "code_interpreter",
    "data_analysis",
    "embodied_rl",
    "formal_verification",
    "intelligence",
    "marketing_intelligence",
    "messaging",
    "system_intelligence",
    # Agent Implementations
    "CodeInterpreterAgent",
    "DataAnalysisAgent",
    "RLAgent",
    "MathAgent",
    "MarketingAgent",
    "ResearchAgent",
    "SystemAgent",
    "BlockchainAgent",
    # Google ADK agents
    "google_adk",
    "ADKGeminiAgent",
    "ADKResearchAgent",
    "ADKCodeAgent",
    "ADKOrchestratorAgent",
    "adk_tool",
]
