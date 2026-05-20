"""
Advanced Neural Architecture Search (NAS) for TruthGPT Optimization Core
Automated neural architecture discovery and optimization
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
import itertools

logger = logging.getLogger(__name__)

class SearchStrategy(Enum):
    """Neural Architecture Search strategies"""
    RANDOM = "random"
    EVOLUTIONARY = "evolutionary"
    REINFORCEMENT = "reinforcement"
    GRADIENT_BASED = "gradient_based"
    DIFFERENTIABLE = "differentiable"

@dataclass
class NASConfig:
    """Configuration for Neural Architecture Search"""
    # Search parameters
    search_strategy: SearchStrategy = SearchStrategy.EVOLUTIONARY
    population_size: int = 50
    generations: int = 100
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    
    # Architecture constraints
    max_layers: int = 20
    min_layers: int = 3
    max_width: int = 1024
    min_width: int = 32
    
    # Search space
    layer_types: List[str] = field(default_factory=lambda: [
        'Linear', 'Conv2d', 'LSTM', 'GRU', 'MultiheadAttention', 'Transformer'
    ])
    activation_types: List[str] = field(default_factory=lambda: [
        'ReLU', 'GELU', 'Swish', 'Mish', 'LeakyReLU'
    ])
    
    # Optimization
    search_budget: int = 1000  # Total evaluations
    early_stopping_patience: int = 20
    performance_threshold: float = 0.95
    
    # Advanced features
    enable_multi_objective: bool = True
    enable_transfer_learning: bool = True
    enable_architecture_pruning: bool = True
    
    def __post_init__(self):
        """Validate NAS configuration"""
        if self.population_size < 2:
            raise ValueError("Population size must be at least 2")
        if self.mutation_rate < 0.0 or self.mutation_rate > 1.0:
            raise ValueError("Mutation rate must be between 0.0 and 1.0")

class ArchitectureGene:
    """Gene representing a layer in neural architecture"""
    
    def __init__(self, layer_type: str, params: Dict[str, Any]):
        self.layer_type = layer_type
        self.params = params
        self.fitness = 0.0
    
    def mutate(self, config: NASConfig):
        """Mutate this gene"""
        # Mutate layer type
        if random.random() < config.mutation_rate:
            self.layer_type = random.choice(config.layer_types)
        
        # Mutate parameters
        for param_name, param_value in self.params.items():
            if random.random() < config.mutation_rate:
                if isinstance(param_value, int):
                    # Mutate integer parameters
                    if param_name in ['out_features', 'hidden_size', 'embed_dim']:
                        self.params[param_name] = random.randint(
                            config.min_width, config.max_width
                        )
                    elif param_name == 'num_heads':
                        self.params[param_name] = random.choice([4, 8, 16, 32])
                elif isinstance(param_value, float):
                    # Mutate float parameters
                    self.params[param_name] = max(0.0, param_value + random.gauss(0, 0.1))
    
    def crossover(self, other: 'ArchitectureGene') -> Tuple['ArchitectureGene', 'ArchitectureGene']:
        """Crossover with another gene"""
        # Create offspring
        child1 = ArchitectureGene(self.layer_type, self.params.copy())
        child2 = ArchitectureGene(other.layer_type, other.params.copy())
        
        # Crossover parameters
        for param_name in self.params:
            if random.random() < 0.5:
                child1.params[param_name] = other.params[param_name]
                child2.params[param_name] = self.params[param_name]
        
        return child1, child2
    
    def to_layer(self) -> nn.Module:
        """Convert gene to PyTorch layer"""
        if self.layer_type == 'Linear':
            return nn.Linear(
                self.params.get('in_features', 128),
                self.params.get('out_features', 64)
            )
        elif self.layer_type == 'Conv2d':
            return nn.Conv2d(
                self.params.get('in_channels', 3),
                self.params.get('out_channels', 32),
                kernel_size=self.params.get('kernel_size', 3),
                stride=self.params.get('stride', 1),
                padding=self.params.get('padding', 1)
            )
        elif self.layer_type == 'LSTM':
            return nn.LSTM(
                input_size=self.params.get('input_size', 128),
                hidden_size=self.params.get('hidden_size', 64),
                num_layers=self.params.get('num_layers', 1),
                batch_first=True
            )
        elif self.layer_type == 'MultiheadAttention':
            return nn.MultiheadAttention(
                embed_dim=self.params.get('embed_dim', 128),
                num_heads=self.params.get('num_heads', 8),
                dropout=self.params.get('dropout', 0.1)
            )
        else:
            # Default to Linear
            return nn.Linear(128, 64)

class NeuralArchitecture:
    """Neural architecture represented as a sequence of genes"""
    
    def __init__(self, genes: List[ArchitectureGene]):
        self.genes = genes
        self.fitness = 0.0
        self.complexity = self._calculate_complexity()
        self.performance_metrics = {}
    
    def _calculate_complexity(self) -> float:
        """Calculate architecture complexity"""
        total_params = 0
        for gene in self.genes:
            if gene.layer_type == 'Linear':
                in_features = gene.params.get('in_features', 128)
                out_features = gene.params.get('out_features', 64)
                total_params += in_features * out_features
            elif gene.layer_type == 'Conv2d':
                in_channels = gene.params.get('in_channels', 3)
                out_channels = gene.params.get('out_channels', 32)
                kernel_size = gene.params.get('kernel_size', 3)
                total_params += in_channels * out_channels * kernel_size * kernel_size
        
        return total_params / 1e6  # Convert to millions
    
    def mutate(self, config: NASConfig):
        """Mutate architecture"""
        # Mutate individual genes
        for gene in self.genes:
            gene.mutate(config)
        
        # Add/remove layers
        if random.random() < config.mutation_rate:
            if len(self.genes) < config.max_layers and random.random() < 0.5:
                # Add new layer
                new_gene = ArchitectureGene(
                    random.choice(config.layer_types),
                    self._generate_random_params(random.choice(config.layer_types))
                )
                insert_pos = random.randint(0, len(self.genes))
                self.genes.insert(insert_pos, new_gene)
            elif len(self.genes) > config.min_layers:
                # Remove layer
                remove_pos = random.randint(0, len(self.genes) - 1)
                del self.genes[remove_pos]
        
        # Update complexity
        self.complexity = self._calculate_complexity()
    
    def crossover(self, other: 'NeuralArchitecture') -> Tuple['NeuralArchitecture', 'NeuralArchitecture']:
        """Crossover with another architecture"""
        # Single-point crossover
        crossover_point = random.randint(1, min(len(self.genes), len(other.genes)) - 1)
        
        child1_genes = self.genes[:crossover_point] + other.genes[crossover_point:]
        child2_genes = other.genes[:crossover_point] + self.genes[crossover_point:]
        
        return NeuralArchitecture(child1_genes), NeuralArchitecture(child2_genes)
    
    def to_model(self, input_size: int = 128, output_size: int = 10) -> nn.Module:
        """Convert architecture to PyTorch model"""
        layers = []
        
        # Input layer
        current_size = input_size
        
        for i, gene in enumerate(self.genes):
            layer = gene.to_layer()
            
            # Adjust input size for Linear layers
            if isinstance(layer, nn.Linear):
                layer.in_features = current_size
                current_size = layer.out_features
            
            layers.append(layer)
            
            # Add activation
            activation = random.choice(['ReLU', 'GELU', 'Swish'])
            if activation == 'ReLU':
                layers.append(nn.ReLU())
            elif activation == 'GELU':
                layers.append(nn.GELU())
            elif activation == 'Swish':
                layers.append(nn.SiLU())  # Swish is SiLU in PyTorch
            
            # Add dropout
            if random.random() < 0.3:
                layers.append(nn.Dropout(0.1))
        
        # Output layer
        layers.append(nn.Linear(current_size, output_size))
        
        return nn.Sequential(*layers)
    
    def _generate_random_params(self, layer_type: str) -> Dict[str, Any]:
        """Generate random parameters for layer type"""
        if layer_type == 'Linear':
            return {
                'in_features': random.randint(32, 512),
                'out_features': random.randint(32, 512)
            }
        elif layer_type == 'Conv2d':
            return {
                'in_channels': random.choice([1, 3, 16, 32]),
                'out_channels': random.choice([16, 32, 64, 128]),
                'kernel_size': random.choice([3, 5, 7]),
                'stride': random.choice([1, 2]),
                'padding': random.choice([0, 1, 2])
            }
        elif layer_type == 'LSTM':
            return {
                'input_size': random.randint(32, 256),
                'hidden_size': random.randint(32, 256),
                'num_layers': random.randint(1, 3)
            }
        elif layer_type == 'MultiheadAttention':
            return {
                'embed_dim': random.choice([64, 128, 256, 512]),
                'num_heads': random.choice([4, 8, 16]),
                'dropout': random.uniform(0.0, 0.3)
            }
        else:
            return {}

class EvolutionaryNAS:
    """Evolutionary Neural Architecture Search"""
    
    def __init__(self, config: NASConfig):
        self.config = config
        self.population = []
        self.generation = 0
        self.best_architecture = None
        self.search_history = []
        
        logger.info("✅ Evolutionary NAS initialized")
    
    def initialize_population(self):
        """Initialize random population"""
        self.population = []
        
        for _ in range(self.config.population_size):
            # Random number of layers
            num_layers = random.randint(self.config.min_layers, self.config.max_layers)
            
            # Generate random genes
            genes = []
            for _ in range(num_layers):
                layer_type = random.choice(self.config.layer_types)
                params = self._generate_random_params(layer_type)
                gene = ArchitectureGene(layer_type, params)
                genes.append(gene)
            
            architecture = NeuralArchitecture(genes)
            self.population.append(architecture)
        
        logger.info(f"✅ Population initialized with {len(self.population)} architectures")
    
    def evaluate_population(self, evaluation_func: Callable[[nn.Module], float]):
        """Evaluate population fitness"""
        for architecture in self.population:
            try:
                # Convert to model
                model = architecture.to_model()
                
                # Evaluate
                fitness = evaluation_func(model)
                architecture.fitness = fitness
                
                # Update best
                if self.best_architecture is None or fitness > self.best_architecture.fitness:
                    self.best_architecture = architecture
                
            except Exception as e:
                logger.warning(f"Architecture evaluation failed: {e}")
                architecture.fitness = 0.0
    
    def evolve_generation(self):
        """Evolve one generation"""
        # Sort by fitness
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        
        # Keep top performers
        elite_size = max(1, self.config.population_size // 10)
        elite = self.population[:elite_size]
        
        # Generate new population
        new_population = elite.copy()
        
        while len(new_population) < self.config.population_size:
            # Selection
            parent1 = self._tournament_selection()
            parent2 = self._tournament_selection()
            
            # Crossover
            if random.random() < self.config.crossover_rate:
                child1, child2 = parent1.crossover(parent2)
            else:
                child1, child2 = parent1, parent2
            
            # Mutation
            child1.mutate(self.config)
            child2.mutate(self.config)
            
            new_population.extend([child1, child2])
        
        # Trim to population size
        self.population = new_population[:self.config.population_size]
        self.generation += 1
        
        # Record generation stats
        avg_fitness = np.mean([arch.fitness for arch in self.population])
        max_fitness = max([arch.fitness for arch in self.population])
        
        self.search_history.append({
            'generation': self.generation,
            'avg_fitness': avg_fitness,
            'max_fitness': max_fitness,
            'best_fitness': self.best_architecture.fitness if self.best_architecture else 0.0
        })
        
        logger.info(f"Generation {self.generation}: avg_fitness={avg_fitness:.4f}, max_fitness={max_fitness:.4f}")
    
    def _tournament_selection(self, tournament_size: int = 3) -> NeuralArchitecture:
        """Tournament selection"""
        tournament = random.sample(self.population, min(tournament_size, len(self.population)))
        return max(tournament, key=lambda x: x.fitness)
    
    def _generate_random_params(self, layer_type: str) -> Dict[str, Any]:
        """Generate random parameters for layer type"""
        if layer_type == 'Linear':
            return {
                'in_features': random.randint(32, 512),
                'out_features': random.randint(32, 512)
            }
        elif layer_type == 'Conv2d':
            return {
                'in_channels': random.choice([1, 3, 16, 32]),
                'out_channels': random.choice([16, 32, 64, 128]),
                'kernel_size': random.choice([3, 5, 7]),
                'stride': random.choice([1, 2]),
                'padding': random.choice([0, 1, 2])
            }
        elif layer_type == 'LSTM':
            return {
                'input_size': random.randint(32, 256),
                'hidden_size': random.randint(32, 256),
                'num_layers': random.randint(1, 3)
            }
        elif layer_type == 'MultiheadAttention':
            return {
                'embed_dim': random.choice([64, 128, 256, 512]),
                'num_heads': random.choice([4, 8, 16]),
                'dropout': random.uniform(0.0, 0.3)
            }
        else:
            return {}
    
    def search(self, evaluation_func: Callable[[nn.Module], float]) -> NeuralArchitecture:
        """Perform architecture search"""
        logger.info("🚀 Starting Neural Architecture Search...")
        
        # Initialize population
        self.initialize_population()
        
        # Search loop
        for generation in range(self.config.generations):
            # Evaluate population
            self.evaluate_population(evaluation_func)
            
            # Check early stopping
            if self.best_architecture and self.best_architecture.fitness >= self.config.performance_threshold:
                logger.info(f"✅ Performance threshold reached at generation {generation}")
                break
            
            # Evolve
            self.evolve_generation()
            
            # Check convergence
            if len(self.search_history) >= self.config.early_stopping_patience:
                recent_fitness = [h['max_fitness'] for h in self.search_history[-self.config.early_stopping_patience:]]
                if max(recent_fitness) - min(recent_fitness) < 0.001:
                    logger.info(f"✅ Convergence detected at generation {generation}")
                    break
        
        logger.info(f"✅ NAS completed. Best fitness: {self.best_architecture.fitness:.4f}")
        return self.best_architecture
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """Get search statistics"""
        if not self.search_history:
            return {}
        
        return {
            'total_generations': self.generation,
            'best_fitness': self.best_architecture.fitness if self.best_architecture else 0.0,
            'final_avg_fitness': self.search_history[-1]['avg_fitness'] if self.search_history else 0.0,
            'fitness_improvement': self.search_history[-1]['max_fitness'] - self.search_history[0]['max_fitness'] if len(self.search_history) > 1 else 0.0,
            'search_history': self.search_history,
            'best_architecture_complexity': self.best_architecture.complexity if self.best_architecture else 0.0
        }

class DifferentiableNAS:
    """Differentiable Neural Architecture Search"""
    
    def __init__(self, config: NASConfig):
        self.config = config
        self.supernet = None
        self.architecture_weights = None
        
        logger.info("✅ Differentiable NAS initialized")
    
    def build_supernet(self, input_size: int = 128, output_size: int = 10):
        """Build supernet containing all possible operations"""
        # This is a simplified implementation
        # In practice, this would be much more sophisticated
        
        self.supernet = nn.ModuleDict({
            'linear_32': nn.Linear(input_size, 32),
            'linear_64': nn.Linear(input_size, 64),
            'linear_128': nn.Linear(input_size, 128),
            'linear_256': nn.Linear(input_size, 256),
            'relu': nn.ReLU(),
            'gelu': nn.GELU(),
            'swish': nn.SiLU(),
            'dropout': nn.Dropout(0.1)
        })
        
        # Initialize architecture weights
        num_ops = len(self.supernet)
        self.architecture_weights = nn.Parameter(torch.randn(num_ops))
        
        logger.info(f"✅ Supernet built with {num_ops} operations")
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through supernet"""
        if self.supernet is None:
            raise ValueError("Supernet not built. Call build_supernet() first.")
        
        # Apply softmax to architecture weights
        weights = torch.softmax(self.architecture_weights, dim=0)
        
        # Weighted combination of operations
        outputs = []
        for i, (name, module) in enumerate(self.supernet.items()):
            if 'linear' in name:
                output = module(x)
                outputs.append(weights[i] * output)
        
        # Combine outputs
        if outputs:
            combined = torch.stack(outputs, dim=0).sum(dim=0)
        else:
            combined = x
        
        # Apply activations
        combined = self.supernet['relu'](combined)
        
        return combined
    
    def search(self, train_loader, val_loader, epochs: int = 100) -> Dict[str, Any]:
        """Perform differentiable architecture search"""
        logger.info("🚀 Starting Differentiable NAS...")
        
        if self.supernet is None:
            self.build_supernet()
        
        optimizer = optim.Adam(self.supernet.parameters(), lr=0.001)
        arch_optimizer = optim.Adam([self.architecture_weights], lr=0.01)
        
        best_accuracy = 0.0
        search_history = []
        
        for epoch in range(epochs):
            # Train architecture weights
            self.supernet.train()
            
            for batch_idx, (data, target) in enumerate(train_loader):
                optimizer.zero_grad()
                arch_optimizer.zero_grad()
                
                output = self.forward(data)
                loss = nn.CrossEntropyLoss()(output, target)
                
                loss.backward()
                optimizer.step()
                arch_optimizer.step()
            
            # Validate
            self.supernet.eval()
            correct = 0
            total = 0
            
            with torch.no_grad():
                for data, target in val_loader:
                    output = self.forward(data)
                    _, predicted = torch.max(output.data, 1)
                    total += target.size(0)
                    correct += (predicted == target).sum().item()
            
            accuracy = correct / total
            best_accuracy = max(best_accuracy, accuracy)
            
            search_history.append({
                'epoch': epoch,
                'accuracy': accuracy,
                'best_accuracy': best_accuracy
            })
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}: Accuracy = {accuracy:.4f}")
        
        logger.info(f"✅ Differentiable NAS completed. Best accuracy: {best_accuracy:.4f}")
        
        return {
            'best_accuracy': best_accuracy,
            'search_history': search_history,
            'final_architecture_weights': self.architecture_weights.detach().cpu().numpy()
        }

# Factory functions
def create_nas_config(**kwargs) -> NASConfig:
    """Create NAS configuration"""
    return NASConfig(**kwargs)

def create_evolutionary_nas(config: NASConfig) -> EvolutionaryNAS:
    """Create evolutionary NAS instance"""
    return EvolutionaryNAS(config)

def create_differentiable_nas(config: NASConfig) -> DifferentiableNAS:
    """Create differentiable NAS instance"""
    return DifferentiableNAS(config)

# Example usage
def example_neural_architecture_search():
    """Example of Neural Architecture Search"""
    # Create configuration
    config = create_nas_config(
        search_strategy=SearchStrategy.EVOLUTIONARY,
        population_size=20,
        generations=50,
        mutation_rate=0.1,
        crossover_rate=0.8
    )
    
    # Create evolutionary NAS
    nas = create_evolutionary_nas(config)
    
    # Define evaluation function
    def evaluate_model(model: nn.Module) -> float:
        """Simple evaluation function"""
        try:
            # Count parameters
            total_params = sum(p.numel() for p in model.parameters())
            
            # Simple fitness based on parameter count and model depth
            depth = len(list(model.modules()))
            
            # Prefer models with moderate complexity
            complexity_score = 1.0 / (1.0 + total_params / 1e6)
            depth_score = 1.0 / (1.0 + abs(depth - 5) / 10)
            
            fitness = complexity_score * depth_score
            return fitness
        except:
            return 0.0
    
    # Perform search
    best_architecture = nas.search(evaluate_model)
    
    # Get statistics
    stats = nas.get_search_statistics()
    
    print(f"✅ Neural Architecture Search Example Complete!")
    print(f"🔍 Search Statistics:")
    print(f"   Total Generations: {stats['total_generations']}")
    print(f"   Best Fitness: {stats['best_fitness']:.4f}")
    print(f"   Fitness Improvement: {stats['fitness_improvement']:.4f}")
    print(f"   Best Architecture Complexity: {stats['best_architecture_complexity']:.2f}M params")
    
    # Convert best architecture to model
    if best_architecture:
        best_model = best_architecture.to_model()
        print(f"🏆 Best Model: {best_model}")
    
    return best_architecture

# Export utilities
__all__ = [
    'SearchStrategy',
    'NASConfig',
    'ArchitectureGene',
    'NeuralArchitecture',
    'EvolutionaryNAS',
    'DifferentiableNAS',
    'create_nas_config',
    'create_evolutionary_nas',
    'create_differentiable_nas',
    'example_neural_architecture_search'
]

if __name__ == "__main__":
    example_neural_architecture_search()
    print("✅ Neural Architecture Search example completed successfully!")







