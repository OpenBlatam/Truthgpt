"""
Advanced Neural Network Active Learning System for TruthGPT Optimization Core
Complete active learning with uncertainty sampling, diversity sampling, and query strategies
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
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class ActiveLearningStrategy(Enum):
    """Active learning strategies"""
    UNCERTAINTY_SAMPLING = "uncertainty_sampling"
    DIVERSITY_SAMPLING = "diversity_sampling"
    QUERY_BY_COMMITTEE = "query_by_committee"
    EXPECTED_MODEL_CHANGE = "expected_model_change"
    BATCH_ACTIVE_LEARNING = "batch_active_learning"
    HYBRID_SAMPLING = "hybrid_sampling"
    ADAPTIVE_SAMPLING = "adaptive_sampling"
    COST_SENSITIVE_SAMPLING = "cost_sensitive_sampling"

class UncertaintyMeasure(Enum):
    """Uncertainty measures"""
    ENTROPY = "entropy"
    MARGIN = "margin"
    LEAST_CONFIDENT = "least_confident"
    VARIANCE = "variance"
    BALD = "bald"
    MAXIMUM_ENTROPY = "maximum_entropy"
    VARIANCE_REDUCTION = "variance_reduction"

class QueryStrategy(Enum):
    """Query strategies"""
    RANDOM_SAMPLING = "random_sampling"
    UNCERTAINTY_BASED = "uncertainty_based"
    DIVERSITY_BASED = "diversity_based"
    HYBRID_STRATEGY = "hybrid_strategy"
    ADAPTIVE_STRATEGY = "adaptive_strategy"
    COST_AWARE_STRATEGY = "cost_aware_strategy"

class ActiveLearningConfig:
    """Configuration for active learning system"""
    # Basic settings
    active_learning_strategy: ActiveLearningStrategy = ActiveLearningStrategy.UNCERTAINTY_SAMPLING
    uncertainty_measure: UncertaintyMeasure = UncertaintyMeasure.ENTROPY
    query_strategy: QueryStrategy = QueryStrategy.UNCERTAINTY_BASED
    
    # Sampling settings
    n_initial_samples: int = 100
    n_query_samples: int = 10
    n_total_samples: int = 1000
    max_iterations: int = 50
    
    # Uncertainty sampling settings
    uncertainty_threshold: float = 0.5
    entropy_threshold: float = 0.8
    margin_threshold: float = 0.1
    
    # Diversity sampling settings
    diversity_method: str = "kmeans"
    n_clusters: int = 10
    diversity_weight: float = 0.5
    
    # Query by committee settings
    n_committee_members: int = 5
    disagreement_threshold: float = 0.3
    
    # Batch active learning settings
    batch_size: int = 20
    batch_diversity_weight: float = 0.3
    
    # Advanced features
    enable_adaptive_sampling: bool = True
    enable_cost_sensitive_sampling: bool = False
    enable_online_learning: bool = True
    enable_model_uncertainty: bool = True
    
    def __post_init__(self):
        """Validate active learning configuration"""
        if self.n_initial_samples <= 0:
            raise ValueError("Number of initial samples must be positive")
        if self.n_query_samples <= 0:
            raise ValueError("Number of query samples must be positive")
        if self.n_total_samples <= 0:
            raise ValueError("Number of total samples must be positive")
        if self.max_iterations <= 0:
            raise ValueError("Maximum iterations must be positive")
        if not (0 <= self.uncertainty_threshold <= 1):
            raise ValueError("Uncertainty threshold must be between 0 and 1")
        if not (0 <= self.entropy_threshold <= 1):
            raise ValueError("Entropy threshold must be between 0 and 1")
        if not (0 <= self.margin_threshold <= 1):
            raise ValueError("Margin threshold must be between 0 and 1")
        if self.n_clusters <= 0:
            raise ValueError("Number of clusters must be positive")
        if not (0 <= self.diversity_weight <= 1):
            raise ValueError("Diversity weight must be between 0 and 1")
        if self.n_committee_members <= 0:
            raise ValueError("Number of committee members must be positive")
        if not (0 <= self.disagreement_threshold <= 1):
            raise ValueError("Disagreement threshold must be between 0 and 1")
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")
        if not (0 <= self.batch_diversity_weight <= 1):
            raise ValueError("Batch diversity weight must be between 0 and 1")

class UncertaintySampler:
    """Uncertainty-based sampling"""
    
    def __init__(self, config: ActiveLearningConfig):
        self.config = config
        self.uncertainty_history = []
        logger.info("✅ Uncertainty Sampler initialized")
    
    def sample_uncertain(self, model: nn.Module, unlabeled_data: np.ndarray, 
                        n_samples: int = None) -> np.ndarray:
        """Sample most uncertain points"""
        logger.info(f"🎯 Sampling uncertain points using measure: {self.config.uncertainty_measure.value}")
        
        if n_samples is None:
            n_samples = self.config.n_query_samples
        
        # Calculate uncertainties
        uncertainties = self._calculate_uncertainties(model, unlabeled_data)
        
        # Select most uncertain points
        uncertain_indices = np.argsort(uncertainties)[-n_samples:]
        uncertain_samples = unlabeled_data[uncertain_indices]
        
        # Store uncertainty history
        self.uncertainty_history.append({
            'uncertainties': uncertainties,
            'selected_indices': uncertain_indices,
            'uncertainty_measure': self.config.uncertainty_measure.value
        })
        
        return uncertain_samples
    
    def _calculate_uncertainties(self, model: nn.Module, data: np.ndarray) -> np.ndarray:
        """Calculate uncertainties for data points"""
        model.eval()
        
        with torch.no_grad():
            # Convert to tensor
            data_tensor = torch.FloatTensor(data)
            
            # Get predictions
            outputs = model(data_tensor)
            probabilities = F.softmax(outputs, dim=1)
            
            if self.config.uncertainty_measure == UncertaintyMeasure.ENTROPY:
                uncertainties = self._calculate_entropy(probabilities)
            elif self.config.uncertainty_measure == UncertaintyMeasure.MARGIN:
                uncertainties = self._calculate_margin(probabilities)
            elif self.config.uncertainty_measure == UncertaintyMeasure.LEAST_CONFIDENT:
                uncertainties = self._calculate_least_confident(probabilities)
            elif self.config.uncertainty_measure == UncertaintyMeasure.VARIANCE:
                uncertainties = self._calculate_variance(probabilities)
            elif self.config.uncertainty_measure == UncertaintyMeasure.BALD:
                uncertainties = self._calculate_bald(probabilities)
            else:
                uncertainties = self._calculate_entropy(probabilities)
            
            return uncertainties.numpy()
    
    def _calculate_entropy(self, probabilities: torch.Tensor) -> torch.Tensor:
        """Calculate entropy uncertainty"""
        log_probs = torch.log(probabilities + 1e-8)
        entropy = -torch.sum(probabilities * log_probs, dim=1)
        return entropy
    
    def _calculate_margin(self, probabilities: torch.Tensor) -> torch.Tensor:
        """Calculate margin uncertainty"""
        sorted_probs, _ = torch.sort(probabilities, dim=1, descending=True)
        margin = sorted_probs[:, 0] - sorted_probs[:, 1]
        return 1 - margin  # Higher margin = lower uncertainty
    
    def _calculate_least_confident(self, probabilities: torch.Tensor) -> torch.Tensor:
        """Calculate least confident uncertainty"""
        max_probs, _ = torch.max(probabilities, dim=1)
        return 1 - max_probs  # Higher max prob = lower uncertainty
    
    def _calculate_variance(self, probabilities: torch.Tensor) -> torch.Tensor:
        """Calculate variance uncertainty"""
        variance = torch.var(probabilities, dim=1)
        return variance
    
    def _calculate_bald(self, probabilities: torch.Tensor) -> torch.Tensor:
        """Calculate BALD uncertainty"""
        # Simplified BALD calculation
        entropy = self._calculate_entropy(probabilities)
        return entropy

class DiversitySampler:
    """Diversity-based sampling"""
    
    def __init__(self, config: ActiveLearningConfig):
        self.config = config
        self.diversity_history = []
        logger.info("✅ Diversity Sampler initialized")
    
    def sample_diverse(self, unlabeled_data: np.ndarray, labeled_data: np.ndarray = None,
                      n_samples: int = None) -> np.ndarray:
        """Sample diverse points"""
        logger.info(f"🎯 Sampling diverse points using method: {self.config.diversity_method}")
        
        if n_samples is None:
            n_samples = self.config.n_query_samples
        
        if self.config.diversity_method == "kmeans":
            diverse_samples = self._kmeans_diversity_sampling(unlabeled_data, n_samples)
        elif self.config.diversity_method == "nearest_neighbors":
            diverse_samples = self._nearest_neighbors_diversity_sampling(unlabeled_data, labeled_data, n_samples)
        elif self.config.diversity_method == "clustering":
            diverse_samples = self._clustering_diversity_sampling(unlabeled_data, n_samples)
        else:
            diverse_samples = self._kmeans_diversity_sampling(unlabeled_data, n_samples)
        
        # Store diversity history
        self.diversity_history.append({
            'method': self.config.diversity_method,
            'n_samples': n_samples,
            'selected_samples': diverse_samples
        })
        
        return diverse_samples
    
    def _kmeans_diversity_sampling(self, data: np.ndarray, n_samples: int) -> np.ndarray:
        """K-means diversity sampling"""
        logger.info("🔍 Performing K-means diversity sampling")
        
        # Cluster data
        kmeans = KMeans(n_clusters=self.config.n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(data)
        
        # Sample from each cluster
        diverse_samples = []
        samples_per_cluster = n_samples // self.config.n_clusters
        
        for cluster_id in range(self.config.n_clusters):
            cluster_indices = np.where(cluster_labels == cluster_id)[0]
            
            if len(cluster_indices) > 0:
                # Sample from cluster
                if len(cluster_indices) >= samples_per_cluster:
                    selected_indices = np.random.choice(cluster_indices, samples_per_cluster, replace=False)
                else:
                    selected_indices = cluster_indices
                
                diverse_samples.extend(data[selected_indices])
        
        # Fill remaining samples randomly
        remaining_samples = n_samples - len(diverse_samples)
        if remaining_samples > 0:
            remaining_indices = np.random.choice(len(data), remaining_samples, replace=False)
            diverse_samples.extend(data[remaining_indices])
        
        return np.array(diverse_samples)
    
    def _nearest_neighbors_diversity_sampling(self, unlabeled_data: np.ndarray, 
                                            labeled_data: np.ndarray, n_samples: int) -> np.ndarray:
        """Nearest neighbors diversity sampling"""
        logger.info("🔍 Performing nearest neighbors diversity sampling")
        
        if labeled_data is None or len(labeled_data) == 0:
            # Random sampling if no labeled data
            indices = np.random.choice(len(unlabeled_data), n_samples, replace=False)
            return unlabeled_data[indices]
        
        # Find points farthest from labeled data
        nn = NearestNeighbors(n_neighbors=1)
        nn.fit(labeled_data)
        
        distances, _ = nn.kneighbors(unlabeled_data)
        distances = distances.flatten()
        
        # Select points with largest distances
        diverse_indices = np.argsort(distances)[-n_samples:]
        return unlabeled_data[diverse_indices]
    
    def _clustering_diversity_sampling(self, data: np.ndarray, n_samples: int) -> np.ndarray:
        """Clustering diversity sampling"""
        logger.info("🔍 Performing clustering diversity sampling")
        
        # Use K-means clustering
        kmeans = KMeans(n_clusters=n_samples, random_state=42)
        cluster_labels = kmeans.fit_predict(data)
        
        # Select one point from each cluster
        diverse_samples = []
        for cluster_id in range(n_samples):
            cluster_indices = np.where(cluster_labels == cluster_id)[0]
            if len(cluster_indices) > 0:
                # Select point closest to cluster center
                cluster_center = kmeans.cluster_centers_[cluster_id]
                distances = np.linalg.norm(data[cluster_indices] - cluster_center, axis=1)
                closest_idx = cluster_indices[np.argmin(distances)]
                diverse_samples.append(data[closest_idx])
        
        return np.array(diverse_samples)

class QueryByCommittee:
    """Query by committee sampling"""
    
    def __init__(self, config: ActiveLearningConfig):
        self.config = config
        self.committee_models = []
        self.committee_history = []
        logger.info("✅ Query by Committee initialized")
    
    def create_committee(self, base_model: nn.Module, n_members: int = None) -> List[nn.Module]:
        """Create committee of models"""
        logger.info(f"👥 Creating committee with {n_members or self.config.n_committee_members} members")
        
        if n_members is None:
            n_members = self.config.n_committee_members
        
        committee = []
        for i in range(n_members):
            # Create model with different initialization
            model = self._create_committee_member(base_model, i)
            committee.append(model)
        
        self.committee_models = committee
        return committee
    
    def _create_committee_member(self, base_model: nn.Module, member_id: int) -> nn.Module:
        """Create committee member with different initialization"""
        # Copy base model
        model = type(base_model)()
        model.load_state_dict(base_model.state_dict())
        
        # Add noise to weights
        for param in model.parameters():
            noise = torch.randn_like(param) * 0.01
            param.data += noise
        
        return model
    
    def query_by_committee(self, unlabeled_data: np.ndarray, n_samples: int = None) -> np.ndarray:
        """Query by committee disagreement"""
        logger.info("🎯 Querying by committee disagreement")
        
        if n_samples is None:
            n_samples = self.config.n_query_samples
        
        if not self.committee_models:
            logger.warning("No committee models available, using random sampling")
            indices = np.random.choice(len(unlabeled_data), n_samples, replace=False)
            return unlabeled_data[indices]
        
        # Calculate disagreements
        disagreements = self._calculate_disagreements(unlabeled_data)
        
        # Select points with highest disagreement
        disagreement_indices = np.argsort(disagreements)[-n_samples:]
        queried_samples = unlabeled_data[disagreement_indices]
        
        # Store committee history
        self.committee_history.append({
            'disagreements': disagreements,
            'selected_indices': disagreement_indices,
            'n_committee_members': len(self.committee_models)
        })
        
        return queried_samples
    
    def _calculate_disagreements(self, data: np.ndarray) -> np.ndarray:
        """Calculate committee disagreements"""
        predictions = []
        
        for model in self.committee_models:
            model.eval()
            with torch.no_grad():
                data_tensor = torch.FloatTensor(data)
                outputs = model(data_tensor)
                predictions.append(F.softmax(outputs, dim=1))
        
        # Calculate disagreement as variance in predictions
        predictions = torch.stack(predictions)
        disagreement = torch.var(predictions, dim=0).sum(dim=1)
        
        return disagreement.numpy()

class ExpectedModelChange:
    """Expected model change sampling"""
    
    def __init__(self, config: ActiveLearningConfig):
        self.config = config
        self.model_change_history = []
        logger.info("✅ Expected Model Change initialized")
    
    def query_expected_model_change(self, model: nn.Module, unlabeled_data: np.ndarray,
                                  labeled_data: np.ndarray, labeled_labels: np.ndarray,
                                  n_samples: int = None) -> np.ndarray:
        """Query points with highest expected model change"""
        logger.info("🎯 Querying expected model change")
        
        if n_samples is None:
            n_samples = self.config.n_query_samples
        
        # Calculate expected model changes
        expected_changes = self._calculate_expected_model_changes(
            model, unlabeled_data, labeled_data, labeled_labels
        )
        
        # Select points with highest expected change
        change_indices = np.argsort(expected_changes)[-n_samples:]
        queried_samples = unlabeled_data[change_indices]
        
        # Store model change history
        self.model_change_history.append({
            'expected_changes': expected_changes,
            'selected_indices': change_indices
        })
        
        return queried_samples
    
    def _calculate_expected_model_changes(self, model: nn.Module, unlabeled_data: np.ndarray,
                                        labeled_data: np.ndarray, labeled_labels: np.ndarray) -> np.ndarray:
        """Calculate expected model changes"""
        model.eval()
        
        expected_changes = []
        
        for i, unlabeled_point in enumerate(unlabeled_data):
            # Get current model predictions
            with torch.no_grad():
                unlabeled_tensor = torch.FloatTensor(unlabeled_point).unsqueeze(0)
                current_pred = model(unlabeled_tensor)
            
            # Calculate expected change for each possible label
            total_change = 0
            
            for possible_label in range(model.fc.out_features if hasattr(model, 'fc') else 10):
                # Simulate adding point with this label
                new_data = np.vstack([labeled_data, unlabeled_point.reshape(1, -1)])
                new_labels = np.append(labeled_labels, possible_label)
                
                # Calculate model change (simplified)
                change = self._simulate_model_change(model, new_data, new_labels)
                total_change += change
            
            expected_changes.append(total_change)
        
        return np.array(expected_changes)
    
    def _simulate_model_change(self, model: nn.Module, data: np.ndarray, labels: np.ndarray) -> float:
        """Simulate model change (simplified)"""
        # Simplified model change calculation
        return np.random.random()

class BatchActiveLearning:
    """Batch active learning"""
    
    def __init__(self, config: ActiveLearningConfig):
        self.config = config
        self.batch_history = []
        logger.info("✅ Batch Active Learning initialized")
    
    def query_batch(self, model: nn.Module, unlabeled_data: np.ndarray,
                   labeled_data: np.ndarray = None, n_samples: int = None) -> np.ndarray:
        """Query batch of samples"""
        logger.info(f"🎯 Querying batch of {n_samples or self.config.batch_size} samples")
        
        if n_samples is None:
            n_samples = self.config.batch_size
        
        # Combine uncertainty and diversity
        uncertainty_sampler = UncertaintySampler(self.config)
        diversity_sampler = DiversitySampler(self.config)
        
        # Calculate uncertainties
        uncertainties = uncertainty_sampler._calculate_uncertainties(model, unlabeled_data)
        
        # Calculate diversity scores
        diversity_scores = self._calculate_diversity_scores(unlabeled_data, labeled_data)
        
        # Combine scores
        combined_scores = (self.config.batch_diversity_weight * diversity_scores + 
                          (1 - self.config.batch_diversity_weight) * uncertainties)
        
        # Select batch
        batch_indices = np.argsort(combined_scores)[-n_samples:]
        batch_samples = unlabeled_data[batch_indices]
        
        # Store batch history
        self.batch_history.append({
            'uncertainties': uncertainties,
            'diversity_scores': diversity_scores,
            'combined_scores': combined_scores,
            'selected_indices': batch_indices,
            'batch_size': n_samples
        })
        
        return batch_samples
    
    def _calculate_diversity_scores(self, unlabeled_data: np.ndarray, 
                                  labeled_data: np.ndarray = None) -> np.ndarray:
        """Calculate diversity scores"""
        if labeled_data is None or len(labeled_data) == 0:
            return np.random.random(len(unlabeled_data))
        
        # Calculate distances to labeled data
        nn = NearestNeighbors(n_neighbors=1)
        nn.fit(labeled_data)
        
        distances, _ = nn.kneighbors(unlabeled_data)
        diversity_scores = distances.flatten()
        
        # Normalize scores
        diversity_scores = diversity_scores / np.max(diversity_scores)
        
        return diversity_scores

class ActiveLearningSystem:
    """Main active learning system"""
    
    def __init__(self, config: ActiveLearningConfig):
        self.config = config
        
        # Components
        self.uncertainty_sampler = UncertaintySampler(config)
        self.diversity_sampler = DiversitySampler(config)
        self.query_by_committee = QueryByCommittee(config)
        self.expected_model_change = ExpectedModelChange(config)
        self.batch_active_learning = BatchActiveLearning(config)
        
        # Active learning state
        self.active_learning_history = []
        self.labeled_data = []
        self.labeled_labels = []
        self.unlabeled_data = []
        
        logger.info("✅ Active Learning System initialized")
    
    def run_active_learning(self, model: nn.Module, initial_data: np.ndarray, 
                           initial_labels: np.ndarray, unlabeled_data: np.ndarray,
                           query_function: Callable = None) -> Dict[str, Any]:
        """Run active learning process"""
        logger.info(f"🚀 Running active learning with strategy: {self.config.active_learning_strategy.value}")
        
        active_learning_results = {
            'start_time': time.time(),
            'config': self.config,
            'stages': {}
        }
        
        # Initialize data
        self.labeled_data = initial_data.copy()
        self.labeled_labels = initial_labels.copy()
        self.unlabeled_data = unlabeled_data.copy()
        
        # Active learning loop
        for iteration in range(self.config.max_iterations):
            logger.info(f"🔄 Active learning iteration {iteration + 1}/{self.config.max_iterations}")
            
            # Stage 1: Query Strategy
            if self.config.active_learning_strategy == ActiveLearningStrategy.UNCERTAINTY_SAMPLING:
                logger.info("🎯 Stage 1: Uncertainty Sampling")
                
                queried_samples = self.uncertainty_sampler.sample_uncertain(
                    model, self.unlabeled_data
                )
            
            elif self.config.active_learning_strategy == ActiveLearningStrategy.DIVERSITY_SAMPLING:
                logger.info("🎯 Stage 1: Diversity Sampling")
                
                queried_samples = self.diversity_sampler.sample_diverse(
                    self.unlabeled_data, self.labeled_data
                )
            
            elif self.config.active_learning_strategy == ActiveLearningStrategy.QUERY_BY_COMMITTEE:
                logger.info("🎯 Stage 1: Query by Committee")
                
                # Create committee if not exists
                if not self.query_by_committee.committee_models:
                    self.query_by_committee.create_committee(model)
                
                queried_samples = self.query_by_committee.query_by_committee(
                    self.unlabeled_data
                )
            
            elif self.config.active_learning_strategy == ActiveLearningStrategy.EXPECTED_MODEL_CHANGE:
                logger.info("🎯 Stage 1: Expected Model Change")
                
                queried_samples = self.expected_model_change.query_expected_model_change(
                    model, self.unlabeled_data, self.labeled_data, self.labeled_labels
                )
            
            elif self.config.active_learning_strategy == ActiveLearningStrategy.BATCH_ACTIVE_LEARNING:
                logger.info("🎯 Stage 1: Batch Active Learning")
                
                queried_samples = self.batch_active_learning.query_batch(
                    model, self.unlabeled_data, self.labeled_data
                )
            
            else:
                # Default to uncertainty sampling
                queried_samples = self.uncertainty_sampler.sample_uncertain(
                    model, self.unlabeled_data
                )
            
            # Stage 2: Label Queries
            if query_function is not None:
                logger.info("🏷️ Stage 2: Label Queries")
                
                queried_labels = query_function(queried_samples)
            else:
                # Simulate labels (for demonstration)
                queried_labels = np.random.randint(0, 10, len(queried_samples))
            
            # Stage 3: Update Data
            logger.info("📊 Stage 3: Update Data")
            
            # Add queried samples to labeled data
            self.labeled_data = np.vstack([self.labeled_data, queried_samples])
            self.labeled_labels = np.append(self.labeled_labels, queried_labels)
            
            # Remove queried samples from unlabeled data
            queried_indices = []
            for queried_sample in queried_samples:
                for i, unlabeled_sample in enumerate(self.unlabeled_data):
                    if np.allclose(queried_sample, unlabeled_sample):
                        queried_indices.append(i)
                        break
            
            self.unlabeled_data = np.delete(self.unlabeled_data, queried_indices, axis=0)
            
            # Store iteration results
            iteration_result = {
                'iteration': iteration,
                'queried_samples': queried_samples,
                'queried_labels': queried_labels,
                'labeled_data_size': len(self.labeled_data),
                'unlabeled_data_size': len(self.unlabeled_data),
                'strategy': self.config.active_learning_strategy.value
            }
            
            active_learning_results['stages'][f'iteration_{iteration}'] = iteration_result
            
            # Check stopping criteria
            if len(self.unlabeled_data) == 0:
                logger.info("✅ No more unlabeled data available")
                break
        
        # Final evaluation
        active_learning_results['end_time'] = time.time()
        active_learning_results['total_duration'] = active_learning_results['end_time'] - active_learning_results['start_time']
        active_learning_results['final_labeled_data'] = self.labeled_data
        active_learning_results['final_labeled_labels'] = self.labeled_labels
        active_learning_results['final_unlabeled_data'] = self.unlabeled_data
        
        # Store results
        self.active_learning_history.append(active_learning_results)
        
        logger.info("✅ Active learning completed")
        return active_learning_results
    
    def generate_active_learning_report(self, results: Dict[str, Any]) -> str:
        """Generate active learning report"""
        report = []
        report.append("=" * 50)
        report.append("ACTIVE LEARNING REPORT")
        report.append("=" * 50)
        
        # Configuration
        report.append("\nACTIVE LEARNING CONFIGURATION:")
        report.append("-" * 32)
        report.append(f"Active Learning Strategy: {self.config.active_learning_strategy.value}")
        report.append(f"Uncertainty Measure: {self.config.uncertainty_measure.value}")
        report.append(f"Query Strategy: {self.config.query_strategy.value}")
        report.append(f"Number of Initial Samples: {self.config.n_initial_samples}")
        report.append(f"Number of Query Samples: {self.config.n_query_samples}")
        report.append(f"Number of Total Samples: {self.config.n_total_samples}")
        report.append(f"Maximum Iterations: {self.config.max_iterations}")
        report.append(f"Uncertainty Threshold: {self.config.uncertainty_threshold}")
        report.append(f"Entropy Threshold: {self.config.entropy_threshold}")
        report.append(f"Margin Threshold: {self.config.margin_threshold}")
        report.append(f"Diversity Method: {self.config.diversity_method}")
        report.append(f"Number of Clusters: {self.config.n_clusters}")
        report.append(f"Diversity Weight: {self.config.diversity_weight}")
        report.append(f"Number of Committee Members: {self.config.n_committee_members}")
        report.append(f"Disagreement Threshold: {self.config.disagreement_threshold}")
        report.append(f"Batch Size: {self.config.batch_size}")
        report.append(f"Batch Diversity Weight: {self.config.batch_diversity_weight}")
        report.append(f"Adaptive Sampling: {'Enabled' if self.config.enable_adaptive_sampling else 'Disabled'}")
        report.append(f"Cost Sensitive Sampling: {'Enabled' if self.config.enable_cost_sensitive_sampling else 'Disabled'}")
        report.append(f"Online Learning: {'Enabled' if self.config.enable_online_learning else 'Disabled'}")
        report.append(f"Model Uncertainty: {'Enabled' if self.config.enable_model_uncertainty else 'Disabled'}")
        
        # Results
        report.append("\nACTIVE LEARNING RESULTS:")
        report.append("-" * 25)
        report.append(f"Total Duration: {results.get('total_duration', 0):.2f} seconds")
        report.append(f"Start Time: {results.get('start_time', 'Unknown')}")
        report.append(f"End Time: {results.get('end_time', 'Unknown')}")
        report.append(f"Final Labeled Data Size: {len(results.get('final_labeled_data', []))}")
        report.append(f"Final Unlabeled Data Size: {len(results.get('final_unlabeled_data', []))}")
        
        # Stage results
        if 'stages' in results:
            report.append(f"\nNumber of Iterations: {len(results['stages'])}")
            
            for stage_name, stage_data in results['stages'].items():
                if isinstance(stage_data, dict):
                    report.append(f"\n{stage_name.upper()}:")
                    report.append("-" * len(stage_name))
                    
                    for key, value in stage_data.items():
                        report.append(f"  {key}: {value}")
        
        return "\n".join(report)
    
    def visualize_active_learning_results(self, save_path: str = None):
        """Visualize active learning results"""
        if not self.active_learning_history:
            logger.warning("No active learning history to visualize")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Plot 1: Active learning duration over time
        durations = [r.get('total_duration', 0) for r in self.active_learning_history]
        axes[0, 0].plot(durations, 'b-', linewidth=2)
        axes[0, 0].set_xlabel('Active Learning Run')
        axes[0, 0].set_ylabel('Duration (seconds)')
        axes[0, 0].set_title('Active Learning Duration Over Time')
        axes[0, 0].grid(True)
        
        # Plot 2: Strategy distribution
        strategies = [self.config.active_learning_strategy.value]
        strategy_counts = [1]
        
        axes[0, 1].pie(strategy_counts, labels=strategies, autopct='%1.1f%%')
        axes[0, 1].set_title('Active Learning Strategy Distribution')
        
        # Plot 3: Uncertainty measure distribution
        uncertainty_measures = [self.config.uncertainty_measure.value]
        measure_counts = [1]
        
        axes[1, 0].pie(measure_counts, labels=uncertainty_measures, autopct='%1.1f%%')
        axes[1, 0].set_title('Uncertainty Measure Distribution')
        
        # Plot 4: Active learning configuration
        config_values = [
            self.config.n_initial_samples,
            self.config.n_query_samples,
            self.config.max_iterations,
            self.config.batch_size
        ]
        config_labels = ['Initial Samples', 'Query Samples', 'Max Iterations', 'Batch Size']
        
        axes[1, 1].bar(config_labels, config_values, color=['blue', 'green', 'orange', 'red'])
        axes[1, 1].set_ylabel('Value')
        axes[1, 1].set_title('Active Learning Configuration')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        
        plt.close()

# Factory functions
def create_active_learning_config(**kwargs) -> ActiveLearningConfig:
    """Create active learning configuration"""
    return ActiveLearningConfig(**kwargs)

def create_uncertainty_sampler(config: ActiveLearningConfig) -> UncertaintySampler:
    """Create uncertainty sampler"""
    return UncertaintySampler(config)

def create_diversity_sampler(config: ActiveLearningConfig) -> DiversitySampler:
    """Create diversity sampler"""
    return DiversitySampler(config)

def create_query_by_committee(config: ActiveLearningConfig) -> QueryByCommittee:
    """Create query by committee"""
    return QueryByCommittee(config)

def create_expected_model_change(config: ActiveLearningConfig) -> ExpectedModelChange:
    """Create expected model change"""
    return ExpectedModelChange(config)

def create_batch_active_learning(config: ActiveLearningConfig) -> BatchActiveLearning:
    """Create batch active learning"""
    return BatchActiveLearning(config)

def create_active_learning_system(config: ActiveLearningConfig) -> ActiveLearningSystem:
    """Create active learning system"""
    return ActiveLearningSystem(config)

# Example usage
def example_active_learning():
    """Example of active learning system"""
    # Create configuration
    config = create_active_learning_config(
        active_learning_strategy=ActiveLearningStrategy.UNCERTAINTY_SAMPLING,
        uncertainty_measure=UncertaintyMeasure.ENTROPY,
        query_strategy=QueryStrategy.UNCERTAINTY_BASED,
        n_initial_samples=100,
        n_query_samples=10,
        n_total_samples=1000,
        max_iterations=50,
        uncertainty_threshold=0.5,
        entropy_threshold=0.8,
        margin_threshold=0.1,
        diversity_method="kmeans",
        n_clusters=10,
        diversity_weight=0.5,
        n_committee_members=5,
        disagreement_threshold=0.3,
        batch_size=20,
        batch_diversity_weight=0.3,
        enable_adaptive_sampling=True,
        enable_cost_sensitive_sampling=False,
        enable_online_learning=True,
        enable_model_uncertainty=True
    )
    
    # Create active learning system
    active_learning_system = create_active_learning_system(config)
    
    # Create dummy model and data
    model = nn.Sequential(
        nn.Linear(784, 256),
        nn.ReLU(),
        nn.Dropout(0.5),
        nn.Linear(256, 128),
        nn.ReLU(),
        nn.Dropout(0.5),
        nn.Linear(128, 10)
    )
    
    # Generate dummy data
    n_samples = 1000
    n_features = 784
    
    initial_data = np.random.randn(100, n_features)
    initial_labels = np.random.randint(0, 10, 100)
    unlabeled_data = np.random.randn(900, n_features)
    
    # Define query function
    def query_function(samples):
        return np.random.randint(0, 10, len(samples))
    
    # Run active learning
    active_learning_results = active_learning_system.run_active_learning(
        model, initial_data, initial_labels, unlabeled_data, query_function
    )
    
    # Generate report
    active_learning_report = active_learning_system.generate_active_learning_report(active_learning_results)
    
    print(f"✅ Active Learning Example Complete!")
    print(f"🚀 Active Learning Statistics:")
    print(f"   Active Learning Strategy: {config.active_learning_strategy.value}")
    print(f"   Uncertainty Measure: {config.uncertainty_measure.value}")
    print(f"   Query Strategy: {config.query_strategy.value}")
    print(f"   Number of Initial Samples: {config.n_initial_samples}")
    print(f"   Number of Query Samples: {config.n_query_samples}")
    print(f"   Number of Total Samples: {config.n_total_samples}")
    print(f"   Maximum Iterations: {config.max_iterations}")
    print(f"   Uncertainty Threshold: {config.uncertainty_threshold}")
    print(f"   Entropy Threshold: {config.entropy_threshold}")
    print(f"   Margin Threshold: {config.margin_threshold}")
    print(f"   Diversity Method: {config.diversity_method}")
    print(f"   Number of Clusters: {config.n_clusters}")
    print(f"   Diversity Weight: {config.diversity_weight}")
    print(f"   Number of Committee Members: {config.n_committee_members}")
    print(f"   Disagreement Threshold: {config.disagreement_threshold}")
    print(f"   Batch Size: {config.batch_size}")
    print(f"   Batch Diversity Weight: {config.batch_diversity_weight}")
    print(f"   Adaptive Sampling: {'Enabled' if config.enable_adaptive_sampling else 'Disabled'}")
    print(f"   Cost Sensitive Sampling: {'Enabled' if config.enable_cost_sensitive_sampling else 'Disabled'}")
    print(f"   Online Learning: {'Enabled' if config.enable_online_learning else 'Disabled'}")
    print(f"   Model Uncertainty: {'Enabled' if config.enable_model_uncertainty else 'Disabled'}")
    
    print(f"\n📊 Active Learning Results:")
    print(f"   Active Learning History Length: {len(active_learning_system.active_learning_history)}")
    print(f"   Total Duration: {active_learning_results.get('total_duration', 0):.2f} seconds")
    print(f"   Final Labeled Data Size: {len(active_learning_results.get('final_labeled_data', []))}")
    print(f"   Final Unlabeled Data Size: {len(active_learning_results.get('final_unlabeled_data', []))}")
    
    # Show stage results summary
    if 'stages' in active_learning_results:
        print(f"   Number of Iterations: {len(active_learning_results['stages'])}")
    
    print(f"\n📋 Active Learning Report:")
    print(active_learning_report)
    
    return active_learning_system

# Export utilities
__all__ = [
    'ActiveLearningStrategy',
    'UncertaintyMeasure',
    'QueryStrategy',
    'ActiveLearningConfig',
    'UncertaintySampler',
    'DiversitySampler',
    'QueryByCommittee',
    'ExpectedModelChange',
    'BatchActiveLearning',
    'ActiveLearningSystem',
    'create_active_learning_config',
    'create_uncertainty_sampler',
    'create_diversity_sampler',
    'create_query_by_committee',
    'create_expected_model_change',
    'create_batch_active_learning',
    'create_active_learning_system',
    'example_active_learning'
]

if __name__ == "__main__":
    example_active_learning()
    print("✅ Active learning example completed successfully!")