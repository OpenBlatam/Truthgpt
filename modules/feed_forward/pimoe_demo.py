"""
PiMoE Token-Level Routing Demo
Demonstrates the capabilities of PiMoE-inspired token-level routing
"""

import torch
import torch.nn as nn
import time
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple, Any
import json
from dataclasses import dataclass

from .pimoe_router import (
    PiMoESystem, 
    ExpertType, 
    create_pimoe_system,
    RoutingDecision
)
from .enhanced_pimoe_integration import (
    EnhancedPiMoEIntegration,
    AdaptivePiMoE,
    create_enhanced_pimoe_integration
)

@dataclass
class DemoConfig:
    """Configuration for PiMoE demo."""
    hidden_size: int = 512
    num_experts: int = 8
    sequence_length: int = 128
    batch_size: int = 4
    num_iterations: int = 100
    enable_visualization: bool = True
    save_results: bool = True

class PiMoEDemo:
    """
    Comprehensive demo for PiMoE token-level routing capabilities.
    """
    
    def __init__(self, config: DemoConfig):
        self.config = config
        self.results = {}
        
        # Initialize PiMoE systems
        self._initialize_systems()
        
    def _initialize_systems(self):
        """Initialize different PiMoE system variants."""
        
        # Basic PiMoE system
        self.basic_pimoe = create_pimoe_system(
            hidden_size=self.config.hidden_size,
            num_experts=self.config.num_experts,
            expert_types=[
                ExpertType.REASONING,
                ExpertType.COMPUTATION,
                ExpertType.MATHEMATICAL,
                ExpertType.LOGICAL,
                ExpertType.LANGUAGE,
                ExpertType.CREATIVE,
                ExpertType.ANALYTICAL
            ]
        )
        
        # Enhanced PiMoE with optimizations
        self.enhanced_pimoe = create_enhanced_pimoe_integration(
            hidden_size=self.config.hidden_size,
            num_experts=self.config.num_experts,
            optimization_level="advanced",
            enable_adaptation=False,
            enable_quantization=True,
            enable_pruning=False
        )
        
        # Adaptive PiMoE with learning
        self.adaptive_pimoe = create_enhanced_pimoe_integration(
            hidden_size=self.config.hidden_size,
            num_experts=self.config.num_experts,
            optimization_level="expert",
            enable_adaptation=True,
            adaptation_rate=0.01,
            performance_threshold=0.8
        )
    
    def run_comprehensive_demo(self) -> Dict[str, Any]:
        """Run comprehensive demonstration of PiMoE capabilities."""
        
        print("🚀 Starting PiMoE Token-Level Routing Demo")
        print("=" * 60)
        
        # Generate test data
        test_data = self._generate_test_data()
        
        # Run performance benchmarks
        print("\n📊 Running Performance Benchmarks...")
        performance_results = self._run_performance_benchmarks(test_data)
        
        # Run routing analysis
        print("\n🎯 Analyzing Token-Level Routing...")
        routing_results = self._analyze_routing_behavior(test_data)
        
        # Run optimization comparison
        print("\n⚡ Comparing Optimization Strategies...")
        optimization_results = self._compare_optimization_strategies(test_data)
        
        # Run adaptation demo
        print("\n🧠 Demonstrating Adaptive Routing...")
        adaptation_results = self._demonstrate_adaptive_routing(test_data)
        
        # Compile results
        self.results = {
            'performance': performance_results,
            'routing_analysis': routing_results,
            'optimization_comparison': optimization_results,
            'adaptation_demo': adaptation_results,
            'config': self.config.__dict__
        }
        
        # Generate visualizations
        if self.config.enable_visualization:
            self._generate_visualizations()
        
        # Save results
        if self.config.save_results:
            self._save_results()
        
        print("\n✅ Demo completed successfully!")
        return self.results
    
    def _generate_test_data(self) -> Dict[str, torch.Tensor]:
        """Generate diverse test data for demonstration."""
        
        # Mathematical reasoning sequences
        math_sequences = torch.randn(
            self.config.batch_size, 
            self.config.sequence_length, 
            self.config.hidden_size
        ) * 0.5 + 1.0  # Bias towards positive values for math
        
        # Language processing sequences
        lang_sequences = torch.randn(
            self.config.batch_size, 
            self.config.sequence_length, 
            self.config.hidden_size
        ) * 0.3  # Lower variance for language
        
        # Creative sequences
        creative_sequences = torch.randn(
            self.config.batch_size, 
            self.config.sequence_length, 
            self.config.hidden_size
        ) * 0.8  # Higher variance for creativity
        
        # Logical reasoning sequences
        logical_sequences = torch.randn(
            self.config.batch_size, 
            self.config.sequence_length, 
            self.config.hidden_size
        ) * 0.4 + 0.2  # Moderate variance with slight bias
        
        return {
            'mathematical': math_sequences,
            'language': lang_sequences,
            'creative': creative_sequences,
            'logical': logical_sequences
        }
    
    def _run_performance_benchmarks(self, test_data: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        """Run performance benchmarks across different systems."""
        
        systems = {
            'Basic PiMoE': self.basic_pimoe,
            'Enhanced PiMoE': self.enhanced_pimoe,
            'Adaptive PiMoE': self.adaptive_pimoe
        }
        
        results = {}
        
        for system_name, system in systems.items():
            print(f"  Testing {system_name}...")
            
            system_results = {
                'latency_ms': [],
                'throughput_tokens_per_sec': [],
                'memory_usage_mb': [],
                'expert_utilization': [],
                'load_balance_score': []
            }
            
            for iteration in range(self.config.num_iterations):
                for data_type, data in test_data.items():
                    start_time = time.time()
                    
                    if system_name == 'Adaptive PiMoE':
                        output, metrics = system(data, return_adaptation_info=True)
                    else:
                        output, metrics = system(data, return_metrics=True)
                    
                    end_time = time.time()
                    
                    # Record metrics
                    system_results['latency_ms'].append(metrics['latency_ms'])
                    system_results['throughput_tokens_per_sec'].append(metrics['throughput_tokens_per_sec'])
                    system_results['memory_usage_mb'].append(metrics['memory_usage_mb'])
                    system_results['expert_utilization'].append(metrics['expert_utilization'])
                    system_results['load_balance_score'].append(metrics['load_balance_score'])
            
            # Calculate averages
            results[system_name] = {
                'avg_latency_ms': np.mean(system_results['latency_ms']),
                'avg_throughput': np.mean(system_results['throughput_tokens_per_sec']),
                'avg_memory_usage': np.mean(system_results['memory_usage_mb']),
                'avg_expert_utilization': np.mean(system_results['expert_utilization']),
                'avg_load_balance': np.mean(system_results['load_balance_score']),
                'std_latency_ms': np.std(system_results['latency_ms']),
                'std_throughput': np.std(system_results['throughput_tokens_per_sec'])
            }
        
        return results
    
    def _analyze_routing_behavior(self, test_data: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        """Analyze token-level routing behavior."""
        
        routing_analysis = {}
        
        for data_type, data in test_data.items():
            print(f"  Analyzing {data_type} sequences...")
            
            # Get routing decisions
            output, routing_info = self.basic_pimoe(data, return_routing_info=True)
            
            # Analyze expert selection patterns
            expert_selections = [decision.expert_id for decision in routing_info['routing_decisions']]
            expert_type_selections = [decision.expert_type for decision in routing_info['routing_decisions']]
            confidence_scores = [decision.confidence for decision in routing_info['routing_decisions']]
            
            # Calculate statistics
            unique_experts = len(set(expert_selections))
            expert_distribution = {i: expert_selections.count(i) for i in range(self.config.num_experts)}
            type_distribution = {et.value: expert_type_selections.count(et) for et in ExpertType}
            
            routing_analysis[data_type] = {
                'unique_experts_used': unique_experts,
                'expert_distribution': expert_distribution,
                'type_distribution': type_distribution,
                'avg_confidence': np.mean(confidence_scores),
                'confidence_std': np.std(confidence_scores),
                'routing_entropy': self._calculate_routing_entropy(expert_selections)
            }
        
        return routing_analysis
    
    def _calculate_routing_entropy(self, expert_selections: List[int]) -> float:
        """Calculate entropy of expert selection distribution."""
        from collections import Counter
        
        counts = Counter(expert_selections)
        total = len(expert_selections)
        
        entropy = 0.0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * np.log2(p)
        
        return entropy
    
    def _compare_optimization_strategies(self, test_data: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        """Compare different optimization strategies."""
        
        strategies = {
            'No Optimization': self.basic_pimoe,
            'Quantization': self.enhanced_pimoe,
            'Adaptive Learning': self.adaptive_pimoe
        }
        
        comparison_results = {}
        
        for strategy_name, system in strategies.items():
            print(f"  Testing {strategy_name}...")
            
            total_latency = 0
            total_throughput = 0
            total_memory = 0
            
            for data_type, data in test_data.items():
                start_time = time.time()
                
                if strategy_name == 'Adaptive Learning':
                    output, info = system(data, return_adaptation_info=True)
                else:
                    output, metrics = system(data, return_metrics=True)
                
                end_time = time.time()
                
                latency = (end_time - start_time) * 1000
                batch_size, seq_len, hidden_size = data.shape
                throughput = (batch_size * seq_len) / (latency / 1000)
                memory = (data.numel() + output.numel()) * 4 / (1024 * 1024)
                
                total_latency += latency
                total_throughput += throughput
                total_memory += memory
            
            comparison_results[strategy_name] = {
                'avg_latency_ms': total_latency / len(test_data),
                'avg_throughput': total_throughput / len(test_data),
                'avg_memory_mb': total_memory / len(test_data)
            }
        
        return comparison_results
    
    def _demonstrate_adaptive_routing(self, test_data: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        """Demonstrate adaptive routing capabilities."""
        
        print("  Running adaptive routing demonstration...")
        
        adaptation_history = []
        
        # Run multiple iterations to show adaptation
        for iteration in range(20):
            for data_type, data in test_data.items():
                output, info = self.adaptive_pimoe(data, return_adaptation_info=True)
                
                adaptation_info = info['adaptation_info']
                metrics = info['metrics']
                
                adaptation_history.append({
                    'iteration': iteration,
                    'data_type': data_type,
                    'performance_score': adaptation_info['performance_score'],
                    'adaptation_applied': adaptation_info['adaptation_applied'],
                    'expert_utilization': metrics['expert_utilization'],
                    'load_balance_score': metrics['load_balance_score']
                })
        
        # Analyze adaptation effectiveness
        performance_scores = [entry['performance_score'] for entry in adaptation_history]
        adaptation_applied_count = sum(1 for entry in adaptation_history if entry['adaptation_applied'])
        
        return {
            'adaptation_history': adaptation_history,
            'final_performance_score': performance_scores[-1],
            'initial_performance_score': performance_scores[0],
            'performance_improvement': performance_scores[-1] - performance_scores[0],
            'adaptations_applied': adaptation_applied_count,
            'adaptation_rate': adaptation_applied_count / len(adaptation_history)
        }
    
    def _generate_visualizations(self):
        """Generate visualization plots."""
        
        if not self.results:
            return
        
        # Create performance comparison plot
        self._plot_performance_comparison()
        
        # Create routing analysis plot
        self._plot_routing_analysis()
        
        # Create adaptation demonstration plot
        self._plot_adaptation_demonstration()
    
    def _plot_performance_comparison(self):
        """Plot performance comparison across systems."""
        
        performance_data = self.results['performance']
        
        systems = list(performance_data.keys())
        latencies = [performance_data[system]['avg_latency_ms'] for system in systems]
        throughputs = [performance_data[system]['avg_throughput'] for system in systems]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Latency comparison
        ax1.bar(systems, latencies, color=['blue', 'green', 'red'])
        ax1.set_title('Average Latency Comparison')
        ax1.set_ylabel('Latency (ms)')
        ax1.tick_params(axis='x', rotation=45)
        
        # Throughput comparison
        ax2.bar(systems, throughputs, color=['blue', 'green', 'red'])
        ax2.set_title('Average Throughput Comparison')
        ax2.set_ylabel('Throughput (tokens/sec)')
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('pimoe_performance_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_routing_analysis(self):
        """Plot routing analysis results."""
        
        routing_data = self.results['routing_analysis']
        
        data_types = list(routing_data.keys())
        expert_utilizations = [routing_data[dt]['unique_experts_used'] for dt in data_types]
        confidences = [routing_data[dt]['avg_confidence'] for dt in data_types]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Expert utilization
        ax1.bar(data_types, expert_utilizations, color=['purple', 'orange', 'cyan', 'pink'])
        ax1.set_title('Expert Utilization by Data Type')
        ax1.set_ylabel('Unique Experts Used')
        ax1.tick_params(axis='x', rotation=45)
        
        # Routing confidence
        ax2.bar(data_types, confidences, color=['purple', 'orange', 'cyan', 'pink'])
        ax2.set_title('Average Routing Confidence by Data Type')
        ax2.set_ylabel('Confidence Score')
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('pimoe_routing_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_adaptation_demonstration(self):
        """Plot adaptation demonstration results."""
        
        adaptation_data = self.results['adaptation_demo']
        history = adaptation_data['adaptation_history']
        
        iterations = [entry['iteration'] for entry in history]
        performance_scores = [entry['performance_score'] for entry in history]
        
        plt.figure(figsize=(12, 6))
        plt.plot(iterations, performance_scores, 'b-', linewidth=2, marker='o')
        plt.title('Adaptive Routing Performance Over Time')
        plt.xlabel('Iteration')
        plt.ylabel('Performance Score')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('pimoe_adaptation_demo.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _save_results(self):
        """Save results to file."""
        
        # Convert numpy arrays to lists for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, dict):
                return {key: convert_numpy(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            else:
                return obj
        
        # Save results
        results_to_save = convert_numpy(self.results)
        
        with open('pimoe_demo_results.json', 'w') as f:
            json.dump(results_to_save, f, indent=2)
        
        print(f"📁 Results saved to pimoe_demo_results.json")
        print(f"📊 Visualizations saved as PNG files")

def run_pimoe_demo():
    """Run the complete PiMoE demonstration."""
    
    # Configuration
    config = DemoConfig(
        hidden_size=512,
        num_experts=8,
        sequence_length=128,
        batch_size=4,
        num_iterations=50,
        enable_visualization=True,
        save_results=True
    )
    
    # Create and run demo
    demo = PiMoEDemo(config)
    results = demo.run_comprehensive_demo()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 DEMO SUMMARY")
    print("=" * 60)
    
    performance = results['performance']
    for system, metrics in performance.items():
        print(f"\n{system}:")
        print(f"  Latency: {metrics['avg_latency_ms']:.2f} ms")
        print(f"  Throughput: {metrics['avg_throughput']:.2f} tokens/sec")
        print(f"  Memory: {metrics['avg_memory_usage']:.2f} MB")
        print(f"  Expert Utilization: {metrics['avg_expert_utilization']:.2f}")
        print(f"  Load Balance: {metrics['avg_load_balance']:.2f}")
    
    adaptation = results['adaptation_demo']
    print(f"\n🧠 Adaptive Routing:")
    print(f"  Performance Improvement: {adaptation['performance_improvement']:.3f}")
    print(f"  Adaptations Applied: {adaptation['adaptations_applied']}")
    print(f"  Adaptation Rate: {adaptation['adaptation_rate']:.2f}")
    
    return results

if __name__ == "__main__":
    # Run the demo
    results = run_pimoe_demo()




