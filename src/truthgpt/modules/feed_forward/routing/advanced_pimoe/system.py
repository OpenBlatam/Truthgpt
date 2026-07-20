import torch
import torch.nn as nn
from typing import List, Optional, Union, Dict, Any, Tuple

from ..pimoe_router import ExpertType, PiMoEExpert
from .base import RoutingStrategy, AdvancedRoutingConfig
from .routers import AttentionBasedRouter, HierarchicalRouter
from .scaling import DynamicExpertScaler
from .communication import CrossExpertCommunicator
from .nas import NeuralArchitectureSearchRouter

class AdvancedPiMoESystem(nn.Module):
    """Advanced PiMoE system with enhanced routing capabilities."""
    def __init__(self, hidden_size: int, num_experts: int, expert_types: List[ExpertType], routing_config: AdvancedRoutingConfig, enable_nas: bool = False):
        super().__init__()
        self.hidden_size, self.num_experts, self.expert_types, self.routing_config, self.enable_nas = hidden_size, num_experts, expert_types, routing_config, enable_nas
        self._initialize_routing_components()
        self._initialize_expert_networks()
        self._initialize_advanced_components()

    def _initialize_routing_components(self):
        if self.routing_config.strategy == RoutingStrategy.ATTENTION_BASED:
            self.router = AttentionBasedRouter(self.hidden_size, self.num_experts, self.expert_types, self.routing_config.attention_heads)
        elif self.routing_config.strategy == RoutingStrategy.HIERARCHICAL:
            self.router = HierarchicalRouter(self.hidden_size, self.num_experts, self.expert_types, self.routing_config.hierarchical_levels)
        else:
            self.router = AttentionBasedRouter(self.hidden_size, self.num_experts, self.expert_types)

    def _initialize_expert_networks(self):
        self.experts = nn.ModuleList([PiMoEExpert(self.hidden_size, self.expert_types[i % len(self.expert_types)]) for i in range(self.num_experts)])

    def _initialize_advanced_components(self):
        self.expert_scaler = DynamicExpertScaler(self.num_experts, self.num_experts * 2, self.routing_config.dynamic_scaling_threshold)
        self.communicator = CrossExpertCommunicator(self.hidden_size, self.num_experts) if self.routing_config.cross_expert_communication else None
        self.nas_router = NeuralArchitectureSearchRouter(self.hidden_size, self.routing_config.nas_search_space) if self.enable_nas else None

    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor] = None, return_advanced_info: bool = False) -> Union[torch.Tensor, Tuple[torch.Tensor, Dict[str, Any]]]:
        if hasattr(self, 'router'):
            if return_advanced_info:
                if isinstance(self.router, AttentionBasedRouter): output, routing_info = self.router(hidden_states, attention_mask, True)
                elif isinstance(self.router, HierarchicalRouter): output, routing_info = self.router(hidden_states, attention_mask, True)
                else: output, routing_info = self.router(hidden_states, attention_mask), None
            else: output, routing_info = self.router(hidden_states, attention_mask), None
        else: output, routing_info = hidden_states, None

        expert_outputs = [expert(output) for expert in self.experts]
        if self.communicator: expert_outputs = self.communicator(expert_outputs, list(range(self.num_experts)))
        final = torch.stack(expert_outputs, dim=1).mean(dim=1) if expert_outputs else output
        return (final, {'routing_info': routing_info, 'expert_outputs': expert_outputs, 'final_output': final}) if return_advanced_info else final

    def get_advanced_metrics(self) -> Dict[str, Any]:
        metrics = {'routing_strategy': self.routing_config.strategy.value, 'num_experts': self.num_experts, 'expert_types': [et.value for et in self.expert_types], 'dynamic_scaling_enabled': self.expert_scaler is not None, 'cross_expert_communication': self.communicator is not None, 'neural_architecture_search': self.nas_router is not None}
        if hasattr(self.router, 'get_expert_usage_stats'): metrics['router_stats'] = self.router.get_expert_usage_stats()
        return metrics

def create_advanced_pimoe_system(hidden_size: int, num_experts: int = 8, expert_types: Optional[List[ExpertType]] = None, routing_strategy: RoutingStrategy = RoutingStrategy.ATTENTION_BASED, enable_nas: bool = False, **kwargs: Any) -> AdvancedPiMoESystem:
    if expert_types is None: expert_types = [ExpertType.REASONING, ExpertType.COMPUTATION, ExpertType.MATHEMATICAL, ExpertType.LOGICAL, ExpertType.LANGUAGE, ExpertType.CREATIVE, ExpertType.ANALYTICAL]
    return AdvancedPiMoESystem(hidden_size, num_experts, expert_types, AdvancedRoutingConfig(strategy=routing_strategy, **kwargs), enable_nas)
