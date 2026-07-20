import random
import numpy as np
from typing import List, Tuple
from ..individual import Individual
from ..types import MutationMethod

def gaussian_mutation(individual: Individual, mutation_strength: float):
    """Gaussian mutation"""
    noise = np.random.normal(0, mutation_strength, individual.genes.shape)
    individual.genes += noise

def uniform_mutation(individual: Individual, mutation_strength: float, bounds: List[Tuple[float, float]]):
    """Uniform mutation"""
    for i in range(len(individual.genes)):
        if random.random() < 0.1:  # 10% chance per gene
            if bounds:
                low, high = bounds[i]
                individual.genes[i] = random.uniform(low, high)
            else:
                individual.genes[i] += random.uniform(-mutation_strength, mutation_strength)

def polynomial_mutation(individual: Individual, mutation_strength: float, bounds: List[Tuple[float, float]]):
    """Polynomial mutation"""
    for i in range(len(individual.genes)):
        if random.random() < 0.1:  # 10% chance per gene
            if bounds:
                low, high = bounds[i]
                delta = random.uniform(-1, 1)
                individual.genes[i] = low + (high - low) * (0.5 + delta * mutation_strength)

def non_uniform_mutation(individual: Individual, mutation_strength: float, bounds: List[Tuple[float, float]]):
    """Non-uniform mutation"""
    for i in range(len(individual.genes)):
        if random.random() < 0.1:  # 10% chance per gene
            if bounds:
                low, high = bounds[i]
                delta = random.uniform(-1, 1)
                individual.genes[i] = low + (high - low) * (0.5 + delta * mutation_strength)

def boundary_mutation(individual: Individual, bounds: List[Tuple[float, float]]):
    """Boundary mutation"""
    if bounds:
        for i in range(len(individual.genes)):
            if random.random() < 0.1:  # 10% chance per gene
                low, high = bounds[i]
                individual.genes[i] = random.choice([low, high])

def creep_mutation(individual: Individual, mutation_strength: float):
    """Creep mutation"""
    for i in range(len(individual.genes)):
        if random.random() < 0.1:  # 10% chance per gene
            individual.genes[i] += random.uniform(-mutation_strength, mutation_strength)
