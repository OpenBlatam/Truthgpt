"""
FrugalGPT Model Cascading & AutoMix Verification (System 5.9).

Based on:
- FrugalGPT (Chen et al., 2023): https://arxiv.org/abs/2305.05176
- AutoMix (Chatterjee et al., 2024): https://arxiv.org/abs/2310.12963
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("optimization.api_cost.cascade")

class ConfidenceScorer:
    """
    AutoMix-inspired Self-Verification (arXiv:2310.12963).
    Evaluates response quality and confidence using multiple heuristics.
    """
    
    def __init__(self, threshold: float = 0.65):
        self.threshold = threshold

    def score(self, response: str, prompt: str) -> float:
        """Score response from 0.0 to 1.0."""
        if not response or len(response.strip()) < 10: 
            return 0.0
            
        score = 0.4 # Lower baseline to be more critical
        
        # 1. Structural signals (up to 0.2)
        if len(response) > 100: score += 0.05
        if len(response) > 500: score += 0.05
        if "```" in response: score += 0.1 # Code blocks are high signal
        if any(m in response for m in ["1.", "-", "###", "**"]): score += 0.1 # Formatting
        
        # 2. Uncertainty signals (Penalty up to -0.6)
        uncertainty_terms = [
            "uncertain", "not sure", "don't know", "cannot verify", "apologize",
            "limited information", "as an ai", "could not find", "unavailable"
        ]
        low_conf_matches = [w for w in uncertainty_terms if w in response.lower()]
        if low_conf_matches:
            score -= (0.2 * len(low_conf_matches))
            
        # 3. Semantic grounding (up to 0.4)
        # Extract entities/keywords from prompt
        prompt_keywords = set(re.findall(r'\w{5,}', prompt.lower())) # Longer words only
        if prompt_keywords:
            resp_words = set(re.findall(r'\w{5,}', response.lower()))
            overlap = len(prompt_keywords & resp_words) / len(prompt_keywords)
            score += overlap * 0.4
            
        # 4. Logic & Connectivity (up to 0.1)
        logic_markers = ["therefore", "because", "consequently", "however", "furthermore", "specifically"]
        if any(marker in response.lower() for marker in logic_markers):
            score += 0.1
            
        # 5. Reasoning Detection (DeepSeek-style thinking blocks)
        if "<think>" in response or "Reasoning:" in response:
            score += 0.15

        final_score = min(1.0, max(0.0, score))
        logger.debug("Scoring response: final=%.2f (overlap=%.2f, uncertainty=%d)", 
                     final_score, overlap if prompt_keywords else 0, len(low_conf_matches))
        return final_score

    def verify(self, response: str, prompt: str) -> Tuple[bool, float]:
        """Returns (is_acceptable, confidence_score)."""
        conf = self.score(response, prompt)
        return conf >= self.threshold, conf

class CascadeRouter:
    """Routes queries through a sequence of models based on cost and capability."""
    
    def __init__(self, models: List[str]):
        self.models = models # Assumed to be ordered cheapest to most expensive

    def get_order(self) -> List[str]:
        return self.models

class ModelCascade:
    """
    FrugalGPT Model Cascade (System 5.9).
    
    Orchestrates the execution through multiple models until a 
    high-confidence answer is obtained.
    """
    
    def __init__(self, models: List[str], threshold: float = 0.7):
        self.models = models
        self.threshold = threshold
        self.verifier = ConfidenceScorer(threshold=threshold)

    async def execute_cascade(self, prompt: str, llm_func, **kwargs) -> Dict[str, Any]:
        """
        Runs the cascade loop.
        llm_func must be an async function taking (prompt, model, **kwargs).
        """
        tried_models = []
        for i, model in enumerate(self.models):
            logger.info("🌊 Cascade Step %d: Attempting with %s", i+1, model)
            tried_models.append(model)
            
            try:
                response = await llm_func(prompt, model=model, **kwargs)
                is_ok, score = self.verifier.verify(response, prompt)
                
                logger.info("📊 Model %s confidence: %.2f (Accepted: %s)", model, score, is_ok)
                
                if is_ok or i == len(self.models) - 1:
                    # If it's the last model, we return it anyway but log it
                    return {
                        "response": response,
                        "model": model,
                        "confidence": score,
                        "escalated": i > 0,
                        "tried_models": tried_models,
                        "final_attempt": i == len(self.models) - 1
                    }
                
                logger.warning("⚠️ Low confidence (%.2f < %.2f). Escalating...", score, self.threshold)
                
            except Exception as e:
                logger.error("❌ Model %s failed: %s", model, str(e))
                if i == len(self.models) - 1:
                    raise e # Re-throw if it's the last model
                continue # Try next model
        
        return {"response": "Cascade failed to produce a result", "error": True}

    def should_escalate(self, response: str, prompt: str) -> bool:
        """Determine if we should escalate based on AutoMix verification."""
        is_ok, score = self.verifier.verify(response, prompt)
        logger.info("Cascade verification: score=%.2f, accepted=%s", score, is_ok)
        return not is_ok
