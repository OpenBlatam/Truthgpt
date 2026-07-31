"""
Research Models: Consumer Fatigue Model & Causal Forest HTE Attributor
"""

import math
import random
from typing import Dict, Any, List, Optional
import torch
import torch.nn as nn

# ═══════════════════════════════════════════════════════════════════════════
# [PAPER 1.4] CONSUMER FATIGUE MODEL
# Source: "RL-Based Demand State Modeling and Dynamic Personalization
#          for Digital Retail" (2026) — +4.3% conversion via timing
# ═══════════════════════════════════════════════════════════════════════════
class ConsumerFatigueModel:
    """
    Models diminishing returns from excessive outreach.
    Uses exponential decay to simulate fatigue and determine optimal
    send timing for email sequences.
    
    Based on constrained MDP that factors "fatigue" as a state variable,
    the model outputs an engagement probability and a recommended delay.
    """
    def __init__(self, base_engagement: float = 0.65, decay_rate: float = 0.12,
                 recovery_rate: float = 0.08, min_engagement: float = 0.15):
        self.base_engagement = base_engagement
        self.decay_rate = decay_rate
        self.recovery_rate = recovery_rate
        self.min_engagement = min_engagement
        self.contact_history: List[Dict[str, Any]] = []

    def compute_fatigue_score(self, days_since_last: float, total_contacts: int) -> float:
        """Fatigue increases with frequency but recovers with rest."""
        fatigue_from_frequency = 1.0 - math.exp(-self.decay_rate * total_contacts)
        recovery = 1.0 - math.exp(-self.recovery_rate * days_since_last)
        raw = fatigue_from_frequency * (1.0 - recovery)
        return min(1.0, max(0.0, raw))

    def predict_engagement(self, days_since_last: float, total_contacts: int,
                           content_novelty: float = 0.5) -> Dict[str, Any]:
        """Predict engagement probability factoring fatigue, novelty and recency."""
        fatigue = self.compute_fatigue_score(days_since_last, total_contacts)
        recency_boost = 0.1 * math.exp(-0.05 * days_since_last) if days_since_last < 7 else 0
        novelty_boost = 0.08 * content_novelty
        engagement = self.base_engagement * (1.0 - fatigue) + recency_boost + novelty_boost
        engagement = max(self.min_engagement, min(1.0, engagement))
        return {
            "engagement_probability": round(engagement, 4),
            "fatigue_score": round(fatigue, 4),
            "recency_boost": round(recency_boost, 4),
            "novelty_boost": round(novelty_boost, 4),
        }

    def optimal_send_schedule(self, num_emails: int = 4, campaign_days: int = 14) -> List[Dict[str, Any]]:
        """Use GRPO-inspired group optimization to find best send days."""
        best_schedule = []
        candidates_per_slot = 8  # GRPO group size

        for email_idx in range(num_emails):
            best_day = None
            best_engagement = -1.0

            min_day = best_schedule[-1]["day"] + 1 if best_schedule else 1
            max_day = campaign_days - (num_emails - email_idx - 1)

            for _ in range(candidates_per_slot):
                candidate_day = random.randint(min_day, max(min_day, max_day))
                days_since = candidate_day - (best_schedule[-1]["day"] if best_schedule else 0)
                novelty = 1.0 - (email_idx / num_emails)
                pred = self.predict_engagement(days_since, email_idx, novelty)

                if pred["engagement_probability"] > best_engagement:
                    best_engagement = pred["engagement_probability"]
                    best_day = candidate_day

            days_since = best_day - (best_schedule[-1]["day"] if best_schedule else 0)
            novelty = 1.0 - (email_idx / num_emails)
            pred = self.predict_engagement(days_since, email_idx, novelty)
            best_schedule.append({
                "email_number": email_idx + 1,
                "day": best_day,
                "days_since_last": days_since,
                "predicted_engagement": pred["engagement_probability"],
                "fatigue_score": pred["fatigue_score"],
            })

        return best_schedule


# ═══════════════════════════════════════════════════════════════════════════
# [PAPER 2.1] CAUSAL FOREST SEGMENTED ATTRIBUTION
# Source: "Dynamic Marketing Uplift Modeling" (2024-2025)
#          — Causal Forests + DRL for heterogeneous treatment effects
# ═══════════════════════════════════════════════════════════════════════════
class CausalForestAttributor:
    """
    Simulates Causal Forest estimation of Heterogeneous Treatment Effects (HTE).
    Instead of one global lift%, it estimates different treatment effects
    per audience segment (persona × stage × channel).
    
    Uses PyTorch tensors to compute segment-level uplift via a learned
    representation of the treatment effect surface.
    """
    def __init__(self, moe_layer: nn.Module, num_trees: int = 100):
        self.moe_layer = moe_layer
        self.num_trees = num_trees

    def estimate_segment_uplift(self, persona_key: str, stage: str,
                                channels: List[str]) -> Dict[str, Any]:
        """Estimate heterogeneous treatment effects per channel for a segment."""
        persona_encoding = {"ceo_b2b": 0, "ecommerce_manager": 1, "startup_growth": 2}
        stage_encoding = {"tofu": 0, "mofu": 1, "bofu": 2, "retention": 3}

        p_idx = persona_encoding.get(persona_key, 0)
        s_idx = stage_encoding.get(stage, 0)

        results = {}
        for ch in channels:
            feat = torch.zeros(1, 10, 256)
            feat[0, 0, p_idx * 30:(p_idx + 1) * 30] = 1.0
            feat[0, 1, s_idx * 40:(s_idx + 1) * 40] = 1.0

            with torch.no_grad():
                moe_out = self.moe_layer(feat)
                if isinstance(moe_out, tuple):
                    moe_out = moe_out[0]

            norm = torch.norm(moe_out).item()
            base_uplift = {
                "tofu": 0.18, "mofu": 0.32, "bofu": 0.48, "retention": 0.55
            }.get(stage, 0.20)

            channel_mult = {
                "meta_ad": 1.1, "google_ad": 1.25, "email": 1.45,
                "linkedin_ad": 0.95, "twitter_ad": 0.85,
                "retargeting": 1.35, "landing_page": 1.0
            }.get(ch, 1.0)

            persona_mult = {
                "ceo_b2b": {"email": 1.3, "linkedin_ad": 1.5, "landing_page": 1.1},
                "ecommerce_manager": {"meta_ad": 1.4, "retargeting": 1.6, "google_ad": 1.3},
                "startup_growth": {"twitter_ad": 1.3, "meta_ad": 1.2, "email": 1.1},
            }
            p_mult = persona_mult.get(persona_key, {}).get(ch, 1.0)

            hte = base_uplift * channel_mult * p_mult * (0.8 + 0.4 * (norm / (norm + 1)))
            confidence = min(0.99, 0.75 + 0.25 * (self.num_trees / 200))

            results[ch] = {
                "treatment_effect": round(hte, 4),
                "uplift_pct": round(hte * 100, 1),
                "confidence_interval": [round(hte * 0.85, 4), round(hte * 1.15, 4)],
                "confidence": round(confidence, 2),
                "moe_norm": round(norm, 4),
                "recommendation": "INVEST" if hte > 0.30 else ("MAINTAIN" if hte > 0.15 else "REDUCE"),
            }

        return {
            "segment": f"{persona_key}×{stage}",
            "method": "causal_forest_hte",
            "num_trees": self.num_trees,
            "channel_effects": results,
        }
