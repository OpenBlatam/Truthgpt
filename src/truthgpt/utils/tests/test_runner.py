"""
TruthGPT Enhanced Utils Test Runner
Run all TruthGPT enhanced utilities tests
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_all_tests():
    """Run all TruthGPT enhanced utilities tests."""
    print("🚀 Running TruthGPT Enhanced Utilities Test Suite")
    print("=" * 60)
    
    # Test files to run
    test_files = [
        "test_truthgpt_enhanced_utils.py",
        "test_truthgpt_advanced_training.py",
        "test_truthgpt_advanced_evaluation.py",
        "test_truthgpt_complete_integration.py",
        "test_truthgpt_package.py"
    ]
    
    # Run tests
    for test_file in test_files:
        print(f"\n📋 Running {test_file}...")
        try:
            result = pytest.main([test_file, "-v", "--tb=short"])
            if result == 0:
                print(f"✅ {test_file} passed")
            else:
                print(f"❌ {test_file} failed")
        except Exception as e:
            print(f"❌ Error running {test_file}: {e}")
    
    print("\n🎉 Test suite completed!")

def run_specific_test(test_file):
    """Run a specific test file."""
    print(f"🚀 Running {test_file}")
    print("=" * 60)
    
    try:
        result = pytest.main([test_file, "-v", "--tb=short"])
        if result == 0:
            print(f"✅ {test_file} passed")
        else:
            print(f"❌ {test_file} failed")
    except Exception as e:
        print(f"❌ Error running {test_file}: {e}")

def run_performance_tests():
    """Run performance tests only."""
    print("🚀 Running TruthGPT Performance Tests")
    print("=" * 60)
    
    performance_tests = [
        "test_truthgpt_enhanced_utils.py::TestTruthGPTEnhancedManager::test_optimize_model_enhanced",
        "test_truthgpt_advanced_training.py::TestTruthGPTTrainingPerformance",
        "test_truthgpt_advanced_evaluation.py::TestTruthGPTEvaluationPerformance"
    ]
    
    for test in performance_tests:
        print(f"\n📋 Running {test}...")
        try:
            result = pytest.main([test, "-v", "--tb=short"])
            if result == 0:
                print(f"✅ {test} passed")
            else:
                print(f"❌ {test} failed")
        except Exception as e:
            print(f"❌ Error running {test}: {e}")
    
    print("\n🎉 Performance tests completed!")

def run_integration_tests():
    """Run integration tests only."""
    print("🚀 Running TruthGPT Integration Tests")
    print("=" * 60)
    
    integration_tests = [
        "test_truthgpt_complete_integration.py",
        "test_truthgpt_package.py::TestTruthGPTPackageIntegration"
    ]
    
    for test in integration_tests:
        print(f"\n📋 Running {test}...")
        try:
            result = pytest.main([test, "-v", "--tb=short"])
            if result == 0:
                print(f"✅ {test} passed")
            else:
                print(f"❌ {test} failed")
        except Exception as e:
            print(f"❌ Error running {test}: {e}")
    
    print("\n🎉 Integration tests completed!")

def run_unit_tests():
    """Run unit tests only."""
    print("🚀 Running TruthGPT Unit Tests")
    print("=" * 60)
    
    unit_tests = [
        "test_truthgpt_enhanced_utils.py::TestTruthGPTEnhancedConfig",
        "test_truthgpt_enhanced_utils.py::TestTruthGPTPerformanceProfiler",
        "test_truthgpt_enhanced_utils.py::TestTruthGPTAdvancedOptimizer",
        "test_truthgpt_advanced_training.py::TestTruthGPTTrainingConfig",
        "test_truthgpt_advanced_training.py::TestTruthGPTAdvancedTrainer",
        "test_truthgpt_advanced_evaluation.py::TestTruthGPTEvaluationConfig",
        "test_truthgpt_advanced_evaluation.py::TestTruthGPTAdvancedEvaluator"
    ]
    
    for test in unit_tests:
        print(f"\n📋 Running {test}...")
        try:
            result = pytest.main([test, "-v", "--tb=short"])
            if result == 0:
                print(f"✅ {test} passed")
            else:
                print(f"❌ {test} failed")
        except Exception as e:
            print(f"❌ Error running {test}: {e}")
    
    print("\n🎉 Unit tests completed!")

def main():
    """Main test runner."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "all":
            run_all_tests()
        elif command == "performance":
            run_performance_tests()
        elif command == "integration":
            run_integration_tests()
        elif command == "unit":
            run_unit_tests()
        elif command == "specific":
            if len(sys.argv) > 2:
                test_file = sys.argv[2]
                run_specific_test(test_file)
            else:
                print("❌ Please specify a test file")
        else:
            print("❌ Unknown command. Available commands:")
            print("   - all: Run all tests")
            print("   - performance: Run performance tests")
            print("   - integration: Run integration tests")
            print("   - unit: Run unit tests")
            print("   - specific <test_file>: Run specific test file")
    else:
        print("🚀 TruthGPT Enhanced Utilities Test Runner")
        print("=" * 60)
        print("Available commands:")
        print("   - all: Run all tests")
        print("   - performance: Run performance tests")
        print("   - integration: Run integration tests")
        print("   - unit: Run unit tests")
        print("   - specific <test_file>: Run specific test file")
        print("\nExample usage:")
        print("   python test_runner.py all")
        print("   python test_runner.py performance")
        print("   python test_runner.py specific test_truthgpt_enhanced_utils.py")

if __name__ == "__main__":
    main()
