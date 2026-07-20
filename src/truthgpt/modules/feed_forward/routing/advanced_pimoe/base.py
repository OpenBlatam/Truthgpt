import enum
from dataclasses import dataclass
from typing import List

class RoutingStrategy(enum.Enum):
    """Advanced routing strategies."""
    ATTENTION_BASED = "attention_based"
    HIERARCHICAL = "hierarchical"
    DYNAMIC_SCALING = "dynamic_scaling"
    CROSS_EXPERT = "cross_expert"
    ADAPTIVE_LEARNING = "adaptive_learning"
    NEURAL_ARCHITECTURE_SEARCH = "neural_architecture_search"

@dataclass
class AdvancedRoutingConfig:
    """Configuration for advanced routing algorithms."""
    strategy: RoutingStrategy = RoutingStrategy.ATTENTION_BASED
    attention_heads: int = 8
    hierarchical_levels: int = 3
    dynamic_scaling_threshold: float = 0.8
    cross_expert_communication: bool = True
    adaptive_learning_rate: float = 0.01
    nas_search_space: int = 100
    temperature_schedule: str = "cosine"
    load_balance_alpha: float = 0.1
    expert_capacity_factor: float = 1.5
    routing_entropy_weight: float = 0.05
