"""
Research Papers Implementations for TruthGPT Optimization Core.
These modules contain exact implementations of state-of-the-art research papers.
"""

from .fp16_stability import FP16Stability
from .elastic_reasoning import ElasticReasoning
from .chain_of_draft import ChainOfDraft
from .snap_kv import SnapKVCacheCompressor
from .speculative_decoding import SpeculativeDrafter
from .entropy_guided_inference import EntropyGuidedInference
from .distinct_leaf_decoding import DistinctLeafEnumerator
from .discriminative_verification import DiscriminativeVerifier
from .adaptive_kv_quant import AdaptiveKVQuantizer
from .moqae_quant import MoQAEQuantizer
from .confspec_reasoning import ConfSpecReasoner
from .speculative_prefill import SpeculativePrefillCompressor
from .intuitor_self_certainty import IntuitorReward
from .echo_ttrl import EchoOptimizer
from .reinforced_attention import ReinforcedAttentionLearner
from .progressive_thought_encoding import ProgressiveThoughtEncoder

__all__ = [
    "FP16Stability",
    "ElasticReasoning",
    "ChainOfDraft",
    "SnapKVCacheCompressor",
    "SpeculativeDrafter",
    # SOTA papers added June 2026
    "EntropyGuidedInference",
    "DistinctLeafEnumerator",
    "DiscriminativeVerifier",
    "AdaptiveKVQuantizer",
    "MoQAEQuantizer",
    "ConfSpecReasoner",
    "SpeculativePrefillCompressor",
    # Best-of-2026 RL / reasoning papers
    "IntuitorReward",
    "EchoOptimizer",
    "ReinforcedAttentionLearner",
    "ProgressiveThoughtEncoder",
]

