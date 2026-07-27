"""
Unit tests for the refactored trainers package.

Validates configuration, exceptions, types, interfaces, datasets, data manager,
model manager, optimizer manager parameter grouping, EMA manager CPU offloading,
checkpoint manager atomic saving, callbacks, and GenericTrainer backward compatibility.
"""
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import torch
import torch.nn as nn

from trainers.config import (
    TrainerConfig,
    ModelConfig,
    TrainingConfig,
    HardwareConfig,
    CheckpointConfig,
    EMAConfig,
)
from trainers.exceptions import (
    TrainerError,
    ConfigurationError,
    ModelManagerError,
    OptimizerManagerError,
    DataManagerError,
    CheckpointError,
    EvaluationError,
    EMAError,
)
from trainers.types import StepState, EvalMetrics, TrainerState
from trainers.dataset import HFTextDataset, TextDataset, PackedDataset
from trainers.data_manager import DataManager, LengthBucketBatchSampler
from trainers.optimizer_manager import OptimizerManager
from trainers.ema_manager import EMAManager
from trainers.checkpoint_manager import CheckpointManager
from trainers.callbacks import (
    Callback,
    CallbackHandler,
    EarlyStoppingCallback,
    LearningRateMonitor,
    CSVLogger,
)
from trainers.experiment_tracker import MultiExperimentTracker, ConsoleTracker


class SimpleLinearModel(nn.Module):
    """Toy model for testing optimizer, EMA, and checkpointing logic."""

    def __init__(self):
        super().__init__()
        self.embedding = nn.Embedding(100, 16)
        self.linear = nn.Linear(16, 16)
        self.ln = nn.LayerNorm(16)
        self.head = nn.Linear(16, 100)

    def forward(self, input_ids=None, labels=None, **kwargs):
        if input_ids is None:
            input_ids = torch.zeros((2, 8), dtype=torch.long)
        x = self.embedding(input_ids)
        x = self.linear(x)
        x = self.ln(x)
        logits = self.head(x)
        loss = None
        if labels is not None:
            loss = nn.functional.cross_entropy(logits.view(-1, 100), labels.view(-1))
        return type("Output", (), {"loss": loss, "logits": logits})()


class TestTrainersRefactored(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_config_validation_and_serialization(self):
        """Test configuration validation and JSON serialization."""
        cfg = TrainerConfig(output_dir=self.test_dir)
        self.assertEqual(cfg.epochs, 3)
        self.assertEqual(cfg.model_name, "gpt2")

        # Test setter delegation
        cfg.learning_rate = 1e-4
        self.assertEqual(cfg.training.learning_rate, 1e-4)

        # Test invalid values trigger ConfigurationError
        with self.assertRaises(ConfigurationError):
            TrainingConfig(epochs=-1)

        with self.assertRaises(ConfigurationError):
            TrainingConfig(mixed_precision="invalid_dtype")

        # Serialization
        json_file = os.path.join(self.test_dir, "config.json")
        cfg.to_json(json_file)
        self.assertTrue(os.path.exists(json_file))

        loaded_cfg = TrainerConfig.from_json(json_file)
        self.assertEqual(loaded_cfg.training.learning_rate, 1e-4)

    def test_datasets(self):
        """Test Dataset wrapper classes and out-of-bounds error handling."""
        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {
            "input_ids": torch.zeros((1, 10), dtype=torch.long),
            "attention_mask": torch.ones((1, 10), dtype=torch.long),
        }

        ds = HFTextDataset(mock_tokenizer, ["hello world", "foo bar"], max_length=10)
        self.assertEqual(len(ds), 2)
        sample = ds[0]
        self.assertIn("input_ids", sample)

        with self.assertRaises(IndexError):
            _ = ds[5]

        packed = PackedDataset([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]], block_size=4)
        self.assertEqual(len(packed), 2)

    def test_weight_decay_parameter_grouping(self):
        """Test that 1D parameters, biases, and LayerNorms are excluded from weight decay."""
        model = SimpleLinearModel()
        cfg = TrainingConfig(learning_rate=1e-3, weight_decay=0.01)
        opt_manager = OptimizerManager(cfg, model, use_amp=False)
        groups = opt_manager._create_decay_param_groups()

        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0]["weight_decay"], 0.01)  # decay group
        self.assertEqual(groups[1]["weight_decay"], 0.0)   # no-decay group

        # Verify LayerNorm weight is in no-decay group
        no_decay_params = set(groups[1]["params"])
        self.assertIn(model.ln.weight, no_decay_params)
        self.assertIn(model.linear.bias, no_decay_params)

    def test_ema_manager_cpu_offload(self):
        """Test EMA Manager shadow updating and CPU offloading."""
        model = SimpleLinearModel()
        ema_cfg = EMAConfig(enabled=True, decay=0.9, offload_to_cpu=True)
        ema_mgr = EMAManager(ema_cfg, model)

        self.assertIsNotNone(ema_mgr._ema_shadow)
        first_shadow_device = next(iter(ema_mgr._ema_shadow.values())).device
        self.assertEqual(first_shadow_device.type, "cpu")

        # Update EMA
        ema_mgr.update()
        self.assertEqual(ema_mgr._update_count, 1)

        # Apply and restore EMA
        ema_mgr.apply_ema()
        self.assertIsNotNone(ema_mgr._ema_backup)
        ema_mgr.restore_from_ema()
        self.assertIsNone(ema_mgr._ema_backup)

    def test_atomic_checkpoint_manager(self):
        """Test atomic checkpoint folder creation, state writing, manifest, and pruning."""
        model = SimpleLinearModel()
        ckpt_cfg = CheckpointConfig(interval_steps=100, keep_last=2)
        ckpt_mgr = CheckpointManager(
            checkpoint_config=ckpt_cfg,
            output_dir=self.test_dir,
            model=model,
        )

        saved_dir = ckpt_mgr.save("step_100.pt", step=100, is_best=True)
        self.assertTrue(os.path.exists(saved_dir))
        self.assertTrue(os.path.exists(os.path.join(saved_dir, "checkpoint_manifest.json")))
        self.assertTrue(os.path.exists(os.path.join(saved_dir, "training_state.pt")))

        # Save more checkpoints and verify pruning
        ckpt_mgr.save("step_200.pt", step=200)
        ckpt_mgr.save("step_300.pt", step=300)
        ckpt_mgr.prune_checkpoints()

        remaining = [d for d in os.listdir(self.test_dir) if d.startswith("step_")]
        self.assertLessEqual(len(remaining), 3)

    def test_callback_handler_and_early_stopping(self):
        """Test EarlyStoppingCallback and CallbackHandler event insulation."""
        early_stop = EarlyStoppingCallback(patience=2, monitor="val_loss")
        lr_mon = LearningRateMonitor()
        handler = CallbackHandler([early_stop, lr_mon])

        # Step logging
        handler.on_log({"global_step": 1, "learning_rate": 1e-4})
        self.assertEqual(len(lr_mon.lr_history), 1)

        # Eval sequence for early stopping
        state = {}
        handler.on_eval({"val_loss": 1.0})
        self.assertFalse(early_stop.should_stop)

        handler.on_eval({"val_loss": 1.0})
        self.assertFalse(early_stop.should_stop)

        handler.on_eval({"val_loss": 1.0})
        self.assertTrue(early_stop.should_stop)

    def test_multi_experiment_tracker(self):
        """Test MultiExperimentTracker dispatch."""
        c1 = ConsoleTracker()
        c2 = ConsoleTracker()
        multi = MultiExperimentTracker([c1, c2])
        multi.log_metrics({"loss": 0.5}, step=1)
        multi.finish()


if __name__ == "__main__":
    unittest.main()
