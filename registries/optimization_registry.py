"""
Optimization Registry Integration Module
Consolidates standard, advanced v1, and advanced v2 optimization registries.
"""

try:
    from utils.optimization_registry import (
        OptimizationRegistry,
        OptimizationConfig,
        apply_optimizations,
        get_optimization_config,
        register_optimization,
        get_optimization_report,
    )
except Exception:
    try:
        from optimization_core.utils.optimization_registry import (
            OptimizationRegistry,
            OptimizationConfig,
            apply_optimizations,
            get_optimization_config,
            register_optimization,
            get_optimization_report,
        )
    except Exception:
        OptimizationRegistry = None
        OptimizationConfig = None
        apply_optimizations = None
        get_optimization_config = None
        register_optimization = None
        get_optimization_report = None

try:
    from optimizers.advanced_optimization_registry import (
        AdvancedOptimizationConfig,
        get_advanced_optimization_config,
        apply_advanced_optimizations,
        get_advanced_optimization_report,
    )
except Exception:
    try:
        from optimization_core.optimizers.advanced_optimization_registry import (
            AdvancedOptimizationConfig,
            get_advanced_optimization_config,
            apply_advanced_optimizations,
            get_advanced_optimization_report,
        )
    except Exception:
        AdvancedOptimizationConfig = None
        get_advanced_optimization_config = None
        apply_advanced_optimizations = None
        get_advanced_optimization_report = None

get_advanced_optimizations = get_advanced_optimization_config

try:
    from optimizers.advanced_optimization_registry_v2 import (
        AdvancedOptimizationConfig as AdvancedOptimizationConfigV2,
        get_advanced_optimization_config as get_advanced_optimization_config_v2,
        apply_advanced_optimizations as apply_advanced_optimizations_v2,
        get_advanced_optimization_report as get_advanced_optimization_report_v2,
    )
except Exception:
    try:
        from optimization_core.optimizers.advanced_optimization_registry_v2 import (
            AdvancedOptimizationConfig as AdvancedOptimizationConfigV2,
            get_advanced_optimization_config as get_advanced_optimization_config_v2,
            apply_advanced_optimizations as apply_advanced_optimizations_v2,
            get_advanced_optimization_report as get_advanced_optimization_report_v2,
        )
    except Exception:
        AdvancedOptimizationConfigV2 = None
        get_advanced_optimization_config_v2 = None
        apply_advanced_optimizations_v2 = None
        get_advanced_optimization_report_v2 = None

try:
    from commit_tracker.optimization_registry import (
        OptimizationRegistry as CommitTrackerOptimizationRegistry,
    )
except Exception:
    try:
        from optimization_core.commit_tracker.optimization_registry import (
            OptimizationRegistry as CommitTrackerOptimizationRegistry,
        )
    except Exception:
        CommitTrackerOptimizationRegistry = None

__all__ = [
    "OptimizationRegistry",
    "OptimizationConfig",
    "apply_optimizations",
    "get_optimization_config",
    "register_optimization",
    "get_optimization_report",
    "AdvancedOptimizationConfig",
    "get_advanced_optimization_config",
    "get_advanced_optimizations",
    "apply_advanced_optimizations",
    "get_advanced_optimization_report",
    "AdvancedOptimizationConfigV2",
    "get_advanced_optimization_config_v2",
    "apply_advanced_optimizations_v2",
    "get_advanced_optimization_report_v2",
    "CommitTrackerOptimizationRegistry",
]
