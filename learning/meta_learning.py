"""
Advanced Meta-Learning System for TruthGPT Optimization Core
Few-shot learning, model-agnostic meta-learning, and rapid adaptation
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
from collections import defaultdict
import itertools

logger = logging.getLogger(__name__)

class MetaLearningAlgorithm(Enum):
    """Meta-learning algorithms"""
    MAML = "maml"  # Model-Agnostic Meta-Learning
    REPTILE = "reptile"
    PROTOMAML = "protomaml"
    META_SGD = "meta_sgd"
    LEARNED_INITIALIZATION = "learned_init"
    GRADIENT_BASED_META = "gradient_based"

class TaskDistribution(Enum):
    """Task distribution types"""
    UNIFORM = "uniform"
    GAUSSIAN = "gaussian"
    MULTIMODAL = "multimodal"
    HIERARCHICAL = "hierarchical"
    ADAPTIVE = "adaptive"

@dataclass
class MetaLearningConfig:
    """Configuration for meta-learning"""
    # Algorithm settings
    algorithm: MetaLearningAlgorithm = MetaLearningAlgorithm.MAML
    task_distribution: TaskDistribution = TaskDistribution.UNIFORM
    
    # Training parameters
    meta_lr: float = 0.001
    inner_lr: float = 0.01
    inner_steps: int = 5
    meta_batch_size: int = 16
    num_tasks: int = 1000
    
    # Task parameters
    support_size: int = 5
    query_size: int = 15
    num_ways: int = 5
    
    # Advanced features
    enable_second_order: bool = True
    enable_learned_initialization: bool = True
    enable_task_embedding: bool = True
    enable_meta_regularization: bool = True
    
    # Performance
    enable_meta_validation: bool = True
    validation_frequency: int = 100
    early_stopping_patience: int = 50
    
    def __post_init__(self):
        """Validate meta-learning configuration"""
        if self.inner_steps < 1:
            raise ValueError("Inner steps must be at least 1")
        if self.support_size < 1 or self.query_size < 1:
            raise ValueError("Support and query sizes must be at least 1")

class TaskGenerator:
    """Generate meta-learning tasks"""
    
    def __init__(self, config: MetaLearningConfig):
        self.config = config
        self.task_counter = 0
        self.task_history = []
        
        logger.info("✅ Task Generator initialized")
    
    def generate_task(self, input_dim: int = 100, output_dim: int = 10) -> Dict[str, Any]:
        """Generate a meta-learning task"""
        task_id = f"task_{self.task_counter}"
        self.task_counter += 1
        
        # Generate support and query sets
        support_data, support_labels = self._generate_data(input_dim, output_dim, self.config.support_size)
        query_data, query_labels = self._generate_data(input_dim, output_dim, self.config.query_size)
        
        task = {
            'task_id': task_id,
            'support_data': support_data,
            'support_labels': support_labels,
            'query_data': query_data,
            'query_labels': query_labels,
            'num_ways': self.config.num_ways,
            'input_dim': input_dim,
            'output_dim': output_dim
        }
        
        self.task_history.append(task)
        return task
    
    def _generate_data(self, input_dim: int, output_dim: int, num_samples: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Generate data for a task"""
        if self.config.task_distribution == TaskDistribution.UNIFORM:
            data = torch.randn(num_samples, input_dim)
            labels = torch.randint(0, output_dim, (num_samples,))
        elif self.config.task_distribution == TaskDistribution.GAUSSIAN:
            # Generate data from different Gaussian distributions
            data = []
            labels = []
            samples_per_class = num_samples // self.config.num_ways
            
            for class_id in range(self.config.num_ways):
                mean = torch.randn(input_dim)
                cov = torch.eye(input_dim) * 0.1
                class_data = torch.distributions.MultivariateNormal(mean, cov).sample((samples_per_class,))
                class_labels = torch.full((samples_per_class,), class_id)
                
                data.append(class_data)
                labels.append(class_labels)
            
            data = torch.cat(data, dim=0)
            labels = torch.cat(labels, dim=0)
            
            # Shuffle
            perm = torch.randperm(len(data))
            data = data[perm]
            labels = labels[perm]
        else:
            # Default to uniform
            data = torch.randn(num_samples, input_dim)
            labels = torch.randint(0, output_dim, (num_samples,))
        
        return data, labels
    
    def generate_task_batch(self, batch_size: int, input_dim: int = 100, output_dim: int = 10) -> List[Dict[str, Any]]:
        """Generate a batch of tasks"""
        tasks = []
        for _ in range(batch_size):
            task = self.generate_task(input_dim, output_dim)
            tasks.append(task)
        return tasks

class MAML:
    """Model-Agnostic Meta-Learning implementation"""
    
    def __init__(self, model: nn.Module, config: MetaLearningConfig):
        self.model = model
        self.config = config
        self.meta_optimizer = optim.Adam(model.parameters(), lr=config.meta_lr)
        
        # Store initial parameters
        self.initial_params = [param.clone().detach() for param in model.parameters()]
        
        logger.info("✅ MAML initialized")
    
    def meta_update(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform meta-update using MAML"""
        total_loss = 0.0
        num_tasks = len(tasks)
        
        # Store original parameters
        original_params = [param.clone().detach() for param in self.model.parameters()]
        
        # Process each task
        task_losses = []
        
        for task in tasks:
            # Inner loop: adapt to task
            adapted_params = self._inner_loop(task)
            
            # Outer loop: evaluate on query set
            query_loss = self._evaluate_on_query(task, adapted_params)
            task_losses.append(query_loss)
            total_loss += query_loss
        
        # Meta-update
        meta_loss = total_loss / num_tasks
        
        self.meta_optimizer.zero_grad()
        meta_loss.backward()
        self.meta_optimizer.step()
        
        return {
            'meta_loss': meta_loss.item(),
            'task_losses': [loss.item() for loss in task_losses],
            'num_tasks': num_tasks
        }
    
    def _inner_loop(self, task: Dict[str, Any]) -> List[torch.Tensor]:
        """Inner loop: adapt model to task"""
        # Get support data
        support_data = task['support_data']
        support_labels = task['support_labels']
        
        # Create temporary optimizer for inner loop
        temp_optimizer = optim.SGD(self.model.parameters(), lr=self.config.inner_lr)
        
        # Store original parameters
        original_params = [param.clone().detach() for param in self.model.parameters()]
        
        # Inner gradient steps
        for step in range(self.config.inner_steps):
            temp_optimizer.zero_grad()
            
            # Forward pass
            outputs = self.model(support_data)
            loss = nn.CrossEntropyLoss()(outputs, support_labels)
            
            # Backward pass
            loss.backward()
            temp_optimizer.step()
        
        # Return adapted parameters
        adapted_params = [param.clone().detach() for param in self.model.parameters()]
        
        # Restore original parameters
        for param, original_param in zip(self.model.parameters(), original_params):
            param.data = original_param.data.clone()
        
        return adapted_params
    
    def _evaluate_on_query(self, task: Dict[str, Any], adapted_params: List[torch.Tensor]) -> torch.Tensor:
        """Evaluate adapted model on query set"""
        # Set adapted parameters
        for param, adapted_param in zip(self.model.parameters(), adapted_params):
            param.data = adapted_param.data.clone()
        
        # Evaluate on query set
        query_data = task['query_data']
        query_labels = task['query_labels']
        
        with torch.no_grad():
            outputs = self.model(query_data)
            loss = nn.CrossEntropyLoss()(outputs, query_labels)
        
        return loss
    
    def adapt_to_task(self, task: Dict[str, Any], num_steps: int = None) -> nn.Module:
        """Adapt model to a specific task"""
        if num_steps is None:
            num_steps = self.config.inner_steps
        
        # Create copy of model
        adapted_model = type(self.model)()
        adapted_model.load_state_dict(self.model.state_dict())
        
        # Adapt model
        optimizer = optim.SGD(adapted_model.parameters(), lr=self.config.inner_lr)
        
        support_data = task['support_data']
        support_labels = task['support_labels']
        
        for step in range(num_steps):
            optimizer.zero_grad()
            
            outputs = adapted_model(support_data)
            loss = nn.CrossEntropyLoss()(outputs, support_labels)
            
            loss.backward()
            optimizer.step()
        
        return adapted_model

class Reptile:
    """Reptile meta-learning algorithm"""
    
    def __init__(self, model: nn.Module, config: MetaLearningConfig):
        self.model = model
        self.config = config
        self.meta_optimizer = optim.Adam(model.parameters(), lr=config.meta_lr)
        
        logger.info("✅ Reptile initialized")
    
    def meta_update(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform meta-update using Reptile"""
        total_loss = 0.0
        num_tasks = len(tasks)
        
        # Store original parameters
        original_params = [param.clone().detach() for param in self.model.parameters()]
        
        # Process each task
        task_losses = []
        adapted_params_list = []
        
        for task in tasks:
            # Inner loop: adapt to task
            adapted_params = self._inner_loop(task)
            adapted_params_list.append(adapted_params)
            
            # Evaluate on query set
            query_loss = self._evaluate_on_query(task, adapted_params)
            task_losses.append(query_loss)
            total_loss += query_loss
        
        # Reptile update: interpolate between original and adapted parameters
        for param in self.model.parameters():
            param.grad = torch.zeros_like(param)
        
        for adapted_params in adapted_params_list:
            for param, adapted_param in zip(self.model.parameters(), adapted_params):
                param.grad += (adapted_param - param) / num_tasks
        
        # Meta-update
        meta_loss = total_loss / num_tasks
        
        self.meta_optimizer.step()
        
        return {
            'meta_loss': meta_loss.item(),
            'task_losses': [loss.item() for loss in task_losses],
            'num_tasks': num_tasks
        }
    
    def _inner_loop(self, task: Dict[str, Any]) -> List[torch.Tensor]:
        """Inner loop: adapt model to task"""
        # Get support data
        support_data = task['support_data']
        support_labels = task['support_labels']
        
        # Create temporary optimizer for inner loop
        temp_optimizer = optim.SGD(self.model.parameters(), lr=self.config.inner_lr)
        
        # Store original parameters
        original_params = [param.clone().detach() for param in self.model.parameters()]
        
        # Inner gradient steps
        for step in range(self.config.inner_steps):
            temp_optimizer.zero_grad()
            
            # Forward pass
            outputs = self.model(support_data)
            loss = nn.CrossEntropyLoss()(outputs, support_labels)
            
            # Backward pass
            loss.backward()
            temp_optimizer.step()
        
        # Return adapted parameters
        adapted_params = [param.clone().detach() for param in self.model.parameters()]
        
        # Restore original parameters
        for param, original_param in zip(self.model.parameters(), original_params):
            param.data = original_param.data.clone()
        
        return adapted_params
    
    def _evaluate_on_query(self, task: Dict[str, Any], adapted_params: List[torch.Tensor]) -> torch.Tensor:
        """Evaluate adapted model on query set"""
        # Set adapted parameters
        for param, adapted_param in zip(self.model.parameters(), adapted_params):
            param.data = adapted_param.data.clone()
        
        # Evaluate on query set
        query_data = task['query_data']
        query_labels = task['query_labels']
        
        with torch.no_grad():
            outputs = self.model(query_data)
            loss = nn.CrossEntropyLoss()(outputs, query_labels)
        
        return loss

class MetaLearner:
    """Main meta-learning system"""
    
    def __init__(self, model: nn.Module, config: MetaLearningConfig):
        self.model = model
        self.config = config
        self.task_generator = TaskGenerator(config)
        
        # Initialize meta-learning algorithm
        if config.algorithm == MetaLearningAlgorithm.MAML:
            self.meta_algorithm = MAML(model, config)
        elif config.algorithm == MetaLearningAlgorithm.REPTILE:
            self.meta_algorithm = Reptile(model, config)
        else:
            self.meta_algorithm = MAML(model, config)  # Default to MAML
        
        # Training state
        self.training_history = []
        self.validation_history = []
        self.best_performance = 0.0
        
        logger.info(f"✅ Meta-Learner initialized with {config.algorithm.value}")
    
    def train(self, num_iterations: int = 1000) -> Dict[str, Any]:
        """Train meta-learner"""
        logger.info(f"🚀 Starting meta-learning training for {num_iterations} iterations")
        
        start_time = time.time()
        
        for iteration in range(num_iterations):
            # Generate task batch
            tasks = self.task_generator.generate_task_batch(
                self.config.meta_batch_size
            )
            
            # Meta-update
            meta_stats = self.meta_algorithm.meta_update(tasks)
            
            # Record training history
            self.training_history.append({
                'iteration': iteration,
                'meta_loss': meta_stats['meta_loss'],
                'avg_task_loss': np.mean(meta_stats['task_losses']),
                'timestamp': time.time()
            })
            
            # Validation
            if self.config.enable_meta_validation and iteration % self.config.validation_frequency == 0:
                val_performance = self.validate()
                self.validation_history.append({
                    'iteration': iteration,
                    'performance': val_performance,
                    'timestamp': time.time()
                })
                
                # Update best performance
                if val_performance > self.best_performance:
                    self.best_performance = val_performance
                
                logger.info(f"Iteration {iteration}: Meta-loss = {meta_stats['meta_loss']:.4f}, "
                          f"Validation = {val_performance:.4f}")
            
            # Early stopping
            if self._check_early_stopping():
                logger.info(f"✅ Early stopping at iteration {iteration}")
                break
        
        total_time = time.time() - start_time
        
        final_stats = {
            'total_iterations': len(self.training_history),
            'total_time': total_time,
            'best_performance': self.best_performance,
            'final_meta_loss': self.training_history[-1]['meta_loss'] if self.training_history else 0.0,
            'training_history': self.training_history,
            'validation_history': self.validation_history
        }
        
        logger.info(f"✅ Meta-learning training completed in {total_time:.2f}s")
        return final_stats
    
    def validate(self) -> float:
        """Validate meta-learner performance"""
        # Generate validation tasks
        val_tasks = self.task_generator.generate_task_batch(10)
        
        total_performance = 0.0
        
        for task in val_tasks:
            # Adapt model to task
            adapted_model = self.meta_algorithm.adapt_to_task(task)
            
            # Evaluate on query set
            query_data = task['query_data']
            query_labels = task['query_labels']
            
            with torch.no_grad():
                outputs = adapted_model(query_data)
                _, predicted = torch.max(outputs, 1)
                accuracy = (predicted == query_labels).float().mean().item()
                total_performance += accuracy
        
        return total_performance / len(val_tasks)
    
    def _check_early_stopping(self) -> bool:
        """Check for early stopping condition"""
        if len(self.validation_history) < self.config.early_stopping_patience:
            return False
        
        # Check if performance has not improved
        recent_performances = [h['performance'] for h in self.validation_history[-self.config.early_stopping_patience:]]
        
        if max(recent_performances) - min(recent_performances) < 0.001:
            return True
        
        return False
    
    def few_shot_learn(self, support_data: torch.Tensor, support_labels: torch.Tensor,
                      query_data: torch.Tensor, query_labels: torch.Tensor,
                      num_adaptation_steps: int = None) -> Tuple[nn.Module, float]:
        """Perform few-shot learning on new task"""
        if num_adaptation_steps is None:
            num_adaptation_steps = self.config.inner_steps
        
        # Create task
        task = {
            'support_data': support_data,
            'support_labels': support_labels,
            'query_data': query_data,
            'query_labels': query_labels
        }
        
        # Adapt model to task
        adapted_model = self.meta_algorithm.adapt_to_task(task, num_adaptation_steps)
        
        # Evaluate performance
        with torch.no_grad():
            outputs = adapted_model(query_data)
            _, predicted = torch.max(outputs, 1)
            accuracy = (predicted == query_labels).float().mean().item()
        
        return adapted_model, accuracy
    
    def get_meta_learning_statistics(self) -> Dict[str, Any]:
        """Get meta-learning statistics"""
        return {
            'algorithm': self.config.algorithm.value,
            'total_iterations': len(self.training_history),
            'best_performance': self.best_performance,
            'final_meta_loss': self.training_history[-1]['meta_loss'] if self.training_history else 0.0,
            'avg_meta_loss': np.mean([h['meta_loss'] for h in self.training_history]) if self.training_history else 0.0,
            'validation_performances': [h['performance'] for h in self.validation_history],
            'config': {
                'meta_lr': self.config.meta_lr,
                'inner_lr': self.config.inner_lr,
                'inner_steps': self.config.inner_steps,
                'meta_batch_size': self.config.meta_batch_size
            }
        }

# Factory functions
def create_meta_learning_config(**kwargs) -> MetaLearningConfig:
    """Create meta-learning configuration"""
    return MetaLearningConfig(**kwargs)

def create_meta_learner(model: nn.Module, config: MetaLearningConfig) -> MetaLearner:
    """Create meta-learner instance"""
    return MetaLearner(model, config)

# Example usage
def example_meta_learning():
    """Example of meta-learning"""
    # Create configuration
    config = create_meta_learning_config(
        algorithm=MetaLearningAlgorithm.MAML,
        meta_lr=0.001,
        inner_lr=0.01,
        inner_steps=5,
        meta_batch_size=8,
        num_tasks=500,
        enable_meta_validation=True,
        validation_frequency=50
    )
    
    # Create model
    model = nn.Sequential(
        nn.Linear(100, 64),
        nn.ReLU(),
        nn.Linear(64, 32),
        nn.ReLU(),
        nn.Linear(32, 10)
    )
    
    # Create meta-learner
    meta_learner = create_meta_learner(model, config)
    
    # Train meta-learner
    training_stats = meta_learner.train(num_iterations=200)
    
    # Get statistics
    stats = meta_learner.get_meta_learning_statistics()
    
    print(f"✅ Meta-Learning Example Complete!")
    print(f"🧠 Meta-Learning Statistics:")
    print(f"   Algorithm: {stats['algorithm']}")
    print(f"   Total Iterations: {stats['total_iterations']}")
    print(f"   Best Performance: {stats['best_performance']:.4f}")
    print(f"   Final Meta-Loss: {stats['final_meta_loss']:.4f}")
    print(f"   Average Meta-Loss: {stats['avg_meta_loss']:.4f}")
    
    # Test few-shot learning
    support_data = torch.randn(5, 100)
    support_labels = torch.randint(0, 10, (5,))
    query_data = torch.randn(15, 100)
    query_labels = torch.randint(0, 10, (15,))
    
    adapted_model, accuracy = meta_learner.few_shot_learn(
        support_data, support_labels, query_data, query_labels
    )
    
    print(f"🎯 Few-Shot Learning Test:")
    print(f"   Support samples: {len(support_data)}")
    print(f"   Query samples: {len(query_data)}")
    print(f"   Accuracy: {accuracy:.4f}")
    
    return meta_learner

# Export utilities
__all__ = [
    'MetaLearningAlgorithm',
    'TaskDistribution',
    'MetaLearningConfig',
    'TaskGenerator',
    'MAML',
    'Reptile',
    'MetaLearner',
    'create_meta_learning_config',
    'create_meta_learner',
    'example_meta_learning'
]

if __name__ == "__main__":
    example_meta_learning()
    print("✅ Meta-learning example completed successfully!")

