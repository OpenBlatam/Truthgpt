import torch
import torch.nn as nn
from typing import List, Union, Tuple, Dict, Any

class CrossExpertCommunicator(nn.Module):
    """Cross-expert communication mechanism for information sharing."""
    def __init__(self, hidden_size: int, num_experts: int, communication_channels: int = 4, dropout: float = 0.1):
        super().__init__()
        self.hidden_size, self.num_experts, self.communication_channels = hidden_size, num_experts, communication_channels
        self.communication_networks = nn.ModuleList([nn.Sequential(nn.Linear(hidden_size, hidden_size // 2), nn.ReLU(), nn.Dropout(dropout), nn.Linear(hidden_size // 2, hidden_size)) for _ in range(communication_channels)])
        self.expert_attention = nn.MultiheadAttention(embed_dim=hidden_size, num_heads=8, dropout=dropout, batch_first=True)
        self.communication_gates = nn.ModuleList([nn.Sequential(nn.Linear(hidden_size, 1), nn.Sigmoid()) for _ in range(num_experts)])

    def forward(self, expert_outputs: List[torch.Tensor], expert_ids: List[int], return_communication_info: bool = False) -> Union[List[torch.Tensor], Tuple[List[torch.Tensor], Dict[str, Any]]]:
        if not expert_outputs: return expert_outputs
        stacked = torch.stack(expert_outputs, dim=1)
        attended, _ = self.expert_attention(stacked, stacked, stacked)
        communicated, info = [], {'communication_channels': []}
        for i, out in enumerate(expert_outputs):
            gate = self.communication_gates[i](out)
            combined = torch.stack([net(out) for net in self.communication_networks], dim=-1).mean(dim=-1)
            communicated.append(gate * combined + (1 - gate) * out)
            info['communication_channels'].append({'expert_id': i, 'gate': gate.item()})
        return (communicated, info) if return_communication_info else communicated
