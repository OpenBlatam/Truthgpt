# 🚀 Training Module Refactoring — Complete Architectural Overview

## Overview

The `optimization_core.training` package has been completely refactored into a modern, decoupled, and extensible subsystem. It provides a thread-safe discovery registry, event-driven callbacks, a fluent pipeline builder, robust atomic checkpointing, exponential moving average (EMA) parameter tracking, multi-backend experiment tracking, and evaluation engines.

---

## 🏛️ Architectural Directory Structure

```
training/
├── __init__.py                  # Unified exports, lazy-loading factory functions & backward compatibility
├── interfaces.py                # Abstract Base Classes (BaseTrainingLoop, BaseCheckpointManager, BaseEMAManager, BaseEvaluator, BaseExperimentTracker, BaseCallback, BaseTrainingPipeline)
├── exceptions.py                # Hierarchical typed exceptions (TrainingError, CheckpointError, CheckpointNotFoundError, CheckpointCorruptedError, EMAError, EvaluationError, ExperimentTrackerError, TrainingConfigurationError, EarlyStoppingTriggered, GradientOverflowError)
├── types.py                     # Dataclasses & Enums (TrainingMode, CheckpointStrategy, EMADecaySchedule, TrackerBackend, StepResult, EpochResult, EvaluationMetrics, CheckpointMetadata, TrainingLoopConfig, CheckpointConfig, EMAConfig, TrackerConfig, TrainingPipelineConfig)
├── registry.py                  # Thread-safe TrainingRegistry, @register_training_component decorator, component discovery & instantiation APIs
├── callbacks.py                 # Comprehensive callback system (BaseCallback, Callback, EarlyStoppingCallback, ModelCheckpointCallback, LRMonitorCallback, MetricsLoggerCallback, GradientNormCallback, ProgressCallback, CallbackHandler)
├── training_loop.py             # Enterprise TrainingLoop (AMP fp16/bf16, grad accumulation, grad norm/val clipping, loss extraction, non-finite guardrails, early stopping)
├── checkpoint_manager.py        # Enterprise CheckpointManager (Atomic temporary-file writes, RNG state capture/restore across torch/numpy/python/cuda, metadata manifests, top-k retention, safe loading)
├── ema_manager.py               # Enterprise EMAManager (Dynamic decay warmup, CPU offloading, precision-aware shadow tracking, exception-safe weight swapping context manager)
├── evaluator.py                 # Enterprise Evaluator (Recursive batch device transfer, AMP evaluation, custom metrics callable registry, perplexity & loss computation)
├── experiment_tracker.py        # Enterprise ExperimentTracker (Multi-backend dispatch: WandB, TensorBoard, MLFlow, Console, Logger, context manager, safe fallbacks)
└── pipeline.py                  # Fluent TrainingPipeline & TrainingPipelineBuilder for end-to-end orchestration
```

---

## 🔑 Key Features & Components

### 1. Unified Factory & Registry Dispatch
Instantiate any training component, manager, or pipeline through a single interface:

```python
from training import (
    create_training_component,
    list_available_training_components,
    get_training_component_info,
)

# Discover registered training components
components = list_available_training_components()
# ['checkpoint_manager', 'ema_manager', 'evaluator', 'experiment_tracker', 'pipeline_builder', 'training_loop', 'training_pipeline']

# Query metadata
info = get_training_component_info("training_loop")

# Direct factory creation
loop = create_training_component("training_loop", {"use_amp": True, "grad_accum_steps": 2})
checkpoint_mgr = create_training_component("checkpoint_manager", {"output_dir": "./checkpoints"})
ema_mgr = create_training_component("ema_manager", {"decay": 0.999})
evaluator = create_training_component("evaluator", {"compute_perplexity": True})
tracker = create_training_component("experiment_tracker", {"trackers": ["console", "in_memory"]})
```

### 2. Fluent Training Pipeline Builder
Construct and orchestrate end-to-end training runs declaratively:

```python
from training import (
    create_pipeline_builder,
    TrainingLoopConfig,
    CheckpointConfig,
    EMAConfig,
    EvaluatorConfig,
    TrackerConfig,
    EarlyStoppingCallback,
)

pipeline = (
    create_pipeline_builder()
    .with_model(model)
    .with_optimizer(optimizer, scheduler)
    .with_data(train_loader=train_loader, val_loader=val_loader)
    .with_training_config(TrainingLoopConfig(use_amp=True, grad_accum_steps=2, max_grad_norm=1.0))
    .with_checkpointing(CheckpointConfig(output_dir="./checkpoints", save_best=True, max_to_keep=3))
    .with_ema(EMAConfig(decay=0.999, offload_to_cpu=True))
    .with_evaluator(EvaluatorConfig(compute_perplexity=True))
    .with_tracker(TrackerConfig(trackers=["console", "wandb"]))
    .with_callbacks([EarlyStoppingCallback(patience=5, mode="min")])
    .build()
)

# Run training
history = pipeline.fit(epochs=10, eval_every_epochs=1)
```

### 3. Atomic Checkpointing with RNG Preservation
Zero risk of corrupted checkpoint files from aborted saves, with complete RNG state preservation:

```python
from training import CheckpointManager, CheckpointConfig

manager = CheckpointManager(
    output_dir="./checkpoints",
    model=model,
    optimizer=optimizer,
    max_to_keep=3,
    metric_name="loss",
    mode="min",
)

# Save with atomic temporary file replacement and manifest updates
path = manager.save(epoch=1, step=100, metrics={"loss": 0.42})

# Restore best checkpoint
checkpoint_data = manager.load(load_best=True, model=model)
```

### 4. Precision-Aware EMA with Weight Swapping
Efficiently track Exponential Moving Average parameters with dynamic decay warmup and context-managed zero-copy evaluation:

```python
from training import EMAManager

ema = EMAManager(decay=0.999, model=model, use_dynamic_decay=True, warmup_steps=1000)

# Step update
ema.update(model, step=current_step)

# Zero-copy weight swap for validation
with ema.swap_weights(model):
    val_loss = evaluator.evaluate(model, val_loader)
```

---

## 🔄 Backward Compatibility Table

| Legacy Name | New Refactored Name | Status |
|:---|:---|:---|
| `TrainingLoop` | `optimization_core.training.TrainingLoop` | ✅ 100% Compatible |
| `CheckpointManager` | `optimization_core.training.CheckpointManager` | ✅ 100% Compatible |
| `EMAManager` | `optimization_core.training.EMAManager` | ✅ 100% Compatible |
| `Evaluator` | `optimization_core.training.Evaluator` | ✅ 100% Compatible |
| `ExperimentTracker` | `optimization_core.training.ExperimentTracker` | ✅ 100% Compatible |
| `TrainingError` | `optimization_core.training.TrainingError` | ✅ 100% Compatible |
| `CheckpointError` | `optimization_core.training.CheckpointError` | ✅ 100% Compatible |
| `EMAError` | `optimization_core.training.EMAError` | ✅ 100% Compatible |
| `EvaluationError` | `optimization_core.training.EvaluationError` | ✅ 100% Compatible |
| `ExperimentTrackerError` | `optimization_core.training.ExperimentTrackerError` | ✅ 100% Compatible |
| `create_training_component` | `optimization_core.training.create_training_component` | ✅ 100% Compatible |
| `list_available_training_components` | `optimization_core.training.list_available_training_components` | ✅ 100% Compatible |

---

## ✅ Verification

Both test suites executed and validated:
- `tests/unit/test_training_refactor.py` (New comprehensive test suite covering all 9 subsystems)
- `tests/unit/test_training_module.py` (Legacy backward-compatibility test suite)
