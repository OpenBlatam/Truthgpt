"""
Advanced Neural Network Multi-Task Learning System for TruthGPT Optimization Core
Complete multi-task learning with shared representations, task balancing, and gradient surgery
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
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
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Task types"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    OBJECT_DETECTION = "object_detection"
    SEGMENTATION = "segmentation"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    QUESTION_ANSWERING = "question_answering"
    SENTIMENT_ANALYSIS = "sentiment_analysis"

class TaskRelationship(Enum):
    """Task relationships"""
    INDEPENDENT = "independent"
    RELATED = "related"
    HIERARCHICAL = "hierarchical"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    DEPENDENT = "dependent"

class SharingStrategy(Enum):
    """Sharing strategies"""
    HARD_SHARING = "hard_sharing"
    SOFT_SHARING = "soft_sharing"
    TASK_SPECIFIC = "task_specific"
    ADAPTIVE_SHARING = "adaptive_sharing"
    HIERARCHICAL_SHARING = "hierarchical_sharing"

class MultiTaskConfig:
    """Configuration for multi-task learning system"""
    # Basic settings
    task_types: List[TaskType] = field(default_factory=lambda: [TaskType.CLASSIFICATION, TaskType.REGRESSION])
    task_relationships: List[TaskRelationship] = field(default_factory=lambda: [TaskRelationship.RELATED])
    sharing_strategy: SharingStrategy = SharingStrategy.HARD_SHARING
    
    # Model architecture
    shared_hidden_dim: int = 512
    task_specific_dim: int = 256
    num_shared_layers: int = 3
    num_task_specific_layers: int = 2
    
    # Training settings
    learning_rate: float = 0.001
    batch_size: int = 32
    num_epochs: int = 100
    
    # Task balancing
    enable_task_balancing: bool = True
    task_balancing_method: str = "uncertainty_weighting"
    task_weights: List[float] = field(default_factory=lambda: [1.0, 1.0])
    
    # Gradient surgery
    enable_gradient_surgery: bool = True
    gradient_surgery_method: str = "pcgrad"
    gradient_surgery_lambda: float = 0.1
    
    # Advanced features
    enable_meta_learning: bool = False
    enable_transfer_learning: bool = True
    enable_continual_learning: bool = False
    enable_adaptive_sharing: bool = True
    
    def __post_init__(self):
        """Validate multi-task configuration"""
        if self.shared_hidden_dim <= 0:
            raise ValueError("Shared hidden dimension must be positive")
        if self.task_specific_dim <= 0:
            raise ValueError("Task-specific dimension must be positive")
        if self.num_shared_layers <= 0:
            raise ValueError("Number of shared layers must be positive")
        if self.num_task_specific_layers <= 0:
            raise ValueError("Number of task-specific layers must be positive")
        if self.learning_rate <= 0:
            raise ValueError("Learning rate must be positive")
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")
        if self.num_epochs <= 0:
            raise ValueError("Number of epochs must be positive")
        if not (0 <= self.gradient_surgery_lambda <= 1):
            raise ValueError("Gradient surgery lambda must be between 0 and 1")

class TaskBalancer:
    """Task balancing for multi-task learning"""
    
    def __init__(self, config: MultiTaskConfig):
        self.config = config
        self.task_losses = []
        self.task_weights = []
        self.balancing_history = []
        logger.info("✅ Task Balancer initialized")
    
    def balance_tasks(self, task_losses: List[float], task_gradients: List[torch.Tensor] = None) -> List[float]:
        """Balance task losses"""
        logger.info(f"⚖️ Balancing tasks using method: {self.config.task_balancing_method}")
        
        if self.config.task_balancing_method == "uncertainty_weighting":
            weights = self._uncertainty_weighting(task_losses)
        elif self.config.task_balancing_method == "gradnorm":
            weights = self._gradnorm_weighting(task_losses, task_gradients)
        elif self.config.task_balancing_method == "dwa":
            weights = self._dwa_weighting(task_losses)
        elif self.config.task_balancing_method == "equal_weighting":
            weights = self._equal_weighting(task_losses)
        else:
            weights = self._uncertainty_weighting(task_losses)
        
        # Store balancing history
        self.balancing_history.append({
            'task_losses': task_losses,
            'task_weights': weights,
            'method': self.config.task_balancing_method
        })
        
        return weights
    
    def _uncertainty_weighting(self, task_losses: List[float]) -> List[float]:
        """Uncertainty weighting for task balancing"""
        logger.info("🎯 Applying uncertainty weighting")
        
        # Calculate uncertainty weights
        weights = []
        for loss in task_losses:
            # Higher loss = higher uncertainty = lower weight
            weight = 1.0 / (loss + 1e-8)
            weights.append(weight)
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        return weights
    
    def _gradnorm_weighting(self, task_losses: List[float], task_gradients: List[torch.Tensor]) -> List[float]:
        """GradNorm weighting for task balancing"""
        logger.info("📊 Applying GradNorm weighting")
        
        if task_gradients is None:
            return self._equal_weighting(task_losses)
        
        # Calculate gradient norms
        grad_norms = []
        for grad in task_gradients:
            grad_norm = torch.norm(grad).item()
            grad_norms.append(grad_norm)
        
        # Calculate weights based on gradient norms
        weights = []
        avg_grad_norm = np.mean(grad_norms)
        
        for grad_norm in grad_norms:
            weight = avg_grad_norm / (grad_norm + 1e-8)
            weights.append(weight)
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        return weights
    
    def _dwa_weighting(self, task_losses: List[float]) -> List[float]:
        """Dynamic Weight Average (DWA) weighting"""
        logger.info("🔄 Applying DWA weighting")
        
        if len(self.task_losses) < 2:
            return self._equal_weighting(task_losses)
        
        # Calculate relative loss changes
        weights = []
        for i, current_loss in enumerate(task_losses):
            if i < len(self.task_losses[-1]):
                previous_loss = self.task_losses[-1][i]
                relative_change = current_loss / (previous_loss + 1e-8)
                weight = relative_change
            else:
                weight = 1.0
            weights.append(weight)
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        return weights
    
    def _equal_weighting(self, task_losses: List[float]) -> List[float]:
        """Equal weighting for all tasks"""
        logger.info("⚖️ Applying equal weighting")
        
        n_tasks = len(task_losses)
        weights = [1.0 / n_tasks] * n_tasks
        
        return weights

class GradientSurgery:
    """Gradient surgery for multi-task learning"""
    
    def __init__(self, config: MultiTaskConfig):
        self.config = config
        self.surgery_history = []
        logger.info("✅ Gradient Surgery initialized")
    
    def apply_gradient_surgery(self, task_gradients: List[torch.Tensor]) -> List[torch.Tensor]:
        """Apply gradient surgery to task gradients"""
        logger.info(f"🔧 Applying gradient surgery using method: {self.config.gradient_surgery_method}")
        
        if self.config.gradient_surgery_method == "pcgrad":
            modified_gradients = self._pcgrad_surgery(task_gradients)
        elif self.config.gradient_surgery_method == "mgda":
            modified_gradients = self._mgda_surgery(task_gradients)
        elif self.config.gradient_surgery_method == "graddrop":
            modified_gradients = self._graddrop_surgery(task_gradients)
        else:
            modified_gradients = self._pcgrad_surgery(task_gradients)
        
        # Store surgery history
        self.surgery_history.append({
            'original_gradients': task_gradients,
            'modified_gradients': modified_gradients,
            'method': self.config.gradient_surgery_method
        })
        
        return modified_gradients
    
    def _pcgrad_surgery(self, task_gradients: List[torch.Tensor]) -> List[torch.Tensor]:
        """PCGrad gradient surgery"""
        logger.info("🔧 Applying PCGrad surgery")
        
        modified_gradients = []
        
        for i, grad_i in enumerate(task_gradients):
            modified_grad = grad_i.clone()
            
            for j, grad_j in enumerate(task_gradients):
                if i != j:
                    # Calculate dot product
                    dot_product = torch.dot(grad_i.flatten(), grad_j.flatten())
                    
                    if dot_product < 0:
                        # Project grad_i onto grad_j
                        projection = dot_product / (torch.norm(grad_j.flatten())**2 + 1e-8)
                        modified_grad = modified_grad - projection * grad_j
            
            modified_gradients.append(modified_grad)
        
        return modified_gradients
    
    def _mgda_surgery(self, task_gradients: List[torch.Tensor]) -> List[torch.Tensor]:
        """MGDA gradient surgery"""
        logger.info("🔧 Applying MGDA surgery")
        
        # Calculate MGDA weights
        mgda_weights = self._calculate_mgda_weights(task_gradients)
        
        # Apply weighted combination
        modified_gradients = []
        for i, grad in enumerate(task_gradients):
            modified_grad = mgda_weights[i] * grad
            modified_gradients.append(modified_grad)
        
        return modified_gradients
    
    def _graddrop_surgery(self, task_gradients: List[torch.Tensor]) -> List[torch.Tensor]:
        """GradDrop gradient surgery"""
        logger.info("🔧 Applying GradDrop surgery")
        
        # Stack gradients
        stacked_gradients = torch.stack(task_gradients, dim=0)
        
        # Calculate gradient magnitudes
        grad_magnitudes = torch.norm(stacked_gradients, dim=1, keepdim=True)
        
        # Calculate drop probabilities
        drop_probs = torch.sigmoid(-grad_magnitudes)
        
        # Apply dropout
        modified_gradients = []
        for i, grad in enumerate(task_gradients):
            mask = torch.rand_like(grad) > drop_probs[i]
            modified_grad = grad * mask.float()
            modified_gradients.append(modified_grad)
        
        return modified_gradients
    
    def _calculate_mgda_weights(self, task_gradients: List[torch.Tensor]) -> List[float]:
        """Calculate MGDA weights"""
        # Simplified MGDA weight calculation
        n_tasks = len(task_gradients)
        weights = [1.0 / n_tasks] * n_tasks
        
        return weights

class SharedRepresentation:
    """Shared representation learning"""
    
    def __init__(self, config: MultiTaskConfig):
        self.config = config
        self.shared_layers = []
        self.representation_history = []
        logger.info("✅ Shared Representation initialized")
    
    def create_shared_representation(self, input_dim: int) -> nn.Module:
        """Create shared representation layers"""
        logger.info(f"🏗️ Creating shared representation with {self.config.num_shared_layers} layers")
        
        layers = []
        current_dim = input_dim
        
        for i in range(self.config.num_shared_layers):
            layers.append(nn.Linear(current_dim, self.config.shared_hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.1))
            current_dim = self.config.shared_hidden_dim
        
        shared_representation = nn.Sequential(*layers)
        
        # Store shared layers
        self.shared_layers = layers
        
        return shared_representation
    
    def update_shared_representation(self, shared_repr: nn.Module, task_gradients: List[torch.Tensor]):
        """Update shared representation based on task gradients"""
        logger.info("🔄 Updating shared representation")
        
        # Calculate average gradient for shared layers
        avg_gradient = torch.zeros_like(list(shared_repr.parameters())[0])
        
        for grad in task_gradients:
            avg_gradient += grad
        
        avg_gradient /= len(task_gradients)
        
        # Update shared representation
        with torch.no_grad():
            for param in shared_repr.parameters():
                param.data -= self.config.learning_rate * avg_gradient
        
        # Store representation history
        self.representation_history.append({
            'avg_gradient': avg_gradient,
            'task_gradients': task_gradients
        })

class MultiTaskHead:
    """Multi-task head for specific tasks"""
    
    def __init__(self, config: MultiTaskConfig, task_type: TaskType):
        self.config = config
        self.task_type = task_type
        self.task_head = None
        logger.info(f"✅ Multi-Task Head for {task_type.value} initialized")
    
    def create_task_head(self, input_dim: int, output_dim: int) -> nn.Module:
        """Create task-specific head"""
        logger.info(f"🎯 Creating task head for {self.task_type.value}")
        
        layers = []
        current_dim = input_dim
        
        for i in range(self.config.num_task_specific_layers):
            if i == self.config.num_task_specific_layers - 1:
                # Output layer
                layers.append(nn.Linear(current_dim, output_dim))
            else:
                # Hidden layers
                layers.append(nn.Linear(current_dim, self.config.task_specific_dim))
                layers.append(nn.ReLU())
                layers.append(nn.Dropout(0.1))
                current_dim = self.config.task_specific_dim
        
        task_head = nn.Sequential(*layers)
        self.task_head = task_head
        
        return task_head

class MultiTaskNetwork:
    """Multi-task neural network"""
    
    def __init__(self, config: MultiTaskConfig):
        self.config = config
        
        # Components
        self.task_balancer = TaskBalancer(config)
        self.gradient_surgery = GradientSurgery(config)
        self.shared_representation = SharedRepresentation(config)
        self.task_heads = {}
        
        # Network components
        self.shared_layers = None
        self.task_specific_layers = {}
        
        logger.info("✅ Multi-Task Network initialized")
    
    def build_network(self, input_dim: int, task_output_dims: Dict[TaskType, int]) -> nn.Module:
        """Build multi-task network"""
        logger.info("🏗️ Building multi-task network")
        
        # Create shared representation
        self.shared_layers = self.shared_representation.create_shared_representation(input_dim)
        
        # Create task-specific heads
        for task_type, output_dim in task_output_dims.items():
            task_head = MultiTaskHead(self.config, task_type)
            self.task_specific_layers[task_type] = task_head.create_task_head(
                self.config.shared_hidden_dim, output_dim
            )
        
        return self
    
    def forward(self, x: torch.Tensor, task_type: TaskType) -> torch.Tensor:
        """Forward pass for specific task"""
        # Shared representation
        shared_features = self.shared_layers(x)
        
        # Task-specific head
        task_output = self.task_specific_layers[task_type](shared_features)
        
        return task_output
    
    def compute_task_losses(self, outputs: Dict[TaskType, torch.Tensor], 
                           targets: Dict[TaskType, torch.Tensor]) -> Dict[TaskType, torch.Tensor]:
        """Compute losses for all tasks"""
        task_losses = {}
        
        for task_type in outputs.keys():
            if task_type == TaskType.CLASSIFICATION:
                loss = F.cross_entropy(outputs[task_type], targets[task_type])
            elif task_type == TaskType.REGRESSION:
                loss = F.mse_loss(outputs[task_type], targets[task_type])
            else:
                loss = F.mse_loss(outputs[task_type], targets[task_type])
            
            task_losses[task_type] = loss
        
        return task_losses
    
    def compute_weighted_loss(self, task_losses: Dict[TaskType, torch.Tensor]) -> torch.Tensor:
        """Compute weighted loss across tasks"""
        if self.config.enable_task_balancing:
            # Get task weights
            loss_values = [loss.item() for loss in task_losses.values()]
            task_weights = self.task_balancer.balance_tasks(loss_values)
            
            # Apply weights
            weighted_loss = torch.tensor(0.0)
            for i, (task_type, loss) in enumerate(task_losses.items()):
                weighted_loss += task_weights[i] * loss
        else:
            # Equal weighting
            weighted_loss = sum(task_losses.values()) / len(task_losses)
        
        return weighted_loss

class MultiTaskTrainer:
    """Multi-task learning trainer"""
    
    def __init__(self, config: MultiTaskConfig):
        self.config = config
        
        # Components
        self.multi_task_network = MultiTaskNetwork(config)
        self.optimizer = None
        self.scheduler = None
        
        # Training state
        self.training_history = []
        self.task_performance = {}
        
        logger.info("✅ Multi-Task Trainer initialized")
    
    def train(self, train_data: Dict[TaskType, Tuple[torch.Tensor, torch.Tensor]], 
              val_data: Dict[TaskType, Tuple[torch.Tensor, torch.Tensor]] = None) -> Dict[str, Any]:
        """Train multi-task model"""
        logger.info(f"🚀 Training multi-task model with {len(train_data)} tasks")
        
        training_results = {
            'start_time': time.time(),
            'config': self.config,
            'epochs': []
        }
        
        # Initialize optimizer
        all_parameters = []
        all_parameters.extend(self.multi_task_network.shared_layers.parameters())
        for task_head in self.multi_task_network.task_specific_layers.values():
            all_parameters.extend(task_head.parameters())
        
        self.optimizer = torch.optim.Adam(all_parameters, lr=self.config.learning_rate)
        
        # Training loop
        for epoch in range(self.config.num_epochs):
            logger.info(f"🔄 Epoch {epoch + 1}/{self.config.num_epochs}")
            
            # Training phase
            train_metrics = self._train_epoch(train_data)
            
            # Validation phase
            val_metrics = {}
            if val_data:
                val_metrics = self._validate_epoch(val_data)
            
            # Store epoch results
            epoch_result = {
                'epoch': epoch,
                'train_metrics': train_metrics,
                'val_metrics': val_metrics
            }
            
            training_results['epochs'].append(epoch_result)
            
            if epoch % 10 == 0:
                logger.info(f"   Epoch {epoch}: Train Loss = {train_metrics.get('total_loss', 0):.4f}")
        
        # Final evaluation
        training_results['end_time'] = time.time()
        training_results['total_duration'] = training_results['end_time'] - training_results['start_time']
        
        # Store results
        self.training_history.append(training_results)
        
        logger.info("✅ Multi-task training completed")
        return training_results
    
    def _train_epoch(self, train_data: Dict[TaskType, Tuple[torch.Tensor, torch.Tensor]]) -> Dict[str, float]:
        """Train for one epoch"""
        self.multi_task_network.shared_layers.train()
        for task_head in self.multi_task_network.task_specific_layers.values():
            task_head.train()
        
        total_loss = 0.0
        task_losses = {}
        
        # Get batch size
        batch_size = self.config.batch_size
        
        # Sample batches from each task
        task_batches = {}
        for task_type, (X, y) in train_data.items():
            n_samples = len(X)
            batch_indices = torch.randperm(n_samples)[:batch_size]
            task_batches[task_type] = (X[batch_indices], y[batch_indices])
        
        # Forward pass for all tasks
        task_outputs = {}
        for task_type, (X, y) in task_batches.items():
            output = self.multi_task_network.forward(X, task_type)
            task_outputs[task_type] = output
        
        # Compute task losses
        task_losses = self.multi_task_network.compute_task_losses(
            task_outputs, {task_type: y for task_type, (X, y) in task_batches.items()}
        )
        
        # Compute weighted loss
        weighted_loss = self.multi_task_network.compute_weighted_loss(task_losses)
        
        # Backward pass
        self.optimizer.zero_grad()
        weighted_loss.backward()
        
        # Apply gradient surgery if enabled
        if self.config.enable_gradient_surgery:
            task_gradients = [loss.grad for loss in task_losses.values()]
            modified_gradients = self.multi_task_network.gradient_surgery.apply_gradient_surgery(task_gradients)
            
            # Update gradients
            for i, (task_type, loss) in enumerate(task_losses.items()):
                loss.grad = modified_gradients[i]
        
        # Update parameters
        self.optimizer.step()
        
        # Store metrics
        metrics = {
            'total_loss': weighted_loss.item(),
            'task_losses': {task_type.value: loss.item() for task_type, loss in task_losses.items()}
        }
        
        return metrics
    
    def _validate_epoch(self, val_data: Dict[TaskType, Tuple[torch.Tensor, torch.Tensor]]) -> Dict[str, float]:
        """Validate for one epoch"""
        self.multi_task_network.shared_layers.eval()
        for task_head in self.multi_task_network.task_specific_layers.values():
            task_head.eval()
        
        total_loss = 0.0
        task_losses = {}
        
        with torch.no_grad():
            # Sample batches from each task
            task_batches = {}
            for task_type, (X, y) in val_data.items():
                n_samples = len(X)
                batch_indices = torch.randperm(n_samples)[:self.config.batch_size]
                task_batches[task_type] = (X[batch_indices], y[batch_indices])
            
            # Forward pass for all tasks
            task_outputs = {}
            for task_type, (X, y) in task_batches.items():
                output = self.multi_task_network.forward(X, task_type)
                task_outputs[task_type] = output
            
            # Compute task losses
            task_losses = self.multi_task_network.compute_task_losses(
                task_outputs, {task_type: y for task_type, (X, y) in task_batches.items()}
            )
            
            # Compute weighted loss
            weighted_loss = self.multi_task_network.compute_weighted_loss(task_losses)
        
        # Store metrics
        metrics = {
            'total_loss': weighted_loss.item(),
            'task_losses': {task_type.value: loss.item() for task_type, loss in task_losses.items()}
        }
        
        return metrics
    
    def generate_training_report(self, results: Dict[str, Any]) -> str:
        """Generate training report"""
        report = []
        report.append("=" * 50)
        report.append("MULTI-TASK LEARNING REPORT")
        report.append("=" * 50)
        
        # Configuration
        report.append("\nMULTI-TASK LEARNING CONFIGURATION:")
        report.append("-" * 35)
        report.append(f"Task Types: {[t.value for t in self.config.task_types]}")
        report.append(f"Task Relationships: {[r.value for r in self.config.task_relationships]}")
        report.append(f"Sharing Strategy: {self.config.sharing_strategy.value}")
        report.append(f"Shared Hidden Dimension: {self.config.shared_hidden_dim}")
        report.append(f"Task-Specific Dimension: {self.config.task_specific_dim}")
        report.append(f"Number of Shared Layers: {self.config.num_shared_layers}")
        report.append(f"Number of Task-Specific Layers: {self.config.num_task_specific_layers}")
        report.append(f"Learning Rate: {self.config.learning_rate}")
        report.append(f"Batch Size: {self.config.batch_size}")
        report.append(f"Number of Epochs: {self.config.num_epochs}")
        report.append(f"Task Balancing: {'Enabled' if self.config.enable_task_balancing else 'Disabled'}")
        report.append(f"Task Balancing Method: {self.config.task_balancing_method}")
        report.append(f"Task Weights: {self.config.task_weights}")
        report.append(f"Gradient Surgery: {'Enabled' if self.config.enable_gradient_surgery else 'Disabled'}")
        report.append(f"Gradient Surgery Method: {self.config.gradient_surgery_method}")
        report.append(f"Gradient Surgery Lambda: {self.config.gradient_surgery_lambda}")
        report.append(f"Meta Learning: {'Enabled' if self.config.enable_meta_learning else 'Disabled'}")
        report.append(f"Transfer Learning: {'Enabled' if self.config.enable_transfer_learning else 'Disabled'}")
        report.append(f"Continual Learning: {'Enabled' if self.config.enable_continual_learning else 'Disabled'}")
        report.append(f"Adaptive Sharing: {'Enabled' if self.config.enable_adaptive_sharing else 'Disabled'}")
        
        # Results
        report.append("\nMULTI-TASK LEARNING RESULTS:")
        report.append("-" * 30)
        report.append(f"Total Duration: {results.get('total_duration', 0):.2f} seconds")
        report.append(f"Start Time: {results.get('start_time', 'Unknown')}")
        report.append(f"End Time: {results.get('end_time', 'Unknown')}")
        report.append(f"Number of Epochs: {len(results.get('epochs', []))}")
        
        # Epoch results
        if 'epochs' in results:
            final_epoch = results['epochs'][-1]
            report.append(f"Final Train Loss: {final_epoch.get('train_metrics', {}).get('total_loss', 0):.4f}")
            
            if 'val_metrics' in final_epoch:
                report.append(f"Final Val Loss: {final_epoch['val_metrics'].get('total_loss', 0):.4f}")
        
        return "\n".join(report)
    
    def visualize_training_results(self, save_path: str = None):
        """Visualize training results"""
        if not self.training_history:
            logger.warning("No training history to visualize")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Plot 1: Training duration over time
        durations = [r.get('total_duration', 0) for r in self.training_history]
        axes[0, 0].plot(durations, 'b-', linewidth=2)
        axes[0, 0].set_xlabel('Training Run')
        axes[0, 0].set_ylabel('Duration (seconds)')
        axes[0, 0].set_title('Multi-Task Training Duration Over Time')
        axes[0, 0].grid(True)
        
        # Plot 2: Task type distribution
        task_types = [t.value for t in self.config.task_types]
        task_counts = [1] * len(task_types)
        
        axes[0, 1].pie(task_counts, labels=task_types, autopct='%1.1f%%')
        axes[0, 1].set_title('Task Type Distribution')
        
        # Plot 3: Sharing strategy distribution
        sharing_strategies = [self.config.sharing_strategy.value]
        strategy_counts = [1]
        
        axes[1, 0].pie(strategy_counts, labels=sharing_strategies, autopct='%1.1f%%')
        axes[1, 0].set_title('Sharing Strategy Distribution')
        
        # Plot 4: Multi-task configuration
        config_values = [
            self.config.shared_hidden_dim,
            self.config.task_specific_dim,
            self.config.num_shared_layers,
            self.config.num_task_specific_layers
        ]
        config_labels = ['Shared Hidden Dim', 'Task-Specific Dim', 'Shared Layers', 'Task-Specific Layers']
        
        axes[1, 1].bar(config_labels, config_values, color=['blue', 'green', 'orange', 'red'])
        axes[1, 1].set_ylabel('Value')
        axes[1, 1].set_title('Multi-Task Configuration')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        
        plt.close()

# Factory functions
def create_multitask_config(**kwargs) -> MultiTaskConfig:
    """Create multi-task configuration"""
    return MultiTaskConfig(**kwargs)

def create_task_balancer(config: MultiTaskConfig) -> TaskBalancer:
    """Create task balancer"""
    return TaskBalancer(config)

def create_gradient_surgery(config: MultiTaskConfig) -> GradientSurgery:
    """Create gradient surgery"""
    return GradientSurgery(config)

def create_shared_representation(config: MultiTaskConfig) -> SharedRepresentation:
    """Create shared representation"""
    return SharedRepresentation(config)

def create_multitask_head(config: MultiTaskConfig, task_type: TaskType) -> MultiTaskHead:
    """Create multi-task head"""
    return MultiTaskHead(config, task_type)

def create_multitask_network(config: MultiTaskConfig) -> MultiTaskNetwork:
    """Create multi-task network"""
    return MultiTaskNetwork(config)

def create_multitask_trainer(config: MultiTaskConfig) -> MultiTaskTrainer:
    """Create multi-task trainer"""
    return MultiTaskTrainer(config)

# Example usage
def example_multitask_learning():
    """Example of multi-task learning system"""
    # Create configuration
    config = create_multitask_config(
        task_types=[TaskType.CLASSIFICATION, TaskType.REGRESSION],
        task_relationships=[TaskRelationship.RELATED],
        sharing_strategy=SharingStrategy.HARD_SHARING,
        shared_hidden_dim=512,
        task_specific_dim=256,
        num_shared_layers=3,
        num_task_specific_layers=2,
        learning_rate=0.001,
        batch_size=32,
        num_epochs=100,
        enable_task_balancing=True,
        task_balancing_method="uncertainty_weighting",
        task_weights=[1.0, 1.0],
        enable_gradient_surgery=True,
        gradient_surgery_method="pcgrad",
        gradient_surgery_lambda=0.1,
        enable_meta_learning=False,
        enable_transfer_learning=True,
        enable_continual_learning=False,
        enable_adaptive_sharing=True
    )
    
    # Create multi-task trainer
    multitask_trainer = create_multitask_trainer(config)
    
    # Create dummy data
    n_samples = 1000
    n_features = 784
    
    # Classification task data
    X_cls = torch.randn(n_samples, n_features)
    y_cls = torch.randint(0, 10, (n_samples,))
    
    # Regression task data
    X_reg = torch.randn(n_samples, n_features)
    y_reg = torch.randn(n_samples, 1)
    
    # Build network
    task_output_dims = {
        TaskType.CLASSIFICATION: 10,
        TaskType.REGRESSION: 1
    }
    
    multitask_trainer.multi_task_network.build_network(n_features, task_output_dims)
    
    # Prepare training data
    train_data = {
        TaskType.CLASSIFICATION: (X_cls[:800], y_cls[:800]),
        TaskType.REGRESSION: (X_reg[:800], y_reg[:800])
    }
    
    val_data = {
        TaskType.CLASSIFICATION: (X_cls[800:], y_cls[800:]),
        TaskType.REGRESSION: (X_reg[800:], y_reg[800:])
    }
    
    # Train multi-task model
    training_results = multitask_trainer.train(train_data, val_data)
    
    # Generate report
    training_report = multitask_trainer.generate_training_report(training_results)
    
    print(f"✅ Multi-Task Learning Example Complete!")
    print(f"🚀 Multi-Task Learning Statistics:")
    print(f"   Task Types: {[t.value for t in config.task_types]}")
    print(f"   Task Relationships: {[r.value for r in config.task_relationships]}")
    print(f"   Sharing Strategy: {config.sharing_strategy.value}")
    print(f"   Shared Hidden Dimension: {config.shared_hidden_dim}")
    print(f"   Task-Specific Dimension: {config.task_specific_dim}")
    print(f"   Number of Shared Layers: {config.num_shared_layers}")
    print(f"   Number of Task-Specific Layers: {config.num_task_specific_layers}")
    print(f"   Learning Rate: {config.learning_rate}")
    print(f"   Batch Size: {config.batch_size}")
    print(f"   Number of Epochs: {config.num_epochs}")
    print(f"   Task Balancing: {'Enabled' if config.enable_task_balancing else 'Disabled'}")
    print(f"   Task Balancing Method: {config.task_balancing_method}")
    print(f"   Task Weights: {config.task_weights}")
    print(f"   Gradient Surgery: {'Enabled' if config.enable_gradient_surgery else 'Disabled'}")
    print(f"   Gradient Surgery Method: {config.gradient_surgery_method}")
    print(f"   Gradient Surgery Lambda: {config.gradient_surgery_lambda}")
    print(f"   Meta Learning: {'Enabled' if config.enable_meta_learning else 'Disabled'}")
    print(f"   Transfer Learning: {'Enabled' if config.enable_transfer_learning else 'Disabled'}")
    print(f"   Continual Learning: {'Enabled' if config.enable_continual_learning else 'Disabled'}")
    print(f"   Adaptive Sharing: {'Enabled' if config.enable_adaptive_sharing else 'Disabled'}")
    
    print(f"\n📊 Multi-Task Learning Results:")
    print(f"   Training History Length: {len(multitask_trainer.training_history)}")
    print(f"   Total Duration: {training_results.get('total_duration', 0):.2f} seconds")
    print(f"   Number of Epochs: {len(training_results.get('epochs', []))}")
    
    # Show final epoch results
    if 'epochs' in training_results and training_results['epochs']:
        final_epoch = training_results['epochs'][-1]
        print(f"   Final Train Loss: {final_epoch.get('train_metrics', {}).get('total_loss', 0):.4f}")
        
        if 'val_metrics' in final_epoch:
            print(f"   Final Val Loss: {final_epoch['val_metrics'].get('total_loss', 0):.4f}")
    
    print(f"\n📋 Multi-Task Learning Report:")
    print(training_report)
    
    return multitask_trainer

# Export utilities
__all__ = [
    'TaskType',
    'TaskRelationship',
    'SharingStrategy',
    'MultiTaskConfig',
    'TaskBalancer',
    'GradientSurgery',
    'SharedRepresentation',
    'MultiTaskHead',
    'MultiTaskNetwork',
    'MultiTaskTrainer',
    'create_multitask_config',
    'create_task_balancer',
    'create_gradient_surgery',
    'create_shared_representation',
    'create_multitask_head',
    'create_multitask_network',
    'create_multitask_trainer',
    'example_multitask_learning'
]

if __name__ == "__main__":
    example_multitask_learning()
    print("✅ Multi-task learning example completed successfully!")