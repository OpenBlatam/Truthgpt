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
            'speed_improvement': [getattr(r, 'speed_improvement', 1.0) for r in results],
            'memory_reduction': [getattr(r, 'memory_reduction', 0.0) for r in results],
            'intelligence_score': [getattr(r, 'intelligence_score', 1.0) for r in results],
            'learning_efficiency': [getattr(r, 'learning_efficiency', 1.0) for r in results],
            'neural_adaptation': [getattr(r, 'neural_adaptation', 0.0) for r in results],
            'cognitive_enhancement': [getattr(r, 'cognitive_enhancement', 0.0) for r in results],
            'artificial_wisdom': [getattr(r, 'artificial_wisdom', 0.0) for r in results]
        }
        
        opt_level = getattr(optimization_level, 'value', str(optimization_level))
        
        return {
            'total_optimizations': len(results),
            'avg_speed_improvement': float(np.mean(metrics['speed_improvement'])),
            'max_speed_improvement': float(max(metrics['speed_improvement'])) if metrics['speed_improvement'] else 1.0,
            'avg_memory_reduction': float(np.mean(metrics['memory_reduction'])),
            'avg_intelligence_score': float(np.mean(metrics['intelligence_score'])),
            'avg_learning_efficiency': float(np.mean(metrics['learning_efficiency'])),
            'avg_neural_adaptation': float(np.mean(metrics['neural_adaptation'])),
            'avg_cognitive_enhancement': float(np.mean(metrics['cognitive_enhancement'])),
            'avg_artificial_wisdom': float(np.mean(metrics['artificial_wisdom'])),
            'optimization_level': opt_level,
            'learning_history_length': len(learning_mechanism.get_learning_history()) if hasattr(learning_mechanism, 'get_learning_history') else 0,
            'experience_buffer_size': len(learning_mechanism.get_experience_buffer()) if hasattr(learning_mechanism, 'get_experience_buffer') else 0,
            'exploration_rate': learning_mechanism.get_exploration_rate() if hasattr(learning_mechanism, 'get_exploration_rate') else 0.1
        }






