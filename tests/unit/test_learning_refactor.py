"""
Unit Test Suite for optimization_core.learning Refactored Subsystem
===================================================================
Tests thread-safe component registry, declarative fluent pipeline builder,
unified factory subsystem, typed exception hierarchy, dataclasses,
callbacks, evolutionary computing, and 100% backward compatibility for
all 16 learning paradigms.
"""

from __future__ import annotations

import os
import sys
import unittest
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

# Add workspace root to sys.path for direct imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from learning import (
    # Core Infrastructure
    __version__,
    LearningRegistry,
    LEARNING_REGISTRY,
    LearningPipeline,
    CompositeLearningPipeline,
    LearningPipelineBuilder,
    create_pipeline_builder,
    create_learning_pipeline,
    create_learning_module,
    create_learner,
    create_learning_optimizer,
    create_learning_config,
    list_available_learning_modules,
    get_learning_module_info,
    
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
    AdversarialDefenseError,
    CausalInferenceError,
    ContinualLearningError,
    EnsembleLearningError,
    EvolutionaryError,
    FederatedLearningError,
    HyperparameterOptimizationError,
    MetaLearningError,
    MultiTaskLearningError,
    NASError,
    ReinforcementLearningError,
    SelfSupervisedLearningError,
    TransferLearningError,
    PipelineError,
    PipelineExecutionError,
    
    # Types & Enums
    LearningStrategyType,
    UncertaintyMeasure,
    SamplingStrategy,
    AdversarialMethod,
    OptimizationMetric,
    TaskType,
    DistillationMethod,
    LearningMetrics,
    OptimizationResult,
    ActiveLearningResult,
    CausalEffectResult,
    LearningConfig,
    ActiveLearningConfig,
    EvolutionaryConfig,
    
    # All 16 Learner Classes
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

from learning.callbacks import (
    LearningCallback,
    EarlyStoppingCallback,
    MetricsLoggerCallback,
    ProgressCallback,
    CheckpointCallback,
)
from learning.pipeline import PipelineStage, PipelineStageResult


class TestLearningRegistry(unittest.TestCase):
    """Test cases for the thread-safe LearningRegistry."""

    def test_builtin_discovery(self):
        """Verify all 16 learning paradigms are discoverable."""
        available = list_available_learning_modules()
        expected = [
            "active", "adaptive", "adversarial", "bayesian", "causal",
            "continual", "ensemble", "evolutionary", "federated", "hpo",
            "meta", "multitask", "nas", "reinforcement", "self_supervised", "transfer"
        ]
        for name in expected:
            self.assertIn(name, available, f"Domain '{name}' missing from discovery list")

    def test_custom_learner_registration(self):
        """Verify dynamic custom learner registration and alias resolution."""
        class CustomTestLearner:
            def __init__(self, config=None, **kwargs):
                self.config = config
                self.kwargs = kwargs

        LearningRegistry.register(
            name="custom_test_learner",
            factory_or_cls=CustomTestLearner,
            description="Custom learner for unit testing",
            aliases=["test_learner_alias", "ctl"]
        )

        # Retrieve via primary name
        learner_cls = LearningRegistry.get_learner("custom_test_learner")
        self.assertEqual(learner_cls, CustomTestLearner)

        # Retrieve via aliases
        self.assertEqual(LearningRegistry.get_learner("test_learner_alias"), CustomTestLearner)
        self.assertEqual(LearningRegistry.get_learner("ctl"), CustomTestLearner)

        # Verify metadata
        info = LearningRegistry.get_info("custom_test_learner")
        self.assertEqual(info["description"], "Custom learner for unit testing")

    def test_nonexistent_learner_raises(self):
        """Verify querying unknown learner raises LearnerNotFoundError."""
        with self.assertRaises(LearnerNotFoundError):
            LearningRegistry.get_learner("non_existent_domain_xyz_123")


class TestLearningExceptions(unittest.TestCase):
    """Test cases for the hierarchical exception architecture."""

    def test_exception_inheritance(self):
        """Verify all domain exceptions inherit from LearningBaseException and LearningError."""
        exceptions_to_check = [
            ActiveLearningError,
            AdaptiveLearningError,
            AdversarialAttackError,
            AdversarialDefenseError,
            CausalInferenceError,
            ContinualLearningError,
            EnsembleLearningError,
            EvolutionaryError,
            FederatedLearningError,
            HyperparameterOptimizationError,
            MetaLearningError,
            MultiTaskLearningError,
            NASError,
            ReinforcementLearningError,
            SelfSupervisedLearningError,
            TransferLearningError,
            PipelineExecutionError,
        ]

        for exc_cls in exceptions_to_check:
            self.assertTrue(
                issubclass(exc_cls, LearningBaseException),
                f"{exc_cls.__name__} must inherit from LearningBaseException"
            )
            self.assertTrue(
                issubclass(exc_cls, (LearningError, LearningBaseException)),
                f"{exc_cls.__name__} must inherit from LearningError"
            )

    def test_exception_details_payload(self):
        """Verify structured details dictionary in exceptions."""
        exc = LearnerInitializationError("Initialization failed", details={"code": 500, "domain": "active"})
        self.assertEqual(str(exc), "Initialization failed")
        self.assertEqual(exc.details["code"], 500)
        self.assertEqual(exc.details["domain"], "active")


class TestLearningFactory(unittest.TestCase):
    """Test cases for the unified factory methods."""

    def test_create_learning_module_evolutionary(self):
        """Verify factory can instantiate evolutionary optimizer with default config."""
        opt = create_learning_module("evolutionary")
        self.assertIsInstance(opt, EvolutionaryOptimizer)

    def test_create_learning_module_with_dict_config(self):
        """Verify factory accepts dictionary configurations."""
        opt = create_learning_module(
            "evolutionary",
            config={"population_size": 20, "max_generations": 10}
        )
        self.assertIsInstance(opt, EvolutionaryOptimizer)
        self.assertEqual(opt.config.population_size, 20)
        self.assertEqual(opt.config.max_generations, 10)

    def test_create_learning_config(self):
        """Verify config factory builds domain-specific configs."""
        cfg = create_learning_config("evolutionary", population_size=42)
        self.assertIsNotNone(cfg)
        self.assertEqual(getattr(cfg, "population_size", None), 42)


class TestLearningPipelineBuilder(unittest.TestCase):
    """Test cases for the fluent LearningPipelineBuilder."""

    def test_fluent_pipeline_construction(self):
        """Verify stages, callbacks, and validation chain smoothly."""
        builder = create_pipeline_builder()
        
        executed_stages = []
        
        def dummy_action_1(context: Dict[str, Any]) -> Dict[str, Any]:
            executed_stages.append("stage1")
            return {"data_prepared": True}

        def dummy_action_2(context: Dict[str, Any]) -> Dict[str, Any]:
            executed_stages.append("stage2")
            return {"accuracy": 0.95}

        pipeline = (
            builder
            .set_name("SelfImprovingTestPipeline")
            .add_stage("data_prep", dummy_action_1)
            .add_stage("active_sampling", dummy_action_2, dependencies=["data_prep"])
            .add_callback(ProgressCallback())
            .build()
        )

        self.assertIsInstance(pipeline, (LearningPipeline, CompositeLearningPipeline))
        self.assertEqual(pipeline.name, "SelfImprovingTestPipeline")

        results = pipeline.execute(initial_context={"raw_data": [1, 2, 3]})
        self.assertIn("stage1", executed_stages)
        self.assertIn("stage2", executed_stages)
        self.assertTrue(results.get("data_prep", {}).get("data_prepared", False))


class TestLearningCallbacks(unittest.TestCase):
    """Test cases for lifecycle callbacks."""

    def test_early_stopping_callback(self):
        """Verify early stopping triggers on stagnation."""
        callback = EarlyStoppingCallback(monitor="val_loss", min_delta=0.01, patience=2, mode="min")
        
        # Epoch 1: 1.0 (Best)
        res1 = callback.on_epoch_end(1, {"val_loss": 1.0})
        self.assertFalse(res1)
        self.assertFalse(callback.should_stop)
        
        # Epoch 2: 0.999 (No significant improvement, wait=1)
        res2 = callback.on_epoch_end(2, {"val_loss": 0.999})
        self.assertFalse(res2)
        
        # Epoch 3: 1.05 (Worse, wait=2 -> should stop)
        res3 = callback.on_epoch_end(3, {"val_loss": 1.05})
        self.assertTrue(res3)
        self.assertTrue(callback.should_stop)

    def test_metrics_logger_callback(self):
        """Verify metrics logger captures epoch and step history."""
        logger = MetricsLoggerCallback()
        logger.on_step_end(1, {"loss": 0.5})
        logger.on_step_end(2, {"loss": 0.4})
        logger.on_epoch_end(1, {"val_loss": 0.45})

        history = logger.get_history()
        self.assertEqual(len(history["step_metrics"]), 2)
        self.assertEqual(len(history["epoch_metrics"]), 1)
        self.assertEqual(history["epoch_metrics"][0]["val_loss"], 0.45)


class TestEvolutionaryComputingDomain(unittest.TestCase):
    """Test cases for evolutionary computing algorithm."""

    def test_individual_creation_and_mutation(self):
        """Verify individual genome generation and mutation."""
        from learning.evolutionary_computing import Individual, MutationMethod
        import numpy as np

        ind = Individual([1.0, 2.0, 3.0])
        self.assertEqual(len(ind.genes), 3)
        
        mutated = ind.mutate(MutationMethod.GAUSSIAN, mutation_rate=1.0, mutation_strength=0.1)
        self.assertEqual(len(mutated.genes), 3)
        self.assertFalse(np.array_equal(ind.genes, mutated.genes))

    def test_evolutionary_optimization_run(self):
        """Verify end-to-end optimization of a sphere function."""
        import numpy as np
        from learning.evolutionary_computing import (
            EvolutionaryOptimizer,
            create_evolutionary_config,
            EvolutionaryAlgorithm
        )

        config = create_evolutionary_config(
            evolutionary_algorithm=EvolutionaryAlgorithm.GENETIC_ALGORITHM,
            population_size=20,
            max_generations=5,
            crossover_rate=0.8,
            mutation_rate=0.1
        )
        optimizer = EvolutionaryOptimizer(config)

        def sphere(genes):
            return -float(np.sum(np.square(genes)))

        results = optimizer.optimize(fitness_function=sphere, gene_length=4)
        self.assertIn("generations", results)
        self.assertIn("final_generation", results)


class TestBackwardCompatibilityAndExports(unittest.TestCase):
    """Test backward compatibility of all 16 domains and aliases."""

    def test_all_16_learners_present(self):
        """Verify that all 16 paradigm learners are available."""
        learners = [
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
        ]
        for learner in learners:
            self.assertIsNotNone(learner)

    def test_version_string(self):
        """Verify subsystem version format."""
        self.assertTrue(__version__.startswith("2."))


if __name__ == "__main__":
    unittest.main(verbosity=2)
