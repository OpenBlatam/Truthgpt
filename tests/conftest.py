"""
Pytest Configuration and Shared Fixtures for TruthGPT Optimization Core.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest
import torch

# Ensure optimization_core root and its parent are on sys.path so that both
# `import optimization_core` and `import tests` (as a sub-package) resolve.
_project_dir = Path(__file__).parent.parent
_parent_dir = _project_dir.parent

if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))
if str(_project_dir) not in sys.path:
    sys.path.insert(0, str(_project_dir))
else:
    # Ensure project_dir has higher precedence than parent_dir
    sys.path.remove(str(_project_dir))
    sys.path.insert(0, str(_project_dir))

# Bootstrap the 'tests' package in sys.modules before importing from it.
# Pytest loads conftest.py before the normal module system has initialized
# the parent package, so sub-package imports like 'tests.fixtures' would fail.
import types as _types_mod
_tests_dir = Path(__file__).parent
if "tests" not in sys.modules or not hasattr(sys.modules.get("tests"), "__path__"):
    _pkg = _types_mod.ModuleType("tests")
    _pkg.__path__ = [str(_tests_dir)]
    _pkg.__file__ = str(_tests_dir / "__init__.py")
    _pkg.__package__ = "tests"
    sys.modules["tests"] = _pkg

from tests.fixtures.test_data import TestDataFactory
from tests.fixtures.mock_components import (
    MockModel,
    MockOptimizer,
    MockAttention,
    MockMLP,
    MockKVCache,
    MockDataset,
    MockTokenizer,
    MockTrainer,
    MockCompiler,
    MockAgent,
    MockEvaluator,
)
from tests.fixtures.test_utils import (
    TestUtils,
    PerformanceProfiler,
    MemoryTracker,
    TestAssertions,
)


@pytest.fixture(scope="session")
def backend_availability() -> dict[str, bool]:
    """Inspect and return available native polyglot backends."""
    availability = {
        "rust": False,
        "cpp": False,
        "julia": False,
        "python": True,
        "cuda": torch.cuda.is_available(),
        "mps": hasattr(torch.backends, "mps") and torch.backends.mps.is_available(),
    }
    try:
        import truthgpt_rust  # type: ignore
        availability["rust"] = True
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        import _cpp_core  # type: ignore
        availability["cpp"] = True
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from julia import TruthGPTCore  # type: ignore
        availability["julia"] = True
    except (ImportError, ModuleNotFoundError):
        pass

    return availability


@pytest.fixture(scope="session")
def test_data_factory() -> TestDataFactory:
    """Provide TestDataFactory instance."""
    return TestDataFactory()


@pytest.fixture(scope="session")
def test_utils() -> TestUtils:
    """Provide TestUtils helper class instance."""
    return TestUtils()


@pytest.fixture(scope="function")
def profiler() -> PerformanceProfiler:
    """Provide a fresh PerformanceProfiler per test function."""
    p = PerformanceProfiler()
    yield p
    p.reset()


@pytest.fixture(scope="function")
def memory_tracker() -> MemoryTracker:
    """Provide a fresh MemoryTracker per test function."""
    m = MemoryTracker()
    yield m
    m.reset()


@pytest.fixture(scope="function")
def mock_model() -> MockModel:
    """Provide standard MockModel instance."""
    return MockModel(input_size=512, hidden_size=1024, output_size=512)


@pytest.fixture(scope="function")
def mock_optimizer() -> MockOptimizer:
    """Provide standard MockOptimizer instance."""
    return MockOptimizer(learning_rate=0.001)


@pytest.fixture(scope="function")
def mock_attention() -> MockAttention:
    """Provide standard MockAttention instance."""
    return MockAttention(d_model=512, n_heads=8)


@pytest.fixture(scope="function")
def mock_mlp() -> MockMLP:
    """Provide standard MockMLP instance."""
    return MockMLP(input_size=512, hidden_size=2048, output_size=512)


@pytest.fixture(scope="function")
def mock_kv_cache() -> MockKVCache:
    """Provide standard MockKVCache instance."""
    return MockKVCache(max_size=1000)


@pytest.fixture(scope="function")
def mock_dataset() -> MockDataset:
    """Provide standard MockDataset instance."""
    return MockDataset(size=100, input_size=512, output_size=512)


@pytest.fixture(scope="function")
def mock_tokenizer() -> MockTokenizer:
    """Provide standard MockTokenizer instance."""
    return MockTokenizer(vocab_size=1000)


@pytest.fixture(scope="function")
def sample_texts(test_data_factory: TestDataFactory) -> list[str]:
    """Provide sample synthetic text strings."""
    return test_data_factory.create_text_samples(num_samples=10)


@pytest.fixture(scope="function")
def sample_tensors(test_data_factory: TestDataFactory) -> dict[str, torch.Tensor]:
    """Provide sample attention tensors."""
    return test_data_factory.create_attention_data()


@pytest.fixture(scope="session")
def device() -> torch.device:
    """Return primary torch device for testing."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set random seed and clear device caches before and after each test."""
    torch.manual_seed(42)
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    yield
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


@pytest.fixture(scope="session", autouse=True)
def isolate_truthgpt_cloud_storage(tmp_path_factory):
    """
    Isolate TruthGPT Cloud storage during test sessions.
    Copies the baseline subscriptions database to a temporary location so
    that running tests never pollutes or modifies the repository's cloud_subscriptions_db.json.
    """
    import os
    import shutil

    base_cloud_dir = Path(__file__).resolve().parent.parent / "truthgpt_cloud"
    orig_db = base_cloud_dir / "cloud_subscriptions_db.json"

    temp_dir = tmp_path_factory.mktemp("truthgpt_cloud_storage")
    isolated_db = temp_dir / "cloud_subscriptions_db.json"

    if orig_db.exists():
        shutil.copy2(str(orig_db), str(isolated_db))
    else:
        isolated_db.write_text("{}", encoding="utf-8")

    old_env = os.environ.get("TRUTHGPT_STORAGE_PATH")
    os.environ["TRUTHGPT_STORAGE_PATH"] = str(isolated_db)

    try:
        import truthgpt_cloud.billing.subscription as sub_mod
        if hasattr(sub_mod, "subscription_manager"):
            sub_mod.subscription_manager.storage_path = str(isolated_db)
            sub_mod.subscription_manager._storage.filepath = str(isolated_db)
    except Exception:
        pass

    yield str(isolated_db)

    if old_env is not None:
        os.environ["TRUTHGPT_STORAGE_PATH"] = old_env
    else:
        os.environ.pop("TRUTHGPT_STORAGE_PATH", None)



def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "performance: marks tests as performance benchmarks")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "requires_rust: requires rust native backend")
    config.addinivalue_line("markers", "requires_cpp: requires cpp native backend")
    config.addinivalue_line("markers", "requires_julia: requires julia native backend")
    config.addinivalue_line("markers", "requires_cuda: requires CUDA GPU acceleration")


def pytest_collection_modifyitems(config, items):
    """Categorize and tag collected tests."""
    for item in items:
        path_str = str(item.fspath).lower()
        if "performance" in path_str or "benchmark" in path_str:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        elif "integration" in path_str:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)
