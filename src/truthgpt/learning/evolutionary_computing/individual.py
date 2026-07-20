import numpy as np
import random
import logging
from typing import List, Tuple
from .types import MutationMethod
from .strategies.mutation import (
    gaussian_mutation,
    uniform_mutation,
    polynomial_mutation,
    non_uniform_mutation,
    boundary_mutation,
    creep_mutation
)

logger = logging.getLogger(__name__)

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
                gaussian_mutation(self, mutation_strength)
            elif mutation_method == MutationMethod.UNIFORM:
                uniform_mutation(self, mutation_strength, bounds)
            elif mutation_method == MutationMethod.POLYNOMIAL:
                polynomial_mutation(self, mutation_strength, bounds)
            elif mutation_method == MutationMethod.NON_UNIFORM:
                non_uniform_mutation(self, mutation_strength, bounds)
            elif mutation_method == MutationMethod.BOUNDARY:
                boundary_mutation(self, bounds)
            elif mutation_method == MutationMethod.CREEP:
                creep_mutation(self, mutation_strength)
            else:
                gaussian_mutation(self, mutation_strength)

def create_individual(genes: np.ndarray, fitness: float = None) -> Individual:
    """Create individual"""
    return Individual(genes, fitness)
