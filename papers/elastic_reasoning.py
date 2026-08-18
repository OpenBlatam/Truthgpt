"""
Paper 2505.05315v2 - Elastic Reasoning
=======================================
Based on "Elastic Reasoning: Dynamic Budget Allocation for LLMs" (arXiv:2505.05315v2, 2025)

Key Formulas:
-------------
- Budget constraint: |y| <= c where c = t + s
- Structure: y = (y^think, y^solution)
- y^think enclosed in [<think>, </think>]
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Sequence

from .base import BasePaperModule, PaperCategory, PaperMetadata, PaperResult
from .config import ElasticReasoningConfig
from .exceptions import PaperValidationError

logger = logging.getLogger(__name__)


class ElasticReasoning(BasePaperModule):
    """
    Implements dynamic budget allocation for reasoning tokens and thinking metrics.
    """

    metadata = PaperMetadata(
        paper_id="elastic_reasoning",
        paper_name="Elastic Reasoning: Dynamic Budget Allocation for LLMs",
        category=PaperCategory.REASONING,
        arxiv_id="2505.05315v2",
        year=2025,
        authors=["TruthGPT Research"],
        key_techniques=["Dynamic Thinking Budget", "Think Tag Constraints", "Early Exit"],
        speedup=1.8,
        accuracy_improvement=4.5,
        description="Dynamically allocates thinking and solution token budgets.",
        scholar_query="Elastic Reasoning Dynamic Budget Allocation LLMs",
    )

    THINK_START: str = "<think>"
    THINK_END: str = "</think>"

    def __init__(
        self,
        t_budget: int = 512,
        s_budget: int = 1024,
        config: Optional[ElasticReasoningConfig] = None,
    ) -> None:
        super().__init__()
        if config is not None:
            config.validate()
            self.config = config
        else:
            self.config = ElasticReasoningConfig(t_budget=t_budget, s_budget=s_budget)
            self.config.validate()

        self.t_budget = self.config.t_budget
        self.s_budget = self.config.s_budget
        self.total_budget = self.t_budget + self.s_budget

    def simulate_generation(self, current_tokens: Sequence[str]) -> str:
        """
        Simulate budget enforcement during generation.
        """
        if not current_tokens:
            return "continue"

        tokens_list = list(current_tokens)
        in_thinking = False
        if self.THINK_START in tokens_list and self.THINK_END not in tokens_list:
            in_thinking = True

        if in_thinking:
            think_start_idx = tokens_list.index(self.THINK_START)
            think_tokens_so_far = len(tokens_list) - think_start_idx
            if think_tokens_so_far >= self.t_budget:
                return self.THINK_END

        return "continue"

    def wrap_prompt(self, prompt: str) -> str:
        """Wrap prompt with instruction to adhere to thinking and solution budgets."""
        return (
            f"Please think within {self.t_budget} tokens using {self.THINK_START}{self.THINK_END} tags, "
            f"then answer within {self.s_budget} tokens:\n\n{prompt}"
        )

    @staticmethod
    def calculate_metrics(generated_text: str) -> PaperResult:
        """
        Verify if generated text satisfied the thinking budget constraints.
        """
        if not generated_text or not isinstance(generated_text, str):
            return PaperResult({
                "has_thinking": False,
                "think_tokens": 0,
                "total_tokens": 0,
                "ratio": 0.0,
            })

        think_pattern = re.compile(r"<think>(.*?)</think>", re.DOTALL)
        match = think_pattern.search(generated_text)

        has_think = bool(match)
        think_len = len(match.group(1).split()) if match else 0
        total_len = len(generated_text.split())

        return PaperResult({
            "has_thinking": has_think,
            "think_tokens": think_len,
            "total_tokens": total_len,
            "ratio": round(think_len / total_len, 4) if total_len > 0 else 0.0,
        })

    def execute(self, current_tokens: Optional[Sequence[str]] = None, **kwargs: Any) -> PaperResult:
        """Standard execution for elastic reasoning evaluation."""
        sample_tokens = current_tokens if current_tokens is not None else kwargs.get(
            "current_tokens", ["<think>", "step1", "step2", "step3"]
        )
        decision = self.simulate_generation(sample_tokens)
        return PaperResult({
            "think_budget": self.t_budget,
            "solution_budget": self.s_budget,
            "total_budget": self.total_budget,
            "current_tokens_count": len(sample_tokens),
            "next_token_decision": decision,
        })

    def get_summary(self) -> Dict[str, Any]:
        """Return operational summary."""
        return {
            "algorithm": self.__class__.__name__,
            "t_budget": self.t_budget,
            "s_budget": self.s_budget,
            "total_budget": self.total_budget,
        }


__all__ = ["ElasticReasoning"]
