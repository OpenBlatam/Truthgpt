"""
TruthGPT Modules Package
Modular components for TruthGPT optimization, compilation, and neural execution.
"""

from __future__ import annotations

import importlib
from typing import Any, Dict, List, Optional

# Core module names available in this directory
_AVAILABLE_MODULES: List[str] = [
    'advanced_caching',
    'advanced_compression',
    'advanced_integration',
    'advanced_integration_orchestration',
    'advanced_memory',
    'advanced_optimization_enhancements',
    'advanced_security',
    'agi_compiler',
    'ai_enhancement',
    'analytics',
    'attention',
    'augmentation',
    'autonomous_computing',
    'autonomous_evolution_compiler',
    'bio_inspired',
    'blockchain',
    'blockchain_web3',
    'caching',
    'compression',
    'config',
    'cosmic_evolution_compiler',
    'cosmic_multidimensional_compiler',
    'cosmic_optimization_system',
    'dashboard',
    'data',
    'dimensional_transcendence_compiler',
    'distributed',
    'distributed_compiler_integration',
    'distributed_computing',
    'divine_evolution_compiler',
    'divine_wisdom_compiler',
    'edge_computing',
    'edge_iot',
    'emotional_ai_compiler',
    'emotional_intelligence',
    'evaluation',
    'federated_learning',
    'federation',
    'hybrid_compiler_example',
    'hybrid_compiler_integration',
    'hyperparameter_optimization',
    'inference',
    'infinite_potential_compiler',
    'infinite_wisdom_compiler',
    'integration',
    'meta_cognitive_learning_compiler',
    'models',
    'monitoring',
    'multi_dimensional_learning',
    'multimodal_processing',
    'neural_architecture_search',
    'neural_compiler_integration',
    'omnipotent_compiler',
    'omniscient_intelligence_compiler',
    'optimizers',
    'orchestration',
    'quantum',
    'quantum_compiler_integration',
    'quantum_computing',
    'quantum_distributed_compiler',
    'quantum_energy_optimization_compiler',
    'quantum_integration',
    'quantum_neural_hybrid_compiler',
    'quantum_neural_networks_compiler',
    'quantum_singularity_compiler',
    'real_time_computing',
    'security',
    'self_evolution',
    'singularity_compiler',
    'streaming',
    'temporal_manipulation',
    'temporal_optimization_compiler',
    'testing',
    'training',
    'transcendent_compiler_integration',
    'transcendent_intelligence_compiler',
    'ultra_advanced_cognitive_computing',
    'ultra_generative_ai',
    'ultra_metaverse',
    'universal_harmony_compiler',
    'universal_transcendence_compiler',
]

_import_cache: Dict[str, Any] = {}


def __getattr__(name: str) -> Any:
    """Lazy import system for optimization modules."""
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    if name in _import_cache:
        return _import_cache[name]

    # Try direct submodule
    if name in _AVAILABLE_MODULES:
        try:
            module = importlib.import_module(f".{name}", package=__name__)
            _import_cache[name] = module
            return module
        except Exception as e:
            raise AttributeError(f"Failed to load module '{name}': {e}") from e

    # Try searching across internal submodules for class/function
    for mod_name in _AVAILABLE_MODULES:
        try:
            module = importlib.import_module(f".{mod_name}", package=__name__)
            if hasattr(module, name):
                val = getattr(module, name)
                _import_cache[name] = val
                return val
        except Exception:
            continue

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> List[str]:
    return sorted(list(globals().keys()) + _AVAILABLE_MODULES)


def list_available_modules() -> List[str]:
    """List all available modules in this directory."""
    return list(_AVAILABLE_MODULES)


def get_module_info(module_name: str) -> Dict[str, Any]:
    """Get metadata about a specific module."""
    if module_name not in _AVAILABLE_MODULES:
        raise ValueError(f"Unknown module: {module_name}")
    return {
        "name": module_name,
        "import_path": f"{__name__}.{module_name}",
        "package": __name__,
        "cached": module_name in _import_cache,
    }


__all__ = [
    "list_available_modules",
    "get_module_info",
] + _AVAILABLE_MODULES
