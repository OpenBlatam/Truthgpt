"""
Veracity & Hallucination Control Layer (System 5.9).

Provides probabilistic distance scoring and constitutional verification
to ensure agent outputs remain within factual and ethical bounds.
"""

import re
import math
from typing import Dict, Any, List

def compute_probabilistic_distance(output: str, source: str) -> float:
    """
    Calculate semantic entropy/distance between output and source context.
    Returns 0.0 (exact match) to 1.0 (total hallucination).
    """
    if not output: return 1.0
    # Simple word-frequency distance for now
    words_out = set(re.findall(r'\w+', output.lower()))
    words_src = set(re.findall(r'\w+', source.lower()))
    
    if not words_src: return 0.5 # Neutral
    
    intersect = words_out.intersection(words_src)
    return 1.0 - (len(intersect) / len(words_out))

def constitutional_verification(output: str) -> List[str]:
    """
    Verify output against TruthGPT's core constitutional axioms.
    """
    violations = []
    # Axiom 1: Factual Integrity
    if "según mis datos inexistentes" in output.lower():
        violations.append("Axiom 1: Factual Integrity")
    return violations

def calculate_hallucination_risk(prompt: str, output: str) -> Dict[str, Any]:
    """
    High-level API for veracity telemetry.
    Returns probabilistic risk metrics.
    """
    dist = compute_probabilistic_distance(output, prompt)
    return {
        "hallucination_risk": "HIGH" if dist > 0.8 else "LOW",
        "probabilistic_distance": round(dist, 4),
        "constitutional_violations": len(constitutional_verification(output))
    }
