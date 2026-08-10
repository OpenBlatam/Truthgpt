"""
Unit Tests for Refactored Optimization Core Factories
======================================================
Validates registry capabilities, exception raising, scope lifecycles, and subsystem factories.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import torch
import torch.nn as nn

from factories import (
    # Registries
    Registry,
    ATTENTION_BACKENDS,
    OPTIMIZERS,
    DATASETS,
    CALLBACKS,
    COLLATORS,
    KV_CACHE_FACTORIES,
    MEMORY_FACTORIES,
    METRICS,
    # Base & Exceptions
    FactoryScope,
    FactoryMetadata,
    KeyNotFoundError,
    DuplicateRegistrationError,
    BuildError,
    # Helper APIs
    create_factory,
    list_available_factories,
    list_factory_items,
    get_factory_info,
    inspect_registry_tree,
    validate_all_factories,
    detect_hardware_capabilities,
    # Attention
    get_attention_backend,
    get_available_attention_backends,
    sdpa_attention,
    math_attention,
    # Optimizer
    get_optimizer,
    create_param_groups,
    build_scheduler,
    # Callback
    get_callback,
    CsvLogger,
    JsonlLogger,
    CompositeLogger,
    # Collate
    get_collator,
    # Dataset
    get_dataset,
    build_synthetic,
    # KV Cache
    get_kv_cache,
    StandardKVCache,
    SlidingWindowKVCache,
    estimate_kv_cache_memory,
    # Memory
    get_memory,
    auto_memory_policy,
    # Metrics
    get_metric,
    MetricAggregator,
)


def test_registry_core_and_events():
    """Test registry registration, fuzzy suggestions, hooks, and singletons."""
    reg = Registry(name="TestRegistry")
    
    events_registered = []
    events_built = []
    
    reg.add_on_register_hook(lambda name, item: events_registered.append(name))
    reg.add_on_build_hook(lambda name, inst: events_built.append(name))

    @reg.register("my_builder", scope=FactoryScope.SINGLETON)
    def my_builder(val: int = 10):
        return {"val": val}

    assert "my_builder" in events_registered
    assert "my_builder" in reg
    
    # Singleton verification
    inst1 = reg.build("my_builder", val=42)
    inst2 = reg.build("my_builder", val=99)  # Should return cached instance inst1
    assert inst1 is inst2
    assert inst1["val"] == 42
    assert "my_builder" in events_built

    # Fuzzy match exception test
    with pytest.raises(KeyNotFoundError) as exc_info:
        reg.get("my_builduer")
    assert "Did you mean: my_builder?" in str(exc_info.value)


def test_unified_dispatcher_and_introspection():
    """Test create_factory dispatcher and registry diagnostics."""
    available = list_available_factories()
    assert "optimizer" in available
    assert "attention" in available
    assert "dataset" in available
    
    opt = create_factory("optimizer", "adamw", [nn.Parameter(torch.randn(2, 2))], lr=1e-3)
    assert isinstance(opt, torch.optim.Optimizer)
    
    tree = inspect_registry_tree()
    assert "adamw" in tree["optimizer"]
    assert "sdpa" in tree["attention"]
    
    validation = validate_all_factories()
    assert all(validation.values())


def test_attention_backends_and_capabilities():
    """Test attention backends and math fallback."""
    backends = get_available_attention_backends()
    assert backends["sdpa"] is True
    assert backends["math"] is True

    fn_sdpa = get_attention_backend("sdpa")
    assert callable(fn_sdpa)
    
    q = torch.randn(2, 4, 8, 16)
    k = torch.randn(2, 4, 8, 16)
    v = torch.randn(2, 4, 8, 16)
    
    out_math = math_attention(q, k, v, is_causal=True)
    assert out_math.shape == (2, 4, 8, 16)


def test_optimizer_factory_and_param_groups():
    """Test optimizers and 1D/2D parameter weight decay grouping."""
    class DummyModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc = nn.Linear(10, 10)
            self.ln = nn.LayerNorm(10)

    model = DummyModel()
    param_groups = create_param_groups(model, weight_decay=0.05)
    assert len(param_groups) == 2
    assert param_groups[0]["weight_decay"] == 0.05
    assert param_groups[1]["weight_decay"] == 0.0

    opt = get_optimizer("adamw", param_groups, lr=1e-3)
    scheduler = build_scheduler(opt, scheduler_type="cosine", num_warmup_steps=10, num_training_steps=100)
    assert scheduler is not None


def test_dataset_factories():
    """Test dataset synthetic data generator and fallback loading."""
    train_texts, val_texts = build_synthetic(num_samples=20, vocab_size=50, seq_len=10)
    assert len(train_texts) == 18
    assert len(val_texts) == 2
    assert isinstance(train_texts[0], str)


def test_kv_cache_factories():
    """Test KV Cache types and memory estimation."""
    std_cache = get_kv_cache("standard", max_batch_size=2, max_seq_len=64, num_heads=4, head_dim=16)
    assert isinstance(std_cache, StandardKVCache)
    
    sliding_cache = get_kv_cache("sliding_window", window_size=32)
    assert isinstance(sliding_cache, SlidingWindowKVCache)
    
    est = estimate_kv_cache_memory(num_layers=12, num_heads=12, head_dim=64, max_seq_len=1024, batch_size=1)
    assert est["megabytes"] > 0


def test_callbacks_and_loggers(tmp_path):
    """Test file loggers and composite loggers."""
    csv_file = str(tmp_path / "test_metrics.csv")
    jsonl_file = str(tmp_path / "test_metrics.jsonl")

    csv_log = get_callback("csv", filepath=csv_file)
    jsonl_log = get_callback("jsonl", filepath=jsonl_file)
    composite = get_callback("composite", loggers=[csv_log, jsonl_log])

    composite.log({"loss": 0.5, "acc": 0.9}, step=1)
    assert (tmp_path / "test_metrics.csv").exists()
    assert (tmp_path / "test_metrics.jsonl").exists()


def test_metrics_and_aggregator():
    """Test metric functions and MetricAggregator."""
    ctx = {"val_loss": 1.0, "accuracy": 0.85, "num_tokens": 1000, "elapsed_sec": 2.0}
    
    assert get_metric("loss", ctx) == 1.0
    assert get_metric("accuracy", ctx) == 0.85
    assert get_metric("throughput", ctx) == 500.0

    agg = MetricAggregator()
    agg.update({"loss": 1.0})
    agg.update({"loss": 0.5})
    assert agg.get_mean("loss") == 0.75


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
