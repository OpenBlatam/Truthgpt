import os
import sys
import logging
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Ensure root directory is in sys.path when run directly
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

logger = logging.getLogger(__name__)


@dataclass
class TestConfig:
    """Configuration for test execution"""
    __test__ = False
    verbose: bool = False
    parallel: bool = False
    timeout: float = 300.0  # 5 minutes
    coverage: bool = False
    benchmark: bool = False
    output_file: Optional[str] = None
    filter_tests: Optional[List[str]] = None


@dataclass
class TestResult:
    """Result of test execution"""
    __test__ = False
    test_name: str
    success: bool
    execution_time: float
    error_message: Optional[str] = None
    performance_metrics: Optional[Dict[str, float]] = None
    coverage_data: Optional[Dict[str, Any]] = None


class TestSuite:
    """Test suite for compiler components"""
    __test__ = False
    
    def __init__(self, name: str):
        self.name = name
        self.tests = []
        self.setup_methods = []
        self.teardown_methods = []
        
    def add_test(self, test_method):
        """Add a test method to the suite"""
        self.tests.append(test_method)

    def add_test_case(self, test_case_class):
        """Add all test methods from a TestCase class"""
        import unittest
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(test_case_class)
        for test in suite:
            test_method = getattr(test, test._testMethodName)
            self.tests.append(test_method)
        
    def add_setup(self, setup_method):
        """Add a setup method"""
        self.setup_methods.append(setup_method)
        
    def add_teardown(self, teardown_method):
        """Add a teardown method"""
        self.teardown_methods.append(teardown_method)
        
    def run_tests(self, config: TestConfig) -> List[TestResult]:
        """Run all tests in the suite"""
        results = []
        
        # Run setup methods
        for setup_method in self.setup_methods:
            try:
                setup_method()
            except Exception as e:
                logger.error(f"Setup method failed: {str(e)}")
                return results
        
        # Run tests
        for test_method in self.tests:
            result = self._run_single_test(test_method, config)
            results.append(result)
        
        # Run teardown methods
        for teardown_method in self.teardown_methods:
            try:
                teardown_method()
            except Exception as e:
                logger.error(f"Teardown method failed: {str(e)}")
        
        return results
    
    def _run_single_test(self, test_method, config: TestConfig) -> TestResult:
        """Run a single test method"""
        test_name = getattr(test_method, '__name__', str(test_method))
        start_time = time.time()
        
        try:
            if config.verbose:
                logger.info(f"Running test: {test_name}")
            
            # Run the test
            test_method()
            
            execution_time = time.time() - start_time
            
            if config.verbose:
                logger.info(f"Test {test_name} passed in {execution_time:.3f}s")
            
            return TestResult(
                test_name=test_name,
                success=True,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            if config.verbose:
                logger.error(f"Test {test_name} failed in {execution_time:.3f}s: {str(e)}")
            
            return TestResult(
                test_name=test_name,
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )


class TestRunner:
    """Main test runner for compiler tests"""
    __test__ = False
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.test_suites = {}
        self.results = []
        
    def add_test_suite(self, suite: TestSuite):
        """Add a test suite"""
        self.test_suites[suite.name] = suite
        
    def run_all_tests(self) -> Dict[str, List[TestResult]]:
        """Run all test suites"""
        all_results = {}
        
        for suite_name, suite in self.test_suites.items():
            logger.info(f"Running test suite: {suite_name}")
            
            suite_results = suite.run_tests(self.config)
            all_results[suite_name] = suite_results
            
            # Log summary
            passed = sum(1 for r in suite_results if r.success)
            total = len(suite_results)
            logger.info(f"Suite {suite_name}: {passed}/{total} tests passed")
        
        self.results = all_results
        return all_results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate test report"""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_time = 0.0
        
        for suite_name, results in self.results.items():
            for result in results:
                total_tests += 1
                total_time += result.execution_time
                if result.success:
                    total_passed += 1
                else:
                    total_failed += 1
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "success_rate": total_passed / total_tests if total_tests > 0 else 0.0,
                "total_time": total_time
            },
            "suites": {}
        }
        
        for suite_name, results in self.results.items():
            suite_passed = sum(1 for r in results if r.success)
            suite_total = len(results)
            suite_time = sum(r.execution_time for r in results)
            
            report["suites"][suite_name] = {
                "total_tests": suite_total,
                "passed": suite_passed,
                "failed": suite_total - suite_passed,
                "success_rate": suite_passed / suite_total if suite_total > 0 else 0.0,
                "total_time": suite_time,
                "tests": [
                    {
                        "name": r.test_name,
                        "success": r.success,
                        "execution_time": r.execution_time,
                        "error": r.error_message
                    }
                    for r in results
                ]
            }
        
        return report
    
    def save_report(self, filename: str):
        """Save test report to file"""
        report = self.generate_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Test report saved to: {filename}")


def create_test_runner(config: TestConfig) -> TestRunner:
    """Create a test runner instance"""
    return TestRunner(config)


def run_all_tests(config: TestConfig = None) -> Dict[str, List[TestResult]]:
    """Run all compiler tests"""
    try:
        from .test_compiler_core import TestCompilerCore
        from .test_aot_compiler import TestAOTCompiler
        from .test_jit_compiler import TestJITCompiler
        from .test_mlir_compiler import TestMLIRCompiler
        from .test_plugin_system import TestPluginSystem
        from .test_tf2tensorrt import TestTF2TensorRT
        from .test_tf2xla import TestTF2XLA
        from .test_runtime_compiler import TestRuntimeCompiler
        from .test_distributed_compiler import TestDistributedCompiler
        from .test_neural_compiler import TestNeuralCompiler
        from .test_kernel_compiler import TestKernelCompiler
    except ImportError:
        from compiler.tests.test_compiler_core import TestCompilerCore
        from compiler.tests.test_aot_compiler import TestAOTCompiler
        from compiler.tests.test_jit_compiler import TestJITCompiler
        from compiler.tests.test_mlir_compiler import TestMLIRCompiler
        from compiler.tests.test_plugin_system import TestPluginSystem
        from compiler.tests.test_tf2tensorrt import TestTF2TensorRT
        from compiler.tests.test_tf2xla import TestTF2XLA
        from compiler.tests.test_runtime_compiler import TestRuntimeCompiler
        from compiler.tests.test_distributed_compiler import TestDistributedCompiler
        from compiler.tests.test_neural_compiler import TestNeuralCompiler
        from compiler.tests.test_kernel_compiler import TestKernelCompiler

    if config is None:
        config = TestConfig()
    
    runner = create_test_runner(config)
    
    # Add test suites using dynamic test case discovery
    core_suite = TestSuite("compiler_core")
    core_suite.add_test_case(TestCompilerCore)
    runner.add_test_suite(core_suite)
    
    aot_suite = TestSuite("aot_compiler")
    aot_suite.add_test_case(TestAOTCompiler)
    runner.add_test_suite(aot_suite)
    
    jit_suite = TestSuite("jit_compiler")
    jit_suite.add_test_case(TestJITCompiler)
    runner.add_test_suite(jit_suite)
    
    mlir_suite = TestSuite("mlir_compiler")
    mlir_suite.add_test_case(TestMLIRCompiler)
    runner.add_test_suite(mlir_suite)
    
    plugin_suite = TestSuite("plugin_system")
    plugin_suite.add_test_case(TestPluginSystem)
    runner.add_test_suite(plugin_suite)
    
    tensorrt_suite = TestSuite("tf2tensorrt")
    tensorrt_suite.add_test_case(TestTF2TensorRT)
    runner.add_test_suite(tensorrt_suite)
    
    xla_suite = TestSuite("tf2xla")
    xla_suite.add_test_case(TestTF2XLA)
    runner.add_test_suite(xla_suite)

    runtime_suite = TestSuite("runtime_compiler")
    runtime_suite.add_test_case(TestRuntimeCompiler)
    runner.add_test_suite(runtime_suite)

    distributed_suite = TestSuite("distributed_compiler")
    distributed_suite.add_test_case(TestDistributedCompiler)
    runner.add_test_suite(distributed_suite)

    neural_suite = TestSuite("neural_compiler")
    neural_suite.add_test_case(TestNeuralCompiler)
    runner.add_test_suite(neural_suite)

    kernel_suite = TestSuite("kernel_compiler")
    kernel_suite.add_test_case(TestKernelCompiler)
    runner.add_test_suite(kernel_suite)
    
    # Run all tests
    return runner.run_all_tests()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = run_all_tests(TestConfig(verbose=True))
    total_passed = sum(sum(1 for r in res if r.success) for res in results.values())
    total_count = sum(len(res) for res in results.values())
    print(f"\n==========================================")
    print(f"Compiler Test Summary: {total_passed}/{total_count} tests passed")
    print(f"==========================================\n")
