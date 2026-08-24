import time
import logging
import numpy as np
from typing import Dict, Any, List, Tuple, Callable, Optional, Union
from .types import EvolutionaryConfig
from .population import Population
from .individual import Individual
from ..interfaces import BaseLearner
from ..registry import LearningRegistry
from ..exceptions import EvolutionaryError

logger = logging.getLogger(__name__)

@LearningRegistry.register_learner("evolutionary", aliases=["evolutionary_computing", "EvolutionaryOptimizer"], paradigm="evolutionary")
class EvolutionaryOptimizer(BaseLearner):
    """Main evolutionary optimizer"""
    
    def __init__(self, config: Optional[Union[EvolutionaryConfig, Dict[str, Any]]] = None, **kwargs: Any):
        if config is None and kwargs:
            config = kwargs
        elif isinstance(config, dict) and kwargs:
            config = {**config, **kwargs}
        if config is None:
            from .types import create_evolutionary_config
            config = create_evolutionary_config()
        elif isinstance(config, dict):
            from .types import create_evolutionary_config
            config = create_evolutionary_config(**config)
        self.config = config
        self.population = Population(config)
        self.optimization_history = []
        logger.info("✅ Evolutionary Optimizer initialized")
    
    def fit(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Fit implementation delegating to optimize."""
        if len(args) >= 2:
            return self.optimize(args[0], args[1], args[2] if len(args) > 2 else None)
        elif "fitness_function" in kwargs and "gene_length" in kwargs:
            return self.optimize(kwargs["fitness_function"], kwargs["gene_length"], kwargs.get("bounds"))
        return self.optimize(lambda g: 0.0, 10, None)

    def evaluate(self, *args: Any, **kwargs: Any) -> Dict[str, float]:
        """Evaluate implementation returning best fitness."""
        if self.optimization_history:
            last = self.optimization_history[-1]
            return {"best_fitness": float(last.get("best_fitness", 0.0))}
        return {}
    
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
        # Moved logic to visualization module, but keeping alias here if desired, 
        # or we can import it. Ideally, separate concerns.
        # For refactor, let's delegate or remove.
        # The legacy code had it as method. We'll import it.
        from .visualization import generate_optimization_report
        return generate_optimization_report(self.config, results)
    
    def visualize_optimization_results(self, save_path: str = None):
        """Visualize optimization results"""
        from .visualization import visualize_optimization_results
        visualize_optimization_results(self.optimization_history, self.config, save_path)

def create_evolutionary_optimizer(
    config: Optional[Union[EvolutionaryConfig, Dict[str, Any]]] = None,
    **kwargs: Any
) -> EvolutionaryOptimizer:
    """Create evolutionary optimizer"""
    return EvolutionaryOptimizer(config=config, **kwargs)

