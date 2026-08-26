"""
Comprehensive Unit Tests for Learning Subsystem
================================================
Validates all 16 learning strategies, configurations, interfaces,
exceptions, types, registry, and pipeline execution.
"""

import os
import sys
import unittest
from typing import Any, Dict, List

# Ensure parent directory is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

OPT_CORE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if OPT_CORE not in sys.path:
    sys.path.insert(0, OPT_CORE)


class TestLearningInfrastructure(unittest.TestCase):
    """Test core types, configs, interfaces, exceptions, registry, and pipeline."""

    def test_imports_and_version(self):
        import optimization_core.learning as learning
        self.assertTrue(hasattr(learning, "__version__"))
        self.assertEqual(learning.__version__, "2.5.0")

    def test_dual_namespace_aliasing(self):
        import optimization_core.learning as opt_learning
        import learning
        self.assertIs(opt_learning, learning)

    def test_types_and_enums(self):
        from optimization_core.learning.types import (
            LearningStrategyType,
            LearningStage,
            UncertaintyMeasureType,
            QueryStrategyType,
            AdaptiveMode,
            AttackType,
            DefenseType,
            AcquisitionFunctionType,
            KernelType,
            ContinualMethodType,
            EnsembleMethodType,
            AggregationMethodType,
            HPOSearchStrategyType,
            MetaAlgorithmType,
            MultitaskLossBalancingType,
            NASStrategyType,
            RLAlgorithmType,
            SSLPretextTaskType,
            TransferMethodType,
            EvaluationResult,
            OptimizationResult,
            LearningStepResult,
            PipelineStageResult,
        )

        self.assertEqual(LearningStrategyType.ACTIVE.value, "active")
        self.assertEqual(LearningStage.FINE_TUNING.value, "fine_tuning")
        self.assertEqual(AttackType.PGD.value, "pgd")
        self.assertEqual(RLAlgorithmType.PPO.value, "ppo")

        eval_res = EvaluationResult(loss=0.42, metrics={"acc": 0.95})
        self.assertEqual(eval_res.get("acc"), 0.95)
        self.assertEqual(eval_res.loss, 0.42)

        opt_res = OptimizationResult(best_score=0.99, total_iterations=10)
        self.assertEqual(opt_res.best_score, 0.99)

        step_res = LearningStepResult(step=1, loss=0.5)
        self.assertEqual(step_res.step, 1)

    def test_configurations_and_validation(self):
        from optimization_core.learning.config import (
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
            MetaConfig,
            MultitaskConfig,
            NASConfig,
            RLConfig,
            SelfSupervisedConfig,
            TransferLearningConfig,
            PipelineConfig,
            LearnerConfigurationError,
        )

        # Master config validation
        cfg = LearningConfig()
        cfg.validate()
        self.assertIsInstance(cfg.active, ActiveLearningConfig)
        self.assertIsInstance(cfg.reinforcement, RLConfig)

        # Serialization to dict and reconstruction
        cfg_dict = cfg.to_dict()
        self.assertIsInstance(cfg_dict, dict)
        self.assertIn("active", cfg_dict)
        self.assertIn("adversarial", cfg_dict)

        restored_cfg = LearningConfig.from_dict(cfg_dict)
        self.assertEqual(restored_cfg.device, cfg.device)

        # Backward compatibility properties
        cfg.learning_rate = 0.005
        self.assertEqual(cfg.learning_rate, 0.005)
        self.assertEqual(cfg.adaptive.learning_rate, 0.005)

        # Error validation checks
        with self.assertRaises(LearnerConfigurationError):
            bad_act = ActiveLearningConfig(n_query_samples=-1)
            bad_act.validate()

        with self.assertRaises(LearnerConfigurationError):
            bad_adv = AdversarialConfig(epsilon=-0.1)
            bad_adv.validate()

    def test_exceptions_hierarchy(self):
        from optimization_core.learning.exceptions import (
            LearningBaseException,
            LearningError,
            LearnerNotFoundError,
            LearnerInitializationError,
            LearnerConfigurationError,
            OptimizationFailedError,
            ConvergenceError,
            StrategyNotSupportedError,
            SamplingError,
            AdversarialAttackError,
            CausalDiscoveryError,
            ContinualLearningError,
            EnsembleError,
            EvolutionaryError,
            FederatedLearningError,
            HyperparameterOptimizationError,
            MetaLearningError,
            MultiTaskLearningError,
            NASError,
            ReinforcementLearningError,
            SelfSupervisedError,
            TransferLearningError,
            PipelineExecutionError,
        )

        err = SamplingError("Uncertainty NaN encountered", details={"sample_id": 42})
        self.assertIsInstance(err, LearningError)
        self.assertIsInstance(err, LearningBaseException)
        self.assertEqual(err.details.get("sample_id"), 42)

        pipe_err = PipelineExecutionError("Stage failed")
        self.assertIsInstance(pipe_err, LearningError)

    def test_registry_and_factories(self):
        from optimization_core.learning.registry import (
            LearningRegistry,
            register_learning_module,
            list_available_learning_modules,
            get_learning_module_info,
            create_learning_module,
            create_learner,
        )

        # Register a mock learner
        class MockLearner:
            def __init__(self, config=None, **kwargs):
                self.config = config
                self.kwargs = kwargs

            def fit(self, data=None):
                return {"loss": 0.1, "fitted": True}

            def evaluate(self, data=None):
                return {"eval_score": 0.99}

        LearningRegistry.register("mock_learner", MockLearner, description="A mock learner for testing")
        self.assertIn("mock_learner", list_available_learning_modules())

        info = get_learning_module_info("mock_learner")
        self.assertEqual(info["name"], "mock_learner")

        inst = create_learning_module("mock_learner", config={"lr": 0.01})
        self.assertIsInstance(inst, MockLearner)
        self.assertEqual(inst.config, {"lr": 0.01})

        learner_inst = create_learner("mock_learner")
        self.assertIsInstance(learner_inst, MockLearner)

    def test_pipeline_execution(self):
        from optimization_core.learning.pipeline import (
            LearningPipeline,
            PipelineStage,
            create_pipeline_builder,
            create_learning_pipeline,
        )
        from optimization_core.learning.config import PipelineConfig

        class DummyPretrain:
            def fit(self, data):
                return {"weights_initialized": True, "loss": 0.5}

        class DummyFineTune:
            def fit(self, data):
                return {"fine_tuned": True, "accuracy": 0.98}

        pipeline = (
            create_pipeline_builder("test_flow")
            .with_config(PipelineConfig(pipeline_name="test_flow", stop_on_stage_failure=True))
            .add_stage("pretrain", DummyPretrain())
            .add_stage("finetune", DummyFineTune())
            .build()
        )

        summary = pipeline.execute(initial_data={"raw": [1, 2, 3]})
        self.assertTrue(summary["success"])
        self.assertEqual(summary["stages_executed"], 2)
        self.assertIn("pretrain", summary["stage_results"])
        self.assertIn("finetune", summary["stage_results"])
        self.assertEqual(summary["stage_results"]["pretrain"].status, "SUCCESS")
        self.assertEqual(summary["stage_results"]["finetune"].status, "SUCCESS")


class TestLearningStrategyExports(unittest.TestCase):
    """Verify that all 16 learning strategies are exportable and resolvable."""

    def test_all_16_strategies_lazy_loading(self):
        import optimization_core.learning as learning

        expected_symbols = [
            # 1. Active Learning
            "ActiveLearner",
            "ActiveLearningStrategy",
            "ActiveLearningSystem",
            "UncertaintySampler",
            
            # 2. Adaptive Learning
            "AdaptiveLearner",
            "AdaptiveLearningStrategy",
            "AdaptiveLearningSystem",
            
            # 3. Adversarial Learning
            "AdversarialLearner",
            "AdversarialLearningSystem",
            "AdversarialAttacker",
            "AdversarialDefense",
            
            # 4. Bayesian Optimization
            "BayesianOptimizer",
            "GaussianProcessModel",
            "AcquisitionFunctionOptimizer",
            
            # 5. Causal Inference
            "CausalInference",
            "CausalInferenceEngine",
            "CausalInferenceSystem",
            
            # 6. Continual Learning
            "ContinualLearner",
            "CLTrainer",
            
            # 7. Ensemble Learning
            "EnsembleLearner",
            "EnsembleManager",
            
            # 8. Evolutionary Computing
            "EvolutionaryOptimizer",
            "Individual",
            "Population",
            
            # 9. Federated Learning
            "FederatedLearner",
            "FederatedServer",
            "FederatedClient",
            
            # 10. Hyperparameter Optimization
            "HyperparameterOptimizer",
            "HpoManager",
            
            # 11. Meta Learning
            "MetaLearner",
            "MAML",
            "Reptile",
            
            # 12. Multi-Task Learning
            "MultitaskLearner",
            "MultitaskModel",
            
            # 13. Neural Architecture Search
            "NASOptimizer",
            "NeuralArchitectureSearch",
            
            # 14. Reinforcement Learning
            "ReinforcementLearner",
            "RLSystem",
            
            # 15. Self-Supervised Learning
            "SelfSupervisedLearner",
            "SelfSupervisedTrainer",
            
            # 16. Transfer Learning
            "TransferLearner",
            "TransferLearningManager",
            "KnowledgeDistiller",
        ]

        for symbol in expected_symbols:
            obj = getattr(learning, symbol, None)
            self.assertIsNotNone(obj, f"Symbol '{symbol}' failed to load from optimization_core.learning")


if __name__ == "__main__":
    unittest.main()
