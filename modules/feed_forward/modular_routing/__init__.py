"""
Modular Routing System
Specialized routing modules for different routing strategies and algorithms.
"""

from .base_router import BaseRouter, RouterConfig, RoutingResult, RoutingStrategy, ExpertType

try:
    from .attention_router import AttentionRouter, AttentionRouterConfig
except ImportError:
    AttentionRouter = None
    AttentionRouterConfig = None

try:
    from .hierarchical_router import HierarchicalRouter, HierarchicalRouterConfig
except ImportError:
    HierarchicalRouter = None
    HierarchicalRouterConfig = None

try:
    from .neural_router import NeuralRouter, NeuralRouterConfig
except ImportError:
    NeuralRouter = None
    NeuralRouterConfig = None

try:
    from .adaptive_router import AdaptiveRouter, AdaptiveRouterConfig
except ImportError:
    AdaptiveRouter = None
    AdaptiveRouterConfig = None

try:
    from .load_balancing_router import LoadBalancingRouter, LoadBalancingRouterConfig
except ImportError:
    LoadBalancingRouter = None
    LoadBalancingRouterConfig = None

class RouterFactory:
    pass

def create_router(*args, **kwargs):
    pass

class RouterRegistry:
    pass

def register_router(*args, **kwargs):
    pass

def get_router(*args, **kwargs):
    pass


__all__ = [
    'BaseRouter',
    'RouterConfig', 
    'RoutingResult',
    'RoutingStrategy',
    'ExpertType',
    'AttentionRouter',
    'AttentionRouterConfig',
    'HierarchicalRouter',
    'HierarchicalRouterConfig',
    'NeuralRouter',
    'NeuralRouterConfig',
    'AdaptiveRouter',
    'AdaptiveRouterConfig',
    'LoadBalancingRouter',
    'LoadBalancingRouterConfig',
    'RouterFactory',
    'create_router',
    'RouterRegistry',
    'register_router',
    'get_router',
]

