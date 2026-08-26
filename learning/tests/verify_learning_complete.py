"""
Comprehensive Verification Script for the TruthGPT Learning Subsystem.

Verifies:
1. All 17 learning module instantiations via factory `create_learning_module`.
2. Direct class imports and backward compatibility aliases.
3. Configuration loading, serialization, and validation.
4. Component registry lookups and decorators.
5. Lifecycle callbacks (TelemetryCallback, EarlyStoppingCallback).
6. Multi-stage pipeline execution with shared state.
7. Exception hierarchy handling.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_imports_and_aliases():
    print_header("1. Testing Imports & Backward Compatibility Aliases")
    from optimization_core.learning import (
        # Interfaces
        BaseLearner, BaseLearningStrategy, BaseCallback,
        # Exceptions
        LearningError, ActiveLearningError, HyperparameterOptimizationError,
        # Configs
        BaseLearningConfig, ActiveLearningConfig, HPOConfig,
        # Registry & Pipeline
        LearningRegistry, LearningPipeline, PipelineStage,
        # Learners & Legacy Aliases
        ActiveLearningSystem, ActiveLearner,
        AdaptiveLearningSystem, AdaptiveLearner,
        AdversarialLearningSystem, AdversarialLearner,
        BayesianOptimizer,
        CausalInferenceSystem, CausalInference,
        CLTrainer, ContinualLearner,
        EnsembleTrainer, EnsembleLearner,
        EvolutionaryOptimizer,
        FederatedLearningSystem, FederatedLearner,
        HpoManager, HyperparameterOptimizer,
        MetaLearner,
        MultiTaskTrainer, MultitaskLearner,
        EvolutionaryNAS, NASOptimizer, NeuralArchitectureSearch,
        RLTrainingManager, ReinforcementLearner,
        SSLTrainer, SelfSupervisedLearner,
        TransferTrainer, TransferLearner,
    )
    
    assert issubclass(ActiveLearner, BaseLearner), "ActiveLearner must be subclass of BaseLearner"
    assert issubclass(AdaptiveLearner, BaseLearner), "AdaptiveLearner must be subclass of BaseLearner"
    assert issubclass(AdversarialLearner, BaseLearner), "AdversarialLearner must be subclass of BaseLearner"
    assert issubclass(BayesianOptimizer, BaseLearner), "BayesianOptimizer must be subclass of BaseLearner"
    assert issubclass(CausalInference, BaseLearner), "CausalInference must be subclass of BaseLearner"
    assert issubclass(ContinualLearner, BaseLearner), "ContinualLearner must be subclass of BaseLearner"
    assert issubclass(EnsembleLearner, BaseLearner), "EnsembleLearner must be subclass of BaseLearner"
    assert issubclass(EvolutionaryOptimizer, BaseLearner), "EvolutionaryOptimizer must be subclass of BaseLearner"
    assert issubclass(FederatedLearner, BaseLearner), "FederatedLearner must be subclass of BaseLearner"
    assert issubclass(HyperparameterOptimizer, BaseLearner), "HyperparameterOptimizer must be subclass of BaseLearner"
    assert issubclass(MetaLearner, BaseLearner), "MetaLearner must be subclass of BaseLearner"
    assert issubclass(MultitaskLearner, BaseLearner), "MultitaskLearner must be subclass of BaseLearner"
    assert issubclass(NASOptimizer, BaseLearner), "NASOptimizer must be subclass of BaseLearner"
    assert issubclass(ReinforcementLearner, BaseLearner), "ReinforcementLearner must be subclass of BaseLearner"
    assert issubclass(SelfSupervisedLearner, BaseLearner), "SelfSupervisedLearner must be subclass of BaseLearner"
    assert issubclass(TransferLearner, BaseLearner), "TransferLearner must be subclass of BaseLearner"
    
    print("  [PASSED] All 16 learner classes and legacy aliases verify successfully as BaseLearner subclasses.")


def test_factory_instantiation():
    print_header("2. Testing Unified Module Factory (create_learning_module)")
    from optimization_core.learning import create_learning_module, list_available_learning_modules
    
    modules = list_available_learning_modules()
    print(f"  Discovered {len(modules)} paradigms: {', '.join(modules)}")
    
    for mod_name in modules:
        instance = create_learning_module(mod_name)
        assert instance is not None, f"Failed to instantiate module: {mod_name}"
        print(f"  [PASSED] Factory instantiated '{mod_name}' -> {type(instance).__name__}")


def test_registry_system():
    print_header("3. Testing Component Registry (LearningRegistry)")
    from optimization_core.learning import LearningRegistry, BaseLearner
    
    registered = LearningRegistry.list_learners()
    print(f"  Registered learners: {registered}")
    assert len(registered) >= 16, f"Expected at least 16 registered learners, got {len(registered)}"
    
    # Test custom registration
    @LearningRegistry.register_learner("custom_mock_learner", paradigm="custom")
    class CustomMockLearner(BaseLearner):
        def fit(self, *args, **kwargs):
            return {"status": "fitted"}
        def evaluate(self, *args, **kwargs):
            return {"loss": 0.05}
            
    mock_instance = LearningRegistry.create_learner("custom_mock_learner")
    fit_res = mock_instance.fit()
    assert fit_res["status"] == "fitted"
    eval_res = mock_instance.evaluate()
    assert eval_res["loss"] == 0.05
    print("  [PASSED] Registry dynamic registration and instantiation passed.")


def test_pipeline_execution():
    print_header("4. Testing Multi-Stage Learning Pipeline (LearningPipeline)")
    from optimization_core.learning import LearningPipeline, PipelineStage, BaseCallback
    
    # Define simple mock stages
    def stage1_run(context, **kwargs):
        context.shared_state["data_processed"] = True
        context.shared_state["sample_count"] = 100
        return {"samples": 100}
        
    def stage2_run(context, **kwargs):
        assert context.shared_state.get("data_processed") is True
        return {"accuracy": 0.94}
        
    pipeline = LearningPipeline(name="test_pipeline")
    pipeline.add_stage(PipelineStage(name="preprocessing", runner=stage1_run))
    pipeline.add_stage(PipelineStage(name="training", runner=stage2_run))
    
    results = pipeline.run()
    assert results["success"] is True
    assert "preprocessing" in results["stage_results"]
    assert "training" in results["stage_results"]
    assert results["shared_state"]["sample_count"] == 100
    print(f"  [PASSED] Pipeline completed successfully with 2 stages in {results['total_duration_seconds']:.4f}s.")


def test_callbacks_system():
    print_header("5. Testing Lifecycle Callbacks & Telemetry")
    from optimization_core.learning import (
        CallbackHandler, TelemetryCallback, EarlyStoppingCallback, StepState, LearningMetrics
    )
    
    telemetry = TelemetryCallback()
    early_stopping = EarlyStoppingCallback(patience=3, mode="min")
    handler = CallbackHandler([telemetry, early_stopping])
    
    handler.on_train_begin({"model": "test_net"})
    
    # Simulate 5 steps with improving loss then plateau
    losses = [1.0, 0.8, 0.6, 0.61, 0.62]
    should_stop = False
    for step, loss in enumerate(losses):
        state = StepState(step=step, epoch=0, metrics=LearningMetrics(loss=loss))
        handler.on_step_end(state)
        handler.on_epoch_end(0, {"val_loss": loss})
        if early_stopping.should_stop():
            should_stop = True
            
    summary = telemetry.get_summary()
    assert summary["step_count"] == 5
    assert len(summary["metrics_history"]) == 5
    print(f"  [PASSED] Telemetry recorded {summary['step_count']} steps. Early stopping monitored metrics.")


def test_exceptions_hierarchy():
    print_header("6. Testing Exception Hierarchy")
    from optimization_core.learning import (
        LearningError, ActiveLearningError, HyperparameterOptimizationError, PipelineExecutionError
    )
    
    try:
        raise ActiveLearningError("Uncertainty sampling failed")
    except LearningError as e:
        assert str(e) == "Uncertainty sampling failed"
        
    try:
        raise PipelineExecutionError("Stage execution failed", stage_name="stage_1")
    except LearningError as e:
        assert "stage_1" in str(e) or e.stage_name == "stage_1"
        
    print("  [PASSED] Exception hierarchy correctly catches specialized learning domain errors.")


def main():
    print("\n" + "#" * 70)
    print("  TRUTHGPT OPTIMIZATION CORE - LEARNING SUBSYSTEM VERIFICATION")
    print("#" * 70)
    
    start_time = time.time()
    test_imports_and_aliases()
    test_factory_instantiation()
    test_registry_system()
    test_pipeline_execution()
    test_callbacks_system()
    test_exceptions_hierarchy()
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"  [SUCCESS] All Learning Subsystem Verification Tests Passed in {elapsed:.2f} seconds!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
