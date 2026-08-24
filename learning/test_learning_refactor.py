"""
Comprehensive Unit & Integration Test Suite for Learning Subsystem
===================================================================
Tests all 16 learning strategy domains, configuration validation,
registry discovery, factory instantiation, fluent multi-stage pipeline,
lazy-import subsystem, and backward compatibility contracts.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
OPT_CORE = Path(__file__).resolve().parent.parent
if str(OPT_CORE) not in sys.path:
    sys.path.insert(0, str(OPT_CORE))


class TestLearningRegistry(unittest.TestCase):
    """Tests for the LearningRegistry and module discovery."""

    def test_all_16_domains_registered(self):
        from optimization_core.learning.registry import list_available_learning_modules, learning_registry
        
        modules = list_available_learning_modules()
        expected = [
            "active", "adaptive", "adversarial", "bayesian", "causal",
            "continual", "ensemble", "evolutionary", "federated", "hpo",
            "meta", "multitask", "nas", "reinforcement", "self_supervised", "transfer"
        ]
        for exp in expected:
            self.assertIn(exp, modules, f"Expected domain '{exp}' in registry")
            info = learning_registry.get_module_info(exp)
            self.assertEqual(info["name"], exp)
            self.assertTrue(len(info["description"]) > 0)

    def test_custom_registration(self):
        from optimization_core.learning.registry import register_learning_module, learning_registry

        @register_learning_module("mock_strategy", category="test", description="A mock learner")
        class MockLearner:
            pass

        self.assertTrue(learning_registry.is_registered("mock_strategy"))
        info = learning_registry.get_module_info("mock_strategy")
        self.assertEqual(info["category"], "test")


class TestLearningConfigs(unittest.TestCase):
    """Tests for all 16 configuration dataclasses and validation."""

    def test_config_instantiation_and_validation(self):
        from optimization_core.learning.config import (
            ActiveLearningConfig, AdaptiveLearningConfig, AdversarialConfig,
            BayesianConfig, CausalConfig, ContinualConfig, EnsembleConfig,
            EvolutionaryConfig, FederatedConfig, HPOConfig, MetaConfig,
            MultitaskConfig, NASConfig, RLConfig, SelfSupervisedConfig,
            TransferLearningConfig, PipelineConfig, LearningConfig
        )

        configs = [
            ActiveLearningConfig(), AdaptiveLearningConfig(), AdversarialConfig(),
            BayesianConfig(), CausalConfig(), ContinualConfig(), EnsembleConfig(),
            EvolutionaryConfig(), FederatedConfig(), HPOConfig(), MetaConfig(),
            MultitaskConfig(), NASConfig(), RLConfig(), SelfSupervisedConfig(),
            TransferLearningConfig(), PipelineConfig(), LearningConfig()
        ]

        for cfg in configs:
            cfg.validate()
            d = cfg.to_dict()
            self.assertIsInstance(d, dict)
            # Roundtrip from_dict
            restored = type(cfg).from_dict(d)
            self.assertIsInstance(restored, type(cfg))

    def test_config_validation_error(self):
        from optimization_core.learning.config import ActiveLearningConfig
        from optimization_core.learning.exceptions import LearnerConfigurationError

        bad_cfg = ActiveLearningConfig(n_query_samples=-5)
        with self.assertRaises(LearnerConfigurationError):
            bad_cfg.validate()


class TestLearningInterfacesAndExceptions(unittest.TestCase):
    """Tests for interfaces, abstract base classes, and typed exceptions."""

    def test_interfaces_hierarchy(self):
        from optimization_core.learning.interfaces import (
            BaseLearner, BaseLearningOptimizer, BaseSampler,
            BaseActiveLearner, BaseAdaptiveLearner, BaseAdversarialLearner,
            BaseBayesianOptimizer, BaseCausalInference, BaseContinualLearner,
            BaseEnsembleLearner, BaseEvolutionaryOptimizer, BaseFederatedLearner,
            BaseHyperparameterOptimizer, BaseMetaLearner, BaseMultitaskLearner,
            BaseNASOptimizer, BaseReinforcementLearner, BaseSelfSupervisedLearner,
            BaseTransferLearner, BaseLearningPipeline
        )

        class DummyLearner(BaseLearner):
            def fit(self, *args, **kwargs): return {"status": "fit"}
            def evaluate(self, *args, **kwargs): return {"score": 1.0}

        dummy = DummyLearner()
        self.assertEqual(dummy.fit()["status"], "fit")
        self.assertEqual(dummy.evaluate()["score"], 1.0)

    def test_exceptions_hierarchy(self):
        from optimization_core.learning.exceptions import (
            LearningBaseException, LearningError, LearnerNotFoundError,
            LearnerInitializationError, LearnerConfigurationError,
            OptimizationFailedError, ConvergenceError, ArchitectureSearchError,
            PipelineError
        )

        err = LearnerNotFoundError("test not found", details={"key": "val"})
        self.assertIsInstance(err, LearningBaseException)
        self.assertEqual(err.details.get("key"), "val")


class TestLearningFactory(unittest.TestCase):
    """Tests for dynamic instantiation via factory subsystem."""

    def test_create_learning_module(self):
        from optimization_core.learning.factory import (
            create_learning_module, create_learning_config
        )

        # Evolutionary
        evo = create_learning_module("evolutionary", max_generations=5, population_size=10)
        self.assertIsNotNone(evo)

        # Active
        active = create_learning_module("active", n_initial_samples=20)
        self.assertIsNotNone(active)

        # HPO
        hpo = create_learning_module("hpo")
        self.assertIsNotNone(hpo)

        # Config creation
        evo_cfg = create_learning_config("evolutionary", population_size=42)
        self.assertEqual(evo_cfg.population_size, 42)


class TestCompositeLearningPipeline(unittest.TestCase):
    """Tests for multi-stage learning pipeline execution."""

    def test_pipeline_execution(self):
        from optimization_core.learning.pipeline import (
            LearningPipeline, PipelineStage, create_learning_pipeline, create_pipeline_builder
        )
        from optimization_core.learning.config import PipelineConfig

        class StageOne:
            def fit(self, data: Dict[str, Any]) -> Dict[str, Any]:
                data["stage_1"] = True
                return data

        class StageTwo:
            def fit(self, data: Dict[str, Any]) -> Dict[str, Any]:
                data["stage_2"] = True
                return data

        pipeline = create_learning_pipeline()
        pipeline.add_stage("pretrain", StageOne())
        pipeline.add_stage("finetune", StageTwo())

        initial_data = {"init": True}
        result = pipeline.execute(initial_data)

        self.assertTrue(result["success"])
        self.assertEqual(result["stages_executed"], 2)
        self.assertTrue(result["final_output"]["stage_1"])
        self.assertTrue(result["final_output"]["stage_2"])

    def test_pipeline_conditional_stage(self):
        from optimization_core.learning.pipeline import LearningPipeline

        class ConditionalStage:
            def fit(self, data): 
                data["ran_cond"] = True
                return data

        pipeline = LearningPipeline()
        pipeline.add_stage(
            "cond_stage",
            ConditionalStage(),
            condition=lambda ctx: ctx.get("enable_cond", False)
        )

        # Should skip
        res_skipped = pipeline.execute({"x": 1}, context={"enable_cond": False})
        self.assertNotIn("ran_cond", res_skipped["final_output"])

        # Should run
        res_ran = pipeline.execute({"x": 1}, context={"enable_cond": True})
        self.assertTrue(res_ran["final_output"].get("ran_cond"))


class TestLazyImportsAndBackwardCompatibility(unittest.TestCase):
    """Tests for lazy imports and seamless backward compatibility."""

    def test_learning_package_lazy_imports(self):
        import optimization_core.learning as l

        # Verify classes from 16 domains are accessible via __getattr__
        self.assertIsNotNone(l.ActiveLearner)
        self.assertIsNotNone(l.AdaptiveLearner)
        self.assertIsNotNone(l.AdversarialLearner)
        self.assertIsNotNone(l.BayesianOptimizer)
        self.assertIsNotNone(l.CausalInference)
        self.assertIsNotNone(l.ContinualLearner)
        self.assertIsNotNone(l.EnsembleLearner)
        self.assertIsNotNone(l.EvolutionaryOptimizer)
        self.assertIsNotNone(l.FederatedLearner)
        self.assertIsNotNone(l.HyperparameterOptimizer)
        self.assertIsNotNone(l.MetaLearner)
        self.assertIsNotNone(l.MultitaskLearner)
        self.assertIsNotNone(l.NASOptimizer)
        self.assertIsNotNone(l.ReinforcementLearner)
        self.assertIsNotNone(l.SelfSupervisedLearner)
        self.assertIsNotNone(l.TransferLearner)

    def test_modules_learning_exports(self):
        import optimization_core.modules.learning as ml

        self.assertIsNotNone(ml.EvolutionaryOptimizer)
        self.assertIsNotNone(ml.CausalInferenceSystem)
        self.assertIsNotNone(ml.ActiveLearningStrategy)
        self.assertIsNotNone(ml.FederatedServer)
        self.assertIsNotNone(ml.TransferLearningManager)
        self.assertIsNotNone(ml.SelfSupervisedTrainer)

    def test_top_level_learning_shim(self):
        from optimization_core import learning
        self.assertIsNotNone(learning)
        self.assertTrue(hasattr(learning, "create_learning_module"))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    unittest.main(verbosity=2)
