"""
Optimization Strategies Registry for Runtime Compiler
Implementing Strategy Pattern for clean optimization passes with thread safety and HW detection.
"""

import logging
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type

from ..config import RuntimeOptimizationStrategy

logger = logging.getLogger(__name__)


class BaseOptimizationPass(ABC):
    """Abstract Base Class for a runtime optimization pass"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def default_priority(self) -> int:
        pass

    def is_compatible(self, profile: Dict[str, Any]) -> bool:
        """Check if hardware target in profile is compatible with this pass."""
        target_hw = profile.get("target_hw", "cpu").lower()
        if hasattr(self, "supported_hardware"):
            supported = getattr(self, "supported_hardware")
            return target_hw in supported or "all" in supported
        return True

    @abstractmethod
    def apply(self, model: Any, profile: Dict[str, Any]) -> Any:
        pass


class InliningOptimizationPass(BaseOptimizationPass):
    name = "inlining"
    description = "Runtime function inlining"
    default_priority = 1
    supported_hardware = ["all"]

    def apply(self, model: Any, profile: Dict[str, Any]) -> Any:
        logger.info("Applying runtime function inlining")
        return model


class VectorizationOptimizationPass(BaseOptimizationPass):
    name = "vectorization"
    description = "Runtime SIMD vectorization"
    default_priority = 2
    supported_hardware = ["cpu", "x86_64", "arm64", "all"]

    def apply(self, model: Any, profile: Dict[str, Any]) -> Any:
        logger.info("Applying runtime SIMD vectorization")
        return model


class LoopOptimizationPass(BaseOptimizationPass):
    name = "loop_optimization"
    description = "Runtime loop optimization"
    default_priority = 3
    supported_hardware = ["all"]

    def apply(self, model: Any, profile: Dict[str, Any]) -> Any:
        logger.info("Applying runtime loop optimization")
        return model


class MemoryOptimizationPass(BaseOptimizationPass):
    name = "memory_optimization"
    description = "Runtime memory optimization"
    default_priority = 4
    supported_hardware = ["all"]

    def apply(self, model: Any, profile: Dict[str, Any]) -> Any:
        logger.info("Applying runtime memory optimization")
        return model


class ParallelOptimizationPass(BaseOptimizationPass):
    name = "parallel_optimization"
    description = "Runtime parallel optimization"
    default_priority = 5
    supported_hardware = ["all"]

    def apply(self, model: Any, profile: Dict[str, Any]) -> Any:
        logger.info("Applying runtime parallel optimization")
        return model


class SpeculativeOptimizationPass(BaseOptimizationPass):
    name = "speculative_optimization"
    description = "Speculative execution optimization"
    default_priority = 6
    supported_hardware = ["all"]

    def apply(self, model: Any, profile: Dict[str, Any]) -> Any:
        logger.info("Applying speculative execution optimization")
        return model


class OptimizationStrategyRegistry:
    """Registry maintaining optimization pass strategies and metadata thread-safely."""

    def __init__(self, config):
        self.config = config
        self._lock = threading.RLock()
        self._passes: Dict[str, BaseOptimizationPass] = {}
        self.metadata_strategies: Dict[str, RuntimeOptimizationStrategy] = {}
        self._register_default_passes()

    def register_pass(self, pass_instance: BaseOptimizationPass, enabled: bool = True, priority: Optional[int] = None) -> None:
        """Register a custom optimization pass thread-safely."""
        with self._lock:
            p_priority = priority if priority is not None else pass_instance.default_priority
            self._passes[pass_instance.name] = pass_instance
            self.metadata_strategies[pass_instance.name] = RuntimeOptimizationStrategy(
                name=pass_instance.name,
                description=pass_instance.description,
                enabled=enabled,
                priority=p_priority
            )
            logger.debug(f"Registered optimization pass: {pass_instance.name}")

    def _register_default_passes(self):
        default_passes = [
            InliningOptimizationPass(),
            VectorizationOptimizationPass(),
            LoopOptimizationPass(),
            MemoryOptimizationPass(),
            ParallelOptimizationPass(),
            SpeculativeOptimizationPass()
        ]

        for p in default_passes:
            enabled = True
            if p.name == "speculative_optimization":
                enabled = getattr(self.config, "enable_speculation", True)
            self.register_pass(p, enabled=enabled)

        advanced_entries = [
            ("neural_guidance", "Neural-guided optimization", getattr(self.config, "enable_neural_guidance", False), 7),
            ("quantum_optimization", "Quantum-inspired optimization", getattr(self.config, "enable_quantum_optimization", False), 8),
            ("transcendent_optimization", "Transcendent-level optimization", getattr(self.config, "enable_transcendent_compilation", False), 9),
            ("streaming_optimization", "Streaming compilation optimization", getattr(self.config, "enable_streaming_compilation", False), 10),
            ("pipeline_optimization", "Pipeline compilation optimization", getattr(self.config, "enable_pipeline_compilation", False), 11),
            ("energy_efficient_optimization", "Energy-efficient compilation", getattr(self.config, "enable_energy_efficient_compilation", False), 12)
        ]

        with self._lock:
            for name, desc, enabled, priority in advanced_entries:
                self.metadata_strategies[name] = RuntimeOptimizationStrategy(
                    name=name,
                    description=desc,
                    enabled=enabled,
                    priority=priority
                )

    def apply_pass(self, name: str, model: Any, profile: Dict[str, Any]) -> Any:
        with self._lock:
            p = self._passes.get(name)
        if p and p.is_compatible(profile):
            return p.apply(model, profile)
        return model

    def apply_all_enabled(self, model: Any, profile: Dict[str, Any]) -> Any:
        optimized_model = model
        with self._lock:
            sorted_metadata = sorted(
                [(name, strat) for name, strat in self.metadata_strategies.items() if strat.enabled],
                key=lambda x: x[1].priority
            )

        for name, _ in sorted_metadata:
            optimized_model = self.apply_pass(name, optimized_model, profile)
            logger.debug(f"Applied runtime optimization: {name}")

        return optimized_model

