"""
Comprehensive Unit Test Suite for optimization_core/trainers package.
"""
import os
import json
import tempfile
import pytest
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

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
    CallbackError,
)
from trainers.types import StepState, EvalMetrics, TrainerState
from trainers.interfaces import (
    IModelManager, IOptimizerManager, IDataManager,
    ICheckpointManager, IEMAManager, IEvaluator, ITrainer, ICallback
)
from trainers.dataset import TextDataset, PackedDataset
from trainers.callbacks import Callback, CallbackHandler, PrintLogger
from trainers.ema_manager import EMAManager
from trainers.checkpoint_manager import CheckpointManager
from trainers.optimizer_manager import OptimizerManager


class DummyModel(nn.Module):
    """Simple model for unit testing."""
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(10, 10)
        self.bias_param = nn.Parameter(torch.zeros(10))
        self.fc2 = nn.Linear(10, 2)
        
    def forward(self, x):
        h = torch.relu(self.fc1(x))
        loss = h.sum()
        return {"loss": loss, "logits": self.fc2(h)}


def test_trainer_config_defaults():
    cfg = TrainerConfig()
    assert cfg.seed == 42
    assert cfg.run_name == "run"
    assert cfg.output_dir == "runs/run"
    assert cfg.model.name_or_path == "gpt2"
    assert cfg.training.epochs == 3
    assert cfg.training.learning_rate == 5e-5


def test_trainer_config_property_delegates():
    cfg = TrainerConfig()
    
    # Getters
    assert cfg.model_name == "gpt2"
    assert cfg.epochs == 3
    assert cfg.mixed_precision == "bf16"
    assert cfg.ema_enabled is True
    assert cfg.learning_rate == 5e-5
    
    # Setters
    cfg.model_name = "distilgpt2"
    assert cfg.model.name_or_path == "distilgpt2"
    
    cfg.epochs = 10
    assert cfg.training.epochs == 10
    
    cfg.learning_rate = 1e-4
    assert cfg.training.learning_rate == 1e-4


def test_trainer_config_validation():
    with pytest.raises(ConfigurationError):
        ModelConfig(name_or_path="")
        
    with pytest.raises(ConfigurationError):
        TrainingConfig(epochs=0)
        
    with pytest.raises(ConfigurationError):
        TrainingConfig(mixed_precision="invalid_precision")
        
    with pytest.raises(ConfigurationError):
        EMAConfig(decay=1.5)


def test_trainer_config_serialization():
    cfg = TrainerConfig(run_name="test_run")
    cfg_dict = cfg.to_dict()
    assert cfg_dict["run_name"] == "test_run"
    
    reconstructed = TrainerConfig.from_dict(cfg_dict)
    assert reconstructed.run_name == "test_run"
    
    json_str = cfg.to_json()
    assert "test_run" in json_str
    
    reconstructed_json = TrainerConfig.from_json(json_str)
    assert reconstructed_json.run_name == "test_run"


def test_exception_hierarchy():
    err = ConfigurationError("Config invalid")
    assert isinstance(err, TrainerError)
    
    err_chk = CheckpointError("Save failed")
    assert isinstance(err_chk, TrainerError)


def test_types_and_dataclasses():
    step_state = StepState(epoch=1, step=10, global_step=10, loss=0.5, learning_rate=1e-4)
    step_dict = step_state.to_dict()
    assert step_dict["epoch"] == 1
    assert step_dict["loss"] == 0.5
    
    eval_metrics = EvalMetrics(loss=0.4, perplexity=1.49)
    eval_dict = eval_metrics.to_dict()
    assert eval_dict["val_loss"] == 0.4
    assert eval_dict["perplexity"] == 1.49
    
    trainer_state = TrainerState(global_step=100, is_training=True)
    assert trainer_state.global_step == 100


def test_dataset_primitives():
    ds = TextDataset(["sample1", "sample2", "sample3"])
    assert len(ds) == 3
    assert ds[0] == "sample1"
    
    token_ids = [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]]
    packed_ds = PackedDataset(token_ids, block_size=4)
    assert len(packed_ds) == 2
    item = packed_ds[0]
    assert "input_ids" in item
    assert "labels" in item
    assert item["input_ids"].shape[0] == 4


def test_callback_handler_dispatch():
    events_called = []

    class MockCallback(Callback):
        def on_train_begin(self, state):
            events_called.append("train_begin")
        def on_step_begin(self, step, state):
            events_called.append(f"step_begin_{step}")

    cb_handler = CallbackHandler([MockCallback()])
    cb_handler.on_train_begin({})
    cb_handler.on_step_begin(1, {})
    
    assert "train_begin" in events_called
    assert "step_begin_1" in events_called


def test_ema_manager_cycles():
    model = DummyModel()
    ema_cfg = EMAConfig(enabled=True, decay=0.9)
    ema_mgr = EMAManager(ema_cfg, model)
    
    # Modify model weights
    with torch.no_grad():
        model.fc1.weight.add_(1.0)
        
    ema_mgr.update()
    ema_mgr.apply_ema()
    ema_mgr.restore_from_ema()
    assert ema_mgr._ema_shadow is not None


def test_checkpoint_manager_save_load_prune():
    with tempfile.TemporaryDirectory() as tmp_dir:
        model = DummyModel()
        chk_cfg = CheckpointConfig(keep_last=2)
        chk_mgr = CheckpointManager(chk_cfg, output_dir=tmp_dir, model=model)
        
        saved_dir1 = chk_mgr.save("step_100.pt", step=100, epoch=1)
        assert os.path.exists(saved_dir1)
        
        saved_dir2 = chk_mgr.save("step_200.pt", step=200, epoch=2)
        assert os.path.exists(saved_dir2)
        
        state = chk_mgr.load(saved_dir1)
        assert state["step"] == 100
        
        chk_mgr.save("step_300.pt", step=300, epoch=3)
        chk_mgr.prune_checkpoints()


def test_optimizer_manager_decay_groups():
    model = DummyModel()
    train_cfg = TrainingConfig(learning_rate=1e-3, weight_decay=0.01)
    opt_mgr = OptimizerManager(train_cfg, model=model, use_amp=False)
    
    groups = opt_mgr._create_decay_param_groups()
    assert len(groups) == 2
    assert groups[0]["weight_decay"] == 0.01
    assert groups[1]["weight_decay"] == 0.0
    
    optimizer = opt_mgr.create_optimizer("adamw")
    assert optimizer is not None
    assert opt_mgr.get_lr() == 1e-3
