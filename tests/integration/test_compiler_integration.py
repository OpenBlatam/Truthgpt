"""
TruthGPT Compiler Integration Tests
Comprehensive test suite for compiler infrastructure integration
"""

import unittest
import logging
import time
import sys
from pathlib import Path
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Any, Optional

# Add workspace path
_root = str(Path(__file__).parent.parent.parent.resolve())
if _root not in sys.path:
    sys.path.insert(0, _root)

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Import components to test
from compiler_integration import (
    TruthGPTCompilerIntegration, TruthGPTCompilationConfig, TruthGPTCompilationResult,
    create_truthgpt_compiler_integration
)

from compiler import (
    CompilationTarget, OptimizationLevel, CompilationConfig,
    create_compiler_core, CompilationResult
)

class TestModel(nn.Module):
    """Simple test model for compiler testing"""
    
    def __init__(self, input_size: int = 100, hidden_size: int = 50, output_size: int = 10):
        super().__init__()
        self.linear1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.linear2 = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        x = self.linear1(x)
        x = self.relu(x)
        x = self.linear2(x)
        return x

class MockOptimizer:
    """Mock optimizer for testing"""
    
    def __init__(self, name: str = "MockOptimizer"):
        self.name = name
        self.optimization_count = 0
        
    def optimize(self, model: Any) -> Any:
        self.optimization_count += 1
        return model

class TestTruthGPTCompilerIntegration(unittest.TestCase):
    """Test suite for TruthGPT compiler integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_model = TestModel()
        self.mock_optimizer = MockOptimizer("TestOptimizer")
        
        # Create test configuration
        self.test_config = TruthGPTCompilationConfig(
            primary_compiler="aot",
            fallback_compilers=["jit", "mlir"],
            optimization_level=OptimizationLevel.STANDARD,
            target_platform=CompilationTarget.CPU,
            enable_truthgpt_optimizations=True,
            enable_profiling=True,
            enable_benchmarking=True,
            auto_select_compiler=True
        )
    
    def test_compiler_integration_creation(self):
        """Test compiler integration creation"""
        integration = create_truthgpt_compiler_integration(self.test_config)
        
        self.assertIsInstance(integration, TruthGPTCompilerIntegration)
        self.assertIsNotNone(integration.compilers)
        self.assertIsInstance(integration.compilers, dict)
        self.assertGreater(len(integration.compilers), 0)
    
    def test_compilation_without_optimizer(self):
        """Test compilation without TruthGPT optimizer"""
        integration = create_truthgpt_compiler_integration(self.test_config)
        
        result = integration.compile_truthgpt_model(self.test_model)
        
        self.assertIsInstance(result, TruthGPTCompilationResult)
        self.assertIsNotNone(result.primary_compiler_used)
        self.assertIsInstance(result.compilation_results, dict)
        self.assertIsInstance(result.performance_metrics, dict)
        self.assertIsInstance(result.optimization_report, dict)
    
    def test_compilation_with_optimizer(self):
        """Test compilation with TruthGPT optimizer"""
        integration = create_truthgpt_compiler_integration(self.test_config)
        
        result = integration.compile_truthgpt_model(self.test_model, self.mock_optimizer)
        
        self.assertIsInstance(result, TruthGPTCompilationResult)
        self.assertIsNotNone(result.primary_compiler_used)
        self.assertIsInstance(result.compilation_results, dict)
        self.assertGreater(self.mock_optimizer.optimization_count, 0)
    
    def test_compiler_selection(self):
        """Test automatic compiler selection"""
        integration = create_truthgpt_compiler_integration(self.test_config)
        
        small_model = TestModel(10, 5, 2)
        large_model = TestModel(1000, 500, 100)
        
        small_result = integration.compile_truthgpt_model(small_model)
        large_result = integration.compile_truthgpt_model(large_model)
        
        self.assertIsNotNone(small_result.primary_compiler_used)
        self.assertIsNotNone(large_result.primary_compiler_used)

class TestCompilerCore(unittest.TestCase):
    """Test suite for core compiler functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_model = TestModel()
        self.test_config = CompilationConfig(
            target=CompilationTarget.CPU,
            optimization_level=OptimizationLevel.STANDARD,
            enable_quantization=True,
            enable_fusion=True
        )
    
    def test_compiler_core_creation(self):
        """Test compiler core creation"""
        compiler = create_compiler_core(self.test_config)
        
        self.assertIsNotNone(compiler)
        self.assertEqual(compiler.config.target, CompilationTarget.CPU)
        self.assertEqual(compiler.config.optimization_level, OptimizationLevel.STANDARD)

def run_compiler_tests():
    """Run all compiler integration tests"""
    test_suite = unittest.TestSuite()
    test_classes = [
        TestTruthGPTCompilerIntegration,
        TestCompilerCore
    ]
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_compiler_tests()
    exit(0 if success else 1)
