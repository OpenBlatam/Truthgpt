"""
Comprehensive Unit Tests for TruthGPT Research Papers Optimization Core
========================================================================
Validates all 18 research paper algorithms, configurations, domain exceptions,
central paper registry, and latency optimization wrappers.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import papers
from papers import (
    PaperError,
    PaperConfigError,
    PaperValidationError,
    PaperNotFoundError,
    PaperCategory,
    PaperMetadata,
    PaperRegistry,
    get_paper_registry,
    AdaptiveKVQuantizer,
    AdaptiveKVQuantConfig,
    AtomicAgenticMemory,
    AtomicMemoryConfig,
    ChainOfDraft,
    ChainOfDraftConfig,
    ConfSpecReasoner,
    ConfSpecConfig,
    DiscriminativeVerifier,
    DiscriminativeVerifierConfig,
    DistinctLeafEnumerator,
    DistinctLeafConfig,
    DynamicTopologyRouter,
    DynamicTopologyConfig,
    EchoOptimizer,
    EchoOptimizerConfig,
    ElasticReasoning,
    ElasticReasoningConfig,
    EntropyGuidedInference,
    EntropyGuidedConfig,
    FP16Stability,
    FP16StabilityConfig,
    IntuitorReward,
    IntuitorConfig,
    MoQAEQuantizer,
    MoQAEConfig,
    ProgressiveThoughtEncoder,
    ProgressiveThoughtConfig,
    ReinforcedAttentionLearner,
    ReinforcedAttentionConfig,
    SnapKVCacheCompressor,
    SnapKVConfig,
    SpeculativeDrafter,
    SpeculativeDecodingConfig,
    SpeculativePrefillCompressor,
    SpeculativePrefillConfig,
)
import latency_optimizations as lo


class TestPaperRegistry:
    """Tests for the centralized PaperRegistry and factory."""

    def test_registry_initialization_and_count(self):
        reg = get_paper_registry()
        papers_list = reg.list_papers()
        assert len(papers_list) >= 18
        stats = reg.get_statistics()
        assert stats["total_papers"] >= 18
        assert "categories" in stats
        assert stats["avg_speedup"] > 1.0

    def test_registry_category_filtering(self):
        reg = get_paper_registry()
        kv_papers = reg.list_papers(category="kv_cache")
        assert len(kv_papers) >= 1
        assert any(p.paper_id == "snap_kv" for p in kv_papers)

        rl_papers = reg.list_papers(category="rl_alignment")
        assert len(rl_papers) >= 3
        assert {p.paper_id for p in rl_papers} >= {"intuitor_self_certainty", "echo_ttrl", "reinforced_attention"}

    def test_registry_search(self):
        reg = get_paper_registry()
        results = reg.search_papers(query="entropy")
        assert any(p.paper_id in ("entropy_guided_inference", "echo_ttrl") for p in results)

        fast_papers = reg.search_papers(min_speedup=2.0)
        assert len(fast_papers) > 0
        assert all((p.speedup or 1.0) >= 2.0 for p in fast_papers)

    def test_registry_create_algorithm(self):
        reg = get_paper_registry()
        snap = reg.create_algorithm("snap_kv", observation_window=16)
        assert isinstance(snap, SnapKVCacheCompressor)
        assert snap.observation_window == 16

        with pytest.raises(PaperNotFoundError):
            reg.create_algorithm("non_existent_paper_xyz")


class TestAdaptiveKVQuant:
    """Tests for Adaptive KV-Cache Quantization."""

    def test_quantize_normal_flow(self):
        quantizer = AdaptiveKVQuantizer(high_bits=8, low_bits=2, high_impact_threshold=0.6)
        res = quantizer.quantize(128)
        assert res["quantized"] is True
        assert res["num_tokens"] == 128
        assert res["high_impact_tokens"] + res["low_impact_tokens"] == 128
        assert 0.0 < res["memory_ratio"] < 1.0
        assert res["memory_savings_pct"] > 0.0

    def test_quantize_edge_cases(self):
        quantizer = AdaptiveKVQuantizer()
        res_zero = quantizer.quantize(0)
        assert res_zero["quantized"] is False
        assert res_zero["memory_ratio"] == 1.0

        with pytest.raises(PaperValidationError):
            quantizer.estimate_token_impact(-5)

    def test_config_validation(self):
        with pytest.raises(PaperConfigError):
            AdaptiveKVQuantConfig(high_bits=2, low_bits=8).validate()
        with pytest.raises(PaperConfigError):
            AdaptiveKVQuantConfig(high_impact_threshold=1.5).validate()


class TestChainOfDraft:
    """Tests for Chain of Draft concise reasoning."""

    def test_templates_and_formatting(self):
        for var in ChainOfDraft.VARIANTS:
            tpl = ChainOfDraft.get_template(var)
            assert "Drafting steps:" in tpl
            assert "Solution:" in tpl

        formatted = ChainOfDraft.format_prompt("Solve 2x+4=10", variant="baseline")
        assert "Drafting steps:" in formatted
        assert "Solve 2x+4=10" in formatted

    def test_draft_validation(self):
        valid_draft = "Drafting steps:\n• 1. [x variable]\n• 2. [subtract 4]\n• 3. [divide 2]\nSolution: x=3"
        assert ChainOfDraft.validate_draft(valid_draft, max_words=5) is True

        long_draft = "Drafting steps:\n• 1. [This is a very long and overly verbose sentence that exceeds the word limit by a lot]\nSolution: x=3"
        assert ChainOfDraft.validate_draft(long_draft, max_words=5) is False

    def test_extract_solution(self):
        full = "Drafting steps:\n• 1. [x]\nSolution:\n42"
        assert ChainOfDraft.extract_solution(full) == "42"


class TestConfSpecReasoning:
    """Tests for ConfSpec step-level speculative reasoning."""

    def test_run_steps(self):
        reasoner = ConfSpecReasoner(confidence_gate=0.7, draft_accuracy=0.9, seed=42)
        res = reasoner.run_steps(10)
        assert res["num_steps"] == 10
        assert res["accepted_without_verify"] + res["verified_steps"] == 10
        assert res["speedup_multiplier"] >= 1.0

    def test_single_step_evaluation(self):
        reasoner = ConfSpecReasoner(confidence_gate=0.8)
        high_conf = reasoner.evaluate_step(0.95)
        assert high_conf["verified"] is False
        assert high_conf["accepted"] is True

        low_conf = reasoner.evaluate_step(0.4, is_correct=True)
        assert low_conf["verified"] is True
        assert low_conf["accepted"] is True

        with pytest.raises(PaperValidationError):
            reasoner.evaluate_step(1.5)


class TestDiscriminativeVerification:
    """Tests for Discriminative Verifier."""

    def test_select_hybrid_winner(self):
        verifier = DiscriminativeVerifier(vote_weight=0.5, verifier_weight=0.5)
        # "A" has 2 votes with low scores (0.2), "B" has 1 vote with high score (0.95)
        candidates = [("A", 0.2), ("A", 0.2), ("B", 0.95)]
        res = verifier.select(candidates)
        assert res["majority_vote_answer"] == "A"
        # B's hybrid score: 0.5*(1/3) + 0.5*(0.95) = 0.1667 + 0.475 = 0.6417
        # A's hybrid score: 0.5*(2/3) + 0.5*(0.2) = 0.3333 + 0.100 = 0.4333
        assert res["selected"] == "B"
        assert res["overrode_majority"] is True

    def test_score_all(self):
        verifier = DiscriminativeVerifier()
        candidates = [("42", 0.9), ("42", 0.8), ("10", 0.1)]
        breakdown = verifier.score_all(candidates)
        assert "42" in breakdown
        assert "10" in breakdown
        assert breakdown["42"]["votes"] == 2.0


class TestDistinctLeafDecoding:
    """Tests for Distinct Leaf Enumeration."""

    def test_enumerate_leaves(self):
        dle = DistinctLeafEnumerator(duplication_rate=0.4)
        res = dle.enumerate_leaves(10)
        assert res["distinct_traces"] == 10
        assert res["vanilla_samples_needed"] > 10
        assert res["samples_saved"] > 0
        assert res["compute_savings_ratio"] > 0.0

    def test_tree_traversal(self):
        dle = DistinctLeafEnumerator()
        tree = dle.simulate_tree_traversal(branching_factor=4, depth=3, prune_ratio=0.25)
        assert tree["dense_leaves"] == 64
        assert tree["pruned_distinct_leaves"] == 27
        assert tree["compute_saved_pct"] > 50.0


class TestEchoTTRL:
    """Tests for ECHO test-time reinforcement learning."""

    def test_optimize_rollouts(self):
        echo = EchoOptimizer(confidence_weight=0.6, entropy_weight=0.4)
        rollouts = [
            {"confidence": 0.9, "dist": [0.8, 0.2]},
            {"confidence": 0.4, "dist": [0.5, 0.5]},
            {"confidence": 0.1, "dist": [0.1, 0.9]},
        ]
        res = echo.optimize(rollouts)
        assert len(res["rewards"]) == 3
        assert len(res["update_weights"]) == 3
        assert sum(res["update_weights"]) == pytest.approx(1.0, abs=1e-3)
        assert res["selected"] == 0


class TestElasticReasoning:
    """Tests for Elastic Reasoning dynamic budget allocation."""

    def test_simulate_and_metrics(self):
        er = ElasticReasoning(t_budget=5, s_budget=10)
        # Thinking phase under budget
        tokens_under = ["<think>", "step1", "step2"]
        assert er.simulate_generation(tokens_under) == "continue"

        # Thinking phase at budget
        tokens_at_budget = ["<think>", "1", "2", "3", "4", "5"]
        assert er.simulate_generation(tokens_at_budget) == "</think>"

        text = "<think> step 1 step 2 </think> final answer"
        metrics = ElasticReasoning.calculate_metrics(text)
        assert metrics["has_thinking"] is True
        assert metrics["think_tokens"] == 4
        assert metrics["total_tokens"] == 8


class TestEntropyGuidedInference:
    """Tests for Entropy-Guided Adaptive Inference."""

    def test_allocate_compute(self):
        egi = EntropyGuidedInference(entropy_threshold=0.5, max_speedup=2.39)
        res = egi.allocate_compute(context_length=8192, segment_size=1024)
        assert res["context_length"] == 8192
        assert res["num_segments"] == 8
        assert res["full_attention_segments"] + res["sparse_attention_segments"] == 8
        assert 1.0 <= res["speedup_multiplier"] <= 2.39

    def test_zero_tokens(self):
        egi = EntropyGuidedInference()
        res = egi.allocate_compute(0)
        assert res["speedup_multiplier"] == 1.0


class TestFP16Stability:
    """Tests for FP16 training stability mechanisms."""

    def test_stability_metrics_fallback(self):
        metrics = FP16Stability.check_stability_metrics([1.0, 2.0, 3.0])
        assert "stable" in metrics
        assert metrics["stable"] is True

    def test_config(self):
        cfg = FP16StabilityConfig(clip_c=2.0)
        cfg.validate()
        assert cfg.clip_c == 2.0


class TestIntuitorSelfCertainty:
    """Tests for INTUITOR self-certainty intrinsic reward."""

    def test_score_group(self):
        intuitor = IntuitorReward(vocab_size=1000)
        # Rollout 1 has high confidence token probs, Rollout 2 has low
        group = [
            [0.9, 0.95, 0.88],
            [0.1, 0.05, 0.12],
        ]
        res = intuitor.score_group(group)
        assert len(res["rewards"]) == 2
        assert res["rewards"][0] > res["rewards"][1]
        assert res["best_rollout"] == 0
        assert len(res["advantages"]) == 2


class TestMoQAEQuant:
    """Tests for MoQAE mixture of quantization-aware experts."""

    def test_route(self):
        moqae = MoQAEQuantizer(quality_budget=0.02, chunk_size=1024)
        res = moqae.route(context_length=4096, chunk_size=1024)
        assert res["num_chunks"] == 4
        assert sum(res["expert_assignments"].values()) == 4
        assert 0.0 < res["memory_ratio"] <= 1.0


class TestProgressiveThoughtEncoding:
    """Tests for Progressive Thought Encoding curriculum."""

    def test_curriculum(self):
        pte = ProgressiveThoughtEncoder(num_stages=4, final_compression=0.25)
        res = pte.curriculum(base_thought_tokens=100)
        assert res["num_stages"] == 4
        assert len(res["stages"]) == 4
        assert res["stages"][0]["thought_tokens"] == 100
        assert res["stages"][-1]["thought_tokens"] == 25
        assert res["training_token_savings_pct"] > 0.0


class TestReinforcedAttention:
    """Tests for Reinforced Attention Learning."""

    def test_reinforce(self):
        ral = ReinforcedAttentionLearner(learning_rate=0.2)
        head_scores = [0.8, 0.2, 0.1, 0.9]
        res = ral.reinforce(head_scores, reward=1.0)
        assert len(res["updated_weights"]) == 4
        assert sum(res["updated_weights"]) == pytest.approx(1.0, abs=1e-3)
        assert res["updated_weights"][3] > res["updated_weights"][2]


class TestSnapKV:
    """Tests for SnapKV cache compression."""

    def test_compress_kv(self):
        snap = SnapKVCacheCompressor(observation_window=16, compression_rate=0.5)
        res = snap.compress_kv_cache(128)
        assert res["compressed"] is True
        assert res["new_size"] == 64
        assert res["tokens_saved"] == 64
        assert res["compression_ratio"] == 0.5


class TestSpeculativeDecoding:
    """Tests for Speculative Decoding drafter."""

    def test_draft_and_verify(self):
        drafter = SpeculativeDrafter(gamma=4, acceptance_probability=0.8)
        res = drafter.draft_and_verify()
        assert res["gamma_proposals"] == 4
        assert 0 <= res["accepted_tokens"] <= 4
        assert res["speedup_multiplier"] >= 1.0

    def test_verify_tokens(self):
        drafter = SpeculativeDrafter()
        draft = [10, 20, 30, 40]
        target = [10, 20, 99, 40]
        verified = drafter.verify_tokens(draft, target)
        assert verified["draft_count"] == 4
        assert verified["accepted_token_ids"] == [10, 20, 99]


class TestSpeculativePrefill:
    """Tests for Speculative Prefill compression."""

    def test_compress_prefill(self):
        sp = SpeculativePrefillCompressor(keep_ratio=0.5, min_keep=16)
        res = sp.compress_prefill(100)
        assert res["compressed"] is True
        assert res["kept_tokens"] == 50
        assert res["dropped_tokens"] == 50
        assert res["speedup_multiplier"] == 2.0

    def test_filter_tokens(self):
        sp = SpeculativePrefillCompressor(keep_ratio=0.5, min_keep=2)
        tokens = ["token_a", "token_b", "token_c", "token_d"]
        filtered = sp.filter_tokens(tokens)
        assert len(filtered) == 2


class TestLatencyOptimizationsWrappers:
    """Tests for high-level wrappers in latency_optimizations.py."""

    def test_all_wrappers_run(self):
        assert "Drafting steps:" in lo.apply_chain_of_draft("test prompt")
        assert "<think>" in lo.apply_elastic_reasoning("test prompt")
        assert lo.apply_snap_kv_compression(100)["compressed"] is True
        assert lo.apply_speculative_decoding()["gamma_proposals"] == 4
        assert lo.apply_entropy_guided_inference(2048)["num_segments"] == 2
        assert lo.apply_distinct_leaf_decoding(5)["distinct_traces"] == 5
        assert lo.apply_discriminative_verification([("A", 0.9)])["selected"] == "A"
        assert lo.apply_adaptive_kv_quant(64)["quantized"] is True
        assert lo.apply_moqae_quant(2048)["num_chunks"] == 1
        assert lo.apply_confspec_reasoning(5)["num_steps"] == 5
        assert lo.apply_speculative_prefill(100)["original_tokens"] == 100
        assert lo.apply_intuitor_reward([[0.9, 0.8]])["best_rollout"] == 0
        assert lo.apply_echo_ttrl([{"confidence": 0.8, "dist": [0.5, 0.5]}])["selected"] == 0
        assert len(lo.apply_reinforced_attention([0.5, 0.5])["updated_weights"]) == 2
        assert lo.apply_progressive_thought_encoding(50)["base_thought_tokens"] == 50
        assert lo.apply_dynamic_topology_routing("test", [{"name": "a", "capabilities": "test"}])["rounds"] == 3
        assert lo.apply_atomic_memory(["obs1", "obs1"])["redundancy_dropped"] == 1
