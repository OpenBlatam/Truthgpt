"""
PiMoE Integration Example for TruthGPT Optimization Core
Demonstrates how to integrate PiMoE token-level routing with existing systems
"""

import torch
import torch.nn as nn
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import json

# Import PiMoE components
from .pimoe_router import (
    PiMoESystem,
    TokenLevelRouter,
    ExpertType,
    RoutingDecision,
    create_pimoe_system
)
from .enhanced_pimoe_integration import (
    EnhancedPiMoEIntegration,
    AdaptivePiMoE,
    create_enhanced_pimoe_integration
)
from .pimoe_demo import PiMoEDemo, DemoConfig

class TruthGPTPiMoEIntegration:
    """
    Integration example showing how to use PiMoE with TruthGPT optimization core.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.hidden_size = config.get('hidden_size', 512)
        self.num_experts = config.get('num_experts', 8)
        self.optimization_level = config.get('optimization_level', 'advanced')
        
        # Initialize PiMoE system
        self.pimoe_system = self._create_pimoe_system()
        
        # Performance tracking
        self.performance_history = []
        
    def _create_pimoe_system(self) -> PiMoESystem:
        """Create PiMoE system based on configuration."""
        
        expert_types = [
            ExpertType.REASONING,
            ExpertType.COMPUTATION,
            ExpertType.MATHEMATICAL,
            ExpertType.LOGICAL,
            ExpertType.LANGUAGE,
            ExpertType.CREATIVE,
            ExpertType.ANALYTICAL
        ]
        
        return create_pimoe_system(
            hidden_size=self.hidden_size,
            num_experts=self.num_experts,
            expert_types=expert_types
        )
    
    def process_sequence(
        self, 
        input_sequence: torch.Tensor,
        return_analysis: bool = False
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, Dict[str, Any]]]:
        """
        Process input sequence through PiMoE system.
        
        Args:
            input_sequence: Input tensor [batch_size, seq_len, hidden_size]
            return_analysis: Whether to return routing analysis
            
        Returns:
            Processed output and optionally routing analysis
        """
        start_time = time.time()
        
        if return_analysis:
            output, routing_info = self.pimoe_system(
                input_sequence, 
                return_routing_info=True
            )
            
            # Analyze routing decisions
            analysis = self._analyze_routing_decisions(routing_info)
            
            # Track performance
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            self.performance_history.append({
                'latency_ms': latency_ms,
                'routing_analysis': analysis,
                'timestamp': time.time()
            })
            
            return output, analysis
        else:
            output = self.pimoe_system(input_sequence)
            
            # Track basic performance
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            self.performance_history.append({
                'latency_ms': latency_ms,
                'timestamp': time.time()
            })
            
            return output
    
    def _analyze_routing_decisions(self, routing_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze routing decisions for insights."""
        
        routing_decisions = routing_info['routing_decisions']
        expert_probs = routing_info['expert_probs']
        
        # Expert usage analysis
        expert_usage = {}
        expert_type_usage = {}
        confidence_scores = []
        
        for decision in routing_decisions:
            expert_id = decision.expert_id
            expert_type = decision.expert_type
            confidence = decision.confidence
            
            # Track expert usage
            expert_usage[expert_id] = expert_usage.get(expert_id, 0) + 1
            expert_type_usage[expert_type.value] = expert_type_usage.get(expert_type.value, 0) + 1
            confidence_scores.append(confidence)
        
        # Calculate statistics
        total_tokens = len(routing_decisions)
        unique_experts = len(expert_usage)
        avg_confidence = np.mean(confidence_scores)
        confidence_std = np.std(confidence_scores)
        
        # Load balance analysis
        expert_distribution = [expert_usage.get(i, 0) for i in range(self.num_experts)]
        load_balance_entropy = self._calculate_entropy(expert_distribution)
        
        return {
            'total_tokens': total_tokens,
            'unique_experts_used': unique_experts,
            'expert_usage_distribution': expert_usage,
            'expert_type_distribution': expert_type_usage,
            'average_confidence': avg_confidence,
            'confidence_std': confidence_std,
            'load_balance_entropy': load_balance_entropy,
            'routing_quality_score': self._calculate_routing_quality(routing_decisions)
        }
    
    def _calculate_entropy(self, distribution: List[int]) -> float:
        """Calculate entropy of distribution."""
        total = sum(distribution)
        if total == 0:
            return 0.0
        
        entropy = 0.0
        for count in distribution:
            if count > 0:
                p = count / total
                entropy -= p * np.log2(p)
        
        return entropy
    
    def _calculate_routing_quality(self, routing_decisions: List[RoutingDecision]) -> float:
        """Calculate overall routing quality score."""
        
        # Factors: confidence, load balance, expert type consistency
        confidences = [decision.confidence for decision in routing_decisions]
        avg_confidence = np.mean(confidences)
        
        # Expert distribution balance
        expert_counts = {}
        for decision in routing_decisions:
            expert_id = decision.expert_id
            expert_counts[expert_id] = expert_counts.get(expert_id, 0) + 1
        
        if len(expert_counts) == 0:
            return 0.0
        
        # Calculate balance score
        counts = list(expert_counts.values())
        max_count = max(counts)
        min_count = min(counts)
        balance_score = 1.0 - (max_count - min_count) / max(max_count, 1)
        
        # Combined quality score
        quality_score = (avg_confidence * 0.6 + balance_score * 0.4)
        
        return quality_score
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        
        if not self.performance_history:
            return {}
        
        latencies = [entry['latency_ms'] for entry in self.performance_history]
        
        return {
            'total_processing_calls': len(self.performance_history),
            'average_latency_ms': np.mean(latencies),
            'min_latency_ms': np.min(latencies),
            'max_latency_ms': np.max(latencies),
            'latency_std_ms': np.std(latencies),
            'system_stats': self.pimoe_system.get_system_stats()
        }
    
    def optimize_for_production(self):
        """Optimize system for production deployment."""
        
        # Enable optimizations
        self.pimoe_system.eval()
        
        # Compile for better performance
        if hasattr(torch, 'compile'):
            self.pimoe_system = torch.compile(self.pimoe_system)
        
        print("✅ System optimized for production deployment")

def demonstrate_pimoe_integration():
    """Demonstrate PiMoE integration with TruthGPT."""
    
    print("🚀 PiMoE Integration Demo for TruthGPT")
    print("=" * 50)
    
    # Configuration
    config = {
        'hidden_size': 512,
        'num_experts': 8,
        'optimization_level': 'advanced'
    }
    
    # Create integration
    integration = TruthGPTPiMoEIntegration(config)
    
    # Generate test data
    batch_size = 2
    seq_len = 128
    hidden_size = config['hidden_size']
    
    test_sequences = {
        'mathematical': torch.randn(batch_size, seq_len, hidden_size) * 0.5 + 1.0,
        'language': torch.randn(batch_size, seq_len, hidden_size) * 0.3,
        'reasoning': torch.randn(batch_size, seq_len, hidden_size) * 0.4 + 0.2,
        'creative': torch.randn(batch_size, seq_len, hidden_size) * 0.8
    }
    
    print("\n📊 Processing different sequence types...")
    
    # Process each sequence type
    results = {}
    for seq_type, sequence in test_sequences.items():
        print(f"  Processing {seq_type} sequences...")
        
        output, analysis = integration.process_sequence(sequence, return_analysis=True)
        
        results[seq_type] = {
            'output_shape': output.shape,
            'routing_analysis': analysis
        }
        
        print(f"    - Output shape: {output.shape}")
        print(f"    - Unique experts used: {analysis['unique_experts_used']}")
        print(f"    - Average confidence: {analysis['average_confidence']:.3f}")
        print(f"    - Routing quality: {analysis['routing_quality_score']:.3f}")
    
    # Get performance summary
    print("\n📈 Performance Summary:")
    performance = integration.get_performance_summary()
    
    print(f"  Total processing calls: {performance['total_processing_calls']}")
    print(f"  Average latency: {performance['average_latency_ms']:.2f} ms")
    print(f"  Min latency: {performance['min_latency_ms']:.2f} ms")
    print(f"  Max latency: {performance['max_latency_ms']:.2f} ms")
    print(f"  Latency std: {performance['latency_std_ms']:.2f} ms")
    
    # System statistics
    system_stats = performance['system_stats']
    print(f"\n🔧 System Statistics:")
    print(f"  Number of experts: {system_stats['num_experts']}")
    print(f"  Expert types: {system_stats['expert_types']}")
    print(f"  System efficiency: {system_stats['system_efficiency']:.3f}")
    
    # Optimize for production
    print("\n⚡ Optimizing for production...")
    integration.optimize_for_production()
    
    print("\n✅ Integration demo completed successfully!")
    
    return results, performance

def compare_with_traditional_moe():
    """Compare PiMoE with traditional MoE approaches."""
    
    print("\n🔄 Comparing PiMoE with Traditional MoE")
    print("=" * 50)
    
    # Traditional MoE (simplified comparison)
    class TraditionalMoE(nn.Module):
        def __init__(self, hidden_size, num_experts):
            super().__init__()
            self.num_experts = num_experts
            self.router = nn.Linear(hidden_size, num_experts)
            self.experts = nn.ModuleList([
                nn.Linear(hidden_size, hidden_size) for _ in range(num_experts)
            ])
        
        def forward(self, x):
            # Traditional routing (not token-level)
            routing_scores = self.router(x.mean(dim=1))  # Global routing
            expert_probs = torch.softmax(routing_scores, dim=-1)
            
            # Simple expert combination
            output = torch.zeros_like(x)
            for i, expert in enumerate(self.experts):
                expert_output = expert(x)
                weight = expert_probs[:, i:i+1].unsqueeze(-1)
                output += weight * expert_output
            
            return output
    
    # Create systems
    hidden_size = 512
    num_experts = 8
    batch_size = 2
    seq_len = 128
    
    traditional_moe = TraditionalMoE(hidden_size, num_experts)
    pimoe_system = create_pimoe_system(hidden_size=hidden_size, num_experts=num_experts)
    
    # Test data
    test_input = torch.randn(batch_size, seq_len, hidden_size)
    
    # Benchmark traditional MoE
    start_time = time.time()
    for _ in range(10):
        traditional_output = traditional_moe(test_input)
    traditional_time = time.time() - start_time
    
    # Benchmark PiMoE
    start_time = time.time()
    for _ in range(10):
        pimoe_output = pimoe_system(test_input)
    pimoe_time = time.time() - start_time
    
    # Results
    print(f"Traditional MoE time: {traditional_time:.4f}s")
    print(f"PiMoE time: {pimoe_time:.4f}s")
    print(f"Speedup: {traditional_time / pimoe_time:.2f}x")
    
    # Output quality comparison
    traditional_norm = torch.norm(traditional_output)
    pimoe_norm = torch.norm(pimoe_output)
    
    print(f"Traditional MoE output norm: {traditional_norm:.4f}")
    print(f"PiMoE output norm: {pimoe_norm:.4f}")
    
    return {
        'traditional_time': traditional_time,
        'pimoe_time': pimoe_time,
        'speedup': traditional_time / pimoe_time,
        'traditional_norm': traditional_norm.item(),
        'pimoe_norm': pimoe_norm.item()
    }

def run_comprehensive_demo():
    """Run comprehensive PiMoE demonstration."""
    
    print("🎯 Comprehensive PiMoE Demonstration")
    print("=" * 60)
    
    # Main integration demo
    integration_results, performance = demonstrate_pimoe_integration()
    
    # Comparison with traditional MoE
    comparison_results = compare_with_traditional_moe()
    
    # Run full demo
    print("\n🎪 Running Full PiMoE Demo...")
    demo_config = DemoConfig(
        hidden_size=512,
        num_experts=8,
        sequence_length=128,
        batch_size=2,
        num_iterations=20,
        enable_visualization=False,  # Disable for this demo
        save_results=False
    )
    
    demo = PiMoEDemo(demo_config)
    demo_results = demo.run_comprehensive_demo()
    
    # Compile final results
    final_results = {
        'integration_demo': integration_results,
        'performance_summary': performance,
        'comparison_with_traditional_moe': comparison_results,
        'full_demo_results': demo_results
    }
    
    print("\n📋 Final Results Summary:")
    print("=" * 40)
    
    # Performance metrics
    perf = performance
    print(f"Average Latency: {perf['average_latency_ms']:.2f} ms")
    print(f"Latency Range: {perf['min_latency_ms']:.2f} - {perf['max_latency_ms']:.2f} ms")
    print(f"System Efficiency: {perf['system_stats']['system_efficiency']:.3f}")
    
    # Comparison results
    comp = comparison_results
    print(f"PiMoE vs Traditional MoE Speedup: {comp['speedup']:.2f}x")
    
    # Demo results
    demo_perf = demo_results['performance']
    print(f"\nDemo Performance Results:")
    for system, metrics in demo_perf.items():
        print(f"  {system}:")
        print(f"    Latency: {metrics['avg_latency_ms']:.2f} ms")
        print(f"    Throughput: {metrics['avg_throughput']:.2f} tokens/sec")
        print(f"    Expert Utilization: {metrics['avg_expert_utilization']:.2f}")
    
    print("\n✅ Comprehensive demo completed successfully!")
    
    return final_results

if __name__ == "__main__":
    # Run the comprehensive demonstration
    results = run_comprehensive_demo()
    
    # Save results
    with open('pimoe_integration_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to pimoe_integration_results.json")




