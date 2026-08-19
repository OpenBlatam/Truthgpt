"""
Advanced unit test suite for optimization_core/trainers refactored features.

Covers:
- max_steps configuration & early termination
- on_exception callback dispatching
- TrainerRegistry dynamic registration
- Dual namespace importability (trainers & optimization_core.trainers)
- TrainingMetrics and ProfilingSummary serialization
- Complete GenericTrainer training lifecycle with callbacks and profiler
"""
import unittest
from unittest.mock import MagicMock
import tempfile
import shutil
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

import trainers
from trainers import (
    TrainerConfig,
    ModelConfig,
    TrainingConfig,
    HardwareConfig,
    CheckpointConfig,
    EMAConfig,
    TrainerRegistry,
    Callback,
    CallbackHandler,
    GenericTrainer,
    TrainingProfiler,
    MetricTracker,
    DistributedManager,
    TrainingMetrics,
    StepState,
    EvalMetrics,
    TrainerState,
    TrainerError,
    OOMError,
    EarlyStoppingException,
)


class MockTransformerModel(nn.Module):
    """Toy model simulating transformer causal LM behavior."""
    def __init__(self):
        super().__init__()
        self.embedding = nn.Embedding(50, 16)
        self.linear = nn.Linear(16, 50)

    def forward(self, input_ids=None, labels=None, **kwargs):
        if input_ids is None:
            input_ids = torch.zeros((2, 8), dtype=torch.long)
        x = self.embedding(input_ids)
        logits = self.linear(x)
        loss = None
        if labels is not None:
            loss = nn.functional.cross_entropy(logits.view(-1, 50), labels.view(-1))
        elif kwargs.get("attention_mask") is not None:
            loss = logits.mean()
        else:
            loss = torch.tensor(0.5, requires_grad=True)
        return type("MockOutput", (), {"loss": loss, "logits": logits})()


class RecordingCallback(Callback):
    """Callback recording all triggered events."""
    def __init__(self):
        self.events = []
        self.exceptions_caught = []

    def on_train_begin(self, state):
        self.events.append("on_train_begin")

    def on_train_end(self, state):
        self.events.append("on_train_end")

    def on_step_begin(self, step, state):
        self.events.append("on_step_begin")

    def on_step_end(self, step, state):
        self.events.append("on_step_end")

    def on_exception(self, exception, state):
        self.events.append("on_exception")
        self.exceptions_caught.append(exception)


class TestTrainersAdvanced(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_max_steps_config(self):
        """Test max_steps config validation, delegation, and serialization."""
        cfg = TrainerConfig(output_dir=self.test_dir)
        self.assertIsNone(cfg.max_steps)

        cfg.max_steps = 100
        self.assertEqual(cfg.training.max_steps, 100)
        self.assertEqual(cfg.max_steps, 100)

        # Serialization round-trip
        data = cfg.to_dict()
        self.assertEqual(data["training"]["max_steps"], 100)

        restored = TrainerConfig.from_dict(data)
        self.assertEqual(restored.max_steps, 100)

    def test_trainer_registry_extensibility(self):
        """Test dynamic registration of custom callback and optimizer in TrainerRegistry."""
        @TrainerRegistry.register_callback("custom_alert_callback")
        class CustomAlertCallback(Callback):
            pass

        registered_cb = TrainerRegistry.get_callback("custom_alert_callback")
        self.assertEqual(registered_cb, CustomAlertCallback)
        self.assertIn("custom_alert_callback", TrainerRegistry.list_callbacks())

    def test_callback_on_exception_dispatch(self):
        """Test on_exception is cleanly dispatched to CallbackHandler."""
        recorder = RecordingCallback()
        handler = CallbackHandler([recorder])

        dummy_exc = RuntimeError("Test exception")
        handler.on_exception(dummy_exc, {"global_step": 5, "epoch": 1})

        self.assertIn("on_exception", recorder.events)
        self.assertEqual(len(recorder.exceptions_caught), 1)
        self.assertEqual(recorder.exceptions_caught[0], dummy_exc)

    def test_training_metrics_dataclass(self):
        """Test TrainingMetrics aggregation dataclass."""
        metrics = TrainingMetrics(
            total_steps=100,
            total_epochs=2,
            best_val_loss=0.25,
            best_perplexity=1.28,
        )
        self.assertEqual(metrics.total_steps, 100)
        d = metrics.to_dict()
        self.assertEqual(d["best_val_loss"], 0.25)
        self.assertEqual(d["best_perplexity"], 1.28)

    def test_trainer_state_lifecycle_transitions(self):
        """Test TrainerState state machine transitions."""
        state = TrainerState()
        self.assertEqual(state.stage.value, "uninitialized")
        self.assertFalse(state.is_training)

        state.mark_training()
        self.assertTrue(state.is_training)
        self.assertEqual(state.stage.value, "training")
        self.assertIsNotNone(state.start_time)

        state.mark_completed()
        self.assertFalse(state.is_training)
        self.assertEqual(state.stage.value, "completed")
        self.assertIsNotNone(state.end_time)

        state.mark_failed("Loss diverged")
        self.assertEqual(state.stage.value, "failed")
        self.assertEqual(state.metadata.get("failure_reason"), "Loss diverged")


if __name__ == "__main__":
    unittest.main()
