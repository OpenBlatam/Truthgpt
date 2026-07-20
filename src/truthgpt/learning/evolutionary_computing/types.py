from enum import Enum
from dataclasses import dataclass, field
import logging

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

@dataclass
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

def create_evolutionary_config(**kwargs) -> EvolutionaryConfig:
    """Create evolutionary configuration"""
    return EvolutionaryConfig(**kwargs)
