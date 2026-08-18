"""
Unit tests for the Research Papers Subsystem Refactoring.
Validates all 18 paper implementations, base abstractions, registry discovery,
structured outputs, and the automated benchmarking suite.
"""

import sys
import unittest
from pathlib import Path

# Ensure optimization_core is at the top of sys.path
opt_core_dir = str(Path(__file__).resolve().parent.parent.parent)
if opt_core_dir in sys.path:
    sys.path.remove(opt_core_dir)
sys.path.insert(0, opt_core_dir)

import papers
from papers import (
    AdaptiveKVQuantizer,
    AtomicAgenticMemory,
    BasePaperAlgorithm,
    BasePaperModule,
    ChainOfDraft,
    ConfSpecReasoner,
    DiscriminativeVerifier,
    DistinctLeafEnumerator,
    DynamicTopologyRouter,
    EchoOptimizer,
    ElasticReasoning,
    EntropyGuidedInference,
    FP16Stability,
    IntuitorReward,
    MoQAEQuantizer,
    PaperBenchmarkSuite,
    PaperCategory,
    PaperMetadata,
    PaperRegistry,
    PaperResult,
    ProgressiveThoughtEncoder,
    ReinforcedAttentionLearner,
    SnapKVCacheCompressor,
    SpeculativeDrafter,
    SpeculativePrefillCompressor,
    default_registry,
    get_paper,
    get_paper_registry,
    list_papers,
    run_benchmark,
    run_paper,
)


class TestPapersFramework(unittest.TestCase):
    """Tests for base classes, protocols, dataclasses, and registry."""

    def test_paper_result_dict_and_attr_compatibility(self):
        """Verify PaperResult supports both dictionary and attribute syntax."""
        res = PaperResult({"speedup": 2.5, "loss": 0.05})
        self.assertEqual(res["speedup"], 2.5)
        self.assertEqual(res.speedup, 2.5)
        self.assertEqual(res.get("loss"), 0.05)

        # Mutate via dict
        res["new_key"] = "test"
        self.assertEqual(res.new_key, "test")

        # Mutate via attr
        res.attr_key = 123
        self.assertEqual(res["attr_key"], 123)

        # to_dict conversion
        d = res.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["speedup"], 2.5)

    def test_paper_metadata_serialization(self):
        """Verify PaperMetadata initialization and dictionary conversion."""
        meta = PaperMetadata(
            paper_id="test_paper",
            paper_name="Test Paper Name",
            arxiv_id="2601.99999",
            category=PaperCategory.REASONING,
            description="Testing paper metadata",
            key_techniques=["Tech A", "Tech B"],
            speedup=2.0,
        )
        d = meta.to_dict()
        self.assertEqual(d["paper_id"], "test_paper")
        self.assertEqual(d["category"], "reasoning")
        self.assertEqual(d["speedup"], 2.0)

    def test_registry_registration_and_discovery(self):
        """Verify registry catalogs all 18 papers with categories and metadata."""
        reg = get_paper_registry()
        stats = reg.get_statistics()
        self.assertGreaterEqual(stats["total_papers"], 18)

        # Retrieve specific paper class and metadata
        cls = get_paper("snap_kv")
        self.assertIsNotNone(cls)
        self.assertEqual(cls, SnapKVCacheCompressor)

        meta = reg.get_metadata("snap_kv")
        self.assertIsNotNone(meta)
        self.assertEqual(meta.paper_id, "snap_kv")

        algo = reg.create_algorithm("snap_kv")
        self.assertIsInstance(algo, SnapKVCacheCompressor)

        # List papers by category
        reasoning_papers = list_papers(category=PaperCategory.REASONING)
        self.assertGreater(len(reasoning_papers), 0)
        pids = [p.paper_id for p in reasoning_papers]
        self.assertIn("chain_of_draft", pids)
        self.assertIn("confspec_reasoning", pids)

        quant_papers = list_papers(category=PaperCategory.QUANTIZATION)
        q_pids = [p.paper_id for p in quant_papers]
        self.assertIn("adaptive_kv_quant", q_pids)
        self.assertIn("moqae_quant", q_pids)

    def test_run_paper_helper(self):
        """Verify dynamic execution via run_paper."""
        res = run_paper("chain_of_draft", draft_text="Drafting steps:\n• 1. [x=1]\nSolution:\n1")
        self.assertIn("is_compliant", res)
        self.assertTrue(res["is_compliant"])

    def test_benchmark_suite(self):
        """Verify automated benchmark suite runs across papers."""
        suite = PaperBenchmarkSuite()
        single = suite.run_single("snap_kv", num_runs=3)
        self.assertEqual(single["paper_id"], "snap_kv")
        self.assertIn("avg_latency_ms", single)
        self.assertGreaterEqual(single["avg_latency_ms"], 0.0)

        all_res = run_benchmark()
        self.assertGreaterEqual(all_res["successful_runs"], 18)
        self.assertEqual(all_res["failed_runs"], 0)


class TestReasoningPapers(unittest.TestCase):
    """Tests for reasoning and test-time compute paper modules."""

    def test_elastic_reasoning(self):
        er = ElasticReasoning(t_budget=5, s_budget=5)
        # Simulation inside thinking
        tokens = ["<think>", "step1", "step2"]
        self.assertEqual(er.simulate_generation(tokens), "continue")

        # Budget exhausted
        long_tokens = ["<think>", "1", "2", "3", "4", "5", "6"]
        self.assertEqual(er.simulate_generation(long_tokens), "</think>")

        # Metrics calculation
        metrics = ElasticReasoning.calculate_metrics("<think> reasoning step here </think> final answer 42")
        self.assertTrue(metrics["has_thinking"])
        self.assertEqual(metrics["think_tokens"], 3)

        # Base execute
        res = er.execute()
        self.assertIn("think_budget", res)

    def test_chain_of_draft(self):
        cod = ChainOfDraft()
        for variant in ChainOfDraft.VARIANTS:
            tmpl = ChainOfDraft.get_template(variant)
            self.assertIn("Drafting steps:", tmpl)
            self.assertIn("Solution:", tmpl)

        valid_draft = "Drafting steps:\n• 1. [x=1]\n• 2. [y=2]\nSolution:\n3"
        self.assertTrue(ChainOfDraft.validate_draft(valid_draft))

        analysis = cod.execute(valid_draft)
        self.assertTrue(analysis["is_compliant"])
        self.assertEqual(analysis["num_steps"], 2)

    def test_confspec_reasoning(self):
        csr = ConfSpecReasoner(confidence_gate=0.7, draft_accuracy=0.9, seed=42)
        res = csr.run_steps(15)
        self.assertEqual(res["num_steps"], 15)
        self.assertGreaterEqual(res["accepted_without_verify"], 0)
        self.assertGreaterEqual(res["speedup_multiplier"], 1.0)
        self.assertIn("speedup_multiplier", res)

    def test_discriminative_verification(self):
        dv = DiscriminativeVerifier(vote_weight=0.5, verifier_weight=0.5)
        cands = [("AnswerA", 0.9), ("AnswerA", 0.8), ("AnswerB", 0.99), ("AnswerA", 0.85)]
        res = dv.select(cands)
        self.assertEqual(res["selected"], "AnswerA")
        self.assertEqual(res["num_candidates"], 4)
        self.assertEqual(res["num_unique_answers"], 2)

        # Empty test
        empty_res = dv.select([])
        self.assertIsNone(empty_res["selected"])

    def test_distinct_leaf_decoding(self):
        dle = DistinctLeafEnumerator(duplication_rate=0.4)
        res = dle.enumerate_leaves(sample_budget=10)
        self.assertEqual(res["distinct_traces"], 10)
        self.assertGreater(res["vanilla_samples_needed"], 10)
        self.assertGreater(res["samples_saved"], 0)
        self.assertTrue(res["deterministic"])

        exp_d = dle.expected_distinct(20)
        self.assertGreater(exp_d, 0)

    def test_progressive_thought_encoding(self):
        pte = ProgressiveThoughtEncoder(num_stages=4, final_compression=0.25)
        res = pte.curriculum(base_thought_tokens=1000)
        self.assertEqual(res["base_thought_tokens"], 1000)
        self.assertEqual(res["num_stages"], 4)
        self.assertEqual(len(res["stages"]), 4)
        self.assertLess(res["final_thought_tokens"], 1000)
        self.assertGreater(res["training_token_savings_pct"], 0.0)


class TestQuantizationAndStabilityPapers(unittest.TestCase):
    """Tests for quantization, KV cache, and training stability modules."""

    def test_fp16_stability(self):
        fps = FP16Stability()
        # Test with list of values
        safe_data = [0.01, 1.5, 20.0, 500.0]
        res = fps.check_stability_metrics(safe_data)
        self.assertTrue(res["stable"])
        self.assertFalse(res["is_overflow"])
        self.assertFalse(res["is_underflow"])

        # Overflow test
        overflow_data = [70000.0, 1.0]
        res_ovf = fps.check_stability_metrics(overflow_data)
        self.assertTrue(res_ovf["is_overflow"])
        self.assertFalse(res_ovf["stable"])

        # Underflow test
        underflow_data = [1e-6, 1.0]
        res_unf = fps.check_stability_metrics(underflow_data)
        self.assertTrue(res_unf["is_underflow"])
        self.assertFalse(res_unf["stable"])

        # IS and TIS functions
        loss_is = FP16Stability.importance_sampling_correction([0.5, 0.5], [0.4, 0.6], [1.0, -1.0])
        self.assertIsInstance(loss_is, float)
        loss_tis = FP16Stability.truncated_is([0.9, 0.1], [0.1, 0.9], [1.0, 1.0], clip_c=1.0)
        self.assertIsInstance(loss_tis, float)

    def test_adaptive_kv_quant(self):
        akv = AdaptiveKVQuantizer(high_bits=8, low_bits=2, high_impact_threshold=0.5, baseline_bits=16)
        res = akv.quantize(num_tokens=100)
        self.assertTrue(res["quantized"])
        self.assertEqual(res["num_tokens"], 100)
        self.assertLess(res["avg_bits_per_token"], 16.0)
        self.assertLess(res["memory_ratio"], 1.0)
        self.assertGreater(res["memory_savings_pct"], 0.0)

        # Edge case: 0 tokens
        zero_res = akv.quantize(0)
        self.assertFalse(zero_res["quantized"])

    def test_moqae_quant(self):
        moqae = MoQAEQuantizer(quality_budget=0.03)
        res = moqae.route(context_length=8192, chunk_size=2048)
        self.assertEqual(res["num_chunks"], 4)
        self.assertIn("expert_assignments", res)
        self.assertLess(res["avg_bits"], 16.0)
        self.assertLess(res["memory_ratio"], 1.0)


class TestInferenceAndKVCachePapers(unittest.TestCase):
    """Tests for inference acceleration and prefill optimization modules."""

    def test_snap_kv(self):
        skv = SnapKVCacheCompressor(observation_window=16, compression_rate=0.4)
        res = skv.compress_kv_cache(current_tokens=256)
        self.assertTrue(res["compressed"])
        self.assertLessEqual(res["new_size"], 256)
        self.assertGreaterEqual(res["new_size"], 16)
        self.assertGreater(res["tokens_saved"], 0)

        # Small context edge case
        small_res = skv.compress_kv_cache(10)
        self.assertFalse(small_res["compressed"])

    def test_speculative_decoding(self):
        sd = SpeculativeDrafter(gamma=4, acceptance_probability=0.8, seed=123)
        res = sd.draft_and_verify()
        self.assertEqual(res["gamma_proposals"], 4)
        self.assertGreaterEqual(res["accepted_tokens"], 0)
        self.assertLessEqual(res["accepted_tokens"], 4)
        self.assertGreaterEqual(res["speedup_multiplier"], 1.0)

    def test_speculative_prefill(self):
        sp = SpeculativePrefillCompressor(keep_ratio=0.5, min_keep=32)
        res = sp.compress_prefill(num_tokens=500)
        self.assertTrue(res["compressed"])
        self.assertEqual(res["original_tokens"], 500)
        self.assertEqual(res["kept_tokens"], 250)
        self.assertEqual(res["dropped_tokens"], 250)
        self.assertAlmostEqual(res["speedup_multiplier"], 2.0)

    def test_entropy_guided_inference(self):
        egi = EntropyGuidedInference(entropy_threshold=0.5, sparse_cost_ratio=0.25)
        res = egi.allocate_compute(context_length=4096, segment_size=1024)
        self.assertEqual(res["context_length"], 4096)
        self.assertEqual(res["num_segments"], 4)
        self.assertEqual(res["full_attention_segments"] + res["sparse_attention_segments"], 4)
        self.assertGreaterEqual(res["speedup_multiplier"], 1.0)


class TestRLAndMultiAgentPapers(unittest.TestCase):
    """Tests for RL reward signals and dynamic multi-agent memory/routing modules."""

    def test_intuitor_self_certainty(self):
        ir = IntuitorReward(vocab_size=32000)
        # High confidence distribution (e.g. 0.99)
        cert_high = ir.self_certainty([0.99, 0.98, 0.95])
        # Low confidence distribution (e.g. 0.05)
        cert_low = ir.self_certainty([0.05, 0.04, 0.06])
        self.assertGreater(cert_high, cert_low)

        # Group scoring
        group = [[0.95, 0.9], [0.3, 0.2], [0.8, 0.7]]
        res = ir.score_group(group)
        self.assertEqual(res["group_size"], 3)
        self.assertEqual(res["best_rollout"], 0)
        self.assertTrue(res["label_free"])

    def test_echo_ttrl(self):
        echo = EchoOptimizer(confidence_weight=0.7, entropy_weight=0.3)
        rollouts = [
            {"confidence": 0.95, "dist": [0.9, 0.05, 0.05]},
            {"confidence": 0.40, "dist": [0.25, 0.25, 0.25, 0.25]},
        ]
        res = echo.optimize(rollouts)
        self.assertEqual(res["selected"], 0)
        self.assertEqual(len(res["rewards"]), 2)
        self.assertEqual(len(res["update_weights"]), 2)
        self.assertAlmostEqual(sum(res["update_weights"]), 1.0, places=3)

    def test_reinforced_attention(self):
        ral = ReinforcedAttentionLearner(learning_rate=0.2)
        contribs = [0.05, 0.6, 0.05, 0.3]
        res = ral.reinforce(contribs, reward=1.0)
        self.assertEqual(res["num_heads"], 4)
        self.assertEqual(len(res["updated_weights"]), 4)
        self.assertAlmostEqual(sum(res["updated_weights"]), 1.0, places=3)
        # Head index 1 was highest contributor, should have highest weight
        self.assertEqual(res["updated_weights"].index(max(res["updated_weights"])), 1)

    def test_atomic_agentic_memory(self):
        mem = AtomicAgenticMemory(dup_threshold=0.85, update_threshold=0.45)
        obs = [
            "Calculate Euler totient function for 100",
            "Calculate Euler totient function for 100 with steps",  # similar -> UPDATE
            "Calculate Euler totient function for 100",            # near-duplicate -> NOOP
            "Deploy Docker image to Kubernetes cluster",           # novel -> ADD
        ]
        res = mem.process(obs)
        self.assertEqual(res["observations_ingested"], 4)
        self.assertGreater(res["redundancy_dropped"], 0)

        # Snapshot & search
        snap = mem.snapshot()
        self.assertGreater(len(snap), 0)
        hits = mem.search("totient function", top_k=2)
        self.assertGreater(len(hits), 0)
        self.assertIn("totient", hits[0]["content"].lower())

    def test_dynamic_topology_routing(self):
        dtr = DynamicTopologyRouter(top_k=2, relevance_threshold=0.1)
        agents = [
            {"name": "math_solver", "capabilities": "algebra calculus computation proof"},
            {"name": "code_refactorer", "capabilities": "python julia rust compiler ast syntax"},
            {"name": "web_crawler", "capabilities": "http browser network scraping html"},
        ]
        res = dtr.route_round("Optimize python compiler AST pass", agents)
        self.assertIn("code_refactorer", res["active_agents"])
        self.assertGreaterEqual(res["edges_saved"], 0)
        self.assertIn("density", res)

        sim = dtr.run("Calculus integral of sin(x)", agents, rounds=2)
        self.assertEqual(sim["rounds"], 2)
        self.assertIn("avg_density", sim)


if __name__ == "__main__":
    unittest.main()
