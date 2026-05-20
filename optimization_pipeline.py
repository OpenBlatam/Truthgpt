# optimization_pipeline.py
# Path: optimization_core/optimization_pipeline.py
"""
Dynamic optimization pipeline that integrates:
  - Chain of Draft (2506.10987v1)
  - Elastic Reasoning (2505.05315v2)
  - FP16 Stability (2510.26788v1)
and makes them configurable via user preferences or CLI flags.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Union

try:
    import torch
except ImportError:
    torch = None  # type: ignore

from papers.chain_of_draft import ChainOfDraft
from papers.elastic_reasoning import ElasticReasoning
from papers.fp16_stability import FP16Stability


class OptimizationPipeline:
    """
    Runs a prompt through a chain of research-backed optimizers.
    Usage:
        pipeline = OptimizationPipeline(user_prefs)
        optimized = pipeline.run(prompt, model=None)
    """
    
    def __init__(self, prefs: Dict[str, Any]):
        self.prefs = prefs
        # Load techniques to skip from user prefs
        self.disabled = set(prefs.get("disabled_sota_techniques", []))
        # Default budgets
        self.chain_draft_variant = prefs.get("chain_draft_variant", "baseline")
        self.t_budget = prefs.get("t_budget", 10)
        self.s_budget = prefs.get("s_budget", 50)
        self.use_fp16 = prefs.get("fp16", False)
        
        self.chain_of_draft = ChainOfDraft()
        self.elastic_reasoning = ElasticReasoning(self.t_budget, self.s_budget)
        self.fp16_stability = FP16Stability()
        
    @staticmethod
    def from_config_file(path: Optional[Path] = None) -> "OptimizationPipeline":
        """Create pipeline from a JSON config file."""
        if path is None:
            path = Path(__file__).parent / "user_preferences.json"
        prefs = {}
        if path.exists():
            try:
                prefs = json.loads(path.read_bytes())
            except Exception:
                pass
        return OptimizationPipeline(prefs)
    
    def run(
        self,
        prompt: str,
        model: Any = None,
        *,
        enable_chain_draft: bool = None,
        enable_elastic: bool = None,
        enable_fp16: bool = None,
        chain_draft_variant: Optional[str] = None,
        t_budget: Optional[int] = None,
        s_budget: Optional[int] = None
    ) -> str:
        """Apply enabled optimizations to the prompt.  Returns the (possibly modified) prompt."""
        modified = prompt
        
        # Determine what is enabled
        cd = enable_chain_draft if enable_chain_draft is not None else ("chain_of_draft" not in self.disabled)
        er = enable_elastic if enable_elastic is not None else ("elastic_reasoning" not in self.disabled)
        fp = enable_fp16 if enable_fp16 is not None else self.use_fp16
        
        # --- 1. Chain of Draft ---
        if cd:
            variant = chain_draft_variant or self.chain_draft_variant
            template = self.chain_of_draft.get_template(variant)
            modified = template + "\n" + modified
            
        # --- 2. Elastic Reasoning (wrap with token budget instructions) ---
        if er:
            t = t_budget if t_budget is not None else self.t_budget
            s = s_budget if s_budget is not None else self.s_budget
            modified = (
                f"Please think within {t} tokens using <think></think> tags,"
                f" then answer within {s} tokens:\n\n{modified}"
            )
            
        # --- 3. FP16 Stability (model-level, applies if model given) ---
        if fp and model is not None and torch is not None:
            try:
                if hasattr(model, 'half'):
                    model.half()
            except Exception:
                pass
                
        return modified
    
    def get_applied_techniques(self, **overrides) -> Dict[str, bool]:
        """Return which techniques were actually applied for a run."""
        return {
            "chain_of_draft": overrides.get("enable_chain_draft", True) and ("chain_of_draft" not in self.disabled),
            "elastic_reasoning": overrides.get("enable_elastic", True) and ("elastic_reasoning" not in self.disabled),
            "fp16_stability": overrides.get("enable_fp16", self.use_fp16) and ("fp16_stability" not in self.disabled),
        }
