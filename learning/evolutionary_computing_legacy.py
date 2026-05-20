"""
Advanced Neural Network Evolutionary Computing System for TruthGPT Optimization Core
Complete evolutionary computing with genetic algorithms, evolutionary strategies, and population-based optimization
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

class SelectionMethod(Enum):
    """Selection methods"""
    ROULETTE_WHEEL = "roulette_wheel"
    TOURNAMENT = "tournament"
    RANK = "rank"
    ELITIST = "elitist"
    STOCHASTIC_UNIVERSAL = "stochastic_universal"
    TRUNCATION = "truncation"

class CrossoverMethod(Enum):
    """Crossover methods"""
    SINGLE_POINT = "single_point"
    TWO_POINT = "two_point"
    UNIFORM = "uniform"
    ARITHMETIC = "arithmetic"
    BLEND = "blend"
    SIMULATED_BINARY = "simulated_binary"

class MutationMethod(Enum):
    """Mutation methods"""
    GAUSSIAN = "gaussian"
    UNIFORM = "uniform"
    POLYNOMIAL = "polynomial"
    NON_UNIFORM = "non_uniform"
    BOUNDARY = "boundary"
    CREEP = "creep"

class EvolutionaryAlgorithm(Enum):
    """Evolutionary algorithms"""
    GENETIC_ALGORITHM = "genetic_algorithm"
    EVOLUTIONARY_STRATEGY = "evolutionary_strategy"
    DIFFERENTIAL_EVOLUTION = "differential_evolution"
    GENETIC_PROGRAMMING = "genetic_programming"
    PARTICLE_SWARM = "particle_swarm"
    ANT_COLONY = "ant_colony"

class EvolutionaryConfig:
    """Configuration for evolutionary computing system"""
    # Basic settings
    evolutionary_algorithm: EvolutionaryAlgorithm = EvolutionaryAlgorithm.GENETIC_ALGORITHM
    selection_method: SelectionMethod = SelectionMethod.TOURNAMENT
    crossover_method: CrossoverMethod = CrossoverMethod.SINGLE_POINT
    mutation_method: MutationMethod = MutationMethod.GAUSSIAN
    
    # Population settings
    population_size: int = 100
    elite_size: int = 10
    tournament_size: int = 3
    
    # Genetic operators
    crossover_rate: float = 0.8
    mutation_rate: float = 0.1
    mutation_strength: float = 0.1
    
    # Evolution settings
    max_generations: int = 1000
    convergence_threshold: float = 1e-6
    stagnation_limit: int = 50
    
    # Multi-objective settings
    enable_multi_objective: bool = False
    n_objectives: int = 2
    pareto_front_size: int = 20
    
    # Advanced features
    enable_adaptive_parameters: bool = True
    enable_diversity_maintenance: bool = True
    enable_local_search: bool = False
    enable_hybrid_evolution: bool = False
    
    def __post_init__(self):
        """Validate evolutionary configuration"""
        if self.population_size <= 0:
            raise ValueError("Population size must be positive")
        if self.elite_size < 0:
            raise ValueError("Elite size must be non-negative")
        if self.tournament_size <= 0:
            raise ValueError("Tournament size must be positive")
        if not (0 <= self.crossover_rate <= 1):
            raise ValueError("Crossover rate must be between 0 and 1")
        if not (0 <= self.mutation_rate <= 1):
            raise ValueError("Mutation rate must be between 0 and 1")
        if self.mutation_strength <= 0:
            raise ValueError("Mutation strength must be positive")
        if self.max_generations <= 0:
            raise ValueError("Maximum generations must be positive")
        if self.convergence_threshold <= 0:
            raise ValueError("Convergence threshold must be positive")
        if self.stagnation_limit <= 0:
            raise ValueError("Stagnation limit must be positive")
        if self.n_objectives <= 0:
            raise ValueError("Number of objectives must be positive")
        if self.pareto_front_size <= 0:
            raise ValueError("Pareto front size must be positive")

class Individual:
    """Individual in evolutionary algorithm"""
    
    def __init__(self, genes: np.ndarray, fitness: float = None):
        self.genes = genes.copy()
        self.fitness = fitness
        self.objectives = []
        self.age = 0
        logger.debug("✅ Individual created")
    
    def copy(self):
        """Create a copy of the individual"""
        new_individual = Individual(self.genes, self.fitness)
        new_individual.objectives = self.objectives.copy()
        new_individual.age = self.age
        return new_individual
    
    def mutate(self, mutation_method: MutationMethod, mutation_rate: float, 
               mutation_strength: float, bounds: List[Tuple[float, float]] = None):
        """Mutate the individual"""
        if random.random() < mutation_rate:
            if mutation_method == MutationMethod.GAUSSIAN:
                self._gaussian_mutation(mutation_strength)
            elif mutation_method == MutationMethod.UNIFORM:
                self._uniform_mutation(mutation_strength, bounds)
            elif mutation_method == MutationMethod.POLYNOMIAL:
                self._polynomial_mutation(mutation_strength, bounds)
            elif mutation_method == MutationMethod.NON_UNIFORM:
                self._non_uniform_mutation(mutation_strength, bounds)
            elif mutation_method == MutationMethod.BOUNDARY:
                self._boundary_mutation(bounds)
            elif mutation_method == MutationMethod.CREEP:
                self._creep_mutation(mutation_strength)
            else:
                self._gaussian_mutation(mutation_strength)
    
    def _gaussian_mutation(self, mutation_strength: float):
        """Gaussian mutation"""
        noise = np.random.normal(0, mutation_strength, self.genes.shape)
        self.genes += noise
    
    def _uniform_mutation(self, mutation_strength: float, bounds: List[Tuple[float, float]]):
        """Uniform mutation"""
        for i in range(len(self.genes)):
            if random.random() < 0.1:  # 10% chance per gene
                if bounds:
                    low, high = bounds[i]
                    self.genes[i] = random.uniform(low, high)
                else:
                    self.genes[i] += random.uniform(-mutation_strength, mutation_strength)
    
    def _polynomial_mutation(self, mutation_strength: float, bounds: List[Tuple[float, float]]):
        """Polynomial mutation"""
        for i in range(len(self.genes)):
            if random.random() < 0.1:  # 10% chance per gene
                if bounds:
                    low, high = bounds[i]
                    delta = random.uniform(-1, 1)
                    self.genes[i] = low + (high - low) * (0.5 + delta * mutation_strength)
    
    def _non_uniform_mutation(self, mutation_strength: float, bounds: List[Tuple[float, float]]):
        """Non-uniform mutation"""
        for i in range(len(self.genes)):
            if random.random() < 0.1:  # 10% chance per gene
                if bounds:
                    low, high = bounds[i]
                    delta = random.uniform(-1, 1)
                    self.genes[i] = low + (high - low) * (0.5 + delta * mutation_strength)
    
    def _boundary_mutation(self, bounds: List[Tuple[float, float]]):
        """Boundary mutation"""
        if bounds:
            for i in range(len(self.genes)):
                if random.random() < 0.1:  # 10% chance per gene
                    low, high = bounds[i]
                    self.genes[i] = random.choice([low, high])
    
    def _creep_mutation(self, mutation_strength: float):
        """Creep mutation"""
        for i in range(len(self.genes)):
            if random.random() < 0.1:  # 10% chance per gene
                self.genes[i] += random.uniform(-mutation_strength, mutation_strength)

class Population:
    """Population in evolutionary algorithm"""
    
    def __init__(self, config: EvolutionaryConfig):
        self.config = config
        self.individuals = []
        self.generation = 0
        self.best_fitness_history = []
        self.average_fitness_history = []
        self.diversity_history = []
        logger.info("✅ Population initialized")
    
    def initialize(self, gene_length: int, bounds: List[Tuple[float, float]] = None):
        """Initialize population with random individuals"""
        logger.info(f"🏗️ Initializing population with {self.config.population_size} individuals")
        
        self.individuals = []
        
        for _ in range(self.config.population_size):
            if bounds:
                genes = np.array([random.uniform(bounds[i][0], bounds[i][1]) 
                                for i in range(gene_length)])
            else:
                genes = np.random.randn(gene_length)
            
            individual = Individual(genes)
            self.individuals.append(individual)
        
        logger.info("✅ Population initialized")
    
    def evaluate_fitness(self, fitness_function: Callable):
        """Evaluate fitness for all individuals"""
        logger.info("📊 Evaluating fitness for all individuals")
        
        for individual in self.individuals:
            if individual.fitness is None:
                individual.fitness = fitness_function(individual.genes)
        
        # Sort by fitness (descending)
        self.individuals.sort(key=lambda x: x.fitness, reverse=True)
        
        # Store fitness history
        best_fitness = self.individuals[0].fitness
        average_fitness = np.mean([ind.fitness for ind in self.individuals])
        
        self.best_fitness_history.append(best_fitness)
        self.average_fitness_history.append(average_fitness)
        
        logger.info(f"   Best fitness: {best_fitness:.4f}, Average fitness: {average_fitness:.4f}")
    
    def select_parents(self) -> List[Individual]:
        """Select parents for reproduction"""
        logger.info(f"👥 Selecting parents using {self.config.selection_method.value}")
        
        if self.config.selection_method == SelectionMethod.ROULETTE_WHEEL:
            return self._roulette_wheel_selection()
        elif self.config.selection_method == SelectionMethod.TOURNAMENT:
            return self._tournament_selection()
        elif self.config.selection_method == SelectionMethod.RANK:
            return self._rank_selection()
        elif self.config.selection_method == SelectionMethod.ELITIST:
            return self._elitist_selection()
        elif self.config.selection_method == SelectionMethod.STOCHASTIC_UNIVERSAL:
            return self._stochastic_universal_selection()
        elif self.config.selection_method == SelectionMethod.TRUNCATION:
            return self._truncation_selection()
        else:
            return self._tournament_selection()
    
    def _roulette_wheel_selection(self) -> List[Individual]:
        """Roulette wheel selection"""
        # Calculate fitness weights
        fitness_values = [ind.fitness for ind in self.individuals]
        min_fitness = min(fitness_values)
        
        # Shift fitness values to be positive
        shifted_fitness = [f - min_fitness + 1e-8 for f in fitness_values]
        total_fitness = sum(shifted_fitness)
        
        # Select parents
        parents = []
        for _ in range(self.config.population_size):
            r = random.uniform(0, total_fitness)
            cumulative = 0
            
            for individual, fitness in zip(self.individuals, shifted_fitness):
                cumulative += fitness
                if cumulative >= r:
                    parents.append(individual.copy())
                    break
        
        return parents
    
    def _tournament_selection(self) -> List[Individual]:
        """Tournament selection"""
        parents = []
        
        for _ in range(self.config.population_size):
            # Select tournament participants
            tournament = random.sample(self.individuals, self.config.tournament_size)
            
            # Select winner
            winner = max(tournament, key=lambda x: x.fitness)
            parents.append(winner.copy())
        
        return parents
    
    def _rank_selection(self) -> List[Individual]:
        """Rank selection"""
        # Sort individuals by fitness
        sorted_individuals = sorted(self.individuals, key=lambda x: x.fitness, reverse=True)
        
        # Assign ranks
        ranks = list(range(1, len(sorted_individuals) + 1))
        
        # Calculate selection probabilities
        total_rank = sum(ranks)
        probabilities = [rank / total_rank for rank in ranks]
        
        # Select parents
        parents = []
        for _ in range(self.config.population_size):
            r = random.uniform(0, 1)
            cumulative = 0
            
            for individual, prob in zip(sorted_individuals, probabilities):
                cumulative += prob
                if cumulative >= r:
                    parents.append(individual.copy())
                    break
        
        return parents
    
    def _elitist_selection(self) -> List[Individual]:
        """Elitist selection"""
        # Keep elite individuals
        elite = self.individuals[:self.config.elite_size]
        
        # Select remaining parents using tournament selection
        remaining_parents = self._tournament_selection()
        
        # Combine elite and selected parents
        parents = elite + remaining_parents[:self.config.population_size - self.config.elite_size]
        
        return parents
    
    def _stochastic_universal_selection(self) -> List[Individual]:
        """Stochastic universal selection"""
        # Calculate fitness weights
        fitness_values = [ind.fitness for ind in self.individuals]
        min_fitness = min(fitness_values)
        
        # Shift fitness values to be positive
        shifted_fitness = [f - min_fitness + 1e-8 for f in fitness_values]
        total_fitness = sum(shifted_fitness)
        
        # Calculate selection interval
        interval = total_fitness / self.config.population_size
        
        # Select parents
        parents = []
        start = random.uniform(0, interval)
        
        for i in range(self.config.population_size):
            r = start + i * interval
            cumulative = 0
            
            for individual, fitness in zip(self.individuals, shifted_fitness):
                cumulative += fitness
                if cumulative >= r:
                    parents.append(individual.copy())
                    break
        
        return parents
    
    def _truncation_selection(self) -> List[Individual]:
        """Truncation selection"""
        # Select top individuals
        top_individuals = self.individuals[:self.config.population_size // 2]
        
        # Duplicate top individuals
        parents = []
        for individual in top_individuals:
            parents.append(individual.copy())
            parents.append(individual.copy())
        
        return parents[:self.config.population_size]
    
    def crossover(self, parents: List[Individual], bounds: List[Tuple[float, float]] = None) -> List[Individual]:
        """Perform crossover to create offspring"""
        logger.info(f"🧬 Performing crossover using {self.config.crossover_method.value}")
        
        offspring = []
        
        for i in range(0, len(parents), 2):
            if i + 1 < len(parents):
                parent1 = parents[i]
                parent2 = parents[i + 1]
                
                if random.random() < self.config.crossover_rate:
                    if self.config.crossover_method == CrossoverMethod.SINGLE_POINT:
                        child1, child2 = self._single_point_crossover(parent1, parent2)
                    elif self.config.crossover_method == CrossoverMethod.TWO_POINT:
                        child1, child2 = self._two_point_crossover(parent1, parent2)
                    elif self.config.crossover_method == CrossoverMethod.UNIFORM:
                        child1, child2 = self._uniform_crossover(parent1, parent2)
                    elif self.config.crossover_method == CrossoverMethod.ARITHMETIC:
                        child1, child2 = self._arithmetic_crossover(parent1, parent2)
                    elif self.config.crossover_method == CrossoverMethod.BLEND:
                        child1, child2 = self._blend_crossover(parent1, parent2)
                    elif self.config.crossover_method == CrossoverMethod.SIMULATED_BINARY:
                        child1, child2 = self._simulated_binary_crossover(parent1, parent2)
                    else:
                        child1, child2 = self._single_point_crossover(parent1, parent2)
                    
                    offspring.extend([child1, child2])
                else:
                    offspring.extend([parent1.copy(), parent2.copy()])
            else:
                offspring.append(parents[i].copy())
        
        return offspring
    
    def _single_point_crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Single point crossover"""
        crossover_point = random.randint(1, len(parent1.genes) - 1)
        
        child1_genes = np.concatenate([parent1.genes[:crossover_point], parent2.genes[crossover_point:]])
        child2_genes = np.concatenate([parent2.genes[:crossover_point], parent1.genes[crossover_point:]])
        
        child1 = Individual(child1_genes)
        child2 = Individual(child2_genes)
        
        return child1, child2
    
    def _two_point_crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Two point crossover"""
        point1 = random.randint(1, len(parent1.genes) - 2)
        point2 = random.randint(point1 + 1, len(parent1.genes) - 1)
        
        child1_genes = np.concatenate([
            parent1.genes[:point1],
            parent2.genes[point1:point2],
            parent1.genes[point2:]
        ])
        child2_genes = np.concatenate([
            parent2.genes[:point1],
            parent1.genes[point1:point2],
            parent2.genes[point2:]
        ])
        
        child1 = Individual(child1_genes)
        child2 = Individual(child2_genes)
        
        return child1, child2
    
    def _uniform_crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Uniform crossover"""
        child1_genes = np.zeros_like(parent1.genes)
        child2_genes = np.zeros_like(parent2.genes)
        
        for i in range(len(parent1.genes)):
            if random.random() < 0.5:
                child1_genes[i] = parent1.genes[i]
                child2_genes[i] = parent2.genes[i]
            else:
                child1_genes[i] = parent2.genes[i]
                child2_genes[i] = parent1.genes[i]
        
        child1 = Individual(child1_genes)
        child2 = Individual(child2_genes)
        
        return child1, child2
    
    def _arithmetic_crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Arithmetic crossover"""
        alpha = random.random()
        
        child1_genes = alpha * parent1.genes + (1 - alpha) * parent2.genes
        child2_genes = (1 - alpha) * parent1.genes + alpha * parent2.genes
        
        child1 = Individual(child1_genes)
        child2 = Individual(child2_genes)
        
        return child1, child2
    
    def _blend_crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Blend crossover (BLX-α)"""
        alpha = 0.5
        
        child1_genes = np.zeros_like(parent1.genes)
        child2_genes = np.zeros_like(parent2.genes)
        
        for i in range(len(parent1.genes)):
            d = abs(parent1.genes[i] - parent2.genes[i])
            low = min(parent1.genes[i], parent2.genes[i]) - alpha * d
            high = max(parent1.genes[i], parent2.genes[i]) + alpha * d
            
            child1_genes[i] = random.uniform(low, high)
            child2_genes[i] = random.uniform(low, high)
        
        child1 = Individual(child1_genes)
        child2 = Individual(child2_genes)
        
        return child1, child2
    
    def _simulated_binary_crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Simulated binary crossover (SBX)"""
        eta = 20  # Distribution index
        
        child1_genes = np.zeros_like(parent1.genes)
        child2_genes = np.zeros_like(parent2.genes)
        
        for i in range(len(parent1.genes)):
            if random.random() < 0.5:
                if abs(parent1.genes[i] - parent2.genes[i]) > 1e-14:
                    if parent1.genes[i] < parent2.genes[i]:
                        y1, y2 = parent1.genes[i], parent2.genes[i]
                    else:
                        y1, y2 = parent2.genes[i], parent1.genes[i]
                    
                    beta = 1.0 + (2.0 * (y1 - 0) / (y2 - y1))
                    alpha = 2.0 - beta**(-eta - 1)
                    
                    if random.random() <= (1.0 / alpha):
                        beta_q = (alpha * random.random())**(1.0 / (eta + 1))
                    else:
                        beta_q = (1.0 / (2.0 - alpha * random.random()))**(1.0 / (eta + 1))
                    
                    c1 = 0.5 * ((y1 + y2) - beta_q * (y2 - y1))
                    c2 = 0.5 * ((y1 + y2) + beta_q * (y2 - y1))
                    
                    child1_genes[i] = c1
                    child2_genes[i] = c2
                else:
                    child1_genes[i] = parent1.genes[i]
                    child2_genes[i] = parent2.genes[i]
            else:
                child1_genes[i] = parent1.genes[i]
                child2_genes[i] = parent2.genes[i]
        
        child1 = Individual(child1_genes)
        child2 = Individual(child2_genes)
        
        return child1, child2
    
    def mutate_offspring(self, offspring: List[Individual], bounds: List[Tuple[float, float]] = None):
        """Mutate offspring"""
        logger.info(f"🧬 Mutating offspring using {self.config.mutation_method.value}")
        
        for individual in offspring:
            individual.mutate(self.config.mutation_method, self.config.mutation_rate, 
                           self.config.mutation_strength, bounds)
    
    def replace_population(self, offspring: List[Individual]):
        """Replace population with offspring"""
        logger.info("🔄 Replacing population with offspring")
        
        # Keep elite individuals
        if self.config.elite_size > 0:
            elite = self.individuals[:self.config.elite_size]
            self.individuals = elite + offspring[:self.config.population_size - self.config.elite_size]
        else:
            self.individuals = offspring[:self.config.population_size]
        
        # Increment generation
        self.generation += 1
        
        # Increment age of all individuals
        for individual in self.individuals:
            individual.age += 1
    
    def calculate_diversity(self) -> float:
        """Calculate population diversity"""
        if len(self.individuals) < 2:
            return 0.0
        
        # Calculate pairwise distances
        distances = []
        for i in range(len(self.individuals)):
            for j in range(i + 1, len(self.individuals)):
                distance = np.linalg.norm(self.individuals[i].genes - self.individuals[j].genes)
                distances.append(distance)
        
        # Return average distance
        diversity = np.mean(distances)
        self.diversity_history.append(diversity)
        
        return diversity
    
    def check_convergence(self) -> bool:
        """Check if population has converged"""
        if len(self.best_fitness_history) < 10:
            return False
        
        # Check if fitness improvement is below threshold
        recent_improvement = abs(self.best_fitness_history[-1] - self.best_fitness_history[-10])
        if recent_improvement < self.config.convergence_threshold:
            return True
        
        # Check if diversity is too low
        if len(self.diversity_history) > 0:
            current_diversity = self.diversity_history[-1]
            if current_diversity < 1e-6:
                return True
        
        return False
    
    def check_stagnation(self) -> bool:
        """Check if population has stagnated"""
        if len(self.best_fitness_history) < self.config.stagnation_limit:
            return False
        
        # Check if best fitness hasn't improved for stagnation_limit generations
        best_fitness = self.best_fitness_history[-1]
        for i in range(len(self.best_fitness_history) - self.config.stagnation_limit, len(self.best_fitness_history)):
            if self.best_fitness_history[i] > best_fitness:
                return False
        
        return True

class EvolutionaryOptimizer:
    """Main evolutionary optimizer"""
    
    def __init__(self, config: EvolutionaryConfig):
        self.config = config
        self.population = Population(config)
        self.optimization_history = []
        logger.info("✅ Evolutionary Optimizer initialized")
    
    def optimize(self, fitness_function: Callable, gene_length: int, 
                bounds: List[Tuple[float, float]] = None) -> Dict[str, Any]:
        """Optimize using evolutionary algorithm"""
        logger.info(f"🚀 Optimizing using {self.config.evolutionary_algorithm.value}")
        
        optimization_results = {
            'start_time': time.time(),
            'config': self.config,
            'generations': []
        }
        
        # Initialize population
        self.population.initialize(gene_length, bounds)
        
        # Evaluate initial fitness
        self.population.evaluate_fitness(fitness_function)
        
        # Evolution loop
        for generation in range(self.config.max_generations):
            logger.info(f"🔄 Generation {generation + 1}/{self.config.max_generations}")
            
            # Select parents
            parents = self.population.select_parents()
            
            # Create offspring through crossover
            offspring = self.population.crossover(parents, bounds)
            
            # Mutate offspring
            self.population.mutate_offspring(offspring, bounds)
            
            # Evaluate offspring fitness
            for individual in offspring:
                individual.fitness = fitness_function(individual.genes)
            
            # Replace population
            self.population.replace_population(offspring)
            
            # Calculate diversity
            diversity = self.population.calculate_diversity()
            
            # Store generation results
            generation_result = {
                'generation': generation,
                'best_fitness': self.population.best_fitness_history[-1],
                'average_fitness': self.population.average_fitness_history[-1],
                'diversity': diversity,
                'best_individual': self.population.individuals[0].genes.copy()
            }
            
            optimization_results['generations'].append(generation_result)
            
            if generation % 10 == 0:
                logger.info(f"   Generation {generation}: Best = {generation_result['best_fitness']:.4f}, "
                          f"Avg = {generation_result['average_fitness']:.4f}, Diversity = {diversity:.4f}")
            
            # Check convergence
            if self.population.check_convergence():
                logger.info("✅ Population converged")
                break
            
            # Check stagnation
            if self.population.check_stagnation():
                logger.info("⚠️ Population stagnated")
                break
        
        # Final evaluation
        optimization_results['end_time'] = time.time()
        optimization_results['total_duration'] = optimization_results['end_time'] - optimization_results['start_time']
        optimization_results['best_solution'] = self.population.individuals[0].genes.copy()
        optimization_results['best_fitness'] = self.population.individuals[0].fitness
        optimization_results['final_generation'] = self.population.generation
        
        # Store results
        self.optimization_history.append(optimization_results)
        
        logger.info("✅ Evolutionary optimization completed")
        return optimization_results
    
    def generate_optimization_report(self, results: Dict[str, Any]) -> str:
        """Generate optimization report"""
        report = []
        report.append("=" * 50)
        report.append("EVOLUTIONARY COMPUTING REPORT")
        report.append("=" * 50)
        
        # Configuration
        report.append("\nEVOLUTIONARY COMPUTING CONFIGURATION:")
        report.append("-" * 35)
        report.append(f"Evolutionary Algorithm: {self.config.evolutionary_algorithm.value}")
        report.append(f"Selection Method: {self.config.selection_method.value}")
        report.append(f"Crossover Method: {self.config.crossover_method.value}")
        report.append(f"Mutation Method: {self.config.mutation_method.value}")
        report.append(f"Population Size: {self.config.population_size}")
        report.append(f"Elite Size: {self.config.elite_size}")
        report.append(f"Tournament Size: {self.config.tournament_size}")
        report.append(f"Crossover Rate: {self.config.crossover_rate}")
        report.append(f"Mutation Rate: {self.config.mutation_rate}")
        report.append(f"Mutation Strength: {self.config.mutation_strength}")
        report.append(f"Maximum Generations: {self.config.max_generations}")
        report.append(f"Convergence Threshold: {self.config.convergence_threshold}")
        report.append(f"Stagnation Limit: {self.config.stagnation_limit}")
        report.append(f"Multi-Objective: {'Enabled' if self.config.enable_multi_objective else 'Disabled'}")
        report.append(f"Number of Objectives: {self.config.n_objectives}")
        report.append(f"Pareto Front Size: {self.config.pareto_front_size}")
        report.append(f"Adaptive Parameters: {'Enabled' if self.config.enable_adaptive_parameters else 'Disabled'}")
        report.append(f"Diversity Maintenance: {'Enabled' if self.config.enable_diversity_maintenance else 'Disabled'}")
        report.append(f"Local Search: {'Enabled' if self.config.enable_local_search else 'Disabled'}")
        report.append(f"Hybrid Evolution: {'Enabled' if self.config.enable_hybrid_evolution else 'Disabled'}")
        
        # Results
        report.append("\nEVOLUTIONARY COMPUTING RESULTS:")
        report.append("-" * 32)
        report.append(f"Total Duration: {results.get('total_duration', 0):.2f} seconds")
        report.append(f"Start Time: {results.get('start_time', 'Unknown')}")
        report.append(f"End Time: {results.get('end_time', 'Unknown')}")
        report.append(f"Final Generation: {results.get('final_generation', 0)}")
        report.append(f"Best Fitness: {results.get('best_fitness', 0):.4f}")
        report.append(f"Best Solution: {results.get('best_solution', 'Unknown')}")
        
        # Generation results
        if 'generations' in results:
            report.append(f"\nNumber of Generations: {len(results['generations'])}")
            
            if results['generations']:
                final_generation = results['generations'][-1]
                report.append(f"Final Best Fitness: {final_generation.get('best_fitness', 0):.4f}")
                report.append(f"Final Average Fitness: {final_generation.get('average_fitness', 0):.4f}")
                report.append(f"Final Diversity: {final_generation.get('diversity', 0):.4f}")
        
        return "\n".join(report)
    
    def visualize_optimization_results(self, save_path: str = None):
        """Visualize optimization results"""
        if not self.optimization_history:
            logger.warning("No optimization history to visualize")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Plot 1: Optimization duration over time
        durations = [r.get('total_duration', 0) for r in self.optimization_history]
        axes[0, 0].plot(durations, 'b-', linewidth=2)
        axes[0, 0].set_xlabel('Optimization Run')
        axes[0, 0].set_ylabel('Duration (seconds)')
        axes[0, 0].set_title('Evolutionary Optimization Duration Over Time')
        axes[0, 0].grid(True)
        
        # Plot 2: Algorithm distribution
        algorithms = [self.config.evolutionary_algorithm.value]
        algorithm_counts = [1]
        
        axes[0, 1].pie(algorithm_counts, labels=algorithms, autopct='%1.1f%%')
        axes[0, 1].set_title('Evolutionary Algorithm Distribution')
        
        # Plot 3: Selection method distribution
        selection_methods = [self.config.selection_method.value]
        method_counts = [1]
        
        axes[1, 0].pie(method_counts, labels=selection_methods, autopct='%1.1f%%')
        axes[1, 0].set_title('Selection Method Distribution')
        
        # Plot 4: Evolutionary configuration
        config_values = [
            self.config.population_size,
            self.config.elite_size,
            self.config.tournament_size,
            self.config.max_generations
        ]
        config_labels = ['Population Size', 'Elite Size', 'Tournament Size', 'Max Generations']
        
        axes[1, 1].bar(config_labels, config_values, color=['blue', 'green', 'orange', 'red'])
        axes[1, 1].set_ylabel('Value')
        axes[1, 1].set_title('Evolutionary Configuration')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        
        plt.close()

# Factory functions
def create_evolutionary_config(**kwargs) -> EvolutionaryConfig:
    """Create evolutionary configuration"""
    return EvolutionaryConfig(**kwargs)

def create_individual(genes: np.ndarray, fitness: float = None) -> Individual:
    """Create individual"""
    return Individual(genes, fitness)

def create_population(config: EvolutionaryConfig) -> Population:
    """Create population"""
    return Population(config)

def create_evolutionary_optimizer(config: EvolutionaryConfig) -> EvolutionaryOptimizer:
    """Create evolutionary optimizer"""
    return EvolutionaryOptimizer(config)

# Example usage
def example_evolutionary_computing():
    """Example of evolutionary computing system"""
    # Create configuration
    config = create_evolutionary_config(
        evolutionary_algorithm=EvolutionaryAlgorithm.GENETIC_ALGORITHM,
        selection_method=SelectionMethod.TOURNAMENT,
        crossover_method=CrossoverMethod.SINGLE_POINT,
        mutation_method=MutationMethod.GAUSSIAN,
        population_size=100,
        elite_size=10,
        tournament_size=3,
        crossover_rate=0.8,
        mutation_rate=0.1,
        mutation_strength=0.1,
        max_generations=1000,
        convergence_threshold=1e-6,
        stagnation_limit=50,
        enable_multi_objective=False,
        n_objectives=2,
        pareto_front_size=20,
        enable_adaptive_parameters=True,
        enable_diversity_maintenance=True,
        enable_local_search=False,
        enable_hybrid_evolution=False
    )
    
    # Create evolutionary optimizer
    evolutionary_optimizer = create_evolutionary_optimizer(config)
    
    # Define fitness function
    def fitness_function(genes):
        # Simulate fitness function (e.g., neural network hyperparameter optimization)
        return -np.sum(genes**2) + np.random.normal(0, 0.1)
    
    # Define bounds
    bounds = [(-5, 5), (-5, 5), (-5, 5)]
    gene_length = len(bounds)
    
    # Optimize
    optimization_results = evolutionary_optimizer.optimize(fitness_function, gene_length, bounds)
    
    # Generate report
    optimization_report = evolutionary_optimizer.generate_optimization_report(optimization_results)
    
    print(f"✅ Evolutionary Computing Example Complete!")
    print(f"🚀 Evolutionary Computing Statistics:")
    print(f"   Evolutionary Algorithm: {config.evolutionary_algorithm.value}")
    print(f"   Selection Method: {config.selection_method.value}")
    print(f"   Crossover Method: {config.crossover_method.value}")
    print(f"   Mutation Method: {config.mutation_method.value}")
    print(f"   Population Size: {config.population_size}")
    print(f"   Elite Size: {config.elite_size}")
    print(f"   Tournament Size: {config.tournament_size}")
    print(f"   Crossover Rate: {config.crossover_rate}")
    print(f"   Mutation Rate: {config.mutation_rate}")
    print(f"   Mutation Strength: {config.mutation_strength}")
    print(f"   Maximum Generations: {config.max_generations}")
    print(f"   Convergence Threshold: {config.convergence_threshold}")
    print(f"   Stagnation Limit: {config.stagnation_limit}")
    print(f"   Multi-Objective: {'Enabled' if config.enable_multi_objective else 'Disabled'}")
    print(f"   Number of Objectives: {config.n_objectives}")
    print(f"   Pareto Front Size: {config.pareto_front_size}")
    print(f"   Adaptive Parameters: {'Enabled' if config.enable_adaptive_parameters else 'Disabled'}")
    print(f"   Diversity Maintenance: {'Enabled' if config.enable_diversity_maintenance else 'Disabled'}")
    print(f"   Local Search: {'Enabled' if config.enable_local_search else 'Disabled'}")
    print(f"   Hybrid Evolution: {'Enabled' if config.enable_hybrid_evolution else 'Disabled'}")
    
    print(f"\n📊 Evolutionary Computing Results:")
    print(f"   Optimization History Length: {len(evolutionary_optimizer.optimization_history)}")
    print(f"   Total Duration: {optimization_results.get('total_duration', 0):.2f} seconds")
    print(f"   Final Generation: {optimization_results.get('final_generation', 0)}")
    print(f"   Best Fitness: {optimization_results.get('best_fitness', 0):.4f}")
    print(f"   Best Solution: {optimization_results.get('best_solution', 'Unknown')}")
    
    # Show generation results summary
    if 'generations' in optimization_results:
        print(f"   Number of Generations: {len(optimization_results['generations'])}")
    
    print(f"\n📋 Evolutionary Computing Report:")
    print(optimization_report)
    
    return evolutionary_optimizer

# Export utilities
__all__ = [
    'SelectionMethod',
    'CrossoverMethod',
    'MutationMethod',
    'EvolutionaryAlgorithm',
    'EvolutionaryConfig',
    'Individual',
    'Population',
    'EvolutionaryOptimizer',
    'create_evolutionary_config',
    'create_individual',
    'create_population',
    'create_evolutionary_optimizer',
    'example_evolutionary_computing'
]

if __name__ == "__main__":
    example_evolutionary_computing()
    print("✅ Evolutionary computing example completed successfully!")