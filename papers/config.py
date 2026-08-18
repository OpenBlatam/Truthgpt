"""
Configuration dataclasses with parameter validation for research paper implementations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .exceptions import PaperConfigError


@dataclass
class BasePaperConfig:
    """Base configuration class with validation helpers."""

    def validate(self) -> None:
        """Validate configuration parameters."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


@dataclass
class AdaptiveKVQuantConfig(BasePaperConfig):
    """Configuration for Adaptive KV-Cache Quantization (arXiv:2604.04722)."""
    high_bits: int = 8
    low_bits: int = 2
    high_impact_threshold: float = 0.6
    baseline_bits: int = 16

    def validate(self) -> None:
        if self.high_bits <= 0 or self.low_bits <= 0 or self.baseline_bits <= 0:
            raise PaperConfigError("Bit widths must be positive integers.")
        if self.low_bits > self.high_bits:
            raise PaperConfigError("low_bits cannot exceed high_bits.")
        if not (0.0 <= self.high_impact_threshold <= 1.0):
            raise PaperConfigError("high_impact_threshold must be between 0.0 and 1.0.")


@dataclass
class AtomicMemoryConfig(BasePaperConfig):
    """Configuration for AtomMem Atomic Agentic Memory (arXiv:2601.08323v2)."""
    dup_threshold: float = 0.85
    update_threshold: float = 0.45
    max_entries: Optional[int] = None

    def validate(self) -> None:
        if not (0.0 <= self.update_threshold <= 1.0):
            raise PaperConfigError("update_threshold must be between 0.0 and 1.0.")
        if not (0.0 <= self.dup_threshold <= 1.0):
            raise PaperConfigError("dup_threshold must be between 0.0 and 1.0.")
        if self.update_threshold > self.dup_threshold:
            raise PaperConfigError("update_threshold cannot exceed dup_threshold.")
        if self.max_entries is not None and self.max_entries <= 0:
            raise PaperConfigError("max_entries must be positive if specified.")


@dataclass
class ChainOfDraftConfig(BasePaperConfig):
    """Configuration for Chain of Draft (arXiv:2506.10987v1)."""
    default_variant: str = "baseline"
    max_words_per_step: int = 5

    def validate(self) -> None:
        allowed = {"baseline", "structured", "hierarchical", "iterative", "code_specific"}
        if self.default_variant not in allowed:
            raise PaperConfigError(f"default_variant must be one of {allowed}.")
        if self.max_words_per_step <= 0:
            raise PaperConfigError("max_words_per_step must be positive.")


@dataclass
class ConfSpecConfig(BasePaperConfig):
    """Configuration for ConfSpec Step-Level Speculative Reasoning (arXiv:2602.18447)."""
    confidence_gate: float = 0.8
    draft_accuracy: float = 0.85
    seed: Optional[int] = None

    def validate(self) -> None:
        if not (0.0 <= self.confidence_gate <= 1.0):
            raise PaperConfigError("confidence_gate must be in [0.0, 1.0].")
        if not (0.0 <= self.draft_accuracy <= 1.0):
            raise PaperConfigError("draft_accuracy must be in [0.0, 1.0].")


@dataclass
class DiscriminativeVerifierConfig(BasePaperConfig):
    """Configuration for Discriminative Verifier (arXiv:2510.14913)."""
    vote_weight: float = 0.5
    verifier_weight: float = 0.5

    def validate(self) -> None:
        if self.vote_weight < 0.0 or self.verifier_weight < 0.0:
            raise PaperConfigError("Weights must be non-negative.")
        if self.vote_weight == 0.0 and self.verifier_weight == 0.0:
            raise PaperConfigError("At least one weight must be positive.")


@dataclass
class DistinctLeafConfig(BasePaperConfig):
    """Configuration for Distinct Leaf Enumeration (arXiv:2604.20500)."""
    duplication_rate: float = 0.45

    def validate(self) -> None:
        if not (0.0 <= self.duplication_rate < 1.0):
            raise PaperConfigError("duplication_rate must be in [0.0, 1.0).")


@dataclass
class DynamicTopologyConfig(BasePaperConfig):
    """Configuration for DyTopo Dynamic Topology Routing (arXiv:2602.06039v1)."""
    top_k: int = 2
    relevance_threshold: float = 0.05

    def validate(self) -> None:
        if self.top_k < 1:
            raise PaperConfigError("top_k must be at least 1.")
        if not (0.0 <= self.relevance_threshold <= 1.0):
            raise PaperConfigError("relevance_threshold must be in [0.0, 1.0].")


@dataclass
class EchoOptimizerConfig(BasePaperConfig):
    """Configuration for ECHO Test-Time RL (arXiv:2602.02150)."""
    confidence_weight: float = 0.6
    entropy_weight: float = 0.4

    def validate(self) -> None:
        if self.confidence_weight < 0.0 or self.entropy_weight < 0.0:
            raise PaperConfigError("Weights must be non-negative.")
        if self.confidence_weight == 0.0 and self.entropy_weight == 0.0:
            raise PaperConfigError("At least one weight must be positive.")


@dataclass
class ElasticReasoningConfig(BasePaperConfig):
    """Configuration for Elastic Reasoning Budget Allocation (arXiv:2505.05315v2)."""
    t_budget: int = 512
    s_budget: int = 1024

    def validate(self) -> None:
        if self.t_budget <= 0:
            raise PaperConfigError("t_budget must be positive.")
        if self.s_budget <= 0:
            raise PaperConfigError("s_budget must be positive.")


@dataclass
class EntropyGuidedConfig(BasePaperConfig):
    """Configuration for Entropy-Guided Inference (arXiv:2606.09508v1)."""
    entropy_threshold: float = 0.55
    sparse_cost_ratio: float = 0.25
    max_speedup: float = 2.39

    def validate(self) -> None:
        if not (0.0 <= self.entropy_threshold <= 1.0):
            raise PaperConfigError("entropy_threshold must be in [0.0, 1.0].")
        if not (0.0 <= self.sparse_cost_ratio <= 1.0):
            raise PaperConfigError("sparse_cost_ratio must be in [0.0, 1.0].")
        if self.max_speedup < 1.0:
            raise PaperConfigError("max_speedup must be >= 1.0.")


@dataclass
class FP16StabilityConfig(BasePaperConfig):
    """Configuration for FP16 Stability Training Mechanisms (arXiv:2510.26788v1)."""
    clip_c: float = 1.0
    epsilon: float = 1e-8

    def validate(self) -> None:
        if self.clip_c <= 0.0:
            raise PaperConfigError("clip_c must be positive.")
        if self.epsilon <= 0.0:
            raise PaperConfigError("epsilon must be positive.")


@dataclass
class IntuitorConfig(BasePaperConfig):
    """Configuration for INTUITOR Self-Certainty RL (arXiv:2505.19590)."""
    vocab_size: int = 32000

    def validate(self) -> None:
        if self.vocab_size <= 1:
            raise PaperConfigError("vocab_size must be greater than 1.")


@dataclass
class MoQAEConfig(BasePaperConfig):
    """Configuration for MoQAE Mixture of Quantization-Aware Experts (arXiv:2506.07533)."""
    quality_budget: float = 0.02
    chunk_size: int = 2048
    experts: Optional[List[Tuple[str, int, float]]] = None

    def validate(self) -> None:
        if self.quality_budget <= 0.0:
            raise PaperConfigError("quality_budget must be positive.")
        if self.chunk_size <= 0:
            raise PaperConfigError("chunk_size must be positive.")


@dataclass
class ProgressiveThoughtConfig(BasePaperConfig):
    """Configuration for Progressive Thought Encoding (arXiv:2602.16839)."""
    num_stages: int = 4
    final_compression: float = 0.3

    def validate(self) -> None:
        if self.num_stages < 1:
            raise PaperConfigError("num_stages must be at least 1.")
        if not (0.0 < self.final_compression <= 1.0):
            raise PaperConfigError("final_compression must be in (0.0, 1.0].")


@dataclass
class ReinforcedAttentionConfig(BasePaperConfig):
    """Configuration for Reinforced Attention Learning (arXiv:2602.04884)."""
    learning_rate: float = 0.1

    def validate(self) -> None:
        if self.learning_rate <= 0.0:
            raise PaperConfigError("learning_rate must be positive.")


@dataclass
class SnapKVConfig(BasePaperConfig):
    """Configuration for SnapKV Cache Compression (arXiv:2404.14469)."""
    observation_window: int = 32
    compression_rate: float = 0.5

    def validate(self) -> None:
        if self.observation_window <= 0:
            raise PaperConfigError("observation_window must be positive.")
        if not (0.0 < self.compression_rate <= 1.0):
            raise PaperConfigError("compression_rate must be in (0.0, 1.0].")


@dataclass
class SpeculativeDecodingConfig(BasePaperConfig):
    """Configuration for Speculative Decoding (arXiv:2211.17192)."""
    gamma: int = 4
    acceptance_probability: float = 0.7
    seed: Optional[int] = None

    def validate(self) -> None:
        if self.gamma < 1:
            raise PaperConfigError("gamma must be at least 1.")
        if not (0.0 <= self.acceptance_probability <= 1.0):
            raise PaperConfigError("acceptance_probability must be in [0.0, 1.0].")


@dataclass
class SpeculativePrefillConfig(BasePaperConfig):
    """Configuration for Speculative Prefill (arXiv:2603.02631)."""
    keep_ratio: float = 0.4
    min_keep: int = 64

    def validate(self) -> None:
        if not (0.0 < self.keep_ratio <= 1.0):
            raise PaperConfigError("keep_ratio must be in (0.0, 1.0].")
        if self.min_keep < 1:
            raise PaperConfigError("min_keep must be positive.")


__all__ = [
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
]
