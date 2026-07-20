"""
Feed Forward Demos
==================
Unified exports for all feed forward demos and examples.
"""

# Import all demo files
from ..pimoe_demo import (
    PiMoEDemo,
    DemoConfig,
    run_pimoe_demo,
)

from ..advanced_pimoe_demo import (
    AdvancedPiMoEDemo,
    run_advanced_pimoe_demo as _run_advanced_pimoe_demo,
)

from ..enhanced_ai_demo import (
    EnhancedAIDemo,
    run_enhanced_ai_demo as _run_enhanced_ai_demo,
)

from ..modular_demo import (
    ModularDemo,
    run_modular_demo as _run_modular_demo,
)

from ..refactored_demo import (
    RefactoredSystemDemo,
    run_refactored_demo,
)

from ..production_demo import (
    ProductionDemo,
)

from ..ultra_optimization_demo import (
    UltraOptimizationDemo,
    run_ultra_optimization_demo as _run_ultra_optimization_demo,
)

try:
    from ..next_generation_ai.next_gen_ai_demo import (
        NextGenAIDemo,
    )
except ImportError:
    NextGenAIDemo = None

try:
    from ..ultra_optimization.hyper_speed_demo import (
        HyperSpeedDemo,
    )
except ImportError:
    HyperSpeedDemo = None

from ..pimoe_integration_example import (
    TruthGPTPiMoEIntegration,
)

# Re-export run functions
run_advanced_pimoe_demo = _run_advanced_pimoe_demo
run_enhanced_ai_demo = _run_enhanced_ai_demo
run_modular_demo = _run_modular_demo
run_ultra_optimization_demo = _run_ultra_optimization_demo

def run_production_demo(config=None):
    """Run production demo."""
    demo = ProductionDemo()
    return demo.run_complete_demo()

def run_next_gen_ai_demo(config=None):
    """Run next gen AI demo."""
    if NextGenAIDemo is None:
        raise ImportError("NextGenAIDemo not available")
    demo = NextGenAIDemo()
    return demo.run_next_gen_ai_demo()

def run_hyper_speed_demo(config=None):
    """Run hyper speed demo."""
    if HyperSpeedDemo is None:
        raise ImportError("HyperSpeedDemo not available")
    demo = HyperSpeedDemo()
    return demo.run_hyper_speed_demo()

def run_pimoe_integration_example(config=None):
    """Run PiMoE integration example."""
    if config is None:
        config = {}
    example = TruthGPTPiMoEIntegration(config)
    # Run the integration example
    return example.run_complete_integration()

# Alias for consistency
PiMoEIntegrationExample = TruthGPTPiMoEIntegration


# Unified demo factory
def create_demo(demo_type: str = "pimoe", config: dict = None):
    """
    Unified factory function to create demos.
    
    Args:
        demo_type: Type of demo to create. Options:
            - "pimoe" - PiMoEDemo
            - "advanced_pimoe" - AdvancedPiMoEDemo
            - "enhanced_ai" - EnhancedAIDemo
            - "modular" - ModularDemo
            - "refactored" - RefactoredSystemDemo
            - "production" - ProductionDemo
            - "ultra_optimization" - UltraOptimizationDemo
            - "next_gen_ai" - NextGenAIDemo
            - "hyper_speed" - HyperSpeedDemo
            - "integration" - PiMoEIntegrationExample
        config: Optional configuration dictionary
    
    Returns:
        The requested demo instance
    """
    if config is None:
        config = {}
    
    demo_type = demo_type.lower()
    
    factory_map = {
        "pimoe": lambda cfg: PiMoEDemo(cfg),
        "advanced_pimoe": lambda cfg: AdvancedPiMoEDemo(cfg),
        "enhanced_ai": lambda cfg: EnhancedAIDemo(cfg),
        "modular": lambda cfg: ModularDemo(cfg),
        "refactored": lambda cfg: RefactoredSystemDemo(cfg),
        "production": lambda cfg: ProductionDemo(),
        "ultra_optimization": lambda cfg: UltraOptimizationDemo(cfg),
        "next_gen_ai": lambda cfg: NextGenAIDemo(cfg),
        "hyper_speed": lambda cfg: HyperSpeedDemo(cfg),
        "integration": lambda cfg: TruthGPTPiMoEIntegration(cfg),
    }
    
    if demo_type not in factory_map:
        available = ", ".join(factory_map.keys())
        raise ValueError(
            f"Unknown demo type: '{demo_type}'. "
            f"Available types: {available}"
        )
    
    factory = factory_map[demo_type]
    return factory(config)


# Registry of all available demos
DEMO_REGISTRY = {
    "pimoe": {
        "class": PiMoEDemo,
        "module": "modules.feed_forward.pimoe_demo",
        "description": "PiMoE token-level routing demo",
    },
    "advanced_pimoe": {
        "class": AdvancedPiMoEDemo,
        "module": "modules.feed_forward.advanced_pimoe_demo",
        "description": "Advanced PiMoE routing demo",
    },
    "enhanced_ai": {
        "class": EnhancedAIDemo,
        "module": "modules.feed_forward.enhanced_ai_demo",
        "description": "Enhanced AI demo",
    },
    "modular": {
        "class": ModularDemo,
        "module": "modules.feed_forward.modular_demo",
        "description": "Modular system demo",
    },
    "refactored": {
        "class": RefactoredSystemDemo,
        "module": "modules.feed_forward.refactored_demo",
        "description": "Refactored system demo",
    },
    "production": {
        "class": ProductionDemo,
        "module": "modules.feed_forward.production_demo",
        "description": "Production system demo",
    },
    "ultra_optimization": {
        "class": UltraOptimizationDemo,
        "module": "modules.feed_forward.ultra_optimization_demo",
        "description": "Ultra optimization demo",
    },
    "next_gen_ai": {
        "class": NextGenAIDemo,
        "module": "modules.feed_forward.next_generation_ai.next_gen_ai_demo",
        "description": "Next generation AI demo",
    },
    "hyper_speed": {
        "class": HyperSpeedDemo,
        "module": "modules.feed_forward.ultra_optimization.hyper_speed_demo",
        "description": "Hyper speed optimization demo",
    },
    "integration": {
        "class": TruthGPTPiMoEIntegration,
        "module": "modules.feed_forward.pimoe_integration_example",
        "description": "PiMoE integration example",
    },
}


def list_available_demos() -> list:
    """List all available demo types."""
    return list(DEMO_REGISTRY.keys())


def get_demo_info(demo_type: str) -> dict:
    """
    Get information about a specific demo.
    
    Args:
        demo_type: Type of demo
    
    Returns:
        Dictionary with demo information
    """
    if demo_type not in DEMO_REGISTRY:
        raise ValueError(f"Unknown demo type: {demo_type}")
    
    registry_entry = DEMO_REGISTRY[demo_type]
    return {
        "type": demo_type,
        "class": registry_entry["class"].__name__,
        "module": registry_entry["module"],
        "description": registry_entry["description"],
    }


__all__ = [
    # Demos
    "PiMoEDemo",
    "DemoConfig",
    "run_pimoe_demo",
    "AdvancedPiMoEDemo",
    "run_advanced_pimoe_demo",
    "EnhancedAIDemo",
    "run_enhanced_ai_demo",
    "ModularDemo",
    "run_modular_demo",
    "RefactoredSystemDemo",
    "run_refactored_demo",
    "ProductionDemo",
    "run_production_demo",
    "UltraOptimizationDemo",
    "run_ultra_optimization_demo",
    "NextGenAIDemo",
    "run_next_gen_ai_demo",
    "HyperSpeedDemo",
    "run_hyper_speed_demo",
    "TruthGPTPiMoEIntegration",
    "PiMoEIntegrationExample",
    "run_pimoe_integration_example",
    # Unified factory
    "create_demo",
    # Registry
    "DEMO_REGISTRY",
    "list_available_demos",
    "get_demo_info",
]

