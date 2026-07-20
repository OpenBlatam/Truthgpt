import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Optional, Union, Dict, Any, Tuple
from ..pimoe_router import ExpertType, RoutingDecision

class AttentionBasedRouter(nn.Module):
    """Attention-based router for sophisticated token-level routing decisions."""
    def __init__(self, hidden_size: int, num_experts: int, expert_types: List[ExpertType], attention_heads: int = 8, dropout: float = 0.1, temperature: float = 1.0):
        super().__init__()
        self.hidden_size, self.num_experts, self.expert_types, self.attention_heads, self.temperature = hidden_size, num_experts, expert_types, attention_heads, temperature
        self.head_dim = hidden_size // attention_heads
        self.routing_network = nn.Sequential(nn.Linear(hidden_size, hidden_size // 2), nn.ReLU(), nn.Dropout(dropout), nn.Linear(hidden_size // 2, num_experts))
        self.register_buffer('expert_loads', torch.zeros(num_experts))
        self.register_buffer('expert_usage_count', torch.zeros(num_experts))

    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor] = None, return_attention_weights: bool = False) -> Union[torch.Tensor, Tuple[torch.Tensor, Dict[str, Any]]]:
        batch_size, seq_len, _ = hidden_states.shape
        routing_scores = self.routing_network(hidden_states) / self.temperature
        probs = F.softmax(routing_scores, dim=-1)
        top_scores, top_indices = torch.topk(probs, k=1, dim=-1)
        self._update_expert_usage(top_indices)
        routed = self._apply_expert_routing(hidden_states, top_indices, top_scores)
        if return_attention_weights:
            return routed, {'expert_probs': probs, 'load_balance_loss': self._calculate_load_balance_loss(probs)}
        return routed

    def _update_expert_usage(self, indices: torch.Tensor):
        for idx in indices.flatten():
            self.expert_usage_count[idx] += 1
            self.expert_loads[idx] += 1

    def _apply_expert_routing(self, hidden, indices, scores):
        batch, seq, hidden_size = hidden.shape
        weights = F.one_hot(indices.squeeze(-1), num_classes=self.num_experts).float()
        routed = torch.zeros_like(hidden)
        for i in range(self.num_experts):
            mask = weights[:, :, i:i+1]
            expert_input = hidden * mask
            routed += (torch.matmul(expert_input, torch.randn(hidden_size, hidden_size, device=hidden.device)) + torch.randn(hidden_size, device=hidden.device)) * mask
        return routed

    def _calculate_load_balance_loss(self, probs):
        usage = torch.mean(probs, dim=[0, 1])
        return F.mse_loss(usage, torch.ones_like(usage) / self.num_experts)

class HierarchicalRouter(nn.Module):
    """Hierarchical router with multi-level routing decisions."""
    def __init__(self, hidden_size: int, num_experts: int, expert_types: List[ExpertType], hierarchical_levels: int = 3, dropout: float = 0.1):
        super().__init__()
        self.hidden_size, self.num_experts, self.hierarchical_levels = hidden_size, num_experts, hierarchical_levels
        self.level_routers = nn.ModuleList([nn.Sequential(nn.Linear(hidden_size, hidden_size // 2), nn.ReLU(), nn.Dropout(dropout), nn.Linear(hidden_size // 2, num_experts)) for _ in range(hierarchical_levels)])
        self.level_expert_assignments = nn.Parameter(torch.randn(hierarchical_levels, num_experts))
        self.hierarchical_weights = nn.Parameter(torch.ones(hierarchical_levels))

    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor] = None, return_hierarchical_info: bool = False) -> Union[torch.Tensor, Tuple[torch.Tensor, Dict[str, Any]]]:
        level_outputs, current = [], hidden_states
        for level in range(self.hierarchical_levels):
            probs = F.softmax(self.level_routers[level](current), dim=-1)
            scores, indices = torch.topk(probs, k=1, dim=-1)
            current = self._apply_level_expert_processing(current, indices, scores, level)
            level_outputs.append(current)
        weights = F.softmax(self.hierarchical_weights, dim=0)
        final = sum(weights[i] * level_outputs[i] for i in range(self.hierarchical_levels))
        return (final, {'level_outputs': level_outputs}) if return_hierarchical_info else final

    def _apply_level_expert_processing(self, hidden, indices, scores, level):
        batch, seq, hidden_size = hidden.shape
        assign = self.level_expert_assignments[level]
        masks = F.one_hot(indices.squeeze(-1), num_classes=self.num_experts).float()
        output = torch.zeros_like(hidden)
        for i in range(self.num_experts):
            mask = masks[:, :, i:i+1]
            expert_input = hidden * mask
            trans = assign[i] * torch.randn(hidden_size, hidden_size, device=hidden.device)
            bias = assign[i] * torch.randn(hidden_size, device=hidden.device)
            output += (torch.matmul(expert_input, trans) + bias) * mask
        return output
