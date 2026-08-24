"""
Statistical Benchmark Utilities and Latency Analyzers for TruthGPT Optimization Core.
"""

from __future__ import annotations

import time
import statistics
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field

from ..types import BenchmarkMetric

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Statistical summary of a micro-benchmark execution."""
    name: str
    avg_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0
    std_ms: float = 0.0
    p50_ms: float = 0.0
    p90_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    throughput: float = 0.0
    num_runs: int = 0
    errors: List[str] = field(default_factory=list)
    speedup_vs_baseline: float = 1.0

    def to_metric(self) -> BenchmarkMetric:
        return BenchmarkMetric(
            name=self.name,
            avg_ms=self.avg_ms,
            min_ms=self.min_ms,
            max_ms=self.max_ms,
            std_ms=self.std_ms,
            p50_ms=self.p50_ms,
            p90_ms=self.p90_ms,
            p95_ms=self.p95_ms,
            p99_ms=self.p99_ms,
            throughput=self.throughput,
            iterations=self.num_runs,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "avg_ms": round(self.avg_ms, 4),
            "min_ms": round(self.min_ms, 4),
            "max_ms": round(self.max_ms, 4),
            "std_ms": round(self.std_ms, 4),
            "p50_ms": round(self.p50_ms, 4),
            "p90_ms": round(self.p90_ms, 4),
            "p95_ms": round(self.p95_ms, 4),
            "p99_ms": round(self.p99_ms, 4),
            "throughput": round(self.throughput, 2),
            "num_runs": self.num_runs,
            "speedup_vs_baseline": round(self.speedup_vs_baseline, 2),
            "errors": self.errors,
        }


def run_benchmark(
    func: Callable[..., Any],
    *args: Any,
    num_runs: int = 10,
    warmup_runs: int = 3,
    name: Optional[str] = None,
    **kwargs: Any,
) -> BenchmarkResult:
    """Run benchmark on a target callable with statistical latency calculation."""
    bench_name = name or getattr(func, '__name__', 'anonymous_benchmark')

    # Warmup
    for _ in range(warmup_runs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            logger.warning("Warmup run failed for '%s': %s", bench_name, e)

    # Measurement
    times: List[float] = []
    errors: List[str] = []

    for i in range(num_runs):
        try:
            t0 = time.perf_counter()
            func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            times.append(elapsed_ms)
        except Exception as e:
            errors.append(f"Run {i + 1}: {e}")
            logger.warning("Benchmark run %d failed for '%s': %s", i + 1, bench_name, e)

    if not times:
        return BenchmarkResult(name=bench_name, num_runs=num_runs, errors=errors)

    sorted_times = sorted(times)
    n = len(sorted_times)
    avg_val = statistics.mean(sorted_times)
    std_val = statistics.stdev(sorted_times) if n > 1 else 0.0

    def get_pct(p: float) -> float:
        idx = min(int(n * p), n - 1)
        return sorted_times[idx]

    return BenchmarkResult(
        name=bench_name,
        avg_ms=avg_val,
        min_ms=sorted_times[0],
        max_ms=sorted_times[-1],
        std_ms=std_val,
        p50_ms=get_pct(0.50),
        p90_ms=get_pct(0.90),
        p95_ms=get_pct(0.95),
        p99_ms=get_pct(0.99),
        throughput=1000.0 / avg_val if avg_val > 0 else 0.0,
        num_runs=n,
        errors=errors,
    )


def compare_benchmarks(
    results: Dict[str, BenchmarkResult],
    baseline: Optional[str] = None,
) -> Dict[str, Any]:
    """Compare multiple benchmark results relative to a designated baseline."""
    comparison: Dict[str, Any] = {}
    baseline_key = baseline or next(iter(results.keys()))
    baseline_result = results.get(baseline_key)

    if not baseline_result or baseline_result.avg_ms <= 0:
        return {k: v.to_dict() for k, v in results.items()}

    base_avg = baseline_result.avg_ms

    for name, res in results.items():
        res_dict = res.to_dict()
        speedup = base_avg / res.avg_ms if res.avg_ms > 0 else 0.0
        res.speedup_vs_baseline = speedup
        res_dict["speedup_vs_baseline"] = round(speedup, 3)
        res_dict["is_faster_than_baseline"] = speedup > 1.0
        comparison[name] = res_dict

    return comparison


def format_benchmark_result(result: BenchmarkResult) -> str:
    """Format benchmark result as a human-readable text card."""
    lines = [
        f"Benchmark: {result.name}",
        f"  Average    : {result.avg_ms:.3f} ms",
        f"  Min / Max  : {result.min_ms:.3f} ms / {result.max_ms:.3f} ms",
        f"  Std Dev    : {result.std_ms:.3f} ms",
        f"  p50 / p95  : {result.p50_ms:.3f} ms / {result.p95_ms:.3f} ms",
        f"  p99        : {result.p99_ms:.3f} ms",
        f"  Throughput : {result.throughput:.1f} ops/sec",
        f"  Iterations : {result.num_runs}",
    ]
    if result.speedup_vs_baseline != 1.0:
        lines.append(f"  Speedup    : {result.speedup_vs_baseline:.2f}x vs baseline")
    return "\n".join(lines)


def benchmark_backends(
    func_map: Dict[str, Callable[..., Any]],
    *args: Any,
    num_runs: int = 10,
    warmup_runs: int = 3,
    baseline_backend: Optional[str] = "python",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Execute benchmarks across polyglot backend candidate implementations."""
    results: Dict[str, BenchmarkResult] = {}
    for backend, fn in func_map.items():
        res = run_benchmark(
            fn,
            *args,
            num_runs=num_runs,
            warmup_runs=warmup_runs,
            name=f"{backend}_backend",
            **kwargs,
        )
        results[backend] = res

    return compare_benchmarks(results, baseline=baseline_backend)


__all__ = [
    "BenchmarkResult",
    "run_benchmark",
    "compare_benchmarks",
    "format_benchmark_result",
    "benchmark_backends",
]
