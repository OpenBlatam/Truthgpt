"""
ADKResearchAgent — Deep research and fact-checking agent via Google ADK.

Specializes in multi-step research tasks: decomposing questions,
searching sources, cross-validating claims, and producing cited answers.
Uses Gemini 2.5 Pro with extended thinking for complex research.

Usage::

    agent = ADKResearchAgent()
    report = await agent.arun(
        "What are the latest breakthroughs in protein folding AI?"
    )
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from agents.domains.google_adk.adk_gemini_agent import ADKGeminiAgent
from agents.domains.google_adk.adk_tools import adk_tool, get_adk_tools

logger = logging.getLogger(__name__)

_RESEARCH_INSTRUCTION = """
You are an expert research agent integrated into the TruthGPT platform.
Your job is to perform deep, multi-step research on any topic.

Research Protocol:
1. Decompose the question into sub-questions.
2. Answer each sub-question using available tools.
3. Cross-validate facts — flag contradictions.
4. Synthesize a structured final report with:
   - Executive Summary
   - Key Findings (with confidence levels: HIGH / MEDIUM / LOW)
   - Open Questions
   - Sources cited

Rules:
- Never fabricate facts or hallucinate citations.
- If information is unavailable, explicitly state it.
- Always separate established facts from inference.
- Label all confidence assessments.
""".strip()


# Research-specific tools
@adk_tool
def decompose_research_question(question: str) -> list:
    """
    Break a complex research question into focused sub-questions.

    Args:
        question: The main research question.

    Returns:
        A list of focused sub-questions to investigate.
    """
    # Lightweight heuristic decomposition (can be swapped for LLM-based)
    prefixes = [
        f"What is {question}?",
        f"What are the main components or aspects of {question}?",
        f"What are recent developments related to {question}?",
        f"What are the limitations or criticisms of {question}?",
        f"What are practical applications of {question}?",
    ]
    return prefixes


@adk_tool
def validate_claim(claim: str, evidence: str) -> dict:
    """
    Assess whether the provided evidence supports a claim.

    Args:
        claim:    The factual claim to validate.
        evidence: Text evidence to evaluate against the claim.

    Returns:
        Dict with 'supported' (bool) and 'confidence' (HIGH/MEDIUM/LOW/NONE).
    """
    claim_lower = claim.lower()
    evidence_lower = evidence.lower()
    # Overlap heuristic — replace with semantic similarity in production
    words = set(claim_lower.split())
    overlap = sum(1 for w in words if w in evidence_lower)
    ratio = overlap / max(len(words), 1)

    if ratio > 0.6:
        return {"supported": True, "confidence": "HIGH"}
    elif ratio > 0.3:
        return {"supported": True, "confidence": "MEDIUM"}
    elif ratio > 0.1:
        return {"supported": False, "confidence": "LOW"}
    else:
        return {"supported": False, "confidence": "NONE"}


class ADKResearchAgent(ADKGeminiAgent):
    """
    Specialized research agent built on ADKGeminiAgent.

    Adds research-specific tools (question decomposition, claim validation)
    and a research-optimized system prompt.
    """

    def __init__(
        self,
        name: str = "adk-research-agent",
        api_key: Optional[str] = None,
    ) -> None:
        # Research-specific tools are already registered via @adk_tool above
        super().__init__(
            name=name,
            instruction=_RESEARCH_INSTRUCTION,
            model="gemini-2.5-pro",
            api_key=api_key,
        )
        self.role = "gemini-adk-research"
