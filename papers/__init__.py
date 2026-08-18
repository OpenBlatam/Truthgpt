"""
Research Papers Subsystem for TruthGPT Optimization Core.
Contains complete, exact implementations of all 18 state-of-the-art research papers.
"""

from .adaptive_kv_quant import AdaptiveKVQuantizer
from .atomic_agentic_memory import AtomicAgenticMemory
from .base import BasePaperModule, PaperCategory, PaperMetadata, PaperResult
from .benchmark import PaperBenchmarkSuite, run_benchmark
from .chain_of_draft import ChainOfDraft
from .config import (
    AdaptiveKVQuantConfig,
    AtomicMemoryConfig,
    BasePaperConfig,
    ChainOfDraftConfig,
    ConfSpecConfig,
    DiscriminativeVerifierConfig,
    DistinctLeafConfig,
    DynamicTopologyConfig,
    EchoOptimizerConfig,
    ElasticReasoningConfig,
    EntropyGuidedConfig,
    FP16StabilityConfig,
    IntuitorConfig,
    MoQAEConfig,
    ProgressiveThoughtConfig,
    ReinforcedAttentionConfig,
    SnapKVConfig,
    SpeculativeDecodingConfig,
    SpeculativePrefillConfig,
)
from .confspec_reasoning import ConfSpecReasoner
from .discriminative_verification import DiscriminativeVerifier
from .distinct_leaf_decoding import DistinctLeafEnumerator
from .dynamic_topology_routing import DynamicTopologyRouter
from .echo_ttrl import EchoOptimizer
from .elastic_reasoning import ElasticReasoning
from .entropy_guided_inference import EntropyGuidedInference
from .exceptions import (
    PaperConfigError,
    PaperError,
    PaperExecutionError,
    PaperNotFoundError,
    PaperValidationError,
)
from .fp16_stability import FP16Stability
from .interfaces import BasePaperAlgorithm, PaperRegistryInterface
from .intuitor_self_certainty import IntuitorReward
from .moqae_quant import MoQAEQuantizer
from .progressive_thought_encoding import ProgressiveThoughtEncoder
from .registry import (
    PaperRegistry,
    create_algorithm,
    default_registry,
    get_module,
    get_paper,
    get_paper_registry,
    list_ids,
    list_papers,
    register_paper,
    run_paper,
)
from .reinforced_attention import ReinforcedAttentionLearner
from .snap_kv import SnapKVCacheCompressor
from .speculative_decoding import SpeculativeDrafter
from .speculative_prefill import SpeculativePrefillCompressor

__all__ = [
    # Base Abstractions & Result Objects
    "BasePaperModule",
    "BasePaperAlgorithm",
    "PaperMetadata",
    "PaperCategory",
    "PaperResult",
    "PaperRegistryInterface",
    # 18 SOTA Research Paper Implementations
    "FP16Stability",
    "ElasticReasoning",
    "ChainOfDraft",
    "SnapKVCacheCompressor",
    "SpeculativeDrafter",
    "EntropyGuidedInference",
    "DistinctLeafEnumerator",
    "DiscriminativeVerifier",
    "AdaptiveKVQuantizer",
    "MoQAEQuantizer",
    "ConfSpecReasoner",
    "SpeculativePrefillCompressor",
    "IntuitorReward",
    "EchoOptimizer",
    "ReinforcedAttentionLearner",
    "ProgressiveThoughtEncoder",
    "DynamicTopologyRouter",
    "AtomicAgenticMemory",
    # Configurations
    "BasePaperConfig",
    "AdaptiveKVQuantConfig",
    "AtomicMemoryConfig",
    "ChainOfDraftConfig",
    "ConfSpecConfig",
    "DiscriminativeVerifierConfig",
    "DistinctLeafConfig",
    "DynamicTopologyConfig",
    "EchoOptimizerConfig",
    "ElasticReasoningConfig",
    "EntropyGuidedConfig",
    "FP16StabilityConfig",
    "IntuitorConfig",
    "MoQAEConfig",
    "ProgressiveThoughtConfig",
    "ReinforcedAttentionConfig",
    "SnapKVConfig",
    "SpeculativeDecodingConfig",
    "SpeculativePrefillConfig",
    # Exceptions
    "PaperError",
    "PaperConfigError",
    "PaperValidationError",
    "PaperExecutionError",
    "PaperNotFoundError",
    # Registry & Dynamic Execution Helpers
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
    # Benchmarking Suite
    "PaperBenchmarkSuite",
    "run_benchmark",
]
