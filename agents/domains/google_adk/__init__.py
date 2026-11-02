"""
Google ADK Domain — Native Gemini agents via google-adk.

Exposes:
  - ADKGeminiAgent        : General-purpose Gemini 2.5 Pro agent
  - ADKResearchAgent      : Deep research / fact-checking agent
  - ADKCodeAgent          : Code generation & review agent
  - ADKOrchestratorAgent  : Multi-agent coordinator
  - adk_tool              : Decorator to register TruthGPT tools for ADK

Install requirement:
    pip install google-adk>=1.0.0
"""

from __future__ import annotations

from agents.domains.google_adk.adk_tools import adk_tool
from agents.domains.google_adk.adk_gemini_agent import ADKGeminiAgent
from agents.domains.google_adk.adk_research_agent import ADKResearchAgent
from agents.domains.google_adk.adk_code_agent import ADKCodeAgent
from agents.domains.google_adk.adk_orchestrator import ADKOrchestratorAgent

__all__ = [
    "adk_tool",
    "ADKGeminiAgent",
    "ADKResearchAgent",
    "ADKCodeAgent",
    "ADKOrchestratorAgent",
]
