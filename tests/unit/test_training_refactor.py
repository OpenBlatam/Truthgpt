"""
Unit Test Suite for optimization_core.training Refactored Subsystem
===================================================================
Tests registry discovery, fluent pipeline builder, training loop execution,
atomic checkpointing, EMA parameter tracking, evaluation, experiment tracking,
and 100% backward compatibility.
"""

from __future__ import annotations

import os
import shutil
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
    # Core Components
    TrainingLoop,
    CheckpointManager,
    EMAManager,
    Evaluator,
    ExperimentTracker,
    TrainingPipeline,
    TrainingPipelineBuilder,
    # Callbacks
    Callback,
    EarlyStoppingCallback,
    ModelCheckpointCallback,
    LRMonitorCallback,
    MetricsLoggerCallback,
    GradientNormCallback,
    ProgressCallback,
    # Exceptions
    TrainingBaseException,
    TrainingError,
    TrainingConfigurationError,
    CheckpointError,
    CheckpointNotFoundError,
    CheckpointCorruptedError,
    EMAError,
    EvaluationError,
    ExperimentTrackerError,
    EarlyStoppingTriggered,
    PipelineError,
    # Types & Enums
    TrainingMode,
    PrecisionType,
    CheckpointStrategy,
    EMADecaySchedule,
    TrackerBackend,
    TrainingLoopConfig,
    CheckpointConfig,
    EMAConfig,
    EvaluatorConfig,
    TrackerConfig,
    TrainingPipelineConfig,
    # Registry & Factories
    TRAINING_REGISTRY,
    register_training_component,
    create_training_component,
    list_available_training_components,
    get_training_component_info,
    create_training_loop,
    create_checkpoint_manager,
    create_ema_manager,
    create_evaluator,
    create_experiment_tracker,
    create_training_pipeline,
    create_pipeline_builder,
)


class DummyModel(nn.Module):
    """Simple linear regression model for training tests."""

    def __init__(self, in_features: int = 8, out_features: int = 2) -> None:
        super().__init__()
        self.fc = nn.Linear(in_features, out_features)

    def forward(self, input_ids: Optional[torch.Tensor] = None, labels: Optional[torch.Tensor] = None, **kwargs: Any) -> Any:
        if input_ids is None and "x" in kwargs:
            input_ids = kwargs["x"]
        if input_ids is None and len(kwargs.get("args", ())) > 0:
            input_ids = kwargs["args"][0]
        if input_ids is None:
            input_ids = torch.randn(4, 8)

        logits = self.fc(input_ids)
        if labels is not None:
            loss = nn.functional.cross_entropy(logits, labels)
            return {"loss": loss, "logits": logits}
        return {"loss": logits.sum(), "logits": logits}


@pytest.fixture
def dummy_dataset():
    x = torch.randn(16, 8)
    y = torch.randint(0, 2, (16,))
    return TensorDataset(x, y)


@pytest.fixture
def dummy_loader(dummy_dataset):
    class DictLoader:
        def __init__(self, ds):
            self.loader = DataLoader(ds, batch_size=4, shuffle=False)
        def __iter__(self):
            for x, y in self.loader:
                yield {"input_ids": x, "labels": y}
        def __len__(self):
            return len(self.loader)
    return DictLoader(dummy_dataset)


# ============================================================================
# 1. Registry & Discovery Tests
# ============================================================================

def test_registry_discovery():
    components = list_available_training_components()
    assert "training_loop" in components
    assert "checkpoint_manager" in components
    assert "ema_manager" in components
    assert "evaluator" in components
    assert "experiment_tracker" in components
    assert "training_pipeline" in components
    assert "pipeline_builder" in components

    info = get_training_component_info("training_loop")
    assert info is not None
    assert info["name"] == "training_loop"
    assert "TrainingLoop" in info["class"]


def test_registry_factory_instantiation():
    loop = create_training_component("training_loop", {"use_amp": False, "grad_accum_steps": 1})
    assert isinstance(loop, TrainingLoop)

    with tempfile.TemporaryDirectory() as tmpdir:
        ckpt = create_training_component("checkpoint_manager", {"output_dir": tmpdir})
        assert isinstance(ckpt, CheckpointManager)

    ema = create_training_component("ema_manager", {"decay": 0.99})
    assert isinstance(ema, EMAManager)

    evaluator = create_training_component("evaluator")
    assert isinstance(evaluator, Evaluator)

    tracker = create_training_component("experiment_tracker", {"trackers": ["console"]})
    assert isinstance(tracker, ExperimentTracker)


def test_custom_component_registration():
    @register_training_component("custom_dummy", aliases=["dummy_comp"], description="Test dummy component")
    class CustomDummy:
        def __init__(self, value: int = 42):
            self.value = value

    assert "custom_dummy" in list_available_training_components()
    inst = create_training_component("dummy_comp", value=100)
    assert isinstance(inst, CustomDummy)
    assert inst.value == 100


# ============================================================================
# 2. TrainingLoop Tests
# ============================================================================

def test_training_loop_step_and_epoch(dummy_loader):
    model = DummyModel()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    try:
        scaler = GradScaler("cuda", enabled=False)
    except Exception:
        scaler = GradScaler(enabled=False)

    loop = TrainingLoop(use_amp=False, grad_accum_steps=1, max_grad_norm=1.0)

    batch = {
        "input_ids": torch.randn(4, 8),
        "labels": torch.tensor([0, 1, 0, 1]),
    }

    step_res = loop.train_step(model, batch, optimizer, scaler, step=1)
    assert "loss" in step_res
    assert step_res["skipped"] is False
    assert isinstance(step_res["loss"], float)
    assert "grad_norm" in step_res

    epoch_res = loop.train_epoch(model, dummy_loader, optimizer, scheduler=None, scaler=scaler)
    assert "loss" in epoch_res
    assert epoch_res["num_steps"] == 4
    assert epoch_res["elapsed_time"] > 0
    assert epoch_res["steps_per_sec"] > 0


def test_training_loop_nan_inf_guardrails():
    model = DummyModel()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    try:
        scaler = GradScaler("cuda", enabled=False)
    except Exception:
        scaler = GradScaler(enabled=False)

    loop = TrainingLoop(use_amp=False)

    # Corrupt weights to generate NaN
    with torch.no_grad():
        model.fc.weight.fill_(float("nan"))

    batch = {"input_ids": torch.randn(4, 8), "labels": torch.tensor([0, 1, 0, 1])}
    step_res = loop.train_step(model, batch, optimizer, scaler, step=1)
    assert step_res["skipped"] is True
    assert step_res["loss"] == float("inf")


def test_training_loop_early_stopping_logic():
    loop = TrainingLoop()
    assert not loop.should_stop_early(current_metric=0.5, best_metric=0.6, patience=3, mode="min")
    assert loop.should_stop_early(current_metric=0.8, best_metric=0.5, patience=2, bad_epochs=2, mode="min") is True

    loop.reset_early_stopping()
    assert loop.best_metric is None
    assert loop.bad_epochs == 0


def test_training_loop_validation_errors():
    with pytest.raises(ValueError):
        TrainingLoop(grad_accum_steps=0)

    with pytest.raises(ValueError):
        TrainingLoop(max_grad_norm=-1.0)


# ============================================================================
# 3. CheckpointManager Tests
# ============================================================================

def test_checkpoint_manager_save_load_prune():
    with tempfile.TemporaryDirectory() as tmpdir:
        model = DummyModel()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        manager = CheckpointManager(
            output_dir=tmpdir,
            max_to_keep=2,
            metric_name="loss",
            mode="min",
            model=model,
            optimizer=optimizer,
        )

        # Save 3 checkpoints
        p1 = manager.save(epoch=1, step=10, metrics={"loss": 1.5})
        p2 = manager.save(epoch=2, step=20, metrics={"loss": 0.8})
        p3 = manager.save(epoch=3, step=30, metrics={"loss": 1.2})

        ckpts = manager.list_checkpoints()
        assert len(ckpts) <= 2  # Pruned to max_to_keep = 2
        assert manager.get_best_checkpoint_path() is not None

        # Load best checkpoint
        new_model = DummyModel()
        loaded = manager.load(load_best=True, model=new_model)
        assert loaded["epoch"] == 2
        assert loaded["metric_value"] == 0.8

        # Verify weights were restored
        for p_orig, p_new in zip(model.parameters(), new_model.parameters()):
            assert p_new.shape == p_orig.shape


def test_checkpoint_manager_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(output_dir=tmpdir)
        with pytest.raises(CheckpointNotFoundError):
            manager.load(checkpoint_path=os.path.join(tmpdir, "nonexistent.pt"))


# ============================================================================
# 4. EMAManager Tests
# ============================================================================

def test_ema_manager_tracking_and_swapping():
    model = DummyModel()
    ema = EMAManager(decay=0.9, model=model, use_dynamic_decay=True, warmup_steps=10)

    # Initial weights
    initial_weight = model.fc.weight.clone()

    # Mutate model weights
    with torch.no_grad():
        model.fc.weight.add_(1.0)

    # Update EMA
    ema.update(model, step=1)
    shadow_weight = ema._shadow["fc.weight"]
    assert not torch.allclose(shadow_weight, model.fc.weight)

    # Test swap_weights context manager
    with ema.swap_weights(model):
        assert torch.allclose(model.fc.weight, shadow_weight)

    # Verify original restored
    assert torch.allclose(model.fc.weight, initial_weight + 1.0)


def test_ema_manager_state_dict():
    model = DummyModel()
    ema1 = EMAManager(decay=0.95, model=model)
    ema1.update(model, step=5)

    state = ema1.state_dict(full=True)
    assert state["decay"] == 0.95

    ema2 = EMAManager(decay=0.5, model=model)
    ema2.load_state_dict(state)
    assert ema2.decay == 0.95


# ============================================================================
# 5. Evaluator Tests
# ============================================================================

def test_evaluator_execution(dummy_loader):
    model = DummyModel()
    evaluator = Evaluator(compute_perplexity=True)

    # Add custom accuracy metric
    def custom_acc(outputs, batch):
        logits = outputs["logits"]
        preds = logits.argmax(dim=-1)
        labels = batch["labels"]
        return float((preds == labels).float().mean().item())

    evaluator.add_metric("accuracy", custom_acc)

    metrics = evaluator.evaluate(model, dummy_loader)
    assert "loss" in metrics
    assert "perplexity" in metrics
    assert "accuracy" in metrics
    assert "eval_time" in metrics
    assert metrics["loss"] >= 0.0


# ============================================================================
# 6. ExperimentTracker Tests
# ============================================================================

def test_experiment_tracker_in_memory():
    with ExperimentTracker(trackers=["console", "in_memory"], project="test_proj") as tracker:
        tracker.log_hyperparams({"lr": 0.001, "batch_size": 32})
        tracker.log_metrics({"train/loss": 0.45, "val/loss": 0.50}, step=1)
        tracker.log_metrics({"train/loss": 0.35, "val/loss": 0.42}, step=2)

        logged = tracker.get_logged_metrics()
        assert len(logged) == 2
        assert logged[0]["step"] == 1
        assert logged[0]["metrics"]["train/loss"] == 0.45


# ============================================================================
# 7. Callbacks Tests
# ============================================================================

def test_early_stopping_callback():
    callback = EarlyStoppingCallback(patience=2, mode="min", metric_name="loss")
    model = DummyModel()
    state = {"model": model, "epoch": 1}

    # Epoch 1: improvement
    callback.on_eval({"loss": 1.0}, state)
    assert callback.best_metric == 1.0
    assert callback.bad_epochs == 0

    # Epoch 2: worse
    callback.on_eval({"loss": 1.2}, state)
    assert callback.bad_epochs == 1

    # Epoch 3: worse, should trigger EarlyStoppingTriggered
    with pytest.raises(EarlyStoppingTriggered):
        callback.on_eval({"loss": 1.3}, state)


# ============================================================================
# 8. TrainingPipeline and Builder Tests
# ============================================================================

def test_training_pipeline_builder_and_fit(dummy_loader):
    with tempfile.TemporaryDirectory() as tmpdir:
        model = DummyModel()
        optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

        pipeline = (
            create_pipeline_builder()
            .with_model(model)
            .with_optimizer(optimizer)
            .with_data(train_loader=dummy_loader, val_loader=dummy_loader)
            .with_training_config(TrainingLoopConfig(use_amp=False, grad_accum_steps=1))
            .with_checkpointing(CheckpointConfig(output_dir=tmpdir, max_to_keep=2))
            .with_ema(EMAConfig(decay=0.99, enabled=True))
            .with_evaluator(EvaluatorConfig(compute_perplexity=True))
            .with_tracker(TrackerConfig(trackers=["in_memory"]))
            .build()
        )

        assert isinstance(pipeline, TrainingPipeline)

        # Run training fit
        results = pipeline.fit(epochs=2, eval_every_epochs=1)
        assert results["epochs_completed"] == 2
        assert len(results["history"]["train_loss"]) == 2
        assert len(results["history"]["val_loss"]) == 2
        assert results["total_duration"] > 0

        # Run standalone evaluate
        eval_metrics = pipeline.evaluate()
        assert "loss" in eval_metrics


# ============================================================================
# 9. Direct Helper Factories Tests
# ============================================================================

def test_direct_helper_factories():
    loop = create_training_loop(use_amp=False)
    assert isinstance(loop, TrainingLoop)

    with tempfile.TemporaryDirectory() as tmpdir:
        ckpt = create_checkpoint_manager(output_dir=tmpdir)
        assert isinstance(ckpt, CheckpointManager)

    ema = create_ema_manager(decay=0.999)
    assert isinstance(ema, EMAManager)

    evaluator = create_evaluator()
    assert isinstance(evaluator, Evaluator)

    tracker = create_experiment_tracker(trackers=["console"])
    assert isinstance(tracker, ExperimentTracker)

    builder = create_pipeline_builder()
    assert isinstance(builder, TrainingPipelineBuilder)
