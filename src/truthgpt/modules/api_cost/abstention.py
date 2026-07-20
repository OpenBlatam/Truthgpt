"""
Early Abstention for LLMs (System 5.9).

Based on:
- Early Abstention (arXiv:2502.09054)
"""

import logging
from typing import Tuple

logger = logging.getLogger("optimization.api_cost.abstention")

class EarlyAbstention:
    """
    Detects queries that are likely to fail or be unanswerable.
    Saves 100% of cost by not calling any LLM.
    """
    
    def __init__(self):
        self.risk_patterns = [
            (r"(?i)predict the future", "Future prediction is not supported"),
            (r"(?i)private information", "PII requests are blocked"),
            (r"(?i)hack into", "Illegal requests are blocked"),
        ]

    def check(self, prompt: str) -> Tuple[bool, str]:
        """
        Check if we should abstain from answering.
        Returns (should_abstain, reason).
        """
        if not prompt or len(prompt.strip()) < 2:
            return True, "Empty or too short prompt"
            
        # Basic pattern matching for early exit
        import re
        for pattern, reason in self.risk_patterns:
            if re.search(pattern, prompt):
                logger.warning("🚫 Early Abstention triggered: %s", reason)
                return True, reason
                
        return False, ""
