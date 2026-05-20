"""
Pytest configuration for TruthGPT optimization core tests
Provides shared fixtures and configuration for all tests
"""

import pytest
import torch
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tests.fixtures.test_data import TestDataFactory
from tests.fixtures.mock_components import MockModel, MockOptimizer, MockAttention, MockMLP, MockKVCache, MockDataset
from tests.fixtures.test_utils import TestUtils, PerformanceProfiler, MemoryTracker

@pytest.fixture(scope="session")
def test_data_factory():
    """Provide test data factory for all tests"""
    return TestDataFactory()

@pytest.fixture(scope="session")
def test_utils():
    """Provide test utilities for all tests"""
    return TestUtils()

@pytest.fixture(scope="function")
def profiler():
    """Provide performance profiler for each test"""
    return PerformanceProfiler()

@pytest.fixture(scope="function")
def memory_tracker():
    """Provide memory tracker for each test"""
    return MemoryTracker()

@pytest.fixture(scope="function")
def mock_model():
    """Provide mock model for testing"""
    return MockModel(input_size=512, hidden_size=1024, output_size=512)

@pytest.fixture(scope="function")
def mock_optimizer():
    """Provide mock optimizer for testing"""
    return MockOptimizer(learning_rate=0.001)

@pytest.fixture(scope="function")
def mock_attention():
    """Provide mock attention for testing"""
    return MockAttention(d_model=512, n_heads=8)

@pytest.fixture(scope="function")
def mock_mlp():
    """Provide mock MLP for testing"""
    return MockMLP(input_size=512, hidden_size=2048, output_size=512)

@pytest.fixture(scope="function")
def mock_kv_cache():
    """Provide mock KV cache for testing"""
    return MockKVCache(max_size=1000)

@pytest.fixture(scope="function")
def mock_dataset():
    """Provide mock dataset for testing"""
    return MockDataset(size=100, input_size=512, output_size=512)

@pytest.fixture(scope="function")
def test_config():
    """Provide test configuration"""
    return TestUtils.create_test_config()

@pytest.fixture(scope="function")
def attention_data(test_data_factory):
    """Provide attention test data"""
    return test_data_factory.create_attention_data()

@pytest.fixture(scope="function")
def mlp_data(test_data_factory):
    """Provide MLP test data"""
    return test_data_factory.create_mlp_data()

@pytest.fixture(scope="function")
def optimization_data(test_data_factory):
    """Provide optimization test data"""
    return test_data_factory.create_optimization_data()

@pytest.fixture(scope="function")
def kv_cache_data(test_data_factory):
    """Provide KV cache test data"""
    return test_data_factory.create_kv_cache_data()

@pytest.fixture(scope="function")
def transformer_data(test_data_factory):
    """Provide transformer test data"""
    return test_data_factory.create_transformer_data()

@pytest.fixture(scope="function")
def quantization_data(test_data_factory):
    """Provide quantization test data"""
    return test_data_factory.create_quantization_data()

@pytest.fixture(scope="function")
def benchmark_data(test_data_factory):
    """Provide benchmark test data"""
    return test_data_factory.create_benchmark_data()

@pytest.fixture(scope="function")
def error_cases(test_data_factory):
    """Provide error test cases"""
    return test_data_factory.create_error_cases()

@pytest.fixture(scope="function")
def performance_data(test_data_factory):
    """Provide performance test data"""
    return test_data_factory.create_performance_data()

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test"""
    # Set random seed for reproducibility
    torch.manual_seed(42)
    
    # Clear CUDA cache if available
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    yield
    
    # Cleanup after each test
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

@pytest.fixture(scope="session")
def device():
    """Provide device for testing"""
    if torch.cuda.is_available():
        return torch.device("cuda")
    else:
        return torch.device("cpu")

@pytest.fixture(scope="function")
def temp_model():
    """Provide temporary model for testing"""
    model = MockModel(input_size=256, hidden_size=512, output_size=256)
    yield model
    # Cleanup is automatic

@pytest.fixture(scope="function")
def temp_optimizer():
    """Provide temporary optimizer for testing"""
    optimizer = MockOptimizer(learning_rate=0.001)
    yield optimizer
    # Cleanup is automatic

@pytest.fixture(scope="function")
def temp_cache():
    """Provide temporary cache for testing"""
    cache = MockKVCache(max_size=100)
    yield cache
    # Cleanup is automatic

# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        # Add markers based on file path
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)
        
        # Add slow marker for tests that take longer
        if "benchmark" in str(item.fspath) or "performance" in str(item.fspath):
            item.add_marker(pytest.mark.slow)

# Test configuration
pytest_plugins = []

# Global test configuration
TEST_CONFIG = {
    "verbose": True,
    "parallel": False,
    "coverage": True,
    "performance": True,
    "integration": True
}




