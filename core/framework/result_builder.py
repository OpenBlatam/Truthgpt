"""
Result Builder Module
Constructs AIOptimizationResult objects
"""

import torch.nn as nn
from typing import Dict, Any

from .models import AIOptimizationResult
from .metrics_calculator import AIOptimizationLevel


class ResultBuilder:
    """Builds AIOptimizationResult objects."""
    
    @staticmethod
    def build(
        optimized_model: nn.Module,
        performance_metrics: Dict[str, float],
        optimization_time: float,
        optimization_level: AIOptimizationLevel,
        techniques_applied: list,
        ai_insights: Dict[str, Any]
    ) -> AIOptimizationResult:
        """Build AIOptimizationResult from components."""
        metrics = performance_metrics or {}
        insights = ai_insights or {}
        techniques = techniques_applied if techniques_applied is not None else []
        return AIOptimizationResult(
            optimized_model=optimized_model,
            speed_improvement=metrics.get('speed_improvement', 1.0),
            memory_reduction=metrics.get('memory_reduction', 0.0),
            accuracy_preservation=metrics.get('accuracy_preservation', 1.0),
            intelligence_score=metrics.get('intelligence_score', 1.0),
            learning_efficiency=metrics.get('learning_efficiency', 1.0),
            optimization_time=optimization_time,
            level=optimization_level,
            techniques_applied=techniques,
            performance_metrics=metrics,
            ai_insights=insights,
            neural_adaptation=metrics.get('neural_adaptation', 0.0),
            cognitive_enhancement=metrics.get('cognitive_enhancement', 0.0),
            artificial_wisdom=metrics.get('artificial_wisdom', 0.0)
        )







