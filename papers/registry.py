"""
Central Registry and Dynamic Factory for TruthGPT Research Paper Implementations.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any, Dict, List, Optional, Type, Union

from .base import BasePaperModule, PaperCategory, PaperMetadata, PaperResult
from .exceptions import PaperNotFoundError
from .interfaces import PaperRegistryInterface

logger = logging.getLogger(__name__)


class PaperRegistry(PaperRegistryInterface):
    """
    Catalog and dynamic factory for all 18 research paper implementation modules.
    """

    def __init__(self) -> None:
        self._papers: Dict[str, PaperMetadata] = {}
        self._classes: Dict[str, Type[BasePaperModule]] = {}
        self._config_classes: Dict[str, Type[Any]] = {}
        self._instances: Dict[str, BasePaperModule] = {}
        self._initialize_catalog()

    def _initialize_catalog(self) -> None:
        """Register all 18 SOTA research paper modules."""
        # 1. FP16 Stability
        from .fp16_stability import FP16Stability
        from .config import FP16StabilityConfig
        self.register(
            metadata=FP16Stability.get_metadata(),
            module_class=FP16Stability,
            config_class=FP16StabilityConfig,
        )

        # 2. Elastic Reasoning
        from .elastic_reasoning import ElasticReasoning
        from .config import ElasticReasoningConfig
        self.register(
            metadata=ElasticReasoning.get_metadata(),
            module_class=ElasticReasoning,
            config_class=ElasticReasoningConfig,
        )

        # 3. Chain of Draft
        from .chain_of_draft import ChainOfDraft
        from .config import ChainOfDraftConfig
        self.register(
            metadata=ChainOfDraft.get_metadata(),
            module_class=ChainOfDraft,
            config_class=ChainOfDraftConfig,
        )

        # 4. SnapKV
        from .snap_kv import SnapKVCacheCompressor
        from .config import SnapKVConfig
        self.register(
            metadata=SnapKVCacheCompressor.get_metadata(),
            module_class=SnapKVCacheCompressor,
            config_class=SnapKVConfig,
        )

        # 5. Speculative Decoding
        from .speculative_decoding import SpeculativeDrafter
        from .config import SpeculativeDecodingConfig
        self.register(
            metadata=SpeculativeDrafter.get_metadata(),
            module_class=SpeculativeDrafter,
            config_class=SpeculativeDecodingConfig,
        )

        # 6. Entropy-Guided Inference
        from .entropy_guided_inference import EntropyGuidedInference
        from .config import EntropyGuidedConfig
        self.register(
            metadata=EntropyGuidedInference.get_metadata(),
            module_class=EntropyGuidedInference,
            config_class=EntropyGuidedConfig,
        )

        # 7. Distinct Leaf Decoding
        from .distinct_leaf_decoding import DistinctLeafEnumerator
        from .config import DistinctLeafConfig
        self.register(
            metadata=DistinctLeafEnumerator.get_metadata(),
            module_class=DistinctLeafEnumerator,
            config_class=DistinctLeafConfig,
        )

        # 8. Discriminative Verification
        from .discriminative_verification import DiscriminativeVerifier
        from .config import DiscriminativeVerifierConfig
        self.register(
            metadata=DiscriminativeVerifier.get_metadata(),
            module_class=DiscriminativeVerifier,
            config_class=DiscriminativeVerifierConfig,
        )

        # 9. Adaptive KV Quantization
        from .adaptive_kv_quant import AdaptiveKVQuantizer
        from .config import AdaptiveKVQuantConfig
        self.register(
            metadata=AdaptiveKVQuantizer.get_metadata(),
            module_class=AdaptiveKVQuantizer,
            config_class=AdaptiveKVQuantConfig,
        )

        # 10. MoQAE Quantization
        from .moqae_quant import MoQAEQuantizer
        from .config import MoQAEConfig
        self.register(
            metadata=MoQAEQuantizer.get_metadata(),
            module_class=MoQAEQuantizer,
            config_class=MoQAEConfig,
        )

        # 11. ConfSpec Reasoning
        from .confspec_reasoning import ConfSpecReasoner
        from .config import ConfSpecConfig
        self.register(
            metadata=ConfSpecReasoner.get_metadata(),
            module_class=ConfSpecReasoner,
            config_class=ConfSpecConfig,
        )

        # 12. Speculative Prefill
        from .speculative_prefill import SpeculativePrefillCompressor
        from .config import SpeculativePrefillConfig
        self.register(
            metadata=SpeculativePrefillCompressor.get_metadata(),
            module_class=SpeculativePrefillCompressor,
            config_class=SpeculativePrefillConfig,
        )

        # 13. INTUITOR Self-Certainty
        from .intuitor_self_certainty import IntuitorReward
        from .config import IntuitorConfig
        self.register(
            metadata=IntuitorReward.get_metadata(),
            module_class=IntuitorReward,
            config_class=IntuitorConfig,
        )

        # 14. ECHO TTRL
        from .echo_ttrl import EchoOptimizer
        from .config import EchoOptimizerConfig
        self.register(
            metadata=EchoOptimizer.get_metadata(),
            module_class=EchoOptimizer,
            config_class=EchoOptimizerConfig,
        )

        # 15. Reinforced Attention
        from .reinforced_attention import ReinforcedAttentionLearner
        from .config import ReinforcedAttentionConfig
        self.register(
            metadata=ReinforcedAttentionLearner.get_metadata(),
            module_class=ReinforcedAttentionLearner,
            config_class=ReinforcedAttentionConfig,
        )

        # 16. Progressive Thought Encoding
        from .progressive_thought_encoding import ProgressiveThoughtEncoder
        from .config import ProgressiveThoughtConfig
        self.register(
            metadata=ProgressiveThoughtEncoder.get_metadata(),
            module_class=ProgressiveThoughtEncoder,
            config_class=ProgressiveThoughtConfig,
        )

        # 17. Dynamic Topology Routing
        from .dynamic_topology_routing import DynamicTopologyRouter
        from .config import DynamicTopologyConfig
        self.register(
            metadata=DynamicTopologyRouter.get_metadata(),
            module_class=DynamicTopologyRouter,
            config_class=DynamicTopologyConfig,
        )

        # 18. Atomic Agentic Memory
        from .atomic_agentic_memory import AtomicAgenticMemory
        from .config import AtomicMemoryConfig
        self.register(
            metadata=AtomicAgenticMemory.get_metadata(),
            module_class=AtomicAgenticMemory,
            config_class=AtomicMemoryConfig,
        )

    def register(
        self,
        metadata: PaperMetadata,
        module_class: Type[BasePaperModule],
        config_class: Optional[Type[Any]] = None,
    ) -> None:
        """Register a paper module class and its metadata."""
        pid = metadata.paper_id.lower()
        self._papers[pid] = metadata
        self._classes[pid] = module_class
        if config_class:
            self._config_classes[pid] = config_class

    def register_paper(
        self,
        metadata: PaperMetadata,
        module_name: str,
        class_name: str,
        config_class_name: Optional[str] = None,
    ) -> None:
        """Legacy helper for registering paper metadata by module/class name."""
        pid = metadata.paper_id.lower()
        self._papers[pid] = metadata
        self._papers[module_name.lower()] = metadata

    def list_papers(self, category: Optional[Union[str, PaperCategory]] = None) -> List[PaperMetadata]:
        """List distinct paper metadata, optionally filtered by category."""
        unique: Dict[str, PaperMetadata] = {p.paper_id: p for p in self._papers.values()}
        if category:
            cat_val = category.value if isinstance(category, PaperCategory) else str(category).lower().strip()
            return [
                p for p in unique.values()
                if (p.category.value == cat_val or p.category.name.lower() == cat_val or str(p.category).lower() == cat_val)
            ]
        return list(unique.values())

    def list_ids(self) -> List[str]:
        """List all unique registered paper identifiers."""
        unique_ids = sorted(list({p.paper_id for p in self._papers.values()}))
        return unique_ids

    def get_paper(self, paper_id: str) -> Optional[Type[BasePaperModule]]:
        """Retrieve the paper implementation class by paper identifier."""
        pid = paper_id.lower().replace("-", "_").strip()
        if pid in self._classes:
            return self._classes[pid]
        # Resolve by class name
        for cls in self._classes.values():
            if cls.__name__.lower() == pid:
                return cls
        return None

    def get_metadata(self, paper_id: str) -> Optional[PaperMetadata]:
        """Retrieve paper metadata by identifier."""
        pid = paper_id.lower().replace("-", "_").strip()
        if pid in self._papers:
            return self._papers[pid]
        cls = self.get_paper(pid)
        if cls:
            return cls.get_metadata()
        return None

    def get_module(self, paper_id: str, **kwargs: Any) -> BasePaperModule:
        """Get or create singleton instance of an algorithm module."""
        pid = paper_id.lower().replace("-", "_").strip()
        if not kwargs and pid in self._instances:
            return self._instances[pid]
        instance = self.create_algorithm(pid, **kwargs)
        if not kwargs:
            self._instances[pid] = instance
        return instance

    def create_algorithm(self, paper_id: str, **kwargs: Any) -> BasePaperModule:
        """Instantiate an algorithm implementation for the given paper ID."""
        pid = paper_id.lower().replace("-", "_").strip()
        cls = self.get_paper(pid)
        if cls is not None:
            return cls(**kwargs)

        # Fallback to dynamic module loading
        clean_id = pid.replace(".", "_")
        try:
            mod = importlib.import_module(f"papers.{clean_id}")
        except ImportError:
            try:
                mod = importlib.import_module(f"optimization_core.papers.{clean_id}")
            except ImportError:
                raise PaperNotFoundError(f"Paper '{paper_id}' not found in registry.")

        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BasePaperModule)
                and attr not in (BasePaperModule, type)
                and not attr_name.endswith("Config")
            ):
                return attr(**kwargs)

        raise PaperNotFoundError(f"No executable algorithm class found for paper '{paper_id}'.")

    def search_papers(
        self,
        query: Optional[str] = None,
        category: Optional[Union[str, PaperCategory]] = None,
        min_speedup: Optional[float] = None,
    ) -> List[PaperMetadata]:
        """Search papers by keyword query, category, or speedup factor."""
        results = self.list_papers(category=category)
        if query:
            q = query.lower().strip()
            results = [
                p for p in results
                if q in p.paper_id.lower()
                or q in p.paper_name.lower()
                or q in p.description.lower()
                or any(q in t.lower() for t in p.key_techniques)
                or any(q in a.lower() for a in p.authors)
            ]
        if min_speedup is not None:
            results = [p for p in results if (p.speedup or 1.0) >= min_speedup]
        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Return catalog overview statistics."""
        papers = self.list_papers()
        categories: Dict[str, int] = {}
        for p in papers:
            cat = p.category.value if isinstance(p.category, PaperCategory) else str(p.category)
            categories[cat] = categories.get(cat, 0) + 1

        avg_speedup = round(sum((p.speedup or 1.0) for p in papers) / len(papers), 2) if papers else 0.0
        return {
            "total_papers": len(papers),
            "categories": categories,
            "avg_speedup": avg_speedup,
            "registered_classes": len(self._classes),
        }

    def run_paper(self, paper_id: str, **kwargs: Any) -> PaperResult:
        """Dynamically execute a registered paper module with given kwargs."""
        module = self.get_module(paper_id)
        return module.execute(**kwargs)


# Global registry singleton
_registry_instance: Optional[PaperRegistry] = None


def get_paper_registry() -> PaperRegistry:
    """Return global PaperRegistry instance."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = PaperRegistry()
    return _registry_instance


# Top-level module helper functions
default_registry = get_paper_registry()


def get_paper(paper_id: str) -> Optional[Type[BasePaperModule]]:
    """Retrieve paper class by identifier."""
    return get_paper_registry().get_paper(paper_id)


def list_papers(category: Optional[Union[str, PaperCategory]] = None) -> List[PaperMetadata]:
    """List registered paper metadata."""
    return get_paper_registry().list_papers(category=category)


def list_ids() -> List[str]:
    """List all registered paper IDs."""
    return get_paper_registry().list_ids()


def get_module(paper_id: str, **kwargs: Any) -> BasePaperModule:
    """Get algorithm instance by paper identifier."""
    return get_paper_registry().get_module(paper_id, **kwargs)


def create_algorithm(paper_id: str, **kwargs: Any) -> BasePaperModule:
    """Create fresh algorithm instance by paper identifier."""
    return get_paper_registry().create_algorithm(paper_id, **kwargs)


def run_paper(paper_id: str, **kwargs: Any) -> PaperResult:
    """Dynamically run paper algorithm."""
    return get_paper_registry().run_paper(paper_id, **kwargs)


def register_paper(
    metadata: PaperMetadata,
    module_class_or_name: Union[Type[BasePaperModule], str],
    class_name: Optional[str] = None,
    config_class_name: Optional[str] = None,
) -> None:
    """Register paper into registry."""
    if isinstance(module_class_or_name, type) and issubclass(module_class_or_name, BasePaperModule):
        get_paper_registry().register(metadata, module_class_or_name)
    else:
        get_paper_registry().register_paper(
            metadata,
            str(module_class_or_name),
            str(class_name or ""),
            config_class_name,
        )


__all__ = [
    "PaperRegistry",
    "get_paper_registry",
    "default_registry",
    "get_paper",
    "list_papers",
    "list_ids",
    "get_module",
    "create_algorithm",
    "run_paper",
    "register_paper",
]
