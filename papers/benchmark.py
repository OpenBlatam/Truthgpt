"""
Automated Benchmarking Suite for TruthGPT Research Papers Subsystem.
Evaluates latency, token compression, memory efficiency, and speedup factors across all 18 papers.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from .base import BasePaperModule, PaperCategory, PaperMetadata, PaperResult
from .registry import PaperRegistry, get_paper_registry

logger = logging.getLogger(__name__)


class PaperBenchmarkSuite:
    """
    Automated benchmark harness for all 18 registered research paper algorithms.
    """

    # Tailored synthetic workloads for all 18 papers
    SAMPLE_PAYLOADS: Dict[str, Dict[str, Any]] = {
        "fp16_stability": {"tensor": [0.01, 0.5, 0.99, -0.2, 0.05, 10.0]},
        "elastic_reasoning": {"current_tokens": ["<think>", "let", "us", "break", "down", "step", "1"]},
        "chain_of_draft": {"draft_text": "Drafting steps:\n• 1. [x=1]\n• 2. [y=2]\nSolution:\n3"},
        "snap_kv": {"current_tokens": 1024},
        "speculative_decoding": {},
        "entropy_guided_inference": {"context_length": 8192, "segment_size": 1024},
        "distinct_leaf_decoding": {"sample_budget": 16},
        "discriminative_verification": {
            "candidates": [("42", 0.95), ("42", 0.88), ("24", 0.30), ("42", 0.92), ("12", 0.10)]
        },
        "adaptive_kv_quant": {"num_tokens": 2048},
        "moqae_quant": {"context_length": 4096, "chunk_size": 1024},
        "confspec_reasoning": {"num_steps": 10},
        "speculative_prefill": {"num_tokens": 4096},
        "intuitor_self_certainty": {
            "group_token_probs": [
                [0.9, 0.85, 0.95, 0.88],
                [0.4, 0.35, 0.50, 0.42],
                [0.7, 0.75, 0.80, 0.72],
            ]
        },
        "echo_ttrl": {
            "rollouts": [
                {"confidence": 0.85, "dist": [0.8, 0.1, 0.05, 0.05]},
                {"confidence": 0.50, "dist": [0.3, 0.3, 0.2, 0.2]},
                {"confidence": 0.92, "dist": [0.9, 0.05, 0.03, 0.02]},
            ]
        },
        "reinforced_attention": {
            "head_contributions": [0.1, 0.4, 0.05, 0.25, 0.05, 0.05, 0.05, 0.05],
            "reward": 1.0,
        },
        "progressive_thought_encoding": {"base_thought_tokens": 1200},
        "atomic_agentic_memory": {
            "observations": [
                "User requested sales report for Q1 2026",
                "User requested sales report for Q1 2026 in PDF format",
                "Server responded with status code 200",
                "Database backup completed at midnight",
            ]
        },
        "dynamic_topology_routing": {
            "message": "Optimize CUDA memory cache for large tensor matrix multiplication",
            "agents": [
                {"name": "gpu_expert", "capabilities": "cuda memory tensor matrix gpu kernel"},
                {"name": "math_solver", "capabilities": "equations algebra calculus logic proof"},
                {"name": "web_searcher", "capabilities": "crawler search engine browser web api"},
                {"name": "code_refactorer", "capabilities": "python rust julia code formatting ast"},
            ],
            "rounds": 2,
        },
    }

    def __init__(self, registry: Optional[PaperRegistry] = None) -> None:
        self.registry = registry or get_paper_registry()

    def run_single(self, paper_id: str, num_runs: int = 10, **kwargs: Any) -> PaperResult:
        """
        Benchmark a single paper algorithm across multiple executions.
        """
        pid = paper_id.lower().replace("-", "_").strip()
        module = self.registry.get_module(pid)
        payload = kwargs if kwargs else self.SAMPLE_PAYLOADS.get(pid, {})

        latencies: List[float] = []
        result: Optional[PaperResult] = None

        runs = max(1, num_runs)
        for _ in range(runs):
            t0 = time.perf_counter()
            result = module.execute(**payload)
            latencies.append(time.perf_counter() - t0)

        avg_latency_ms = (sum(latencies) / len(latencies)) * 1000.0
        meta = module.get_metadata()

        return PaperResult({
            "paper_id": pid,
            "paper_name": meta.paper_name,
            "category": meta.category.value if hasattr(meta.category, "value") else str(meta.category),
            "num_runs": len(latencies),
            "avg_latency_ms": round(avg_latency_ms, 4),
            "min_latency_ms": round(min(latencies) * 1000.0, 4),
            "max_latency_ms": round(max(latencies) * 1000.0, 4),
            "sample_result": result.to_dict() if hasattr(result, "to_dict") else dict(result) if isinstance(result, dict) else str(result),
        })

    def run_all(self, num_runs: int = 10) -> PaperResult:
        """
        Run benchmarks across all registered paper algorithms in catalog.
        """
        paper_ids = self.registry.list_ids()
        results: Dict[str, Any] = {}
        total_time_ms = 0.0
        success_count = 0
        errors: Dict[str, str] = {}

        for pid in paper_ids:
            try:
                res = self.run_single(pid, num_runs=num_runs)
                results[pid] = res.to_dict()
                total_time_ms += res.avg_latency_ms
                success_count += 1
            except Exception as e:
                logger.error("Failed to benchmark paper '%s': %s", pid, e, exc_info=True)
                errors[pid] = str(e)

        return PaperResult({
            "total_papers_tested": len(paper_ids),
            "successful_runs": success_count,
            "failed_runs": len(errors),
            "total_avg_latency_ms": round(total_time_ms, 4),
            "benchmarks": results,
            "errors": errors,
        })


def run_benchmark(paper_id: Optional[str] = None, num_runs: int = 10) -> PaperResult:
    """Convenience entrypoint for benchmarking papers."""
    suite = PaperBenchmarkSuite()
    if paper_id:
        return suite.run_single(paper_id, num_runs=num_runs)
    return suite.run_all(num_runs=num_runs)


__all__ = [
    "PaperBenchmarkSuite",
    "run_benchmark",
]
