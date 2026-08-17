"""
Unit Test Suite for optimization_core/training package.
"""
import os
import tempfile
import pytest
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

try:
    from torch.amp import GradScaler
except ImportError:
    from torch.cuda.amp import GradScaler  # type: ignore

from training import (
    TrainingLoop,
    TrainingError,
    CheckpointManager,
    CheckpointError,
    EMAManager,
    EMAError,
    Evaluator,
    EvaluationError,
    ExperimentTracker,
    ExperimentTrackerError,
)
from training_system import create_training_component, list_available_training_components


class SimpleModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(8, 2)

    def forward(self, input_ids=None, labels=None, **kwargs):
        if input_ids is None and "x" in kwargs:
            input_ids = kwargs["x"]
        if input_ids is None and len(kwargs.get("args", ())) > 0:
            input_ids = kwargs["args"][0]

        logits = self.fc(input_ids)
        if labels is not None:
            loss = nn.functional.cross_entropy(logits, labels)
            return {"loss": loss, "logits": logits}
        return {"loss": logits.sum(), "logits": logits}


def test_training_loop_step_and_epoch():
    model = SimpleModel()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    try:
        scaler = GradScaler('cuda', enabled=False)
    except Exception:
        scaler = GradScaler(enabled=False)

    loop = TrainingLoop(use_amp=False, grad_accum_steps=1, max_grad_val=1.0)

    batch = {
        "input_ids": torch.randn(4, 8),
        "labels": torch.tensor([0, 1, 0, 1]),
    }

    step_res = loop.train_step(model, batch, optimizer, scaler, step=1)
    assert "loss" in step_res
    assert step_res["skipped"] is False
    assert isinstance(step_res["loss"], float)

    # Epoch training
    dataset = TensorDataset(torch.randn(8, 8), torch.tensor([0, 1] * 4))

    class DictDataLoader:
        def __init__(self, ds):
            self.ds = ds
        def __iter__(self):
            for x, y in DataLoader(self.ds, batch_size=4):
                yield {"input_ids": x, "labels": y}
        def __len__(self):
            return 2

    loader = DictDataLoader(dataset)
    epoch_res = loop.train_epoch(model, loader, optimizer, scheduler=None, scaler=scaler)
    assert "loss" in epoch_res
    assert epoch_res["num_steps"] == 2
    assert epoch_res["elapsed_time"] > 0


def test_training_loop_interface_and_validation():
    loop = TrainingLoop(use_amp=False, grad_accum_steps=2)
    assert loop.generate("hello world") == "hello world"

    loop.reset_early_stopping()
    assert loop.best_metric is None
    assert loop.bad_epochs == 0

    # Test invalid grad_accum_steps
    with pytest.raises(ValueError):
        TrainingLoop(grad_accum_steps=0)

    # Test invalid max_grad_norm
    with pytest.raises(ValueError):
        TrainingLoop(max_grad_norm=0.0)


def test_training_loop_should_stop_early():
    loop = TrainingLoop()

    # Mode = min (loss)
    # Metric improved (current 0.5 < best 1.0) -> should NOT stop
    assert loop.should_stop_early(current_metric=0.5, best_metric=1.0, patience=3, mode="min", bad_epochs=0) is False

    # Metric degraded (current 1.2 >= best 1.0) with bad_epochs < patience -> should NOT stop
    assert loop.should_stop_early(current_metric=1.2, best_metric=1.0, patience=3, mode="min", bad_epochs=2) is False

    # Metric degraded (current 1.2 >= best 1.0) with bad_epochs >= patience -> SHOULD stop
    assert loop.should_stop_early(current_metric=1.2, best_metric=1.0, patience=3, mode="min", bad_epochs=3) is True

    # Mode = max (accuracy)
    # Metric degraded (current 0.7 <= best 0.9) with bad_epochs >= patience -> SHOULD stop
    assert loop.should_stop_early(current_metric=0.7, best_metric=0.9, patience=2, mode="max", bad_epochs=2) is True


def test_checkpoint_manager_save_load_prune_and_queries():
    with tempfile.TemporaryDirectory() as tmp_dir:
        model = SimpleModel()
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
        manager = CheckpointManager(output_dir=tmp_dir, model=model, optimizer=optimizer)

        # Save step 10 checkpoint
        save_path = manager.save(filename="step_10.pt", step=10, epoch=1, metrics={"loss": 0.5})
        assert os.path.exists(save_path)
        assert os.path.exists(os.path.join(save_path, "training_state.pt"))
        assert os.path.exists(os.path.join(save_path, "checkpoint_manifest.json"))

        # Load checkpoint
        loaded_state = manager.load(save_path)
        assert loaded_state["step"] == 10
        assert "model_state_dict" in loaded_state

        # Save step 20 & step 30
        manager.save(filename="step_20.pt", step=20, epoch=2, metrics={"loss": 0.3})
        manager.save(filename="step_30.pt", step=30, epoch=3, metrics={"loss": 0.4})

        # Test query helpers
        ckpts = manager.list_checkpoints()
        assert len(ckpts) == 3
        latest = manager.get_latest_checkpoint()
        assert "step_30" in latest
        best = manager.find_best_checkpoint(metric_name="loss", mode="min")
        assert "step_20" in best

        # Prune keeping last 2
        manager.checkpoint_config = type("Cfg", (), {"keep_last": 2})()
        manager.prune_checkpoints()

        entries = os.listdir(tmp_dir)
        assert "step_10" not in entries
        assert "step_20" in entries
        assert "step_30" in entries


def test_ema_manager_weights_and_scope():
    model = SimpleModel()
    ema = EMAManager(decay=0.9, model=model, use_dynamic_decay=True)
    assert len(ema._shadow) > 0
    assert ema.get_decay(step=1) < 0.9

    initial_weight = model.fc.weight.clone()
    with torch.no_grad():
        model.fc.weight.add_(2.0)

    ema.update()

    # Scope swapping test
    with ema.ema_scope():
        assert not torch.allclose(model.fc.weight, initial_weight + 2.0)

    # Restored original weight after scope exit
    assert torch.allclose(model.fc.weight, initial_weight + 2.0)

    # Permanent copy to model
    ema.copy_shadow_to_model()
    assert not torch.allclose(model.fc.weight, initial_weight + 2.0)

    # State dict load / save
    sd = ema.state_dict()
    assert len(sd) == len(ema._shadow)
    ema.load_state_dict(sd)

    # Test invalid decay
    with pytest.raises(ValueError):
        EMAManager(decay=1.5)


def test_evaluator():
    model = SimpleModel()
    evaluator = Evaluator(use_amp=False)

    batch_x = torch.randn(4, 8)
    batch_y = torch.tensor([0, 1, 0, 1])

    class SingleBatchLoader:
        def __iter__(self):
            yield {"input_ids": batch_x, "labels": batch_y, "metadata_string": "test_sample"}

    def custom_fn(outputs, batch):
        return {"custom_metric": 1.0}

    metrics = evaluator.evaluate(model, SingleBatchLoader(), custom_metric_fn=custom_fn)
    assert "loss" in metrics
    assert "perplexity" in metrics
    assert "custom_metric" in metrics
    assert metrics["custom_metric"] == 1.0
    assert isinstance(metrics["loss"], float)
    assert isinstance(metrics["perplexity"], float)

    computed = evaluator.compute_metrics(torch.randn(4, 2), batch_y)
    assert "accuracy" in computed

    best_val = evaluator.select_best_metric(metrics, "loss")
    assert best_val == metrics["loss"]

    with pytest.raises(EvaluationError):
        evaluator.evaluate(None, SingleBatchLoader())


def test_experiment_tracker():
    tracker = ExperimentTracker(trackers=["console"])
    with tracker:
        tracker.log({"loss": 0.5, "acc": 0.95}, step=1)
        tracker.log_metrics({"loss": 0.4}, step=2)
        tracker.log_hyperparams({"lr": 1e-4, "batch_size": 32})
        tracker.log_artifact("dummy.txt")


def test_training_system_integration():
    components = list_available_training_components()
    assert "training_loop" in components
    assert "experiment_tracker" in components

    loop = create_training_component("training_loop", {"use_amp": False})
    assert isinstance(loop, TrainingLoop)
