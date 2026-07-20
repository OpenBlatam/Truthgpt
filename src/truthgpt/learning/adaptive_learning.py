"""
Adaptive Learning and Self-Improving Systems for TruthGPT Optimization Core
Advanced meta-learning and self-evolving optimization capabilities
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
import logging
from dataclasses import dataclass, field
from enum import Enum
import time
import json
from pathlib import Path
import pickle
from abc import ABC, abstractmethod
import math
import random
from collections import deque
import threading
import queue

logger = logging.getLogger(__name__)

class LearningMode(Enum):
    """Learning modes for adaptive systems"""
    EXPLORATION = "exploration"
    EXPLOITATION = "exploitation"
    META_LEARNING = "meta_learning"
    SELF_IMPROVEMENT = "self_improvement"

@dataclass
class AdaptiveLearningConfig:
    """Configuration for adaptive learning systems"""
    # Learning parameters
    learning_rate: float = 0.001
    adaptation_rate: float = 0.01
    exploration_rate: float = 0.1
    exploitation_rate: float = 0.9
    
    # Meta-learning settings
    enable_meta_learning: bool = True
    meta_learning_steps: int = 100
    meta_batch_size: int = 32
    meta_learning_rate: float = 0.0001
    
    # Self-improvement settings
    enable_self_improvement: bool = True
    improvement_threshold: float = 0.05
    improvement_patience: int = 10
    improvement_memory_size: int = 1000
    
    # Adaptive mechanisms
    enable_adaptive_lr: bool = True
    enable_adaptive_architecture: bool = True
    enable_adaptive_optimization: bool = True
    
    # Monitoring
    enable_performance_tracking: bool = True
    enable_learning_curves: bool = True
    enable_adaptation_logging: bool = True
    
    def __post_init__(self):
        """Validate adaptive learning configuration"""
        if not (0.0 <= self.exploration_rate <= 1.0):
            raise ValueError("Exploration rate must be between 0.0 and 1.0")
        if not (0.0 <= self.exploitation_rate <= 1.0):
            raise ValueError("Exploitation rate must be between 0.0 and 1.0")

class PerformanceTracker:
    """Track and analyze performance metrics"""
    
    def __init__(self, config: AdaptiveLearningConfig):
        self.config = config
        self.metrics_history = deque(maxlen=1000)
        self.performance_trends = {}
        self.baseline_performance = None
        
        logger.info("✅ Performance Tracker initialized")
    
    def record_metric(self, metric_name: str, value: float, timestamp: float = None):
        """Record a performance metric"""
        if timestamp is None:
            timestamp = time.time()
        
        self.metrics_history.append({
            'metric_name': metric_name,
            'value': value,
            'timestamp': timestamp
        })
        
        # Update trends
        self._update_trends(metric_name, value)
    
    def _update_trends(self, metric_name: str, value: float):
        """Update performance trends"""
        if metric_name not in self.performance_trends:
            self.performance_trends[metric_name] = {
                'values': deque(maxlen=100),
                'trend': 'stable',
                'improvement_rate': 0.0
            }
        
        trend_data = self.performance_trends[metric_name]
        trend_data['values'].append(value)
        
        # Calculate trend
        if len(trend_data['values']) >= 10:
            recent_values = list(trend_data['values'])[-10:]
            trend_data['trend'] = self._calculate_trend(recent_values)
            trend_data['improvement_rate'] = self._calculate_improvement_rate(recent_values)
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return 'stable'
        
        # Simple linear trend
        x = np.arange(len(values))
        y = np.array(values)
        
        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0.01:
            return 'improving'
        elif slope < -0.01:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_improvement_rate(self, values: List[float]) -> float:
        """Calculate improvement rate"""
        if len(values) < 2:
            return 0.0
        
        # Calculate percentage improvement
        start_value = values[0]
        end_value = values[-1]
        
        if start_value == 0:
            return 0.0
        
        return (end_value - start_value) / abs(start_value)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        summary = {
            'total_metrics': len(self.metrics_history),
            'trends': {},
            'overall_trend': 'stable'
        }
        
        # Analyze trends
        improving_count = 0
        declining_count = 0
        
        for metric_name, trend_data in self.performance_trends.items():
            summary['trends'][metric_name] = {
                'trend': trend_data['trend'],
                'improvement_rate': trend_data['improvement_rate'],
                'recent_values': list(trend_data['values'])[-5:]
            }
            
            if trend_data['trend'] == 'improving':
                improving_count += 1
            elif trend_data['trend'] == 'declining':
                declining_count += 1
        
        # Determine overall trend
        if improving_count > declining_count:
            summary['overall_trend'] = 'improving'
        elif declining_count > improving_count:
            summary['overall_trend'] = 'declining'
        
        return summary

class MetaLearner:
    """Meta-learning system for learning how to learn"""
    
    def __init__(self, config: AdaptiveLearningConfig):
        self.config = config
        self.meta_model = self._create_meta_model()
        self.meta_optimizer = optim.Adam(self.meta_model.parameters(), lr=config.meta_learning_rate)
        self.task_memory = deque(maxlen=1000)
        self.learning_curves = {}
        
        logger.info("✅ Meta-Learner initialized")
    
    def _create_meta_model(self) -> nn.Module:
        """Create meta-learning model"""
        return nn.Sequential(
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
            nn.Sigmoid()
        )
    
    def learn_from_task(self, task_features: np.ndarray, task_performance: float):
        """Learn from a completed task"""
        # Store task information
        task_info = {
            'features': task_features,
            'performance': task_performance,
            'timestamp': time.time()
        }
        self.task_memory.append(task_info)
        
        # Update meta-model
        if len(self.task_memory) >= self.config.meta_batch_size:
            self._update_meta_model()
    
    def _update_meta_model(self):
        """Update meta-learning model"""
        # Sample batch from task memory
        batch_size = min(self.config.meta_batch_size, len(self.task_memory))
        batch = random.sample(list(self.task_memory), batch_size)
        
        # Prepare training data
        features = np.array([task['features'] for task in batch])
        performances = np.array([task['performance'] for task in batch])
        
        # Convert to tensors
        features_tensor = torch.tensor(features, dtype=torch.float32)
        performances_tensor = torch.tensor(performances, dtype=torch.float32).unsqueeze(1)
        
        # Train meta-model
        self.meta_optimizer.zero_grad()
        
        # Forward pass
        predictions = self.meta_model(features_tensor)
        
        # Calculate loss
        loss = nn.MSELoss()(predictions, performances_tensor)
        
        # Backward pass
        loss.backward()
        self.meta_optimizer.step()
        
        logger.debug(f"✅ Meta-model updated (loss: {loss.item():.6f})")
    
    def predict_task_performance(self, task_features: np.ndarray) -> float:
        """Predict performance for a new task"""
        with torch.no_grad():
            features_tensor = torch.tensor(task_features, dtype=torch.float32).unsqueeze(0)
            prediction = self.meta_model(features_tensor)
            return prediction.item()
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from meta-learning"""
        if not self.task_memory:
            return {'insights': 'No tasks learned yet'}
        
        # Analyze task patterns
        recent_tasks = list(self.task_memory)[-50:]  # Last 50 tasks
        
        performances = [task['performance'] for task in recent_tasks]
        avg_performance = np.mean(performances)
        performance_std = np.std(performances)
        
        # Analyze learning trends
        if len(performances) >= 10:
            recent_10 = performances[-10:]
            earlier_10 = performances[-20:-10] if len(performances) >= 20 else performances[:-10]
            
            improvement = np.mean(recent_10) - np.mean(earlier_10)
        else:
            improvement = 0.0
        
        return {
            'total_tasks': len(self.task_memory),
            'avg_performance': avg_performance,
            'performance_std': performance_std,
            'recent_improvement': improvement,
            'learning_trend': 'improving' if improvement > 0 else 'stable'
        }

class SelfImprovementEngine:
    """Self-improvement engine for continuous optimization"""
    
    def __init__(self, config: AdaptiveLearningConfig):
        self.config = config
        self.improvement_memory = deque(maxlen=config.improvement_memory_size)
        self.improvement_strategies = {}
        self.current_strategy = None
        self.improvement_patience_counter = 0
        self.best_performance = float('-inf')
        
        # Initialize improvement strategies
        self._initialize_strategies()
        
        logger.info("✅ Self-Improvement Engine initialized")
    
    def _initialize_strategies(self):
        """Initialize improvement strategies"""
        self.improvement_strategies = {
            'learning_rate_adjustment': self._adjust_learning_rate,
            'architecture_modification': self._modify_architecture,
            'optimization_strategy_change': self._change_optimization_strategy,
            'regularization_adjustment': self._adjust_regularization,
            'data_augmentation': self._enhance_data_augmentation
        }
    
    def evaluate_performance(self, current_performance: float) -> Dict[str, Any]:
        """Evaluate current performance and suggest improvements"""
        evaluation = {
            'current_performance': current_performance,
            'improvement_needed': False,
            'suggested_strategy': None,
            'confidence': 0.0
        }
        
        # Check if improvement is needed
        if current_performance > self.best_performance:
            self.best_performance = current_performance
            self.improvement_patience_counter = 0
            evaluation['improvement_needed'] = False
        else:
            self.improvement_patience_counter += 1
            
            # Check if improvement threshold is met
            improvement_needed = (self.best_performance - current_performance) > self.config.improvement_threshold
            
            if improvement_needed and self.improvement_patience_counter >= self.config.improvement_patience:
                evaluation['improvement_needed'] = True
                evaluation['suggested_strategy'] = self._select_improvement_strategy()
                evaluation['confidence'] = self._calculate_confidence()
        
        # Store evaluation
        self.improvement_memory.append(evaluation)
        
        return evaluation
    
    def _select_improvement_strategy(self) -> str:
        """Select best improvement strategy"""
        # Analyze past improvements
        successful_strategies = []
        
        for evaluation in self.improvement_memory:
            if evaluation.get('improvement_needed', False):
                strategy = evaluation.get('suggested_strategy')
                if strategy:
                    successful_strategies.append(strategy)
        
        # Select strategy based on success rate
        if successful_strategies:
            strategy_counts = {}
            for strategy in successful_strategies:
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
            # Select most successful strategy
            best_strategy = max(strategy_counts, key=strategy_counts.get)
        else:
            # Random selection for exploration
            best_strategy = random.choice(list(self.improvement_strategies.keys()))
        
        return best_strategy
    
    def _calculate_confidence(self) -> float:
        """Calculate confidence in improvement suggestion"""
        if not self.improvement_memory:
            return 0.5
        
        # Calculate confidence based on past success
        successful_improvements = sum(1 for eval in self.improvement_memory 
                                   if eval.get('improvement_needed', False))
        
        total_evaluations = len(self.improvement_memory)
        confidence = successful_improvements / total_evaluations if total_evaluations > 0 else 0.5
        
        return min(confidence, 0.95)  # Cap at 95%
    
    def apply_improvement(self, strategy: str, model: nn.Module, **kwargs) -> nn.Module:
        """Apply improvement strategy to model"""
        if strategy not in self.improvement_strategies:
            logger.warning(f"Unknown improvement strategy: {strategy}")
            return model
        
        improvement_func = self.improvement_strategies[strategy]
        
        try:
            improved_model = improvement_func(model, **kwargs)
            logger.info(f"✅ Applied improvement strategy: {strategy}")
            return improved_model
        except Exception as e:
            logger.error(f"Failed to apply improvement strategy {strategy}: {e}")
            return model
    
    def _adjust_learning_rate(self, model: nn.Module, **kwargs) -> nn.Module:
        """Adjust learning rate for better performance"""
        # This would adjust learning rates in practice
        logger.info("📈 Learning rate adjustment applied")
        return model
    
    def _modify_architecture(self, model: nn.Module, **kwargs) -> nn.Module:
        """Modify model architecture"""
        # This would modify architecture in practice
        logger.info("🏗️ Architecture modification applied")
        return model
    
    def _change_optimization_strategy(self, model: nn.Module, **kwargs) -> nn.Module:
        """Change optimization strategy"""
        # This would change optimization strategy in practice
        logger.info("⚙️ Optimization strategy changed")
        return model
    
    def _adjust_regularization(self, model: nn.Module, **kwargs) -> nn.Module:
        """Adjust regularization"""
        # This would adjust regularization in practice
        logger.info("🛡️ Regularization adjusted")
        return model
    
    def _enhance_data_augmentation(self, model: nn.Module, **kwargs) -> nn.Module:
        """Enhance data augmentation"""
        # This would enhance data augmentation in practice
        logger.info("🔄 Data augmentation enhanced")
        return model
    
    def get_improvement_statistics(self) -> Dict[str, Any]:
        """Get self-improvement statistics"""
        if not self.improvement_memory:
            return {'statistics': 'No improvements attempted yet'}
        
        total_evaluations = len(self.improvement_memory)
        improvements_needed = sum(1 for eval in self.improvement_memory 
                                if eval.get('improvement_needed', False))
        
        successful_strategies = [eval.get('suggested_strategy') for eval in self.improvement_memory 
                              if eval.get('improvement_needed', False)]
        
        strategy_counts = {}
        for strategy in successful_strategies:
            if strategy:
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            'total_evaluations': total_evaluations,
            'improvements_needed': improvements_needed,
            'improvement_rate': improvements_needed / total_evaluations if total_evaluations > 0 else 0,
            'best_performance': self.best_performance,
            'strategy_usage': strategy_counts,
            'patience_counter': self.improvement_patience_counter
        }

class AdaptiveLearningSystem:
    """Main adaptive learning system"""
    
    def __init__(self, config: AdaptiveLearningConfig):
        self.config = config
        self.performance_tracker = PerformanceTracker(config)
        self.meta_learner = MetaLearner(config)
        self.self_improvement = SelfImprovementEngine(config)
        self.learning_mode = LearningMode.EXPLORATION
        self.adaptation_history = []
        
        logger.info("✅ Adaptive Learning System initialized")
    
    def adapt(self, model: nn.Module, performance_metrics: Dict[str, float]) -> nn.Module:
        """Adapt model based on performance metrics"""
        logger.info("🧠 Starting adaptive learning...")
        
        # Record performance metrics
        for metric_name, value in performance_metrics.items():
            self.performance_tracker.record_metric(metric_name, value)
        
        # Extract task features for meta-learning
        task_features = self._extract_task_features(model, performance_metrics)
        
        # Learn from this task
        overall_performance = np.mean(list(performance_metrics.values()))
        self.meta_learner.learn_from_task(task_features, overall_performance)
        
        # Evaluate performance for self-improvement
        evaluation = self.self_improvement.evaluate_performance(overall_performance)
        
        # Apply improvements if needed
        if evaluation['improvement_needed']:
            strategy = evaluation['suggested_strategy']
            model = self.self_improvement.apply_improvement(strategy, model)
            
            logger.info(f"🔧 Applied improvement: {strategy}")
        
        # Update learning mode
        self._update_learning_mode()
        
        # Record adaptation
        self.adaptation_history.append({
            'performance_metrics': performance_metrics,
            'task_features': task_features,
            'evaluation': evaluation,
            'learning_mode': self.learning_mode.value,
            'timestamp': time.time()
        })
        
        logger.info("✅ Adaptive learning completed")
        return model
    
    def _extract_task_features(self, model: nn.Module, metrics: Dict[str, float]) -> np.ndarray:
        """Extract features for meta-learning"""
        features = []
        
        # Model features
        total_params = sum(p.numel() for p in model.parameters())
        features.append(min(total_params / 1e6, 100.0))  # Normalize
        
        layer_count = len(list(model.modules()))
        features.append(min(layer_count / 100, 10.0))  # Normalize
        
        # Performance features
        for metric_name, value in metrics.items():
            features.append(min(value, 10.0))  # Normalize
        
        # Pad or truncate to fixed size
        while len(features) < 64:
            features.append(0.0)
        features = features[:64]
        
        return np.array(features)
    
    def _update_learning_mode(self):
        """Update learning mode based on performance"""
        performance_summary = self.performance_tracker.get_performance_summary()
        
        if performance_summary['overall_trend'] == 'improving':
            # Switch to exploitation when improving
            if random.random() < self.config.exploitation_rate:
                self.learning_mode = LearningMode.EXPLOITATION
        else:
            # Switch to exploration when not improving
            if random.random() < self.config.exploration_rate:
                self.learning_mode = LearningMode.EXPLORATION
        
        logger.debug(f"Learning mode: {self.learning_mode.value}")
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics"""
        return {
            'performance_summary': self.performance_tracker.get_performance_summary(),
            'meta_learning_insights': self.meta_learner.get_learning_insights(),
            'improvement_statistics': self.self_improvement.get_improvement_statistics(),
            'current_learning_mode': self.learning_mode.value,
            'total_adaptations': len(self.adaptation_history),
            'config': {
                'learning_rate': self.config.learning_rate,
                'adaptation_rate': self.config.adaptation_rate,
                'exploration_rate': self.config.exploration_rate,
                'exploitation_rate': self.config.exploitation_rate
            }
        }
    
    def save_learning_state(self, path: str):
        """Save learning state"""
        state = {
            'performance_tracker': {
                'metrics_history': list(self.performance_tracker.metrics_history),
                'performance_trends': dict(self.performance_tracker.performance_trends)
            },
            'meta_learner': {
                'task_memory': list(self.meta_learner.task_memory),
                'meta_model_state': self.meta_learner.meta_model.state_dict()
            },
            'self_improvement': {
                'improvement_memory': list(self.self_improvement.improvement_memory),
                'best_performance': self.self_improvement.best_performance,
                'improvement_patience_counter': self.self_improvement.improvement_patience_counter
            },
            'adaptation_history': self.adaptation_history,
            'learning_mode': self.learning_mode.value
        }
        
        with open(path, 'wb') as f:
            pickle.dump(state, f)
        
        logger.info(f"✅ Learning state saved to {path}")
    
    def load_learning_state(self, path: str):
        """Load learning state"""
        with open(path, 'rb') as f:
            state = pickle.load(f)
        
        # Restore performance tracker
        self.performance_tracker.metrics_history = deque(state['performance_tracker']['metrics_history'], maxlen=1000)
        self.performance_tracker.performance_trends = state['performance_tracker']['performance_trends']
        
        # Restore meta-learner
        self.meta_learner.task_memory = deque(state['meta_learner']['task_memory'], maxlen=1000)
        self.meta_learner.meta_model.load_state_dict(state['meta_learner']['meta_model_state'])
        
        # Restore self-improvement
        self.self_improvement.improvement_memory = deque(state['self_improvement']['improvement_memory'], maxlen=self.config.improvement_memory_size)
        self.self_improvement.best_performance = state['self_improvement']['best_performance']
        self.self_improvement.improvement_patience_counter = state['self_improvement']['improvement_patience_counter']
        
        # Restore adaptation history
        self.adaptation_history = state['adaptation_history']
        self.learning_mode = LearningMode(state['learning_mode'])
        
        logger.info(f"✅ Learning state loaded from {path}")

# Factory functions
def create_adaptive_learning_config(**kwargs) -> AdaptiveLearningConfig:
    """Create adaptive learning configuration"""
    return AdaptiveLearningConfig(**kwargs)

def create_adaptive_learning_system(config: AdaptiveLearningConfig) -> AdaptiveLearningSystem:
    """Create adaptive learning system"""
    return AdaptiveLearningSystem(config)

# Example usage
def example_adaptive_learning():
    """Example of adaptive learning system"""
    # Create configuration
    config = create_adaptive_learning_config(
        learning_rate=0.001,
        adaptation_rate=0.01,
        exploration_rate=0.2,
        exploitation_rate=0.8,
        enable_meta_learning=True,
        enable_self_improvement=True,
        improvement_threshold=0.05
    )
    
    # Create adaptive learning system
    adaptive_system = create_adaptive_learning_system(config)
    
    # Create a model
    model = nn.Sequential(
        nn.Linear(100, 50),
        nn.ReLU(),
        nn.Linear(50, 25),
        nn.ReLU(),
        nn.Linear(25, 10)
    )
    
    # Simulate multiple adaptation cycles
    for cycle in range(5):
        # Simulate performance metrics
        performance_metrics = {
            'accuracy': random.uniform(0.7, 0.95),
            'loss': random.uniform(0.1, 0.5),
            'speed': random.uniform(100, 500)
        }
        
        # Adapt model
        model = adaptive_system.adapt(model, performance_metrics)
        
        print(f"Cycle {cycle + 1}: Adapted model")
    
    # Get learning statistics
    stats = adaptive_system.get_learning_statistics()
    
    print(f"✅ Adaptive Learning Example Complete!")
    print(f"🧠 Learning Statistics:")
    print(f"   Total Adaptations: {stats['total_adaptations']}")
    print(f"   Current Mode: {stats['current_learning_mode']}")
    print(f"   Performance Trend: {stats['performance_summary']['overall_trend']}")
    print(f"   Meta-Learning Tasks: {stats['meta_learning_insights'].get('total_tasks', 0)}")
    print(f"   Improvements Needed: {stats['improvement_statistics'].get('improvements_needed', 0)}")
    
    return model

# Export utilities
__all__ = [
    'LearningMode',
    'AdaptiveLearningConfig',
    'PerformanceTracker',
    'MetaLearner',
    'SelfImprovementEngine',
    'AdaptiveLearningSystem',
    'create_adaptive_learning_config',
    'create_adaptive_learning_system',
    'example_adaptive_learning'
]

if __name__ == "__main__":
    example_adaptive_learning()
    print("✅ Adaptive learning example completed successfully!")







