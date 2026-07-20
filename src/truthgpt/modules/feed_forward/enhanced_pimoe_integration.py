"""
Enhanced PiMoE Integration for TruthGPT Optimization Core
Integrates token-level routing with existing optimization frameworks
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Union, Any
import math
import time
from dataclasses import dataclass
from .pimoe_router import (
    PiMoESystem, 
    TokenLevelRouter, 
    ExpertType, 
    RoutingDecision,
    create_pimoe_system
)

@dataclass
class OptimizationMetrics:
    """Metrics for tracking optimization performance."""
    latency_ms: float
    throughput_tokens_per_sec: float
    memory_usage_mb: float
    expert_utilization: float
    load_balance_score: float
    routing_accuracy: float

class EnhancedPiMoEIntegration(nn.Module):
    """
    Enhanced PiMoE integration with TruthGPT optimization core.
    Provides seamless integration with existing optimization frameworks.
    """
    
    def __init__(
        self,
        hidden_size: int,
        num_experts: int = 8,
        expert_types: Optional[List[ExpertType]] = None,
        optimization_level: str = "advanced",
        enable_quantization: bool = True,
        enable_pruning: bool = False,
        enable_distillation: bool = False,
        router_config: Optional[Dict[str, Any]] = None,
        expert_config: Optional[Dict[str, Any]] = None
    ):
        super().__init__()
        
        self.hidden_size = hidden_size
        self.num_experts = num_experts
        self.optimization_level = optimization_level
        self.enable_quantization = enable_quantization
        self.enable_pruning = enable_pruning
        self.enable_distillation = enable_distillation
        
        # Initialize PiMoE system
        self.pimoe_system = create_pimoe_system(
            hidden_size=hidden_size,
            num_experts=num_experts,
            expert_types=expert_types,
            router_config=router_config,
            expert_config=expert_config
        )
        
        # Optimization components
        self._setup_optimization_components()
        
        # Performance tracking
        self.performance_tracker = PerformanceTracker()
        
    def _setup_optimization_components(self):
        """Setup optimization-specific components."""
        
        # Quantization support
        if self.enable_quantization:
            self.quantization_config = {
                'weight_bits': 8,
                'activation_bits': 8,
                'dynamic_range': True
            }
        
        # Pruning support
        if self.enable_pruning:
            self.pruning_config = {
                'sparsity_ratio': 0.1,
                'structured_pruning': True,
                'magnitude_threshold': 0.01
            }
        
        # Distillation support
        if self.enable_distillation:
            self.distillation_config = {
                'temperature': 3.0,
                'alpha': 0.7,
                'beta': 0.3
            }
    
    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        return_metrics: bool = False,
        enable_optimization: bool = True
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, Dict[str, Any]]]:
        """
        Enhanced forward pass with optimization support.
        """
        start_time = time.time()
        
        # Apply optimizations if enabled
        if enable_optimization:
            hidden_states = self._apply_pre_optimizations(hidden_states)
        
        # PiMoE processing
        if return_metrics:
            output, routing_info = self.pimoe_system(
                hidden_states,
                attention_mask,
                return_routing_info=True
            )
        else:
            output = self.pimoe_system(hidden_states, attention_mask)
            routing_info = None
        
        # Apply post-optimizations
        if enable_optimization:
            output = self._apply_post_optimizations(output)
        
        # Calculate metrics
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        if return_metrics:
            metrics = self._calculate_metrics(
                hidden_states, 
                output, 
                routing_info, 
                latency_ms
            )
            return output, metrics
        
        return output
    
    def _apply_pre_optimizations(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """Apply pre-processing optimizations."""
        # Input normalization
        if hasattr(self, 'input_norm'):
            hidden_states = self.input_norm(hidden_states)
        
        # Quantization if enabled
        if self.enable_quantization:
            hidden_states = self._quantize_input(hidden_states)
        
        return hidden_states
    
    def _apply_post_optimizations(self, output: torch.Tensor) -> torch.Tensor:
        """Apply post-processing optimizations."""
        # Output scaling
        if hasattr(self, 'output_scale'):
            output = output * self.output_scale
        
        # Dequantization if needed
        if self.enable_quantization:
            output = self._dequantize_output(output)
        
        return output
    
    def _quantize_input(self, x: torch.Tensor) -> torch.Tensor:
        """Quantize input for efficiency."""
        if not hasattr(self, 'input_quantizer'):
            self.input_quantizer = torch.quantization.QuantStub()
        
        return self.input_quantizer(x)
    
    def _dequantize_output(self, x: torch.Tensor) -> torch.Tensor:
        """Dequantize output."""
        if not hasattr(self, 'output_dequantizer'):
            self.output_dequantizer = torch.quantization.DeQuantStub()
        
        return self.output_dequantizer(x)
    
    def _calculate_metrics(
        self,
        input_tensor: torch.Tensor,
        output_tensor: torch.Tensor,
        routing_info: Optional[Dict[str, Any]],
        latency_ms: float
    ) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        
        # Basic metrics
        batch_size, seq_len, hidden_size = input_tensor.shape
        total_tokens = batch_size * seq_len
        
        # Throughput calculation
        throughput_tokens_per_sec = total_tokens / (latency_ms / 1000) if latency_ms > 0 else 0
        
        # Memory usage estimation
        memory_usage_mb = (input_tensor.numel() + output_tensor.numel()) * 4 / (1024 * 1024)  # Assuming float32
        
        # Expert utilization
        expert_utilization = 0.0
        if routing_info and 'routing_decisions' in routing_info:
            unique_experts = len(set(decision.expert_id for decision in routing_info['routing_decisions']))
            expert_utilization = unique_experts / self.num_experts
        
        # Load balance score
        load_balance_score = 0.0
        if routing_info and 'router_stats' in routing_info:
            load_balance_score = routing_info['router_stats'].get('load_balance_ratio', 0.0)
        
        # Routing accuracy (simplified)
        routing_accuracy = 0.0
        if routing_info and 'routing_decisions' in routing_info:
            high_confidence_decisions = sum(1 for decision in routing_info['routing_decisions'] 
                                         if decision.confidence > 0.7)
            routing_accuracy = high_confidence_decisions / len(routing_info['routing_decisions'])
        
        return {
            'latency_ms': latency_ms,
            'throughput_tokens_per_sec': throughput_tokens_per_sec,
            'memory_usage_mb': memory_usage_mb,
            'expert_utilization': expert_utilization,
            'load_balance_score': load_balance_score,
            'routing_accuracy': routing_accuracy,
            'total_tokens': total_tokens,
            'batch_size': batch_size,
            'sequence_length': seq_len
        }
    
    def optimize_for_inference(self):
        """Optimize the model for inference."""
        self.eval()
        
        # Enable quantization
        if self.enable_quantization:
            self._enable_quantization()
        
        # Apply pruning
        if self.enable_pruning:
            self._apply_pruning()
        
        # Compile for better performance
        if hasattr(torch, 'compile'):
            self.pimoe_system = torch.compile(self.pimoe_system)
    
    def _enable_quantization(self):
        """Enable quantization for the model."""
        # Quantize the router
        self.pimoe_system.router = torch.quantization.quantize_dynamic(
            self.pimoe_system.router,
            {nn.Linear},
            dtype=torch.qint8
        )
        
        # Quantize experts
        for i, expert in enumerate(self.pimoe_system.experts):
            self.pimoe_system.experts[i] = torch.quantization.quantize_dynamic(
                expert,
                {nn.Linear},
                dtype=torch.qint8
            )
    
    def _apply_pruning(self):
        """Apply structured pruning to the model."""
        if not hasattr(self, 'pruning_config'):
            return
        
        # Prune router weights
        self._prune_module(self.pimoe_system.router)
        
        # Prune expert weights
        for expert in self.pimoe_system.experts:
            self._prune_module(expert)
    
    def _prune_module(self, module: nn.Module):
        """Apply pruning to a specific module."""
        for name, param in module.named_parameters():
            if 'weight' in name:
                # Magnitude-based pruning
                threshold = torch.quantile(torch.abs(param), self.pruning_config['sparsity_ratio'])
                mask = torch.abs(param) > threshold
                param.data *= mask.float()
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive optimization report."""
        system_stats = self.pimoe_system.get_system_stats()
        
        return {
            'system_stats': system_stats,
            'optimization_config': {
                'quantization_enabled': self.enable_quantization,
                'pruning_enabled': self.enable_pruning,
                'distillation_enabled': self.enable_distillation,
                'optimization_level': self.optimization_level
            },
            'performance_metrics': self.performance_tracker.get_metrics(),
            'recommendations': self._generate_optimization_recommendations()
        }
    
    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on current performance."""
        recommendations = []
        
        system_stats = self.pimoe_system.get_system_stats()
        load_balance_ratio = system_stats['router_stats']['load_balance_ratio']
        
        if load_balance_ratio < 0.8:
            recommendations.append("Consider adjusting expert capacity or routing temperature for better load balancing")
        
        if system_stats['router_stats']['total_usage'] < 100:
            recommendations.append("Increase training iterations to improve expert utilization")
        
        if self.enable_quantization:
            recommendations.append("Quantization is enabled - monitor accuracy impact")
        
        if self.enable_pruning:
            recommendations.append("Pruning is enabled - verify model performance")
        
        return recommendations

class PerformanceTracker:
    """Tracks performance metrics over time."""
    
    def __init__(self):
        self.metrics_history = []
        self.max_history = 1000
    
    def add_metrics(self, metrics: Dict[str, Any]):
        """Add new metrics to history."""
        self.metrics_history.append(metrics)
        
        # Keep only recent history
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics."""
        if not self.metrics_history:
            return {}
        
        # Calculate averages
        avg_metrics = {}
        for key in self.metrics_history[0].keys():
            values = [m[key] for m in self.metrics_history if key in m]
            if values:
                avg_metrics[f'avg_{key}'] = sum(values) / len(values)
                avg_metrics[f'min_{key}'] = min(values)
                avg_metrics[f'max_{key}'] = max(values)
        
        return avg_metrics

class AdaptivePiMoE(nn.Module):
    """
    Adaptive PiMoE system that adjusts routing based on performance feedback.
    """
    
    def __init__(
        self,
        hidden_size: int,
        num_experts: int = 8,
        adaptation_rate: float = 0.01,
        performance_threshold: float = 0.8
    ):
        super().__init__()
        
        self.hidden_size = hidden_size
        self.num_experts = num_experts
        self.adaptation_rate = adaptation_rate
        self.performance_threshold = performance_threshold
        
        # Initialize base PiMoE system
        self.pimoe_system = create_pimoe_system(
            hidden_size=hidden_size,
            num_experts=num_experts
        )
        
        # Adaptation components
        self.performance_tracker = PerformanceTracker()
        self.adaptation_history = []
        
    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        return_adaptation_info: bool = False
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, Dict[str, Any]]]:
        """
        Adaptive forward pass with performance-based routing adjustment.
        """
        # Get routing decisions
        output, routing_info = self.pimoe_system(
            hidden_states,
            attention_mask,
            return_routing_info=True
        )
        
        # Track performance
        metrics = self._calculate_performance_metrics(hidden_states, output, routing_info)
        self.performance_tracker.add_metrics(metrics)
        
        # Adapt routing if needed
        adaptation_info = None
        if return_adaptation_info:
            adaptation_info = self._adapt_routing(metrics)
        
        if return_adaptation_info:
            return output, {
                'routing_info': routing_info,
                'metrics': metrics,
                'adaptation_info': adaptation_info
            }
        
        return output
    
    def _calculate_performance_metrics(
        self,
        input_tensor: torch.Tensor,
        output_tensor: torch.Tensor,
        routing_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate performance metrics for adaptation."""
        # Basic performance metrics
        batch_size, seq_len, hidden_size = input_tensor.shape
        
        # Expert utilization
        unique_experts = len(set(decision.expert_id for decision in routing_info['routing_decisions']))
        expert_utilization = unique_experts / self.num_experts
        
        # Load balance
        load_balance_score = routing_info['router_stats']['load_balance_ratio']
        
        # Routing confidence
        avg_confidence = sum(decision.confidence for decision in routing_info['routing_decisions']) / len(routing_info['routing_decisions'])
        
        return {
            'expert_utilization': expert_utilization,
            'load_balance_score': load_balance_score,
            'routing_confidence': avg_confidence,
            'total_tokens': batch_size * seq_len
        }
    
    def _adapt_routing(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt routing based on performance metrics."""
        adaptation_info = {
            'adaptation_applied': False,
            'changes': [],
            'performance_score': 0.0
        }
        
        # Calculate overall performance score
        performance_score = (
            metrics['expert_utilization'] * 0.4 +
            metrics['load_balance_score'] * 0.4 +
            metrics['routing_confidence'] * 0.2
        )
        
        adaptation_info['performance_score'] = performance_score
        
        # Adapt if performance is below threshold
        if performance_score < self.performance_threshold:
            # Adjust router temperature
            current_temp = self.pimoe_system.router.temperature
            new_temp = current_temp * (1 + self.adaptation_rate)
            self.pimoe_system.router.temperature = new_temp
            
            adaptation_info['adaptation_applied'] = True
            adaptation_info['changes'].append(f"Adjusted temperature: {current_temp:.3f} -> {new_temp:.3f}")
            
            # Adjust load balance weight
            current_lb_weight = self.pimoe_system.router.load_balance_weight
            new_lb_weight = current_lb_weight * (1 + self.adaptation_rate)
            self.pimoe_system.router.load_balance_weight = new_lb_weight
            
            adaptation_info['changes'].append(f"Adjusted load balance weight: {current_lb_weight:.3f} -> {new_lb_weight:.3f}")
        
        # Record adaptation
        self.adaptation_history.append({
            'timestamp': time.time(),
            'performance_score': performance_score,
            'adaptation_applied': adaptation_info['adaptation_applied'],
            'changes': adaptation_info['changes']
        })
        
        return adaptation_info

def create_enhanced_pimoe_integration(
    hidden_size: int,
    num_experts: int = 8,
    optimization_level: str = "advanced",
    enable_adaptation: bool = True,
    **kwargs
) -> Union[EnhancedPiMoEIntegration, AdaptivePiMoE]:
    """
    Factory function to create enhanced PiMoE integration.
    """
    if enable_adaptation:
        return AdaptivePiMoE(
            hidden_size=hidden_size,
            num_experts=num_experts,
            **kwargs
        )
    else:
        return EnhancedPiMoEIntegration(
            hidden_size=hidden_size,
            num_experts=num_experts,
            optimization_level=optimization_level,
            **kwargs
        )




