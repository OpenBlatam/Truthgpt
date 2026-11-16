"""
ADKResearchAgent — Deep research and fact-checking agent via Google ADK.

Specializes in multi-step research tasks: decomposing questions,
searching sources, cross-validating claims, and producing cited answers.
Uses Gemini 2.5 Pro with a structured research protocol.

Usage::

    agent = ADKResearchAgent()
    report = await agent.process(
        "What are the latest breakthroughs in protein folding AI?"
    )
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from agents.domains.google_adk.adk_gemini_agent import ADKGeminiAgent
from agents.domains.google_adk.adk_tools import adk_tool

logger = logging.getLogger(__name__)

_RESEARCH_INSTRUCTION = """\
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
- Label all confidence assessments.\
"""


# ═══════════════════════════════════════════════════════════════════════════
# Research-domain tools
# ═══════════════════════════════════════════════════════════════════════════

_STOP_WORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "can", "could", "of", "in", "to", "for",
    "with", "on", "at", "from", "by", "as", "or", "and", "but", "not",
    "no", "so", "if", "it", "its", "that", "this", "what", "how",
})


@adk_tool(category="research")
def decompose_research_question(question: str) -> list:
    """Break a complex research question into focused sub-questions.

    Uses template-based decomposition across five analytical dimensions:
    definition, components, developments, criticisms, and applications.

    Args:
        question: The main research question.

    Returns:
        A list of focused sub-questions to investigate.
    """
    # Extract the core subject by stripping interrogative prefixes
    subject = re.sub(
        r"^(what|how|why|when|where|who|explain|describe|analyze)\s+(is|are|does|do|did|was|were)?\s*",
        "",
        question.strip().rstrip("?"),
        flags=re.IGNORECASE,
    ).strip() or question

    return [
        f"What is {subject} and how is it defined?",
        f"What are the key components, mechanisms, or principles of {subject}?",
        f"What are the most recent developments or breakthroughs related to {subject}?",
        f"What are the known limitations, criticisms, or open problems regarding {subject}?",
        f"What are the most impactful practical applications of {subject}?",
    ]


@adk_tool(category="research")
def validate_claim(claim: str, evidence: str) -> dict:
    """Assess whether the provided evidence supports a claim.

    Uses Jaccard-like token overlap with stop-word filtering for a
    lightweight heuristic.  Replace with an NLI model in production.

    Args:
        claim:    The factual claim to validate.
        evidence: Text evidence to evaluate against the claim.

    Returns:
        Dict with ``supported`` (bool), ``confidence``
        (HIGH / MEDIUM / LOW / NONE), and ``overlap_ratio`` (float).
    """
    def _tokenize(text: str) -> set:
        return {
            w for w in re.findall(r"\w+", text.lower())
            if w not in _STOP_WORDS and len(w) > 1
        }

    claim_tokens = _tokenize(claim)
    evidence_tokens = _tokenize(evidence)

    if not claim_tokens:
        return {"supported": False, "confidence": "NONE", "overlap_ratio": 0.0}

    intersection = claim_tokens & evidence_tokens
    ratio = len(intersection) / len(claim_tokens)

    if ratio >= 0.6:
        level = "HIGH"
    elif ratio >= 0.35:
        level = "MEDIUM"
    elif ratio >= 0.15:
        level = "LOW"
    else:
        level = "NONE"

    return {
        "supported": ratio >= 0.35,
        "confidence": level,
        "overlap_ratio": round(ratio, 3),
    }


@adk_tool(category="research")
def extract_key_entities(text: str) -> list:
    """Extract likely named entities (capitalised multi-word spans) from text.

    A zero-dependency heuristic — use a proper NER model for production.

    Args:
        text: The input text to analyse.

    Returns:
        De-duplicated list of capitalised entity-like spans.
    """
    # Match sequences of capitalised words (2+ chars each)
    spans = re.findall(r"\b(?:[A-Z][a-z]{1,}(?:\s+[A-Z][a-z]{1,})+)\b", text)
    seen: set = set()
    unique: list = []
    for s in spans:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


# ═══════════════════════════════════════════════════════════════════════════
# Agent class
# ═══════════════════════════════════════════════════════════════════════════

class ADKResearchAgent(ADKGeminiAgent):
    """
    Specialized research agent built on ``ADKGeminiAgent``.

    Inherits the full ``BaseAgent`` lifecycle and ADK session management.
    Adds research-specific tools (decomposition, claim validation,
    entity extraction) and a structured research system prompt.
    """

    def __init__(
        self,
        name: str = "adk-research-agent",
        model: str = "gemini-2.5-pro",
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__(
            name=name,
            role="gemini-adk-research",
            instruction=_RESEARCH_INSTRUCTION,
            model=model,
            api_key=api_key,
        )
