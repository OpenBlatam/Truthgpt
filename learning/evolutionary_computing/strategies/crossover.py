import random
import numpy as np
from typing import Tuple
from ..individual import Individual
from ..types import CrossoverMethod

def single_point_crossover(parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
    """Single point crossover"""
    crossover_point = random.randint(1, len(parent1.genes) - 1)
    
    child1_genes = np.concatenate([parent1.genes[:crossover_point], parent2.genes[crossover_point:]])
    child2_genes = np.concatenate([parent2.genes[:crossover_point], parent1.genes[crossover_point:]])
    
    child1 = Individual(child1_genes)
    child2 = Individual(child2_genes)
    
    return child1, child2

def two_point_crossover(parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
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

def uniform_crossover(parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
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

def arithmetic_crossover(parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
    """Arithmetic crossover"""
    alpha = random.random()
    
    child1_genes = alpha * parent1.genes + (1 - alpha) * parent2.genes
    child2_genes = (1 - alpha) * parent1.genes + alpha * parent2.genes
    
    child1 = Individual(child1_genes)
    child2 = Individual(child2_genes)
    
    return child1, child2

def blend_crossover(parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
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

def simulated_binary_crossover(parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
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
