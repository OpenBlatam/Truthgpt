"""
Advanced Neural Network Continual Learning System for TruthGPT Optimization Core
Complete continual learning with EWC, replay buffers, and progressive networks
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

class CLStrategy(Enum):
    """Continual learning strategies"""
    EWC = "ewc"
    REPLAY_BUFFER = "replay_buffer"
    PROGRESSIVE_NETWORKS = "progressive_networks"
    MULTI_TASK_LEARNING = "multi_task_learning"
    LIFELONG_LEARNING = "lifelong_learning"
    META_LEARNING = "meta_learning"
    TRANSFER_LEARNING = "transfer_learning"
    DOMAIN_ADAPTATION = "domain_adaptation"

class ReplayStrategy(Enum):
    """Replay strategies"""
    RANDOM_REPLAY = "random_replay"
    STRATEGIC_REPLAY = "strategic_replay"
    EXPERIENCE_REPLAY = "experience_replay"
    GENERATIVE_REPLAY = "generative_replay"
    PROTOTYPE_REPLAY = "prototype_replay"
    CORE_SET_REPLAY = "core_set_replay"

class MemoryType(Enum):
    """Memory types"""
    EPISODIC_MEMORY = "episodic_memory"
    SEMANTIC_MEMORY = "semantic_memory"
    WORKING_MEMORY = "working_memory"
    LONG_TERM_MEMORY = "long_term_memory"
    SHORT_TERM_MEMORY = "short_term_memory"

class ContinualLearningConfig:
    """Configuration for continual learning system"""
    # Basic settings
    cl_strategy: CLStrategy = CLStrategy.EWC
    replay_strategy: ReplayStrategy = ReplayStrategy.RANDOM_REPLAY
    memory_type: MemoryType = MemoryType.EPISODIC_MEMORY
    
    # Model settings
    model_dim: int = 512
    hidden_dim: int = 256
    num_tasks: int = 5
    
    # EWC settings
    ewc_lambda: float = 1000.0
    ewc_importance: float = 1.0
    
    # Replay settings
    replay_buffer_size: int = 1000
    replay_batch_size: int = 32
    replay_frequency: int = 10
    
    # Progressive networks
    enable_progressive_networks: bool = True
    progressive_expansion_factor: float = 1.2
    
    # Multi-task learning
    enable_multi_task_learning: bool = True
    task_balancing_weight: float = 0.5
    
    # Lifelong learning
    enable_lifelong_learning: bool = True
    knowledge_retention_rate: float = 0.8
    
    # Advanced features
    enable_catastrophic_forgetting_prevention: bool = True
    enable_knowledge_distillation: bool = True
    enable_meta_learning: bool = False
    
    def __post_init__(self):
        """Validate continual learning configuration"""
        if self.model_dim <= 0:
            raise ValueError("Model dimension must be positive")
        if self.hidden_dim <= 0:
            raise ValueError("Hidden dimension must be positive")
        if self.num_tasks <= 0:
            raise ValueError("Number of tasks must be positive")
        if self.ewc_lambda <= 0:
            raise ValueError("EWC lambda must be positive")
        if self.ewc_importance <= 0:
            raise ValueError("EWC importance must be positive")
        if self.replay_buffer_size <= 0:
            raise ValueError("Replay buffer size must be positive")
        if self.replay_batch_size <= 0:
            raise ValueError("Replay batch size must be positive")
        if self.replay_frequency <= 0:
            raise ValueError("Replay frequency must be positive")
        if self.progressive_expansion_factor <= 0:
            raise ValueError("Progressive expansion factor must be positive")
        if not (0 <= self.task_balancing_weight <= 1):
            raise ValueError("Task balancing weight must be between 0 and 1")
        if not (0 <= self.knowledge_retention_rate <= 1):
            raise ValueError("Knowledge retention rate must be between 0 and 1")

class EWC:
    """Elastic Weight Consolidation implementation"""
    
    def __init__(self, config: ContinualLearningConfig):
        self.config = config
        self.fisher_information = {}
        self.optimal_params = {}
        self.training_history = []
        logger.info("✅ EWC initialized")
    
    def compute_fisher_information(self, model: nn.Module, data: torch.Tensor, 
                                 labels: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Compute Fisher information matrix"""
        logger.info("🐟 Computing Fisher information matrix")
        
        model.train()
        fisher_info = {}
        
        # Compute gradients
        for param_name, param in model.named_parameters():
            if param.requires_grad:
                fisher_info[param_name] = torch.zeros_like(param)
        
        # Compute Fisher information for each sample
        for i in range(data.shape[0]):
            model.zero_grad()
            
            # Forward pass
            output = model(data[i:i+1])
            loss = F.cross_entropy(output, labels[i:i+1])
            
            # Backward pass
            loss.backward()
            
            # Accumulate Fisher information
            for param_name, param in model.named_parameters():
                if param.requires_grad and param.grad is not None:
                    fisher_info[param_name] += param.grad ** 2
        
        # Average Fisher information
        for param_name in fisher_info:
            fisher_info[param_name] /= data.shape[0]
        
        return fisher_info
    
    def update_fisher_information(self, model: nn.Module, data: torch.Tensor, 
                                labels: torch.Tensor):
        """Update Fisher information matrix"""
        logger.info("🔄 Updating Fisher information matrix")
        
        # Compute new Fisher information
        new_fisher_info = self.compute_fisher_information(model, data, labels)
        
        # Update existing Fisher information
        for param_name, param in model.named_parameters():
            if param.requires_grad:
                if param_name in self.fisher_information:
                    # Combine with existing Fisher information
                    self.fisher_information[param_name] = \
                        self.config.ewc_importance * self.fisher_information[param_name] + \
                        new_fisher_info[param_name]
                else:
                    self.fisher_information[param_name] = new_fisher_info[param_name]
        
        # Store optimal parameters
        for param_name, param in model.named_parameters():
            if param.requires_grad:
                self.optimal_params[param_name] = param.data.clone()
    
    def compute_ewc_loss(self, model: nn.Module) -> torch.Tensor:
        """Compute EWC loss"""
        ewc_loss = 0.0
        
        for param_name, param in model.named_parameters():
            if param.requires_grad and param_name in self.fisher_information:
                # EWC loss: lambda * Fisher * (theta - theta*)^2
                fisher_info = self.fisher_information[param_name]
                optimal_param = self.optimal_params[param_name]
                
                ewc_loss += (fisher_info * (param - optimal_param) ** 2).sum()
        
        return self.config.ewc_lambda * ewc_loss
    
    def train_with_ewc(self, model: nn.Module, data: torch.Tensor, 
                      labels: torch.Tensor, num_epochs: int = 10) -> Dict[str, Any]:
        """Train model with EWC"""
        logger.info("🏋️ Training with EWC")
        
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()
        
        training_losses = []
        ewc_losses = []
        
        for epoch in range(num_epochs):
            epoch_loss = 0.0
            epoch_ewc_loss = 0.0
            
            # Forward pass
            output = model(data)
            task_loss = criterion(output, labels)
            
            # EWC loss
            ewc_loss = self.compute_ewc_loss(model)
            
            # Total loss
            total_loss = task_loss + ewc_loss
            
            # Backward pass
            optimizer.zero_grad()
            total_loss.backward()
            optimizer.step()
            
            epoch_loss += task_loss.item()
            epoch_ewc_loss += ewc_loss.item()
            
            training_losses.append(epoch_loss)
            ewc_losses.append(epoch_ewc_loss)
            
            if epoch % 5 == 0:
                logger.info(f"   Epoch {epoch}: Task Loss = {task_loss.item():.4f}, EWC Loss = {ewc_loss.item():.4f}")
        
        training_result = {
            'strategy': CLStrategy.EWC.value,
            'epochs': num_epochs,
            'training_losses': training_losses,
            'ewc_losses': ewc_losses,
            'final_task_loss': training_losses[-1],
            'final_ewc_loss': ewc_losses[-1],
            'status': 'success'
        }
        
        self.training_history.append(training_result)
        return training_result

class ReplayBuffer:
    """Replay buffer implementation"""
    
    def __init__(self, config: ContinualLearningConfig):
        self.config = config
        self.buffer = []
        self.buffer_labels = []
        self.current_size = 0
        self.training_history = []
        logger.info("✅ Replay Buffer initialized")
    
    def add_samples(self, data: torch.Tensor, labels: torch.Tensor):
        """Add samples to replay buffer"""
        logger.info(f"📝 Adding {data.shape[0]} samples to replay buffer")
        
        for i in range(data.shape[0]):
            if self.current_size < self.config.replay_buffer_size:
                # Add new sample
                self.buffer.append(data[i].clone())
                self.buffer_labels.append(labels[i].item())
                self.current_size += 1
            else:
                # Replace random sample
                idx = random.randint(0, self.config.replay_buffer_size - 1)
                self.buffer[idx] = data[i].clone()
                self.buffer_labels[idx] = labels[i].item()
    
    def get_samples(self, num_samples: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get samples from replay buffer"""
        if self.current_size == 0:
            return torch.tensor([]), torch.tensor([])
        
        # Sample indices
        if num_samples >= self.current_size:
            indices = list(range(self.current_size))
        else:
            indices = random.sample(range(self.current_size), num_samples)
        
        # Get samples
        samples = torch.stack([self.buffer[i] for i in indices])
        labels = torch.tensor([self.buffer_labels[i] for i in indices])
        
        return samples, labels
    
    def train_with_replay(self, model: nn.Module, new_data: torch.Tensor, 
                         new_labels: torch.Tensor, num_epochs: int = 10) -> Dict[str, Any]:
        """Train model with replay"""
        logger.info("🔄 Training with replay")
        
        # Add new samples to buffer
        self.add_samples(new_data, new_labels)
        
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()
        
        training_losses = []
        replay_losses = []
        
        for epoch in range(num_epochs):
            epoch_loss = 0.0
            epoch_replay_loss = 0.0
            
            # Train on new data
            output = model(new_data)
            task_loss = criterion(output, new_labels)
            epoch_loss += task_loss.item()
            
            # Train on replay data
            if self.current_size > 0:
                replay_data, replay_labels = self.get_samples(self.config.replay_batch_size)
                
                if replay_data.shape[0] > 0:
                    replay_output = model(replay_data)
                    replay_loss = criterion(replay_output, replay_labels)
                    epoch_replay_loss += replay_loss.item()
                    
                    # Combined loss
                    total_loss = task_loss + replay_loss
                else:
                    total_loss = task_loss
            else:
                total_loss = task_loss
            
            # Backward pass
            optimizer.zero_grad()
            total_loss.backward()
            optimizer.step()
            
            training_losses.append(epoch_loss)
            replay_losses.append(epoch_replay_loss)
            
            if epoch % 5 == 0:
                logger.info(f"   Epoch {epoch}: Task Loss = {task_loss.item():.4f}, Replay Loss = {epoch_replay_loss:.4f}")
        
        training_result = {
            'strategy': CLStrategy.REPLAY_BUFFER.value,
            'epochs': num_epochs,
            'training_losses': training_losses,
            'replay_losses': replay_losses,
            'final_task_loss': training_losses[-1],
            'final_replay_loss': replay_losses[-1],
            'buffer_size': self.current_size,
            'status': 'success'
        }
        
        self.training_history.append(training_result)
        return training_result

class ProgressiveNetwork:
    """Progressive network implementation"""
    
    def __init__(self, config: ContinualLearningConfig):
        self.config = config
        self.task_networks = {}
        self.task_adapters = {}
        self.current_task = 0
        self.training_history = []
        logger.info("✅ Progressive Network initialized")
    
    def create_task_network(self, task_id: int) -> nn.Module:
        """Create network for specific task"""
        network = nn.Sequential(
            nn.Linear(self.config.model_dim, self.config.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.config.hidden_dim, self.config.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.config.hidden_dim, 10)  # 10 classes
        )
        
        return network
    
    def create_task_adapter(self, task_id: int) -> nn.Module:
        """Create adapter for specific task"""
        adapter = nn.Sequential(
            nn.Linear(self.config.model_dim, self.config.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.config.hidden_dim, 10)  # 10 classes
        )
        
        return adapter
    
    def add_task(self, task_id: int):
        """Add new task to progressive network"""
        logger.info(f"➕ Adding task {task_id} to progressive network")
        
        # Create task network
        self.task_networks[task_id] = self.create_task_network(task_id)
        
        # Create task adapter
        self.task_adapters[task_id] = self.create_task_adapter(task_id)
        
        self.current_task = task_id
    
    def forward(self, x: torch.Tensor, task_id: int) -> torch.Tensor:
        """Forward pass for specific task"""
        if task_id not in self.task_networks:
            raise ValueError(f"Task {task_id} not found in progressive network")
        
        # Use task-specific network
        output = self.task_networks[task_id](x)
        
        return output
    
    def train_task(self, task_id: int, data: torch.Tensor, 
                  labels: torch.Tensor, num_epochs: int = 10) -> Dict[str, Any]:
        """Train specific task"""
        logger.info(f"🏋️ Training task {task_id}")
        
        # Add task if not exists
        if task_id not in self.task_networks:
            self.add_task(task_id)
        
        # Get task network
        task_network = self.task_networks[task_id]
        optimizer = torch.optim.Adam(task_network.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()
        
        training_losses = []
        
        for epoch in range(num_epochs):
            epoch_loss = 0.0
            
            # Forward pass
            output = task_network(data)
            loss = criterion(output, labels)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            training_losses.append(epoch_loss)
            
            if epoch % 5 == 0:
                logger.info(f"   Epoch {epoch}: Loss = {loss.item():.4f}")
        
        training_result = {
            'strategy': CLStrategy.PROGRESSIVE_NETWORKS.value,
            'task_id': task_id,
            'epochs': num_epochs,
            'training_losses': training_losses,
            'final_loss': training_losses[-1],
            'status': 'success'
        }
        
        self.training_history.append(training_result)
        return training_result

class MultiTaskLearner:
    """Multi-task learning implementation"""
    
    def __init__(self, config: ContinualLearningConfig):
        self.config = config
        self.shared_encoder = self._create_shared_encoder()
        self.task_heads = {}
        self.task_weights = {}
        self.training_history = []
        logger.info("✅ Multi-Task Learner initialized")
    
    def _create_shared_encoder(self) -> nn.Module:
        """Create shared encoder"""
        encoder = nn.Sequential(
            nn.Linear(self.config.model_dim, self.config.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.config.hidden_dim, self.config.hidden_dim),
            nn.ReLU()
        )
        
        return encoder
    
    def create_task_head(self, task_id: int) -> nn.Module:
        """Create task-specific head"""
        head = nn.Sequential(
            nn.Linear(self.config.hidden_dim, self.config.hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(self.config.hidden_dim // 2, 10)  # 10 classes
        )
        
        return head
    
    def add_task(self, task_id: int):
        """Add new task"""
        logger.info(f"➕ Adding task {task_id} to multi-task learner")
        
        # Create task head
        self.task_heads[task_id] = self.create_task_head(task_id)
        
        # Initialize task weight
        self.task_weights[task_id] = 1.0
    
    def forward(self, x: torch.Tensor, task_id: int) -> torch.Tensor:
        """Forward pass for specific task"""
        if task_id not in self.task_heads:
            raise ValueError(f"Task {task_id} not found in multi-task learner")
        
        # Shared encoder
        shared_features = self.shared_encoder(x)
        
        # Task-specific head
        output = self.task_heads[task_id](shared_features)
        
        return output
    
    def train_multi_task(self, task_data: Dict[int, Tuple[torch.Tensor, torch.Tensor]], 
                        num_epochs: int = 10) -> Dict[str, Any]:
        """Train multi-task learning"""
        logger.info("🏋️ Training multi-task learning")
        
        # Add tasks if not exist
        for task_id in task_data.keys():
            if task_id not in self.task_heads:
                self.add_task(task_id)
        
        # Create optimizer
        all_params = list(self.shared_encoder.parameters())
        for task_head in self.task_heads.values():
            all_params.extend(list(task_head.parameters()))
        
        optimizer = torch.optim.Adam(all_params, lr=0.001)
        criterion = nn.CrossEntropyLoss()
        
        training_losses = []
        task_losses = defaultdict(list)
        
        for epoch in range(num_epochs):
            epoch_loss = 0.0
            
            # Train on each task
            for task_id, (data, labels) in task_data.items():
                # Forward pass
                output = self.forward(data, task_id)
                loss = criterion(output, labels)
                
                # Weighted loss
                weighted_loss = self.task_weights[task_id] * loss
                epoch_loss += weighted_loss.item()
                
                task_losses[task_id].append(loss.item())
            
            # Backward pass
            optimizer.zero_grad()
            epoch_loss.backward()
            optimizer.step()
            
            training_losses.append(epoch_loss)
            
            if epoch % 5 == 0:
                logger.info(f"   Epoch {epoch}: Total Loss = {epoch_loss:.4f}")
        
        training_result = {
            'strategy': CLStrategy.MULTI_TASK_LEARNING.value,
            'epochs': num_epochs,
            'training_losses': training_losses,
            'task_losses': dict(task_losses),
            'final_loss': training_losses[-1],
            'status': 'success'
        }
        
        self.training_history.append(training_result)
        return training_result

class LifelongLearner:
    """Lifelong learning implementation"""
    
    def __init__(self, config: ContinualLearningConfig):
        self.config = config
        self.knowledge_base = {}
        self.task_memory = {}
        self.learning_history = []
        logger.info("✅ Lifelong Learner initialized")
    
    def store_knowledge(self, task_id: int, knowledge: Dict[str, Any]):
        """Store knowledge for task"""
        logger.info(f"💾 Storing knowledge for task {task_id}")
        
        self.knowledge_base[task_id] = knowledge
    
    def retrieve_knowledge(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve knowledge for task"""
        if task_id in self.knowledge_base:
            return self.knowledge_base[task_id]
        return None
    
    def transfer_knowledge(self, source_task: int, target_task: int) -> Dict[str, Any]:
        """Transfer knowledge between tasks"""
        logger.info(f"🔄 Transferring knowledge from task {source_task} to task {target_task}")
        
        source_knowledge = self.retrieve_knowledge(source_task)
        if source_knowledge is None:
            return {'status': 'failed', 'reason': 'Source knowledge not found'}
        
        # Transfer knowledge (simplified)
        transferred_knowledge = {
            'source_task': source_task,
            'target_task': target_task,
            'transferred_features': source_knowledge.get('features', []),
            'transferred_weights': source_knowledge.get('weights', {}),
            'transfer_success': True
        }
        
        return transferred_knowledge
    
    def learn_lifelong(self, task_id: int, data: torch.Tensor, 
                      labels: torch.Tensor) -> Dict[str, Any]:
        """Learn lifelong"""
        logger.info(f"🧠 Learning lifelong for task {task_id}")
        
        # Store task memory
        self.task_memory[task_id] = {
            'data_shape': data.shape,
            'labels_shape': labels.shape,
            'timestamp': time.time()
        }
        
        # Extract knowledge
        knowledge = {
            'task_id': task_id,
            'features': data.mean(dim=0).tolist(),
            'weights': {},
            'timestamp': time.time()
        }
        
        # Store knowledge
        self.store_knowledge(task_id, knowledge)
        
        # Transfer knowledge from previous tasks
        transfer_results = []
        for prev_task_id in self.knowledge_base.keys():
            if prev_task_id != task_id:
                transfer_result = self.transfer_knowledge(prev_task_id, task_id)
                transfer_results.append(transfer_result)
        
        learning_result = {
            'strategy': CLStrategy.LIFELONG_LEARNING.value,
            'task_id': task_id,
            'knowledge_stored': True,
            'transfer_results': transfer_results,
            'status': 'success'
        }
        
        self.learning_history.append(learning_result)
        return learning_result

class CLTrainer:
    """Continual learning trainer"""
    
    def __init__(self, config: ContinualLearningConfig):
        self.config = config
        
        # Components
        self.ewc = EWC(config)
        self.replay_buffer = ReplayBuffer(config)
        self.progressive_network = ProgressiveNetwork(config)
        self.multi_task_learner = MultiTaskLearner(config)
        self.lifelong_learner = LifelongLearner(config)
        
        # Continual learning state
        self.cl_history = []
        
        logger.info("✅ Continual Learning Trainer initialized")
    
    def train_continual_learning(self, task_data: Dict[int, Tuple[torch.Tensor, torch.Tensor]]) -> Dict[str, Any]:
        """Train continual learning"""
        logger.info(f"🚀 Training continual learning with strategy: {self.config.cl_strategy.value}")
        
        cl_results = {
            'start_time': time.time(),
            'config': self.config,
            'stages': {}
        }
        
        # Stage 1: EWC Training
        if self.config.cl_strategy == CLStrategy.EWC:
            logger.info("🐟 Stage 1: EWC Training")
            
            ewc_results = []
            for task_id, (data, labels) in task_data.items():
                # Create simple model for EWC
                model = nn.Sequential(
                    nn.Linear(self.config.model_dim, self.config.hidden_dim),
                    nn.ReLU(),
                    nn.Linear(self.config.hidden_dim, 10)
                )
                
                # Train with EWC
                ewc_result = self.ewc.train_with_ewc(model, data, labels)
                ewc_results.append(ewc_result)
            
            cl_results['stages']['ewc_training'] = ewc_results
        
        # Stage 2: Replay Buffer Training
        elif self.config.cl_strategy == CLStrategy.REPLAY_BUFFER:
            logger.info("🔄 Stage 2: Replay Buffer Training")
            
            replay_results = []
            for task_id, (data, labels) in task_data.items():
                # Create simple model for replay
                model = nn.Sequential(
                    nn.Linear(self.config.model_dim, self.config.hidden_dim),
                    nn.ReLU(),
                    nn.Linear(self.config.hidden_dim, 10)
                )
                
                # Train with replay
                replay_result = self.replay_buffer.train_with_replay(model, data, labels)
                replay_results.append(replay_result)
            
            cl_results['stages']['replay_training'] = replay_results
        
        # Stage 3: Progressive Networks Training
        elif self.config.cl_strategy == CLStrategy.PROGRESSIVE_NETWORKS:
            logger.info("➕ Stage 3: Progressive Networks Training")
            
            progressive_results = []
            for task_id, (data, labels) in task_data.items():
                # Train progressive network
                progressive_result = self.progressive_network.train_task(task_id, data, labels)
                progressive_results.append(progressive_result)
            
            cl_results['stages']['progressive_training'] = progressive_results
        
        # Stage 4: Multi-Task Learning Training
        elif self.config.cl_strategy == CLStrategy.MULTI_TASK_LEARNING:
            logger.info("🏋️ Stage 4: Multi-Task Learning Training")
            
            multi_task_result = self.multi_task_learner.train_multi_task(task_data)
            
            cl_results['stages']['multi_task_training'] = multi_task_result
        
        # Stage 5: Lifelong Learning Training
        elif self.config.cl_strategy == CLStrategy.LIFELONG_LEARNING:
            logger.info("🧠 Stage 5: Lifelong Learning Training")
            
            lifelong_results = []
            for task_id, (data, labels) in task_data.items():
                # Train lifelong learning
                lifelong_result = self.lifelong_learner.learn_lifelong(task_id, data, labels)
                lifelong_results.append(lifelong_result)
            
            cl_results['stages']['lifelong_training'] = lifelong_results
        
        # Final evaluation
        cl_results['end_time'] = time.time()
        cl_results['total_duration'] = cl_results['end_time'] - cl_results['start_time']
        
        # Store results
        self.cl_history.append(cl_results)
        
        logger.info("✅ Continual learning training completed")
        return cl_results
    
    def generate_cl_report(self, results: Dict[str, Any]) -> str:
        """Generate continual learning report"""
        report = []
        report.append("=" * 50)
        report.append("CONTINUAL LEARNING REPORT")
        report.append("=" * 50)
        
        # Configuration
        report.append("\nCONTINUAL LEARNING CONFIGURATION:")
        report.append("-" * 35)
        report.append(f"CL Strategy: {self.config.cl_strategy.value}")
        report.append(f"Replay Strategy: {self.config.replay_strategy.value}")
        report.append(f"Memory Type: {self.config.memory_type.value}")
        report.append(f"Model Dim: {self.config.model_dim}")
        report.append(f"Hidden Dim: {self.config.hidden_dim}")
        report.append(f"Number of Tasks: {self.config.num_tasks}")
        report.append(f"EWC Lambda: {self.config.ewc_lambda}")
        report.append(f"EWC Importance: {self.config.ewc_importance}")
        report.append(f"Replay Buffer Size: {self.config.replay_buffer_size}")
        report.append(f"Replay Batch Size: {self.config.replay_batch_size}")
        report.append(f"Replay Frequency: {self.config.replay_frequency}")
        report.append(f"Progressive Networks: {'Enabled' if self.config.enable_progressive_networks else 'Disabled'}")
        report.append(f"Progressive Expansion Factor: {self.config.progressive_expansion_factor}")
        report.append(f"Multi-Task Learning: {'Enabled' if self.config.enable_multi_task_learning else 'Disabled'}")
        report.append(f"Task Balancing Weight: {self.config.task_balancing_weight}")
        report.append(f"Lifelong Learning: {'Enabled' if self.config.enable_lifelong_learning else 'Disabled'}")
        report.append(f"Knowledge Retention Rate: {self.config.knowledge_retention_rate}")
        report.append(f"Catastrophic Forgetting Prevention: {'Enabled' if self.config.enable_catastrophic_forgetting_prevention else 'Disabled'}")
        report.append(f"Knowledge Distillation: {'Enabled' if self.config.enable_knowledge_distillation else 'Disabled'}")
        report.append(f"Meta Learning: {'Enabled' if self.config.enable_meta_learning else 'Disabled'}")
        
        # Results
        report.append("\nCONTINUAL LEARNING RESULTS:")
        report.append("-" * 30)
        report.append(f"Total Duration: {results.get('total_duration', 0):.2f} seconds")
        report.append(f"Start Time: {results.get('start_time', 'Unknown')}")
        report.append(f"End Time: {results.get('end_time', 'Unknown')}")
        
        # Stage results
        if 'stages' in results:
            for stage_name, stage_data in results['stages'].items():
                report.append(f"\n{stage_name.upper()}:")
                report.append("-" * len(stage_name))
                
                if isinstance(stage_data, list):
                    for i, task_data in enumerate(stage_data):
                        report.append(f"  Task {i + 1}:")
                        if isinstance(task_data, dict):
                            for key, value in task_data.items():
                                report.append(f"    {key}: {value}")
                elif isinstance(stage_data, dict):
                    for key, value in stage_data.items():
                        report.append(f"  {key}: {value}")
        
        return "\n".join(report)
    
    def visualize_cl_results(self, save_path: str = None):
        """Visualize continual learning results"""
        if not self.cl_history:
            logger.warning("No continual learning history to visualize")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Plot 1: Training duration over time
        durations = [r.get('total_duration', 0) for r in self.cl_history]
        axes[0, 0].plot(durations, 'b-', linewidth=2)
        axes[0, 0].set_xlabel('Training Run')
        axes[0, 0].set_ylabel('Duration (seconds)')
        axes[0, 0].set_title('Continual Learning Duration Over Time')
        axes[0, 0].grid(True)
        
        # Plot 2: CL strategy distribution
        cl_strategies = [self.config.cl_strategy.value]
        strategy_counts = [1]
        
        axes[0, 1].pie(strategy_counts, labels=cl_strategies, autopct='%1.1f%%')
        axes[0, 1].set_title('CL Strategy Distribution')
        
        # Plot 3: Replay strategy distribution
        replay_strategies = [self.config.replay_strategy.value]
        replay_counts = [1]
        
        axes[1, 0].pie(replay_counts, labels=replay_strategies, autopct='%1.1f%%')
        axes[1, 0].set_title('Replay Strategy Distribution')
        
        # Plot 4: Continual learning configuration
        config_values = [
            self.config.model_dim,
            self.config.hidden_dim,
            self.config.num_tasks,
            self.config.replay_buffer_size
        ]
        config_labels = ['Model Dim', 'Hidden Dim', 'Num Tasks', 'Buffer Size']
        
        axes[1, 1].bar(config_labels, config_values, color=['blue', 'green', 'orange', 'red'])
        axes[1, 1].set_ylabel('Value')
        axes[1, 1].set_title('Continual Learning Configuration')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        
        plt.close()

# Factory functions
def create_cl_config(**kwargs) -> ContinualLearningConfig:
    """Create continual learning configuration"""
    return ContinualLearningConfig(**kwargs)

def create_ewc(config: ContinualLearningConfig) -> EWC:
    """Create EWC"""
    return EWC(config)

def create_replay_buffer(config: ContinualLearningConfig) -> ReplayBuffer:
    """Create replay buffer"""
    return ReplayBuffer(config)

def create_progressive_network(config: ContinualLearningConfig) -> ProgressiveNetwork:
    """Create progressive network"""
    return ProgressiveNetwork(config)

def create_multi_task_learner(config: ContinualLearningConfig) -> MultiTaskLearner:
    """Create multi-task learner"""
    return MultiTaskLearner(config)

def create_lifelong_learner(config: ContinualLearningConfig) -> LifelongLearner:
    """Create lifelong learner"""
    return LifelongLearner(config)

def create_cl_trainer(config: ContinualLearningConfig) -> CLTrainer:
    """Create continual learning trainer"""
    return CLTrainer(config)

# Example usage
def example_continual_learning():
    """Example of continual learning system"""
    # Create configuration
    config = create_cl_config(
        cl_strategy=CLStrategy.EWC,
        replay_strategy=ReplayStrategy.RANDOM_REPLAY,
        memory_type=MemoryType.EPISODIC_MEMORY,
        model_dim=512,
        hidden_dim=256,
        num_tasks=5,
        ewc_lambda=1000.0,
        ewc_importance=1.0,
        replay_buffer_size=1000,
        replay_batch_size=32,
        replay_frequency=10,
        enable_progressive_networks=True,
        progressive_expansion_factor=1.2,
        enable_multi_task_learning=True,
        task_balancing_weight=0.5,
        enable_lifelong_learning=True,
        knowledge_retention_rate=0.8,
        enable_catastrophic_forgetting_prevention=True,
        enable_knowledge_distillation=True,
        enable_meta_learning=False
    )
    
    # Create continual learning trainer
    cl_trainer = create_cl_trainer(config)
    
    # Create dummy task data
    task_data = {}
    for task_id in range(config.num_tasks):
        batch_size = 32
        data = torch.randn(batch_size, config.model_dim)
        labels = torch.randint(0, 10, (batch_size,))
        task_data[task_id] = (data, labels)
    
    # Train continual learning
    cl_results = cl_trainer.train_continual_learning(task_data)
    
    # Generate report
    cl_report = cl_trainer.generate_cl_report(cl_results)
    
    print(f"✅ Continual Learning Example Complete!")
    print(f"🚀 Continual Learning Statistics:")
    print(f"   CL Strategy: {config.cl_strategy.value}")
    print(f"   Replay Strategy: {config.replay_strategy.value}")
    print(f"   Memory Type: {config.memory_type.value}")
    print(f"   Model Dim: {config.model_dim}")
    print(f"   Hidden Dim: {config.hidden_dim}")
    print(f"   Number of Tasks: {config.num_tasks}")
    print(f"   EWC Lambda: {config.ewc_lambda}")
    print(f"   EWC Importance: {config.ewc_importance}")
    print(f"   Replay Buffer Size: {config.replay_buffer_size}")
    print(f"   Replay Batch Size: {config.replay_batch_size}")
    print(f"   Replay Frequency: {config.replay_frequency}")
    print(f"   Progressive Networks: {'Enabled' if config.enable_progressive_networks else 'Disabled'}")
    print(f"   Progressive Expansion Factor: {config.progressive_expansion_factor}")
    print(f"   Multi-Task Learning: {'Enabled' if config.enable_multi_task_learning else 'Disabled'}")
    print(f"   Task Balancing Weight: {config.task_balancing_weight}")
    print(f"   Lifelong Learning: {'Enabled' if config.enable_lifelong_learning else 'Disabled'}")
    print(f"   Knowledge Retention Rate: {config.knowledge_retention_rate}")
    print(f"   Catastrophic Forgetting Prevention: {'Enabled' if config.enable_catastrophic_forgetting_prevention else 'Disabled'}")
    print(f"   Knowledge Distillation: {'Enabled' if config.enable_knowledge_distillation else 'Disabled'}")
    print(f"   Meta Learning: {'Enabled' if config.enable_meta_learning else 'Disabled'}")
    
    print(f"\n📊 Continual Learning Results:")
    print(f"   CL History Length: {len(cl_trainer.cl_history)}")
    print(f"   Total Duration: {cl_results.get('total_duration', 0):.2f} seconds")
    
    # Show stage results summary
    if 'stages' in cl_results:
        for stage_name, stage_data in cl_results['stages'].items():
            print(f"   {stage_name}: {len(stage_data) if isinstance(stage_data, list) else 'N/A'} results")
    
    print(f"\n📋 Continual Learning Report:")
    print(cl_report)
    
    return cl_trainer

# Export utilities
__all__ = [
    'CLStrategy',
    'ReplayStrategy',
    'MemoryType',
    'ContinualLearningConfig',
    'EWC',
    'ReplayBuffer',
    'ProgressiveNetwork',
    'MultiTaskLearner',
    'LifelongLearner',
    'CLTrainer',
    'create_cl_config',
    'create_ewc',
    'create_replay_buffer',
    'create_progressive_network',
    'create_multi_task_learner',
    'create_lifelong_learner',
    'create_cl_trainer',
    'example_continual_learning'
]

if __name__ == "__main__":
    example_continual_learning()
    print("✅ Continual learning example completed successfully!")