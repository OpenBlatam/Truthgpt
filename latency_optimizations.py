"""
Latency and Efficiency Optimization Wrappers
============================================
Exposes high-level utility functions wrapping research paper implementations
for convenient consumption throughout TruthGPT.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from papers.adaptive_kv_quant import AdaptiveKVQuantizer
from papers.atomic_agentic_memory import AtomicAgenticMemory
from papers.chain_of_draft import ChainOfDraft
from papers.confspec_reasoning import ConfSpecReasoner
from papers.discriminative_verification import DiscriminativeVerifier
from papers.distinct_leaf_decoding import DistinctLeafEnumerator
from papers.dynamic_topology_routing import DynamicTopologyRouter
from papers.echo_ttrl import EchoOptimizer
from papers.elastic_reasoning import ElasticReasoning
from papers.entropy_guided_inference import EntropyGuidedInference
from papers.fp16_stability import FP16Stability
from papers.intuitor_self_certainty import IntuitorReward
from papers.moqae_quant import MoQAEQuantizer
from papers.progressive_thought_encoding import ProgressiveThoughtEncoder
from papers.reinforced_attention import ReinforcedAttentionLearner
from papers.snap_kv import SnapKVCacheCompressor
from papers.speculative_decoding import SpeculativeDrafter
from papers.speculative_prefill import SpeculativePrefillCompressor


def apply_chain_of_draft(prompt: str, variant: str = "baseline") -> str:
    """Prepend Chain of Draft template to prompt."""
    return ChainOfDraft.format_prompt(prompt, variant=variant)


def apply_elastic_reasoning(
    prompt: str,
    t_budget: int = 512,
    s_budget: int = 1024,
    wrapper: bool = True,
) -> str:
    """Wrap prompt with thinking and solution token budget instructions."""
    elastic = ElasticReasoning(t_budget=t_budget, s_budget=s_budget)
    if wrapper:
        return elastic.wrap_prompt(prompt)
    return prompt


def apply_fp16_stability(model: Any) -> Any:
    """Configure model for FP16 stability if supported."""
    try:
        if hasattr(model, "half"):
            model.half()
    except Exception:
        pass
    return model


def check_tensor_stability(tensor: Any) -> Dict[str, Any]:
    """Run FP16 stability check on tensor."""
    return FP16Stability.check_stability_metrics(tensor)


def apply_snap_kv_compression(
    current_tokens: int,
    observation_window: int = 32,
    compression_rate: float = 0.5,
) -> Dict[str, Any]:
    """Simulate SnapKV cache compression."""
    compressor = SnapKVCacheCompressor(observation_window, compression_rate)
    return compressor.compress_kv_cache(current_tokens)


def apply_speculative_decoding(
    gamma: int = 4,
    acceptance_probability: float = 0.7,
) -> Dict[str, Any]:
    """Simulate Speculative Decoding acceleration."""
    drafter = SpeculativeDrafter(gamma, acceptance_probability)
    return drafter.draft_and_verify()


def apply_entropy_guided_inference(
    context_length: int,
    segment_size: int = 1024,
    entropy_threshold: float = 0.55,
) -> Dict[str, Any]:
    """Simulate entropy-guided adaptive attention (arXiv:2606.09508v1)."""
    engine = EntropyGuidedInference(entropy_threshold=entropy_threshold)
    return engine.allocate_compute(context_length, segment_size=segment_size)


def apply_distinct_leaf_decoding(
    sample_budget: int = 8,
    duplication_rate: float = 0.45,
) -> Dict[str, Any]:
    """Simulate deterministic distinct-leaf enumeration for self-consistency (arXiv:2604.20500)."""
    enumerator = DistinctLeafEnumerator(duplication_rate=duplication_rate)
    return enumerator.enumerate_leaves(sample_budget)


def apply_discriminative_verification(
    candidates: Sequence[Tuple[str, float]],
    vote_weight: float = 0.5,
    verifier_weight: float = 0.5,
) -> Dict[str, Any]:
    """Hybrid vote + discriminative-verifier answer selection (arXiv:2510.14913)."""
    verifier = DiscriminativeVerifier(vote_weight=vote_weight, verifier_weight=verifier_weight)
    return verifier.select(list(candidates))


def apply_adaptive_kv_quant(
    num_tokens: int,
    high_bits: int = 8,
    low_bits: int = 2,
) -> Dict[str, Any]:
    """Adaptive per-token KV-cache quantization (arXiv:2604.04722)."""
    return AdaptiveKVQuantizer(high_bits=high_bits, low_bits=low_bits).quantize(num_tokens)


def apply_moqae_quant(context_length: int, chunk_size: int = 2048) -> Dict[str, Any]:
    """Mixture of Quantization-Aware Experts routing (arXiv:2506.07533)."""
    return MoQAEQuantizer().route(context_length, chunk_size=chunk_size)


def apply_confspec_reasoning(
    num_steps: int = 12,
    confidence_gate: float = 0.8,
) -> Dict[str, Any]:
    """Confidence-gated step-level speculative reasoning (arXiv:2602.18447)."""
    return ConfSpecReasoner(confidence_gate=confidence_gate).run_steps(num_steps)


def apply_speculative_prefill(num_tokens: int, keep_ratio: float = 0.4) -> Dict[str, Any]:
    """Draft-guided training-free prefill compression (arXiv:2603.02631)."""
    return SpeculativePrefillCompressor(keep_ratio=keep_ratio).compress_prefill(num_tokens)


def apply_intuitor_reward(group_token_probs: Sequence[Sequence[float]]) -> Dict[str, Any]:
    """Label-free self-certainty RL reward, GRPO-style (arXiv:2505.19590)."""
    return IntuitorReward().score_group(list(group_token_probs))


def apply_echo_ttrl(rollouts: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Entropy-confidence hybrid reward for test-time RL (arXiv:2602.02150)."""
    return EchoOptimizer().optimize(list(rollouts))


def apply_reinforced_attention(
    head_contributions: Sequence[float],
    reward: float = 1.0,
) -> Dict[str, Any]:
    """Reward-weighted reinforcement of attention heads (arXiv:2602.04884)."""
    return ReinforcedAttentionLearner().reinforce(list(head_contributions), reward)


def apply_progressive_thought_encoding(
    base_thought_tokens: int,
    num_stages: int = 4,
) -> Dict[str, Any]:
    """Progressive thought compression curriculum for efficient training (arXiv:2602.16839)."""
    return ProgressiveThoughtEncoder(num_stages=num_stages).curriculum(base_thought_tokens)


def apply_dynamic_topology_routing(
    query: str,
    agents: Sequence[Dict[str, str]],
    top_k: int = 2,
    rounds: int = 3,
) -> Dict[str, Any]:
    """Semantic-matching dynamic multi-agent topology routing (arXiv:2602.06039v1)."""
    return DynamicTopologyRouter(top_k=top_k).run(query, list(agents), rounds=rounds)


def apply_atomic_memory(
    observations: Sequence[str],
    dup_threshold: float = 0.85,
    update_threshold: float = 0.45,
) -> Dict[str, Any]:
    """Atomic-operation learnable agentic memory (arXiv:2601.08323v2)."""
    mem = AtomicAgenticMemory(dup_threshold=dup_threshold, update_threshold=update_threshold)
    return mem.process(list(observations))


__all__ = [
    "apply_chain_of_draft",
    "apply_elastic_reasoning",
    "apply_fp16_stability",
    "check_tensor_stability",
    "apply_snap_kv_compression",
    "apply_speculative_decoding",
    "apply_entropy_guided_inference",
    "apply_distinct_leaf_decoding",
    "apply_discriminative_verification",
    "apply_adaptive_kv_quant",
    "apply_moqae_quant",
    "apply_confspec_reasoning",
    "apply_speculative_prefill",
    "apply_intuitor_reward",
    "apply_echo_ttrl",
    "apply_reinforced_attention",
    "apply_progressive_thought_encoding",
    "apply_dynamic_topology_routing",
    "apply_atomic_memory",
]
