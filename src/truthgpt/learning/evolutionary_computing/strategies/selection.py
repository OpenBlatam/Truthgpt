import random
import numpy as np
from typing import List
from ..individual import Individual
from ..types import SelectionMethod

def roulette_wheel_selection(population: List[Individual], population_size: int) -> List[Individual]:
    """Roulette wheel selection"""
    # Calculate fitness weights
    fitness_values = [ind.fitness for ind in population]
    min_fitness = min(fitness_values)
    
    # Shift fitness values to be positive
    shifted_fitness = [f - min_fitness + 1e-8 for f in fitness_values]
    total_fitness = sum(shifted_fitness)
    
    # Select parents
    parents = []
    for _ in range(population_size):
        r = random.uniform(0, total_fitness)
        cumulative = 0
        
        for individual, fitness in zip(population, shifted_fitness):
            cumulative += fitness
            if cumulative >= r:
                parents.append(individual.copy())
                break
    
    return parents

def tournament_selection(population: List[Individual], population_size: int, tournament_size: int) -> List[Individual]:
    """Tournament selection"""
    parents = []
    
    for _ in range(population_size):
        # Select tournament participants
        tournament = random.sample(population, tournament_size)
        
        # Select winner
        winner = max(tournament, key=lambda x: x.fitness)
        parents.append(winner.copy())
    
    return parents

def rank_selection(population: List[Individual], population_size: int) -> List[Individual]:
    """Rank selection"""
    # Sort individuals by fitness
    sorted_individuals = sorted(population, key=lambda x: x.fitness, reverse=True)
    
    # Assign ranks
    ranks = list(range(1, len(sorted_individuals) + 1))
    
    # Calculate selection probabilities
    total_rank = sum(ranks)
    probabilities = [rank / total_rank for rank in ranks]
    
    # Select parents
    parents = []
    for _ in range(population_size):
        r = random.uniform(0, 1)
        cumulative = 0
        
        for individual, prob in zip(sorted_individuals, probabilities):
            cumulative += prob
            if cumulative >= r:
                parents.append(individual.copy())
                break
    
    return parents

def elitist_selection(population: List[Individual], population_size: int, elite_size: int, tournament_size: int) -> List[Individual]:
    """Elitist selection"""
    # Keep elite individuals
    sorted_population = sorted(population, key=lambda x: x.fitness, reverse=True)
    elite = sorted_population[:elite_size]
    
    # Select remaining parents using tournament selection
    if population_size > elite_size:
        remaining_parents = tournament_selection(population, population_size, tournament_size)
        parents = elite + remaining_parents[:population_size - elite_size]
    else:
        parents = elite[:population_size]
    
    return parents

def stochastic_universal_selection(population: List[Individual], population_size: int) -> List[Individual]:
    """Stochastic universal selection"""
    # Calculate fitness weights
    fitness_values = [ind.fitness for ind in population]
    min_fitness = min(fitness_values)
    
    # Shift fitness values to be positive
    shifted_fitness = [f - min_fitness + 1e-8 for f in fitness_values]
    total_fitness = sum(shifted_fitness)
    
    # Calculate selection interval
    interval = total_fitness / population_size
    
    # Select parents
    parents = []
    start = random.uniform(0, interval)
    
    for i in range(population_size):
        r = start + i * interval
        cumulative = 0
        
        for individual, fitness in zip(population, shifted_fitness):
            cumulative += fitness
            if cumulative >= r:
                parents.append(individual.copy())
                break
    
    return parents

def truncation_selection(population: List[Individual], population_size: int) -> List[Individual]:
    """Truncation selection"""
    # Sort and select top individuals
    sorted_individuals = sorted(population, key=lambda x: x.fitness, reverse=True)
    top_individuals = sorted_individuals[:population_size // 2]
    
    # Duplicate top individuals
    parents = []
    for individual in top_individuals:
        parents.append(individual.copy())
        if len(parents) < population_size:
            parents.append(individual.copy())
    
    return parents[:population_size]
