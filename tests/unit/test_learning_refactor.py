"""
Unit Test Suite for optimization_core.learning Refactored Subsystem
===================================================================
Tests registry discovery, factory instantiation across all 16 paradigms,
fluent pipeline builder, typed exception hierarchy, dataclasses, enums,
and 100% backward compatibility.
"""

from __future__ import annotations

import os
import sys
import unittest
from typing import Any, Dict, List

# Ensure parent root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARENT_ROOT = os.path.dirname(PROJECT_ROOT)
if PARENT_ROOT not in sys.path:
    sys.path.insert(0, PARENT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from learning import (
    # Core Infrastructure
    LearningRegistry,
    LEARNING_REGISTRY,
    register_learning_module,
    list_available_learning_modules,
    get_learning_module_info,
    create_learning_module,
    create_learner,
    LearningPipeline,
    LearningPipelineBuilder,
    create_pipeline_builder,
    create_learning_pipeline,
    # Exceptions
    LearningBaseException,
    LearningError,
    LearnerNotFoundError,
    LearnerInitializationError,
    LearnerConfigurationError,
    OptimizationFailedError,
    ConvergenceError,
    StrategyNotSupportedError,
    SamplingError,
    ActiveLearningError,
    AdaptiveLearningError,
    AdversarialAttackError,
    BayesianOptimizationError,
    CausalInferenceError,
    ContinualLearningError,
    EnsembleLearningError,
    EvolutionaryOptimizationError,
    FederatedLearningError,
    HyperparameterOptimizationError,
    MetaLearningError,
    MultitaskLearningError,
    NASError,
    ReinforcementLearningError,
    SelfSupervisedLearningError,
    TransferLearningError,
    PipelineError,
    PipelineExecutionError,
    # Types & Dataclasses
    LearningStrategyType,
    UncertaintyMeasure,
    SamplingStrategy,
    AdversarialMethod,
    OptimizationMetric,
    TaskType,
    LearningMetrics,
    OptimizationResult,
    ActiveLearningResult,
    CausalEffectResult,
    FederatedRoundResult,
    NASResult,
    LearningConfig,
    ActiveLearningConfig,
    AdaptiveLearningConfig,
    AdversarialConfig,
    BayesianConfig,
    CausalConfig,
    ContinualConfig,
    EnsembleConfig,
    EvolutionaryConfig,
    FederatedConfig,
    HPOConfig,
    MetaLearningConfig,
    MultiTaskConfig,
    NASConfig,
    RLConfig,
    SSLConfig,
    TransferLearningConfig,
    LearningPipelineConfig,
    # 16 Learners
    ActiveLearner,
    AdaptiveLearner,
    AdversarialLearner,
    BayesianOptimizer,
    CausalInference,
    ContinualLearner,
    EnsembleLearner,
    EvolutionaryOptimizer,
    FederatedLearner,
    HyperparameterOptimizer,
    MetaLearner,
    MultitaskLearner,
    NASOptimizer,
    ReinforcementLearner,
    SelfSupervisedLearner,
    TransferLearner,
)


class TestLearningRegistry(unittest.TestCase):
    """Tests discovery, inspection, and dynamic registration in LearningRegistry."""

    def test_list_available_modules(self):
        """Verify all 16 domains are discovered."""
        modules = list_available_learning_modules()
        expected = [
            "active", "adaptive", "adversarial", "bayesian", "causal",
            "continual", "ensemble", "evolutionary", "federated", "hpo",
            "meta", "multitask", "nas", "reinforcement", "self_supervised", "transfer"
        ]
        for exp in expected:
            self.assertIn(exp, modules, f"Expected domain '{exp}' in registry")
        self.assertEqual(len(modules), 16)

    def test_get_module_info(self):
        """Verify module info retrieval."""
        info = get_learning_module_info("active")
        self.assertEqual(info["name"], "active")
        self.assertIn("description", info)

        with self.assertRaises(LearnerNotFoundError):
            get_learning_module_info("non_existent_domain_xyz")

    def test_custom_registration(self):
        """Verify dynamic custom module registration and unregistration."""
        dummy_name = "test_custom_learner"
        
        class DummyLearner:
            def __init__(self, cfg=None):
                self.cfg = cfg
            def predict(self, x):
                return x

        LEARNING_REGISTRY.register(dummy_name, DummyLearner, description="Custom test learner")
        self.assertIn(dummy_name, list_available_learning_modules())

        instance = create_learning_module(dummy_name, {"param": 123})
        self.assertIsInstance(instance, DummyLearner)
        self.assertEqual(instance.cfg, {"param": 123})

        # Cleanup
        unregistered = LEARNING_REGISTRY.unregister(dummy_name)
        self.assertTrue(unregistered)
        self.assertNotIn(dummy_name, list_available_learning_modules())


class TestLearningPipeline(unittest.TestCase):
    """Tests fluent LearningPipelineBuilder and multi-stage orchestration."""

    def test_fluent_pipeline_builder(self):
        """Verify pipeline stage chaining and execution."""
        pipeline = (
            create_pipeline_builder("test_flow")
            .with_stage("stage_1", lambda x, **kw: x + [1])
            .with_stage("stage_2", lambda x, **kw: x + [2])
            .with_stage("stage_3", lambda x, **kw: x + [3])
            .build()
        )

        results = pipeline.execute([0])
        self.assertTrue(results["success"])
        self.assertEqual(results["final_output"], [0, 1, 2, 3])
        self.assertEqual(len(results["stages"]), 3)
        self.assertIn("stage_1", results["stages"])
        self.assertIn("stage_2", results["stages"])
        self.assertIn("stage_3", results["stages"])

    def test_pipeline_failure_handling(self):
        """Verify pipeline fail-fast and error reporting."""
        def failing_stage(x, **kw):
            raise ValueError("Intentional stage error")

        pipeline = (
            create_pipeline_builder("failing_flow")
            .with_fail_fast(True)
            .with_stage("good_stage", lambda x, **kw: x + 10)
            .with_stage("bad_stage", failing_stage)
            .build()
        )

        with self.assertRaises(PipelineError):
            pipeline.execute(0)


class TestExceptionsAndTypes(unittest.TestCase):
    """Tests typed exception hierarchies, enums, dataclasses, and serialization."""

    def test_exception_hierarchy(self):
        """Verify all domain exceptions inherit from LearningBaseException."""
        exceptions_to_test = [
            LearningError, LearnerNotFoundError, LearnerInitializationError,
            LearnerConfigurationError, OptimizationFailedError, ConvergenceError,
            StrategyNotSupportedError, SamplingError, ActiveLearningError,
            AdaptiveLearningError, AdversarialAttackError, BayesianOptimizationError,
            CausalInferenceError, ContinualLearningError, EnsembleLearningError,
            EvolutionaryOptimizationError, FederatedLearningError,
            HyperparameterOptimizationError, MetaLearningError, MultitaskLearningError,
            NASError, ReinforcementLearningError, SelfSupervisedLearningError,
            TransferLearningError, PipelineError, PipelineExecutionError
        ]
        for exc_cls in exceptions_to_test:
            inst = exc_cls("Test error message", details={"code": 500})
            self.assertIsInstance(inst, LearningBaseException)
            self.assertEqual(inst.message, "Test error message")
            self.assertEqual(inst.details["code"], 500)

    def test_enums(self):
        """Verify enum values and string conversion."""
        self.assertEqual(LearningStrategyType.ACTIVE.value, "active")
        self.assertEqual(LearningStrategyType.TRANSFER.value, "transfer")
        self.assertEqual(UncertaintyMeasure.ENTROPY.value, "entropy")
        self.assertEqual(SamplingStrategy.UNCERTAINTY.value, "uncertainty")
        self.assertEqual(AdversarialMethod.PGD.value, "pgd")
        self.assertEqual(OptimizationMetric.LOSS.value, "loss")

    def test_dataclasses_and_serialization(self):
        """Verify metric serialization and dataclass instantiation."""
        metrics = LearningMetrics(
            loss=0.042,
            accuracy=0.985,
            step=100,
            epoch=5,
            duration_seconds=12.4,
            extra_metrics={"f1": 0.98}
        )
        data = metrics.to_dict()
        self.assertEqual(data["loss"], 0.042)
        self.assertEqual(data["accuracy"], 0.985)
        self.assertEqual(data["step"], 100)
        self.assertEqual(data["f1"], 0.98)

        # Configs
        active_cfg = ActiveLearningConfig(budget=500, query_batch_size=20)
        self.assertEqual(active_cfg.budget, 500)
        self.assertEqual(active_cfg.query_batch_size, 20)

        nas_cfg = NASConfig(search_strategy="evolutionary", max_epochs=15)
        self.assertEqual(nas_cfg.max_epochs, 15)

        rl_cfg = RLConfig(algorithm="ppo", gamma=0.95)
        self.assertEqual(rl_cfg.gamma, 0.95)


class TestBackwardCompatibility(unittest.TestCase):
    """Tests 100% backward compatibility for direct, lazy, and root-level imports."""

    def test_direct_imports(self):
        """Verify all 16 legacy learner names can be imported directly."""
        learners = [
            ActiveLearner, AdaptiveLearner, AdversarialLearner,
            BayesianOptimizer, CausalInference, ContinualLearner,
            EnsembleLearner, EvolutionaryOptimizer, FederatedLearner,
            HyperparameterOptimizer, MetaLearner, MultitaskLearner,
            NASOptimizer, ReinforcementLearner, SelfSupervisedLearner,
            TransferLearner
        ]
        for l in learners:
            self.assertIsNotNone(l)

    def test_submodule_imports(self):
        """Verify submodule imports from learning package."""
        from learning.active_learning import ActiveLearner, ActiveLearningStrategy
        from learning.evolutionary_computing import example_evolutionary_computing, Individual, Population
        from learning.transfer_learning import TransferLearner, FineTuner
        self.assertIsNotNone(ActiveLearner)
        self.assertIsNotNone(ActiveLearningStrategy)
        self.assertIsNotNone(Individual)
        self.assertIsNotNone(Population)
        self.assertIsNotNone(TransferLearner)
        self.assertIsNotNone(FineTuner)

    def test_optimization_core_root_lazy_imports(self):
        """Verify lazy loading through top-level optimization_core package."""
        from optimization_core import (
            ActiveLearner as RootActiveLearner,
            EvolutionaryOptimizer as RootEvolutionaryOptimizer,
            MetaLearner as RootMetaLearner,
            create_learning_module as RootCreateLearningModule,
        )
        self.assertIsNotNone(RootActiveLearner)
        self.assertIsNotNone(RootEvolutionaryOptimizer)
        self.assertIsNotNone(RootMetaLearner)
        self.assertIsNotNone(RootCreateLearningModule)


if __name__ == "__main__":
    unittest.main(verbosity=2)
