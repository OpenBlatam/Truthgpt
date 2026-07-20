"""
Advanced AI-Driven Routing System
Next-generation routing with reinforcement learning, quantum-inspired algorithms, and adaptive intelligence.
"""

from .reinforcement_router import ReinforcementRouter, ReinforcementRouterConfig
from .quantum_router import QuantumRouter, QuantumRouterConfig
from .federated_router import FederatedRouter, FederatedRouterConfig
from .neuromorphic_router import NeuromorphicRouter, NeuromorphicRouterConfig
from .multi_modal_router import MultiModalRouter, MultiModalRouterConfig
from .self_healing_router import SelfHealingRouter, SelfHealingRouterConfig
from .adaptive_intelligence_router import AdaptiveIntelligenceRouter, AdaptiveIntelligenceRouterConfig
from .blockchain_router import BlockchainRouter, BlockchainRouterConfig
from .edge_router import EdgeRouter, EdgeRouterConfig
from .ai_router_factory import AIRouterFactory, create_ai_router
from .ai_router_registry import AIRouterRegistry, register_ai_router, get_ai_router

__all__ = [
    # Reinforcement Learning Router
    'ReinforcementRouter',
    'ReinforcementRouterConfig',
    
    # Quantum-Inspired Router
    'QuantumRouter',
    'QuantumRouterConfig',
    
    # Federated Learning Router
    'FederatedRouter',
    'FederatedRouterConfig',
    
    # Neuromorphic Router
    'NeuromorphicRouter',
    'NeuromorphicRouterConfig',
    
    # Multi-Modal Router
    'MultiModalRouter',
    'MultiModalRouterConfig',
    
    # Self-Healing Router
    'SelfHealingRouter',
    'SelfHealingRouterConfig',
    
    # Adaptive Intelligence Router
    'AdaptiveIntelligenceRouter',
    'AdaptiveIntelligenceRouterConfig',
    
    # Blockchain Router
    'BlockchainRouter',
    'BlockchainRouterConfig',
    
    # Edge Router
    'EdgeRouter',
    'EdgeRouterConfig',
    
    # Factory and Registry
    'AIRouterFactory',
    'create_ai_router',
    'AIRouterRegistry',
    'register_ai_router',
    'get_ai_router'
]




