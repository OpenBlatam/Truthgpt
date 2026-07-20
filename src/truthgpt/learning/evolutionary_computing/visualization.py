import matplotlib.pyplot as plt
import logging
from typing import Dict, Any, List
from .types import EvolutionaryConfig

logger = logging.getLogger(__name__)

def generate_optimization_report(config: EvolutionaryConfig, results: Dict[str, Any]) -> str:
    """Generate optimization report"""
    report = []
    report.append("=" * 50)
    report.append("EVOLUTIONARY COMPUTING REPORT")
    report.append("=" * 50)
    
    # Configuration
    report.append("\nEVOLUTIONARY COMPUTING CONFIGURATION:")
    report.append("-" * 35)
    report.append(f"Evolutionary Algorithm: {config.evolutionary_algorithm.value}")
    report.append(f"Selection Method: {config.selection_method.value}")
    report.append(f"Crossover Method: {config.crossover_method.value}")
    report.append(f"Mutation Method: {config.mutation_method.value}")
    report.append(f"Population Size: {config.population_size}")
    report.append(f"Elite Size: {config.elite_size}")
    report.append(f"Tournament Size: {config.tournament_size}")
    report.append(f"Crossover Rate: {config.crossover_rate}")
    report.append(f"Mutation Rate: {config.mutation_rate}")
    report.append(f"Mutation Strength: {config.mutation_strength}")
    report.append(f"Maximum Generations: {config.max_generations}")
    report.append(f"Convergence Threshold: {config.convergence_threshold}")
    report.append(f"Stagnation Limit: {config.stagnation_limit}")
    report.append(f"Multi-Objective: {'Enabled' if config.enable_multi_objective else 'Disabled'}")
    report.append(f"Number of Objectives: {config.n_objectives}")
    report.append(f"Pareto Front Size: {config.pareto_front_size}")
    report.append(f"Adaptive Parameters: {'Enabled' if config.enable_adaptive_parameters else 'Disabled'}")
    report.append(f"Diversity Maintenance: {'Enabled' if config.enable_diversity_maintenance else 'Disabled'}")
    report.append(f"Local Search: {'Enabled' if config.enable_local_search else 'Disabled'}")
    report.append(f"Hybrid Evolution: {'Enabled' if config.enable_hybrid_evolution else 'Disabled'}")
    
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

def visualize_optimization_results(optimization_history: List[Dict[str, Any]], config: EvolutionaryConfig, save_path: str = None):
    """Visualize optimization results"""
    if not optimization_history:
        logger.warning("No optimization history to visualize")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot 1: Optimization duration over time
    durations = [r.get('total_duration', 0) for r in optimization_history]
    axes[0, 0].plot(durations, 'b-', linewidth=2)
    axes[0, 0].set_xlabel('Optimization Run')
    axes[0, 0].set_ylabel('Duration (seconds)')
    axes[0, 0].set_title('Evolutionary Optimization Duration Over Time')
    axes[0, 0].grid(True)
    
    # Plot 2: Algorithm distribution
    algorithms = [config.evolutionary_algorithm.value]
    algorithm_counts = [1]
    
    axes[0, 1].pie(algorithm_counts, labels=algorithms, autopct='%1.1f%%')
    axes[0, 1].set_title('Evolutionary Algorithm Distribution')
    
    # Plot 3: Selection method distribution
    selection_methods = [config.selection_method.value]
    method_counts = [1]
    
    axes[1, 0].pie(method_counts, labels=selection_methods, autopct='%1.1f%%')
    axes[1, 0].set_title('Selection Method Distribution')
    
    # Plot 4: Evolutionary configuration
    config_values = [
        config.population_size,
        config.elite_size,
        config.tournament_size,
        config.max_generations
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
