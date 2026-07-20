"""
PiMoE: Token-Level Routing for Integrating High-Precision Computation and Reasoning
Inspired by the PiMoE paper for dynamic expert routing at token level
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Union, Any
import math
import numpy as np
from dataclasses import dataclass
from enum import Enum

class ExpertType(Enum):
    """Types of experts for different computation tasks."""
    REASONING = "reasoning"
    COMPUTATION = "computation"
    LANGUAGE = "language"
    MATHEMATICAL = "mathematical"
    LOGICAL = "logical"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"

@dataclass
class RoutingDecision:
    """Represents a routing decision for a token."""
    token_id: int
    expert_id: int
    expert_type: ExpertType
    confidence: float
    routing_score: float
    load_balance_weight: float

class TokenLevelRouter(nn.Module):
    """
    PiMoE-inspired token-level router for dynamic expert selection.
    Routes tokens to appropriate experts based on content and context.
    """
    
    def __init__(
        self,
        hidden_size: int,
        num_experts: int,
        expert_types: List[ExpertType],
        router_hidden_size: Optional[int] = None,
        temperature: float = 1.0,
        load_balance_weight: float = 0.1,
        expert_capacity_factor: float = 1.25,
        use_gating: bool = True,
        use_auxiliary_loss: bool = True,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.hidden_size = hidden_size
        self.num_experts = num_experts
        self.expert_types = expert_types
        self.router_hidden_size = router_hidden_size or hidden_size // 2
        self.temperature = temperature
        self.load_balance_weight = load_balance_weight
        self.expert_capacity_factor = expert_capacity_factor
        self.use_gating = use_gating
        self.use_auxiliary_loss = use_auxiliary_loss
        self.dropout = dropout
        
        # Router network for token-level decisions
        self.router_network = nn.Sequential(
            nn.Linear(hidden_size, self.router_hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(self.router_hidden_size, num_experts)
        )
        
        # Expert type classifier
        self.expert_type_classifier = nn.Linear(hidden_size, len(expert_types))
        
        # Gating mechanism for fine-grained control
        if self.use_gating:
            self.gate_network = nn.Sequential(
                nn.Linear(hidden_size, self.router_hidden_size),
                nn.Tanh(),
                nn.Linear(self.router_hidden_size, 1),
                nn.Sigmoid()
            )
        
        # Load balancing tracking
        self.register_buffer('expert_loads', torch.zeros(num_experts))
        self.register_buffer('expert_usage_count', torch.zeros(num_experts))
        
    def forward(
        self, 
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        return_routing_info: bool = False
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, Dict[str, Any]]]:
        """
        Forward pass with token-level routing.
        
        Args:
            hidden_states: Input hidden states [batch_size, seq_len, hidden_size]
            attention_mask: Attention mask for valid tokens
            return_routing_info: Whether to return routing decisions
            
        Returns:
            Routed hidden states and optionally routing information
        """
        batch_size, seq_len, hidden_size = hidden_states.shape
        
        # Flatten for token-level processing
        flat_hidden = hidden_states.view(-1, hidden_size)  # [batch_size * seq_len, hidden_size]
        
        # Get routing scores for each token
        routing_scores = self.router_network(flat_hidden)  # [batch_size * seq_len, num_experts]
        
        # Apply temperature scaling
        routing_scores = routing_scores / self.temperature
        
        # Get expert type predictions
        expert_type_logits = self.expert_type_classifier(flat_hidden)
        expert_type_probs = F.softmax(expert_type_logits, dim=-1)
        
        # Gating mechanism
        if self.use_gating:
            gate_scores = self.gate_network(flat_hidden)  # [batch_size * seq_len, 1]
            routing_scores = routing_scores * gate_scores
        
        # Apply softmax for expert selection
        expert_probs = F.softmax(routing_scores, dim=-1)
        
        # Top-k expert selection (k=1 for token-level routing)
        top_expert_scores, top_expert_indices = torch.topk(expert_probs, k=1, dim=-1)
        
        # Create routing decisions
        routing_decisions = []
        for i in range(flat_hidden.size(0)):
            expert_id = top_expert_indices[i].item()
            expert_type_idx = torch.argmax(expert_type_probs[i]).item()
            expert_type = self.expert_types[expert_type_idx]
            
            decision = RoutingDecision(
                token_id=i,
                expert_id=expert_id,
                expert_type=expert_type,
                confidence=top_expert_scores[i].item(),
                routing_score=routing_scores[i, expert_id].item(),
                load_balance_weight=self._calculate_load_balance_weight(expert_id)
            )
            routing_decisions.append(decision)
        
        # Update expert usage statistics
        self._update_expert_usage(top_expert_indices)
        
        # Apply expert routing
        routed_hidden = self._apply_expert_routing(
            flat_hidden, 
            top_expert_indices, 
            top_expert_scores
        )
        
        # Reshape back to original dimensions
        routed_hidden = routed_hidden.view(batch_size, seq_len, hidden_size)
        
        if return_routing_info:
            routing_info = {
                'routing_decisions': routing_decisions,
                'expert_probs': expert_probs,
                'expert_type_probs': expert_type_probs,
                'load_balance_loss': self._calculate_load_balance_loss(expert_probs),
                'auxiliary_loss': self._calculate_auxiliary_loss(expert_type_probs, routing_decisions)
            }
            return routed_hidden, routing_info
        
        return routed_hidden
    
    def _calculate_load_balance_weight(self, expert_id: int) -> float:
        """Calculate load balancing weight for an expert."""
        if self.expert_usage_count[expert_id] == 0:
            return 1.0
        return 1.0 / (1.0 + self.expert_usage_count[expert_id].item())
    
    def _update_expert_usage(self, expert_indices: torch.Tensor):
        """Update expert usage statistics."""
        for expert_id in expert_indices:
            self.expert_usage_count[expert_id] += 1
            self.expert_loads[expert_id] += 1
    
    def _apply_expert_routing(
        self, 
        hidden_states: torch.Tensor, 
        expert_indices: torch.Tensor, 
        expert_scores: torch.Tensor
    ) -> torch.Tensor:
        """
        Apply expert routing to hidden states.
        This is a simplified version - in practice, this would route to actual expert networks.
        """
        # For now, we'll apply a weighted transformation based on expert selection
        # In a full implementation, this would route to different expert networks
        
        # Create expert-specific transformations
        expert_weights = F.one_hot(expert_indices.squeeze(), num_classes=self.num_experts).float()
        
        # Apply expert-specific scaling
        expert_scales = torch.randn(self.num_experts, self.hidden_size, device=hidden_states.device)
        expert_biases = torch.randn(self.num_experts, self.hidden_size, device=hidden_states.device)
        
        # Weighted combination of expert transformations
        weighted_scales = torch.sum(expert_weights.unsqueeze(-1) * expert_scales.unsqueeze(0), dim=1)
        weighted_biases = torch.sum(expert_weights.unsqueeze(-1) * expert_biases.unsqueeze(0), dim=1)
        
        # Apply transformation
        routed_hidden = hidden_states * weighted_scales + weighted_biases
        
        return routed_hidden
    
    def _calculate_load_balance_loss(self, expert_probs: torch.Tensor) -> torch.Tensor:
        """Calculate load balancing auxiliary loss."""
        if not self.use_auxiliary_loss:
            return torch.tensor(0.0, device=expert_probs.device)
        
        # Calculate expert usage frequency
        expert_usage = torch.mean(expert_probs, dim=0)
        
        # Calculate load balance loss (encourage uniform usage)
        uniform_usage = torch.ones_like(expert_usage) / self.num_experts
        load_balance_loss = F.mse_loss(expert_usage, uniform_usage)
        
        return self.load_balance_weight * load_balance_loss
    
    def _calculate_auxiliary_loss(
        self, 
        expert_type_probs: torch.Tensor, 
        routing_decisions: List[RoutingDecision]
    ) -> torch.Tensor:
        """Calculate auxiliary loss for expert type consistency."""
        if not self.use_auxiliary_loss:
            return torch.tensor(0.0, device=expert_type_probs.device)
        
        # Encourage consistency between expert type predictions and routing decisions
        type_consistency_loss = 0.0
        
        for i, decision in enumerate(routing_decisions):
            expert_type_idx = self.expert_types.index(decision.expert_type)
            predicted_type_prob = expert_type_probs[i, expert_type_idx]
            
            # Loss for type-expert consistency
            type_consistency_loss += (1.0 - predicted_type_prob) * decision.confidence
        
        return type_consistency_loss / len(routing_decisions)
    
    def get_expert_usage_stats(self) -> Dict[str, Any]:
        """Get expert usage statistics."""
        total_usage = self.expert_usage_count.sum().item()
        
        return {
            'expert_usage_counts': self.expert_usage_count.cpu().numpy().tolist(),
            'expert_loads': self.expert_loads.cpu().numpy().tolist(),
            'total_usage': total_usage,
            'usage_distribution': (self.expert_usage_count / max(total_usage, 1)).cpu().numpy().tolist(),
            'load_balance_ratio': self._calculate_load_balance_ratio()
        }
    
    def _calculate_load_balance_ratio(self) -> float:
        """Calculate how well-balanced the expert usage is."""
        if self.expert_usage_count.sum() == 0:
            return 1.0
        
        usage_ratios = self.expert_usage_count / self.expert_usage_count.sum()
        uniform_ratio = 1.0 / self.num_experts
        
        # Calculate coefficient of variation (lower is better)
        mean_ratio = usage_ratios.mean()
        std_ratio = usage_ratios.std()
        
        if mean_ratio == 0:
            return 1.0
        
        cv = std_ratio / mean_ratio
        balance_ratio = 1.0 / (1.0 + cv)
        
        return balance_ratio.item()

class PiMoEExpert(nn.Module):
    """
    Individual expert network for PiMoE system.
    Each expert specializes in a specific type of computation.
    """
    
    def __init__(
        self,
        hidden_size: int,
        expert_type: ExpertType,
        intermediate_size: Optional[int] = None,
        activation: str = "gelu",
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.hidden_size = hidden_size
        self.expert_type = expert_type
        self.intermediate_size = intermediate_size or hidden_size * 4
        self.activation = activation
        self.dropout = dropout
        
        # Expert-specific architecture based on type
        if expert_type == ExpertType.REASONING:
            self._build_reasoning_expert()
        elif expert_type == ExpertType.COMPUTATION:
            self._build_computation_expert()
        elif expert_type == ExpertType.MATHEMATICAL:
            self._build_mathematical_expert()
        elif expert_type == ExpertType.LOGICAL:
            self._build_logical_expert()
        else:
            self._build_general_expert()
    
    def _build_reasoning_expert(self):
        """Build expert specialized for reasoning tasks."""
        self.layers = nn.Sequential(
            nn.Linear(self.hidden_size, self.intermediate_size),
            nn.LayerNorm(self.intermediate_size),
            nn.GELU(),
            nn.Dropout(self.dropout),
            nn.Linear(self.intermediate_size, self.intermediate_size // 2),
            nn.LayerNorm(self.intermediate_size // 2),
            nn.GELU(),
            nn.Dropout(self.dropout),
            nn.Linear(self.intermediate_size // 2, self.hidden_size)
        )
    
    def _build_computation_expert(self):
        """Build expert specialized for high-precision computation."""
        self.layers = nn.Sequential(
            nn.Linear(self.hidden_size, self.intermediate_size * 2),
            nn.LayerNorm(self.intermediate_size * 2),
            nn.ReLU(),
            nn.Dropout(self.dropout),
            nn.Linear(self.intermediate_size * 2, self.intermediate_size),
            nn.LayerNorm(self.intermediate_size),
            nn.ReLU(),
            nn.Dropout(self.dropout),
            nn.Linear(self.intermediate_size, self.hidden_size)
        )
    
    def _build_mathematical_expert(self):
        """Build expert specialized for mathematical operations."""
        self.layers = nn.Sequential(
            nn.Linear(self.hidden_size, self.intermediate_size),
            nn.LayerNorm(self.intermediate_size),
            nn.SiLU(),  # Swish activation for mathematical tasks
            nn.Dropout(self.dropout),
            nn.Linear(self.intermediate_size, self.hidden_size)
        )
    
    def _build_logical_expert(self):
        """Build expert specialized for logical reasoning."""
        self.layers = nn.Sequential(
            nn.Linear(self.hidden_size, self.intermediate_size),
            nn.LayerNorm(self.intermediate_size),
            nn.Tanh(),
            nn.Dropout(self.dropout),
            nn.Linear(self.intermediate_size, self.hidden_size)
        )
    
    def _build_general_expert(self):
        """Build general-purpose expert."""
        self.layers = nn.Sequential(
            nn.Linear(self.hidden_size, self.intermediate_size),
            nn.LayerNorm(self.intermediate_size),
            nn.GELU(),
            nn.Dropout(self.dropout),
            nn.Linear(self.intermediate_size, self.hidden_size)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the expert."""
        return self.layers(x)

class PiMoESystem(nn.Module):
    """
    Complete PiMoE system integrating token-level routing with expert networks.
    """
    
    def __init__(
        self,
        hidden_size: int,
        num_experts: int,
        expert_types: List[ExpertType],
        router_config: Optional[Dict[str, Any]] = None,
        expert_config: Optional[Dict[str, Any]] = None
    ):
        super().__init__()
        
        self.hidden_size = hidden_size
        self.num_experts = num_experts
        self.expert_types = expert_types
        
        # Initialize router
        router_config = router_config or {}
        self.router = TokenLevelRouter(
            hidden_size=hidden_size,
            num_experts=num_experts,
            expert_types=expert_types,
            **router_config
        )
        
        # Initialize expert networks
        expert_config = expert_config or {}
        self.experts = nn.ModuleList([
            PiMoEExpert(
                hidden_size=hidden_size,
                expert_type=expert_types[i % len(expert_types)],
                **expert_config
            )
            for i in range(num_experts)
        ])
        
        # Expert capacity management
        self.expert_capacity = int(hidden_size * 1.25)  # 25% buffer
        
    def forward(
        self, 
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        return_routing_info: bool = False
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, Dict[str, Any]]]:
        """
        Forward pass through the PiMoE system.
        """
        batch_size, seq_len, hidden_size = hidden_states.shape
        
        # Get routing decisions
        if return_routing_info:
            routed_hidden, routing_info = self.router(
                hidden_states, 
                attention_mask, 
                return_routing_info=True
            )
        else:
            routed_hidden = self.router(hidden_states, attention_mask)
            routing_info = None
        
        # Apply expert processing
        expert_outputs = self._apply_expert_processing(
            routed_hidden, 
            routing_info['routing_decisions'] if routing_info else None
        )
        
        if return_routing_info:
            routing_info['expert_outputs'] = expert_outputs
            return expert_outputs, routing_info
        
        return expert_outputs
    
    def _apply_expert_processing(
        self, 
        hidden_states: torch.Tensor, 
        routing_decisions: Optional[List[RoutingDecision]]
    ) -> torch.Tensor:
        """Apply expert processing based on routing decisions."""
        if routing_decisions is None:
            # Fallback to uniform processing
            return self._uniform_expert_processing(hidden_states)
        
        batch_size, seq_len, hidden_size = hidden_states.shape
        flat_hidden = hidden_states.view(-1, hidden_size)
        
        # Process each token through its assigned expert
        expert_outputs = []
        for i, decision in enumerate(routing_decisions):
            expert_id = decision.expert_id
            expert_output = self.experts[expert_id](flat_hidden[i:i+1])
            expert_outputs.append(expert_output)
        
        # Stack outputs
        expert_output = torch.cat(expert_outputs, dim=0)
        expert_output = expert_output.view(batch_size, seq_len, hidden_size)
        
        return expert_output
    
    def _uniform_expert_processing(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """Fallback uniform processing when routing decisions are not available."""
        # Use the first expert for all tokens
        batch_size, seq_len, hidden_size = hidden_states.shape
        flat_hidden = hidden_states.view(-1, hidden_size)
        
        expert_output = self.experts[0](flat_hidden)
        expert_output = expert_output.view(batch_size, seq_len, hidden_size)
        
        return expert_output
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        router_stats = self.router.get_expert_usage_stats()
        
        return {
            'router_stats': router_stats,
            'num_experts': self.num_experts,
            'expert_types': [et.value for et in self.expert_types],
            'expert_capacity': self.expert_capacity,
            'system_efficiency': self._calculate_system_efficiency()
        }
    
    def _calculate_system_efficiency(self) -> float:
        """Calculate overall system efficiency."""
        router_stats = self.router.get_expert_usage_stats()
        load_balance_ratio = router_stats['load_balance_ratio']
        
        # Factor in expert utilization
        expert_utilization = min(1.0, router_stats['total_usage'] / (self.num_experts * 100))
        
        # Combined efficiency metric
        efficiency = (load_balance_ratio * 0.7 + expert_utilization * 0.3)
        
        return efficiency

def create_pimoe_system(
    hidden_size: int,
    num_experts: int = 8,
    expert_types: Optional[List[ExpertType]] = None,
    router_config: Optional[Dict[str, Any]] = None,
    expert_config: Optional[Dict[str, Any]] = None
) -> PiMoESystem:
    """
    Factory function to create a PiMoE system with default configurations.
    """
    if expert_types is None:
        expert_types = [
            ExpertType.REASONING,
            ExpertType.COMPUTATION,
            ExpertType.MATHEMATICAL,
            ExpertType.LOGICAL,
            ExpertType.LANGUAGE,
            ExpertType.CREATIVE,
            ExpertType.ANALYTICAL
        ]
    
    return PiMoESystem(
        hidden_size=hidden_size,
        num_experts=num_experts,
        expert_types=expert_types,
        router_config=router_config,
        expert_config=expert_config
    )




