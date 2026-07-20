"""
Data Models for AI Optimization
"""

import torch.nn as nn
from dataclasses import dataclass, field
from typing import Dict, Any, List
from .metrics_calculator import AIOptimizationLevel


@dataclass
class AIOptimizationResult:
    """Result of AI optimization."""
    optimized_model: nn.Module
    speed_improvement: float
    memory_reduction: float
    accuracy_preservation: float
    intelligence_score: float
    learning_efficiency: float
    optimization_time: float
    level: AIOptimizationLevel
    techniques_applied: List[str]
    performance_metrics: Dict[str, float]
    ai_insights: Dict[str, Any] = field(default_factory=dict)
    neural_adaptation: float = 0.0
    cognitive_enhancement: float = 0.0
    artificial_wisdom: float = 0.0






