import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Any, Tuple
from collections import defaultdict

class NeuralArchitectureSearchRouter(nn.Module):
    """Neural Architecture Search for optimal expert configurations."""
    def __init__(self, hidden_size: int, search_space_size: int = 100, population_size: int = 20, mutation_rate: float = 0.1, crossover_rate: float = 0.8):
        super().__init__()
        self.hidden_size, self.search_space_size, self.population_size, self.mutation_rate, self.crossover_rate = hidden_size, search_space_size, population_size, mutation_rate, crossover_rate
        self.architecture_space = {'num_layers': [1, 2, 3, 4, 5], 'hidden_sizes': [hidden_size // 4, hidden_size // 2, hidden_size, hidden_size * 2], 'activations': ['relu', 'gelu', 'swish', 'tanh'], 'dropout_rates': [0.0, 0.1, 0.2, 0.3], 'normalization': ['layer_norm', 'batch_norm', 'group_norm', 'none']}
        self.population = [{k: np.random.choice(v) for k, v in self.architecture_space.items()} for _ in range(population_size)]
        self.performance_history = defaultdict(list)

    def evaluate_architecture(self, architecture, performance):
        latency_score = 1.0 / (1.0 + performance.get('latency_ms', 0))
        throughput_score = performance.get('throughput_tokens_per_sec', 0) / 1000
        memory_score = 1.0 / (1.0 + performance.get('memory_usage_mb', 0) / 100)
        penalty = architecture['num_layers'] * 0.1 + architecture['hidden_sizes'] / self.hidden_size * 0.1
        return (latency_score * 0.4 + throughput_score * 0.4 + memory_score * 0.2) - penalty

    def evolve_population(self, performance_data):
        fitness = [self.evaluate_architecture(arch, performance_data.get(i, {})) for i, arch in enumerate(self.population)]
        sorted_indices = np.argsort(fitness)[::-1]
        new_pop = [self.population[i] for i in sorted_indices[:self.population_size // 4]]
        while len(new_pop) < self.population_size:
            p1, p2 = self._tournament(fitness), self._tournament(fitness)
            c1, c2 = self._crossover(self.population[p1], self.population[p2]) if np.random.random() < self.crossover_rate else (self.population[p1].copy(), self.population[p2].copy())
            new_pop.extend([self._mutate(c1) if np.random.random() < self.mutation_rate else c1, self._mutate(c2) if np.random.random() < self.mutation_rate else c2])
        self.population = new_pop[:self.population_size]
        return self.population

    def _tournament(self, fitness, size=3):
        indices = np.random.choice(len(fitness), size, replace=False)
        return indices[np.argmax([fitness[i] for i in indices])]

    def _crossover(self, p1, p2):
        c1, c2 = p1.copy(), p2.copy()
        for k in c1.keys():
            if np.random.random() < 0.5: c1[k], c2[k] = c2[k], p1[k]
        return c1, c2

    def _mutate(self, ind):
        mut = ind.copy()
        for k, v in self.architecture_space.items():
            if np.random.random() < 0.3: mut[k] = np.random.choice(v)
        return mut
