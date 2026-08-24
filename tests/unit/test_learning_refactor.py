"""
Comprehensive Unit Test Suite for Refactored optimization_core.learning Subsystem.
=================================================================================
Validates:
1. Module imports (root lazy imports, direct imports, dual namespace resolution).
2. Central LearningRegistry component discovery, registration, and inspection.
3. Unified factory instantiation (`create_learning_module` and `create_learner`) across all 16 learning domains.
4. Fluent LearningPipelineBuilder chaining and sequential execution.
5. Enums, Dataclasses, Configuration Schemas, and Metric Telemetry.
6. Typed Exception hierarchy and error propagation.
"""

import sys
import os
import unittest
from typing import Dict, Any

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)


class TestLearningImportsAndNamespaces(unittest.TestCase):
    """Test module imports across canonical and legacy namespaces."""

    def test_direct_learning_module_import(self):
        """Test importing learning module directly."""
        import learning
        self.assertIsNotNone(learning)
        self.assertTrue(hasattr(learning, "create_learning_module"))
        self.assertTrue(hasattr(learning, "list_available_learning_modules"))
        self.assertTrue(hasattr(learning, "LEARNING_REGISTRY"))

    def test_optimization_core_learning_import(self):
        """Test importing through optimization_core.learning."""
        import optimization_core.learning as ocl
        self.assertIsNotNone(ocl)
        self.assertTrue(hasattr(ocl, "create_learning_module"))
        self.assertTrue(hasattr(ocl, "LearningPipelineBuilder"))

    def test_optimization_core_root_lazy_imports(self):
        """Test accessing learning symbols from root optimization_core package."""
        import optimization_core as opt
        self.assertTrue(hasattr(opt, "ActiveLearner"))
        self.assertTrue(hasattr(opt, "EvolutionaryOptimizer"))
        self.assertTrue(hasattr(opt, "BayesianOptimizer"))
        self.assertTrue(hasattr(opt, "create_learning_module"))
        self.assertTrue(hasattr(opt, "LearningPipelineBuilder"))

    def test_dual_namespace_identity(self):
        """Test that learning and optimization_core.learning point to identical objects."""
        import learning
        import optimization_core.learning as ocl
        self.assertIs(learning.create_learning_module, ocl.create_learning_module)
        self.assertIs(learning.LEARNING_REGISTRY, ocl.LEARNING_REGISTRY)


class TestLearningRegistry(unittest.TestCase):
    """Test thread-safe LearningRegistry and discovery APIs."""

    def setUp(self):
        from learning.registry import LEARNING_REGISTRY
        self.registry = LEARNING_REGISTRY

    def test_registered_16_domains(self):
        """Verify all 16 core learning strategy domains are registered."""
        available = self.registry.list_available()
        expected_domains = [
            "active", "adaptive", "adversarial", "bayesian",
            "causal", "continual", "ensemble", "evolutionary",
            "federated", "hpo", "meta", "multitask",
            "nas", "reinforcement", "self_supervised", "transfer"
        ]
        for domain in expected_domains:
            self.assertIn(domain, available, f"Domain '{domain}' missing from registry")

    def test_get_module_info(self):
        """Test metadata retrieval for registered modules."""
        info = self.registry.get_info("active")
        self.assertEqual(info["name"], "active")
        self.assertEqual(info["category"], "sampling")
        self.assertIn("ActiveLearningSystem", info["learner_class"])
        self.assertIn("sampling", info["tags"])

    def test_custom_module_registration(self):
        """Test registering and retrieving custom learner components."""
        class CustomDummyLearner:
            def __init__(self, cfg=None):
                self.cfg = cfg or {}
            def fit(self, *args, **kwargs):
                return {"custom": True}

        self.registry.register(
            name="custom_dummy",
            category="custom",
            description="Custom test learner",
            factory_fn=lambda cfg=None: CustomDummyLearner(cfg),
            tags=["test", "custom"],
            override=True
        )

        self.assertTrue(self.registry.is_registered("custom_dummy"))
        instance = self.registry.create("custom_dummy", config={"lr": 0.05})
        self.assertIsInstance(instance, CustomDummyLearner)
        self.assertEqual(instance.cfg, {"lr": 0.05})

        # Cleanup
        self.registry.unregister("custom_dummy")
        self.assertFalse(self.registry.is_registered("custom_dummy"))


class TestUnifiedFactoryAllDomains(unittest.TestCase):
    """Test instantiate all 16 learning modules via create_learning_module."""

    def test_instantiate_active_learning(self):
        from learning import create_learning_module
        active = create_learning_module("active")
        self.assertIsNotNone(active)
        self.assertTrue(hasattr(active, "run_active_learning") or hasattr(active, "query_samples"))

    def test_instantiate_adaptive_learning(self):
        from learning import create_learning_module
        adaptive = create_learning_module("adaptive")
        self.assertIsNotNone(adaptive)
        self.assertTrue(hasattr(adaptive, "adapt"))

    def test_instantiate_adversarial_learning(self):
        from learning import create_learning_module
        adv = create_learning_module("adversarial")
        self.assertIsNotNone(adv)
        self.assertTrue(hasattr(adv, "run_adversarial_learning") or hasattr(adv, "attacker"))

    def test_instantiate_bayesian_optimization(self):
        from learning import create_learning_module
        bayes = create_learning_module("bayesian")
        self.assertIsNotNone(bayes)
        self.assertTrue(hasattr(bayes, "optimize"))

    def test_instantiate_causal_inference(self):
        from learning import create_learning_module
        causal = create_learning_module("causal")
        self.assertIsNotNone(causal)
        self.assertTrue(hasattr(causal, "run_causal_inference") or hasattr(causal, "discovery"))

    def test_instantiate_continual_learning(self):
        from learning import create_learning_module
        cl = create_learning_module("continual")
        self.assertIsNotNone(cl)
        self.assertTrue(hasattr(cl, "train_continual") or hasattr(cl, "learn_task"))

    def test_instantiate_ensemble_learning(self):
        from learning import create_learning_module
        ensemble = create_learning_module("ensemble")
        self.assertIsNotNone(ensemble)
        self.assertTrue(hasattr(ensemble, "train_ensemble") or hasattr(ensemble, "voting_ensemble"))

    def test_instantiate_evolutionary_computing(self):
        from learning import create_learning_module
        evo = create_learning_module("evolutionary")
        self.assertIsNotNone(evo)
        self.assertTrue(hasattr(evo, "optimize"))

    def test_instantiate_federated_learning(self):
        from learning import create_learning_module
        fed = create_learning_module("federated")
        self.assertIsNotNone(fed)
        self.assertTrue(hasattr(fed, "run_federated_learning") or hasattr(fed, "server"))

    def test_instantiate_hpo(self):
        from learning import create_learning_module
        hpo = create_learning_module("hpo")
        self.assertIsNotNone(hpo)
        self.assertTrue(hasattr(hpo, "run_optimization") or hasattr(hpo, "optimize"))

    def test_instantiate_meta_learning(self):
        from learning import create_learning_module
        meta = create_learning_module("meta")
        self.assertIsNotNone(meta)
        self.assertTrue(hasattr(meta, "meta_train") or hasattr(meta, "train"))

    def test_instantiate_multitask_learning(self):
        from learning import create_learning_module
        mt = create_learning_module("multitask")
        self.assertIsNotNone(mt)
        self.assertTrue(hasattr(mt, "train_multitask") or hasattr(mt, "train_step"))

    def test_instantiate_nas(self):
        from learning import create_learning_module
        nas = create_learning_module("nas")
        self.assertIsNotNone(nas)
        self.assertTrue(hasattr(nas, "search"))

    def test_instantiate_reinforcement_learning(self):
        from learning import create_learning_module
        rl = create_learning_module("reinforcement")
        self.assertIsNotNone(rl)
        self.assertTrue(hasattr(rl, "train_agent"))

    def test_instantiate_self_supervised_learning(self):
        from learning import create_learning_module
        ssl = create_learning_module("self_supervised")
        self.assertIsNotNone(ssl)
        self.assertTrue(hasattr(ssl, "train_ssl") or hasattr(ssl, "pretrain_step"))

    def test_instantiate_transfer_learning(self):
        from learning import create_learning_module
        transfer = create_learning_module("transfer")
        self.assertIsNotNone(transfer)
        self.assertTrue(hasattr(transfer, "train_transfer") or hasattr(transfer, "fine_tune"))

    def test_alias_resolution(self):
        """Test that common aliases resolve to proper modules."""
        from learning import create_learning_module
        hpo1 = create_learning_module("hyperparameter_optimization")
        hpo2 = create_learning_module("hpo")
        self.assertEqual(type(hpo1), type(hpo2))

        ssl1 = create_learning_module("ssl")
        ssl2 = create_learning_module("self_supervised")
        self.assertEqual(type(ssl1), type(ssl2))


class TestLearningPipeline(unittest.TestCase):
    """Test fluent LearningPipelineBuilder and multi-stage orchestration."""

    def test_pipeline_builder_fluent_execution(self):
        from learning.pipeline import create_pipeline_builder
        from learning.types import LearningPipelineConfig

        # Define lightweight dummy stages
        class Stage1Pretrain:
            def fit(self, data=None, **kwargs):
                return {"pretrain_loss": 0.25, "features": [1, 2, 3]}

        class Stage2Active:
            def query_samples(self, prev_output, **kwargs):
                return {"queried_indices": [0, 1], "count": len(prev_output.get("features", []))}

        class Stage3Eval:
            def evaluate(self, prev_output, **kwargs):
                return {"accuracy": 0.96}

        builder = create_pipeline_builder("test_end_to_end_pipeline")
        pipeline = (
            builder
            .with_fail_fast(True)
            .with_stage("pretrain", Stage1Pretrain())
            .with_stage("active_query", Stage2Active())
            .with_stage("eval", Stage3Eval())
            .build()
        )

        results = pipeline.execute(initial_data={"raw_inputs": [10, 20]})
        self.assertTrue(results["success"])
        self.assertIn("pretrain", results["stages"])
        self.assertIn("active_query", results["stages"])
        self.assertIn("eval", results["stages"])
        self.assertEqual(results["stages"]["pretrain"]["output"]["pretrain_loss"], 0.25)
        self.assertEqual(results["stages"]["active_query"]["output"]["count"], 3)


class TestTypesAndConfigs(unittest.TestCase):
    """Test Enums, dataclass schemas, and metrics telemetry."""

    def test_configs_initialization(self):
        from learning.types import (
            ActiveLearningConfig,
            AdaptiveLearningConfig,
            AdversarialConfig,
            BayesianOptimizationConfig,
            LearningPipelineConfig,
        )

        al_cfg = ActiveLearningConfig(n_initial_samples=50, n_query_samples=5)
        self.assertEqual(al_cfg.n_initial_samples, 50)
        self.assertEqual(al_cfg.n_query_samples, 5)

        pipe_cfg = LearningPipelineConfig(name="prod_pipeline", fail_fast=False)
        self.assertEqual(pipe_cfg.name, "prod_pipeline")
        self.assertFalse(pipe_cfg.fail_fast)

    def test_learning_metrics(self):
        from learning.types import LearningMetrics, StepState
        metrics = LearningMetrics(best_metric_name="val_loss")
        metrics.add_step(StepState(step=1, epoch=1, loss=0.5, metrics={"val_loss": 0.45}))
        metrics.add_step(StepState(step=2, epoch=1, loss=0.3, metrics={"val_loss": 0.25}))

        self.assertEqual(metrics.total_steps, 2)
        self.assertEqual(metrics.best_metric_value, 0.25)
        self.assertEqual(len(metrics.history), 2)


class TestExceptionHierarchy(unittest.TestCase):
    """Test typed exceptions and inheritance hierarchy."""

    def test_exceptions(self):
        from learning.exceptions import (
            LearningBaseException,
            LearningError,
            LearnerNotFoundError,
            LearnerInitializationError,
            PipelineError,
        )

        self.assertTrue(issubclass(LearningError, LearningBaseException))
        self.assertTrue(issubclass(LearnerNotFoundError, LearningBaseException))
        self.assertTrue(issubclass(LearnerInitializationError, LearningBaseException))
        self.assertTrue(issubclass(PipelineError, LearningBaseException))

        err = LearnerNotFoundError("Module not found", details={"module": "non_existent"})
        self.assertEqual(err.details.get("module"), "non_existent")


if __name__ == "__main__":
    unittest.main(verbosity=2)
