"""
Backward-compatibility shims for the deleted *_optimization_core modules.

Each shim wraps :class:`UnifiedTruthGPTOptimizer` at the corresponding
:class:`OptimizationLevel`. Prefer using ``UnifiedTruthGPTOptimizer``
directly in new code.
"""
from .enhanced_optimization_core import (
    EnhancedOptimizationCore,
    EnhancedOptimizationConfig,
    create_enhanced_optimization_core,
)
from .hybrid_optimization_core import (
    HybridOptimizationCore,
    HybridOptimizationConfig,
    create_hybrid_optimization_core,
)
from .mega_enhanced_optimization_core import (
    MegaEnhancedOptimizationCore,
    MegaEnhancedOptimizationConfig,
    create_mega_enhanced_optimization_core,
)
from .supreme_optimization_core import (
    SupremeOptimizationCore,
    SupremeOptimizationConfig,
    create_supreme_optimization_core,
)
from .transcendent_optimization_core import (
    TranscendentOptimizationCore,
    TranscendentOptimizationConfig,
    create_transcendent_optimization_core,
)
from .ultra_enhanced_optimization_core import (
    UltraEnhancedOptimizationCore,
    UltraEnhancedOptimizationConfig,
    create_ultra_enhanced_optimization_core,
)
from .ultra_fast_optimization_core import (
    UltraFastOptimizationCore,
    UltraFastOptimizationConfig,
    create_ultra_fast_optimization_core,
)

__all__ = [
    "EnhancedOptimizationCore",
    "EnhancedOptimizationConfig",
    "create_enhanced_optimization_core",
    "HybridOptimizationCore",
    "HybridOptimizationConfig",
    "create_hybrid_optimization_core",
    "MegaEnhancedOptimizationCore",
    "MegaEnhancedOptimizationConfig",
    "create_mega_enhanced_optimization_core",
    "SupremeOptimizationCore",
    "SupremeOptimizationConfig",
    "create_supreme_optimization_core",
    "TranscendentOptimizationCore",
    "TranscendentOptimizationConfig",
    "create_transcendent_optimization_core",
    "UltraEnhancedOptimizationCore",
    "UltraEnhancedOptimizationConfig",
    "create_ultra_enhanced_optimization_core",
    "UltraFastOptimizationCore",
    "UltraFastOptimizationConfig",
    "create_ultra_fast_optimization_core",
]
