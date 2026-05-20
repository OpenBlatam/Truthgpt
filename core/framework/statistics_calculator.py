"""
Statistics Calculator Module
Calculates statistics from optimization history
"""

import numpy as np
from typing import Dict, Any, List

from .models import AIOptimizationResult
from .learning_mechanism import LearningMechanism
from .metrics_calculator import AIOptimizationLevel


class StatisticsCalculator:
    """Calculates statistics from optimization results."""
    
    @staticmethod
    def calculate(
        optimization_history: List[AIOptimizationResult],
        optimization_level: AIOptimizationLevel,
        learning_mechanism: LearningMechanism
    ) -> Dict[str, Any]:
        """Calculate statistics from optimization history."""
        if not optimization_history:
            return {}
        
        results = list(optimization_history)
        
        metrics = {
            'speed_improvement': [r.speed_improvement for r in results],
            'memory_reduction': [r.memory_reduction for r in results],
            'intelligence_score': [r.intelligence_score for r in results],
            'learning_efficiency': [r.learning_efficiency for r in results],
            'neural_adaptation': [r.neural_adaptation for r in results],
            'cognitive_enhancement': [r.cognitive_enhancement for r in results],
            'artificial_wisdom': [r.artificial_wisdom for r in results]
        }
        
        return {
            'total_optimizations': len(results),
            'avg_speed_improvement': np.mean(metrics['speed_improvement']),
            'max_speed_improvement': max(metrics['speed_improvement']),
            'avg_memory_reduction': np.mean(metrics['memory_reduction']),
            'avg_intelligence_score': np.mean(metrics['intelligence_score']),
            'avg_learning_efficiency': np.mean(metrics['learning_efficiency']),
            'avg_neural_adaptation': np.mean(metrics['neural_adaptation']),
            'avg_cognitive_enhancement': np.mean(metrics['cognitive_enhancement']),
            'avg_artificial_wisdom': np.mean(metrics['artificial_wisdom']),
            'optimization_level': optimization_level.value,
            'learning_history_length': len(learning_mechanism.get_learning_history()),
            'experience_buffer_size': len(learning_mechanism.get_experience_buffer()),
            'exploration_rate': learning_mechanism.get_exploration_rate()
        }






