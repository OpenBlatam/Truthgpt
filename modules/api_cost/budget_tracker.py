"""
Token Budget Tracking & Cost Calculation (System 5.9).
"""

import json
import time
import os
import logging
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger("optimization.api_cost.budget")

@dataclass
class SpendMetrics:
    total_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    request_count: int = 0

class TokenCounter:
    """Estimates tokens from text with multi-lingual awareness."""
    
    @staticmethod
    def count(text: str) -> int:
        if not text: return 0
        # Improved heuristic: words + punctuation + special chars
        # English: ~4 chars/token, Code: ~3 chars/token, Spanish: ~3.5 chars/token
        # We'll use a slightly more conservative 3.5 average.
        words = len(re.findall(r'\w+', text))
        non_words = len(re.findall(r'[^\w\s]', text))
        return int(words + (non_words * 0.5))

class CostCalculator:
    """Calculates USD cost based on model pricing."""
    
    def __init__(self, pricing: Dict[str, Dict[str, float]]):
        self.pricing = pricing

    def calculate(self, model: str, input_tokens: int, output_tokens: int) -> float:
        rates = self.pricing.get(model, {'input': 0.0, 'output': 0.0})
        # Pricing in config is per 1M tokens
        cost = (input_tokens * rates.get('input', 0) + output_tokens * rates.get('output', 0)) / 1_000_000
        return cost

class BudgetTracker:
    """
    Tracks API spend and enforces limits with savings analytics.
    """
    
    def __init__(self, daily_limit: float = 2.0, persistence_path: str = ".budget.json"):
        self.daily_limit = daily_limit
        self.persistence_path = persistence_path
        self.metrics = SpendMetrics()
        self.savings_usd: float = 0.0
        self._load()

    def _load(self):
        if os.path.exists(self.persistence_path):
            try:
                with open(self.persistence_path, 'r') as f:
                    data = json.load(f)
                    if data.get('date') == time.strftime("%Y-%m-%d"):
                        self.metrics = SpendMetrics(**data.get('metrics', {}))
                        self.savings_usd = data.get('savings_usd', 0.0)
            except Exception as e:
                logger.error("Failed to load budget: %s", e)

    def _save(self):
        try:
            with open(self.persistence_path, 'w') as f:
                json.dump({
                    'date': time.strftime("%Y-%m-%d"),
                    'metrics': asdict(self.metrics),
                    'savings_usd': self.savings_usd
                }, f, indent=2)
        except Exception as e:
            logger.error("Failed to save budget: %s", e)

    def update(self, cost_usd: float, input_tokens: int, output_tokens: int, raw_cost_usd: Optional[float] = None):
        self.metrics.total_usd += cost_usd
        self.metrics.input_tokens += input_tokens
        self.metrics.output_tokens += output_tokens
        self.metrics.request_count += 1
        
        if raw_cost_usd is not None and raw_cost_usd > cost_usd:
            self.savings_usd += (raw_cost_usd - cost_usd)
            
        self._save()
        
        savings_pct = (self.savings_usd / (self.metrics.total_usd + self.savings_usd) * 100) if (self.metrics.total_usd + self.savings_usd) > 0 else 0
        logger.info("💸 Spend: $%.4f | Savings: $%.4f (%.1f%%) | Total: $%.2f/$%.2f", 
                    cost_usd, self.savings_usd, savings_pct, self.metrics.total_usd, self.daily_limit)

    def is_within_budget(self) -> bool:
        return self.metrics.total_usd < self.daily_limit
