import torch
import torch.nn as nn
from typing import Dict, Any

class DynamicExpertScaler(nn.Module):
    """Dynamic expert scaling based on load and performance."""
    def __init__(self, base_num_experts: int, max_num_experts: int = 16, scaling_threshold: float = 0.8, scaling_factor: float = 1.5):
        super().__init__()
        self.base_num_experts, self.max_num_experts, self.scaling_threshold, self.scaling_factor = base_num_experts, max_num_experts, scaling_threshold, scaling_factor
        self.register_buffer('current_num_experts', torch.tensor(base_num_experts))
        self.register_buffer('expert_loads', torch.zeros(max_num_experts))
        self.register_buffer('expert_performance', torch.ones(max_num_experts))
        self.scaling_network = nn.Sequential(nn.Linear(max_num_experts * 2, 64), nn.ReLU(), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1), nn.Sigmoid())

    def forward(self, expert_loads: torch.Tensor, expert_performance: torch.Tensor) -> Dict[str, Any]:
        decision = self.scaling_network(torch.cat([expert_loads, expert_performance], dim=-1))
        if decision > self.scaling_threshold:
            action, new = "scale_up", min(int(self.current_num_experts * self.scaling_factor), self.max_num_experts)
        elif decision < (1 - self.scaling_threshold):
            action, new = "scale_down", max(int(self.current_num_experts / self.scaling_factor), self.base_num_experts)
        else:
            action, new = "maintain", int(self.current_num_experts.item())
        return {'scaling_decision': decision.item(), 'action': action, 'current_experts': self.current_num_experts.item(), 'new_experts': new, 'scaling_factor': self.scaling_factor}

    def update_expert_metrics(self, expert_loads: torch.Tensor, expert_performance: torch.Tensor) -> None:
        self.expert_loads, self.expert_performance = expert_loads, expert_performance
