import numpy as np
import random
import logging
from typing import List, Tuple, Callable, Dict
from .types import EvolutionaryConfig, SelectionMethod, CrossoverMethod
from .individual import Individual
from .strategies.selection import (
    roulette_wheel_selection,
    tournament_selection,
    rank_selection,
    elitist_selection,
    stochastic_universal_selection,
    truncation_selection
)
from .strategies.crossover import (
    single_point_crossover,
    two_point_crossover,
    uniform_crossover,
    arithmetic_crossover,
    blend_crossover,
    simulated_binary_crossover
)

logger = logging.getLogger(__name__)

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
            return roulette_wheel_selection(self.individuals, self.config.population_size)
        elif self.config.selection_method == SelectionMethod.TOURNAMENT:
            return tournament_selection(self.individuals, self.config.population_size, self.config.tournament_size)
        elif self.config.selection_method == SelectionMethod.RANK:
            return rank_selection(self.individuals, self.config.population_size)
        elif self.config.selection_method == SelectionMethod.ELITIST:
            return elitist_selection(self.individuals, self.config.population_size, 
                                   self.config.elite_size, self.config.tournament_size)
        elif self.config.selection_method == SelectionMethod.STOCHASTIC_UNIVERSAL:
            return stochastic_universal_selection(self.individuals, self.config.population_size)
        elif self.config.selection_method == SelectionMethod.TRUNCATION:
            return truncation_selection(self.individuals, self.config.population_size)
        else:
            return tournament_selection(self.individuals, self.config.population_size, self.config.tournament_size)
    
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
                        child1, child2 = single_point_crossover(parent1, parent2)
                    elif self.config.crossover_method == CrossoverMethod.TWO_POINT:
                        child1, child2 = two_point_crossover(parent1, parent2)
                    elif self.config.crossover_method == CrossoverMethod.UNIFORM:
                        child1, child2 = uniform_crossover(parent1, parent2)
                    elif self.config.crossover_method == CrossoverMethod.ARITHMETIC:
                        child1, child2 = arithmetic_crossover(parent1, parent2)
                    elif self.config.crossover_method == CrossoverMethod.BLEND:
                        child1, child2 = blend_crossover(parent1, parent2)
                    elif self.config.crossover_method == CrossoverMethod.SIMULATED_BINARY:
                        child1, child2 = simulated_binary_crossover(parent1, parent2)
                    else:
                        child1, child2 = single_point_crossover(parent1, parent2)
                    
                    offspring.extend([child1, child2])
                else:
                    offspring.extend([parent1.copy(), parent2.copy()])
            else:
                offspring.append(parents[i].copy())
        
        return offspring
    
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
        
        # Calculate pairwise distances (vectorized if possible, simple loop here)
        # For large populations, this O(N^2) might be slow. Optimization: check subset or stats.
        # Keeping original logic for now, but simplified if numpy allows.
        
        # Stack genes for vectorized calculation
        genes = np.stack([ind.genes for ind in self.individuals])
        
        # Pairwise distance matrix
        # Use simple mean of std dev as diversity proxy for speed? 
        # Original code used pairwise distances. Let's keep it but maybe optimize later.
        # Actually, let's stick to original implementation logic for fidelity.
        
        distances = []
        for i in range(len(self.individuals)):
            for j in range(i + 1, len(self.individuals)):
                distance = np.linalg.norm(self.individuals[i].genes - self.individuals[j].genes)
                distances.append(distance)
        
        diversity = np.mean(distances) if distances else 0.0
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

def create_population(config: EvolutionaryConfig) -> Population:
    """Create population"""
    return Population(config)
