"""
Comprehensive Unit Tests for Optimization Core Factories
=========================================================
Tests for Registry, Attention, Optimizer, Scheduler, Datasets, Callbacks,
Collators, KV Cache, Memory Managers, Metrics, and Master Unified Orchestrator.
Run with: pytest tests/test_factories_comprehensive.py -v
"""

import math
import os
import pytest
import torch
import torch.nn as nn


def test_registry_advanced_features():
    """Test priority, aliasing, lifecycle hooks, search, and deprecation in Registry."""
    from factories.registry import Registry

    reg = Registry[str]("TestRegistry")

    # Priority & Metadata registration
    @reg.register("high_priority", priority=100, tags=["prod"], description="High priority item")
    def high_item():
        return "high"

    @reg.register("low_priority", priority=10, tags=["dev"], description="Low priority item")
    def low_item():
        return "low"

    # Alias registration
    reg.register_alias("high_alias", "high_priority")

    # Key lookup
    assert reg.get("high_priority") == high_item
    assert reg.get("high_alias") == high_item
    assert reg.build("high_alias") == "high"

    # Priority ordering in keys()
    keys = reg.keys()
    assert keys[0] == "high_priority"
    assert keys[1] == "low_priority"

    # Tag filtering & search
    assert reg.list_by_tag("prod") == ["high_priority"]
    assert "high_priority" in reg.search("high")

    # Hooks
    registered_items = []
    built_items = []
    reg.add_register_hook(lambda name, item: registered_items.append(name))
    reg.add_build_hook(lambda name, item: built_items.append(name))


    @reg.register("hooked_item")
    def hooked_fn():
        return "hooked"

    assert "hooked_item" in registered_items
    reg.build("hooked_item")
    assert "hooked_item" in built_items

    # Deprecation warning
    @reg.register("deprecated_item", deprecated=True, deprecation_msg="Use new_item instead.")
    def legacy_fn():
        return "legacy"

    with pytest.warns(DeprecationWarning, match="Use new_item instead."):
        assert reg.get("deprecated_item") == legacy_fn

    # Missing item suggestion hint
    with pytest.raises(KeyError, match="Did you mean: high_priority"):
        reg.get("high_priorit")

    # Serialization
    manifest = reg.to_dict()
    assert manifest["registry_name"] == "TestRegistry"
    assert "high_priority" in manifest["items"]


def test_attention_factory():
    """Test attention backend construction and auto-selection."""
    from factories.attention import (
        ATTENTION_BACKENDS,
        AttentionConfig,
        auto_select_attention_backend,
        build_sdpa,
        sdpa_attention,
    )

    assert "sdpa" in ATTENTION_BACKENDS
    assert "flash" in ATTENTION_BACKENDS
    assert "triton" in ATTENTION_BACKENDS
    assert "xformers" in ATTENTION_BACKENDS

    # SDPA Execution
    q = torch.randn(2, 4, 16, 32)
    k = torch.randn(2, 4, 16, 32)
    v = torch.randn(2, 4, 16, 32)

    out = sdpa_attention(q, k, v, is_causal=True)
    assert out.shape == q.shape

    sdpa_fn = ATTENTION_BACKENDS.build("sdpa")
    out_built = sdpa_fn(q, k, v, is_causal=True)
    assert out_built.shape == q.shape

    backend = auto_select_attention_backend(seq_len=2048, head_dim=64)
    assert isinstance(backend, str)


def test_optimizer_and_scheduler_factory():
    """Test optimizers, schedulers, and parameter group weight decay partitioning."""
    from factories.optimizer import (
        OPTIMIZERS,
        SCHEDULERS,
        OptimizerConfig,
        create_param_groups,
    )

    model = nn.Sequential(
        nn.Linear(32, 64),
        nn.BatchNorm1d(64),
        nn.ReLU(),
        nn.Linear(64, 10),
    )

    # Param groups
    param_groups = create_param_groups(model, weight_decay=0.01)
    assert len(param_groups) == 2
    assert param_groups[0]["weight_decay"] == 0.01
    assert param_groups[1]["weight_decay"] == 0.0

    # Build Optimizers
    opt_adamw = OPTIMIZERS.build("adamw", param_groups, lr=1e-3)
    assert isinstance(opt_adamw, torch.optim.Optimizer)

    opt_sgd = OPTIMIZERS.build("sgd", model.parameters(), lr=1e-2)
    assert isinstance(opt_sgd, torch.optim.Optimizer)

    opt_lion = OPTIMIZERS.build("lion", model.parameters(), lr=1e-4)
    assert isinstance(opt_lion, torch.optim.Optimizer)

    # Build Schedulers
    sched_cosine = SCHEDULERS.build("cosine", opt_adamw, total_steps=100, warmup_steps=10)
    assert sched_cosine is not None

    sched_onecycle = SCHEDULERS.build("onecycle", opt_adamw, max_lr=1e-3, total_steps=100)
    assert sched_onecycle is not None


def test_datasets_factory():
    """Test synthetic benchmark datasets and local file dataset builders."""
    from factories.datasets import DATASETS, build_synthetic

    assert "synthetic" in DATASETS
    assert "hf" in DATASETS
    assert "jsonl" in DATASETS

    train_data, val_data = DATASETS.build("synthetic", num_samples=100, seq_len_words=10)
    assert len(train_data) == 90
    assert len(val_data) == 10
    assert isinstance(train_data[0], str)


def test_callbacks_factory(tmp_path):
    """Test callbacks, CSV loggers, JSON loggers, early stopping, and CompositeCallback."""
    from factories.callbacks import (
        CALLBACKS,
        CSVLoggerCallback,
        CompositeCallback,
        EarlyStoppingCallback,
        build_composite_callback,
    )

    assert "print" in CALLBACKS
    assert "wandb" in CALLBACKS
    assert "tensorboard" in CALLBACKS

    # CSV Logger
    csv_file = os.path.join(tmp_path, "metrics.csv")
    csv_cb = CSVLoggerCallback(filename=csv_file)
    csv_cb.log({"loss": 0.5, "acc": 0.9}, step=1)
    assert os.path.exists(csv_file)

    # Early stopping
    es = EarlyStoppingCallback(monitor="val_loss", patience=2)
    es.on_epoch_end(1, {"val_loss": 0.5})
    es.on_epoch_end(2, {"val_loss": 0.6})
    es.on_epoch_end(3, {"val_loss": 0.7})
    assert es.should_stop is True

    # Composite Callback
    comp = build_composite_callback(["print", csv_cb])
    comp.log({"loss": 0.4}, step=2)


def test_collate_factory():
    """Test language modeling collator dynamic padding and sequence packing."""
    from factories.collate import COLLATE

    assert "lm" in COLLATE
    assert "packed_lm" in COLLATE

    class DummyTokenizer:
        pad_token_id = 0

        def __call__(self, texts, truncation=True, max_length=128, padding=False, **kwargs):
            return [{"input_ids": [101, 200, 300]} for _ in texts]

    tok = DummyTokenizer()

    collate_fn = COLLATE.build("lm", tokenizer=tok, max_length=128)
    batch = ["sample text 1", "sample text two long"]
    out = collate_fn(batch)

    assert "input_ids" in out
    assert "attention_mask" in out
    assert "labels" in out
    assert out["input_ids"].shape[0] == 2


def test_kv_cache_factory():
    """Test KV Cache building."""
    from factories.kv_cache import KV_CACHE, SlidingWindowKVCache

    assert "none" in KV_CACHE
    assert "paged" in KV_CACHE
    assert "sliding_window" in KV_CACHE

    none_cache = KV_CACHE.build("none")
    assert none_cache is None

    paged_cache = KV_CACHE.build("paged", num_heads=4, head_dim=32, max_tokens=256)
    assert paged_cache is not None

    sw_cache = KV_CACHE.build("sliding_window", num_heads=4, head_dim=32, window_size=128)
    assert isinstance(sw_cache, SlidingWindowKVCache)


def test_memory_factory():
    """Test memory manager policy construction."""
    from factories.memory import MEMORY_MANAGERS

    assert "adaptive" in MEMORY_MANAGERS
    assert "static" in MEMORY_MANAGERS

    mem_adaptive = MEMORY_MANAGERS.build("adaptive")
    assert mem_adaptive is not None

    mem_static = MEMORY_MANAGERS.build("static")
    assert mem_static is not None


def test_metrics_factory():
    """Test metrics calculators."""
    from factories.metrics import METRICS

    ctx = {"val_loss": 1.0, "accuracy": 0.85, "latency_p99": 12.5}

    loss_val = METRICS.build("loss", ctx)
    assert loss_val == 1.0

    ppl_val = METRICS.build("ppl", ctx)
    assert math.isclose(ppl_val, math.exp(1.0), rel_tol=1e-4)

    acc_val = METRICS.build("accuracy", ctx)
    assert acc_val == 0.85

    bpc_val = METRICS.build("bpc", ctx)
    assert math.isclose(bpc_val, 1.0 / math.log(2), rel_tol=1e-4)


def test_master_factory_orchestration():
    """Test create_factory, info inspection, and MasterFactory pipelines."""
    from factories import (
        MasterFactory,
        create_factory,
        get_factory_info,
        list_available_factories,
        list_factory_items,
    )

    available = list_available_factories()
    assert "optimizer" in available
    assert "attention" in available

    opt_items = list_factory_items("optimizer")
    assert "adamw" in opt_items

    info = get_factory_info("attention")
    assert info["type"] == "attention"

    # Test create_factory
    opt_fn = create_factory("optimizer", "adamw", params=[nn.Parameter(torch.empty(2, 2))])
    assert isinstance(opt_fn, torch.optim.Optimizer)

    # Test MasterFactory build from dict config
    mf = MasterFactory()
    config = {
        "attention": {"backend": "sdpa"},
        "kv_cache": {"type": "paged", "num_heads": 4, "head_dim": 32},
        "memory": {"policy": "adaptive"},
    }
    built = mf.build_from_config(config)
    assert "attention" in built
    assert "kv_cache" in built
    assert "memory" in built


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
