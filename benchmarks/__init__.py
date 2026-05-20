"""
Unified Benchmarks System
=========================
Centralized access to all benchmark systems in optimization_core.
"""

# Import benchmark modules
try:
    from .benchmarks import (
        BenchmarkSuite,
        run_benchmarks,
    )
except ImportError:
    BenchmarkSuite = None
    run_benchmarks = None

try:
    from .comprehensive_benchmark_system import (
        ComprehensiveBenchmarkSystem,
        BenchmarkConfig,
        run_comprehensive_benchmarks,
    )
except ImportError:
    ComprehensiveBenchmarkSystem = None
    BenchmarkConfig = None
    run_comprehensive_benchmarks = None

try:
    from .olympiad_benchmarks import (
        OlympiadBenchmarkSuite,
        OlympiadBenchmarkConfig,
        OlympiadProblem,
        ProblemCategory,
        DifficultyLevel,
        get_olympiad_benchmark_config,
    )
except ImportError:
    OlympiadBenchmarkSuite = None
    OlympiadBenchmarkConfig = None
    OlympiadProblem = None
    ProblemCategory = None
    DifficultyLevel = None
    get_olympiad_benchmark_config = None

try:
    from .tensorflow_benchmark_system import (
        TensorFlowBenchmarkSystem,
        run_tensorflow_benchmarks,
    )
except ImportError:
    TensorFlowBenchmarkSystem = None
    run_tensorflow_benchmarks = None


# Unified benchmark factory
def create_benchmark(
    benchmark_type: str = "comprehensive",
    config: dict = None
):
    """
    Unified factory function to create benchmarks.
    
    Args:
        benchmark_type: Type of benchmark to create. Options:
            - "comprehensive" - ComprehensiveBenchmarkSystem
            - "olympiad" - OlympiadBenchmarkSuite
            - "tensorflow" - TensorFlowBenchmarkSystem
            - "basic" - BenchmarkSuite
        config: Optional configuration dictionary
    
    Returns:
        The requested benchmark instance
    """
    if config is None:
        config = {}
    
    benchmark_type = benchmark_type.lower()
    
    factory_map = {
        "comprehensive": lambda cfg: ComprehensiveBenchmarkSystem(cfg) if ComprehensiveBenchmarkSystem else None,
        "olympiad": lambda cfg: OlympiadBenchmarkSuite(cfg) if OlympiadBenchmarkSuite else None,
        "tensorflow": lambda cfg: TensorFlowBenchmarkSystem(cfg) if TensorFlowBenchmarkSystem else None,
        "basic": lambda cfg: BenchmarkSuite(cfg) if BenchmarkSuite else None,
    }
    
    if benchmark_type not in factory_map:
        available = ", ".join(factory_map.keys())
        raise ValueError(
            f"Unknown benchmark type: '{benchmark_type}'. "
            f"Available types: {available}"
        )
    
    factory = factory_map[benchmark_type]
    benchmark = factory(config)
    
    if benchmark is None:
        raise ImportError(f"Benchmark type '{benchmark_type}' is not available (module not found)")
    
    return benchmark


# Registry of all available benchmarks
BENCHMARK_REGISTRY = {
    "comprehensive": {
        "class": ComprehensiveBenchmarkSystem,
        "module": "benchmarks.comprehensive_benchmark_system",
        "description": "Comprehensive benchmark system",
    },
    "olympiad": {
        "class": OlympiadBenchmarkSuite,
        "module": "benchmarks.olympiad_benchmarks",
        "description": "Olympiad benchmark suite",
    },
    "tensorflow": {
        "class": TensorFlowBenchmarkSystem,
        "module": "benchmarks.tensorflow_benchmark_system",
        "description": "TensorFlow benchmark system",
    },
    "basic": {
        "class": BenchmarkSuite,
        "module": "benchmarks.benchmarks",
        "description": "Basic benchmark suite",
    },
}


def list_available_benchmarks() -> list:
    """List all available benchmark types."""
    return [k for k, v in BENCHMARK_REGISTRY.items() if v["class"] is not None]


def get_benchmark_info(benchmark_type: str) -> dict:
    """
    Get information about a specific benchmark.
    
    Args:
        benchmark_type: Type of benchmark
    
    Returns:
        Dictionary with benchmark information
    """
    if benchmark_type not in BENCHMARK_REGISTRY:
        raise ValueError(f"Unknown benchmark type: {benchmark_type}")
    
    registry_entry = BENCHMARK_REGISTRY[benchmark_type]
    
    if registry_entry["class"] is None:
        raise ImportError(f"Benchmark type '{benchmark_type}' is not available (module not found)")
    
    return {
        "type": benchmark_type,
        "class": registry_entry["class"].__name__,
        "module": registry_entry["module"],
        "description": registry_entry["description"],
    }


__all__ = [
    # Basic benchmarks
    "BenchmarkSuite",
    "run_benchmarks",
    # Comprehensive benchmarks
    "ComprehensiveBenchmarkSystem",
    "BenchmarkConfig",
    "run_comprehensive_benchmarks",
    # Olympiad benchmarks
    "OlympiadBenchmarkSuite",
    "OlympiadBenchmarkConfig",
    "OlympiadProblem",
    "ProblemCategory",
    "DifficultyLevel",
    "get_olympiad_benchmark_config",
    # TensorFlow benchmarks
    "TensorFlowBenchmarkSystem",
    "run_tensorflow_benchmarks",
    # Unified factory
    "create_benchmark",
    # Registry
    "BENCHMARK_REGISTRY",
    "list_available_benchmarks",
    "get_benchmark_info",
]

