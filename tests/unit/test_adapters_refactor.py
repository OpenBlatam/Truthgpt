"""
Comprehensive Unit Tests for Refactored Adapters Package.
Tests cover ObjectStore, BaseAdapter/BaseDynamicAdapter, OptimizerAdapter,
DataAdapter, ModelAdapter, TrainingAdapter, TruthGPTAdapters,
EnterpriseTruthGPTAdapter, and the unified create_adapter factory.
"""

import os
import tempfile
import unittest
import torch
import torch.nn as nn
from pydantic import BaseModel

import sys
# Ensure optimization_core and parent directory are in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_opt_core_dir = os.path.abspath(os.path.join(_current_dir, "..", ".."))
_parent_dir = os.path.dirname(_opt_core_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)
if _opt_core_dir not in sys.path:
    sys.path.insert(0, _opt_core_dir)

import optimization_core.adapters as adapters
from optimization_core.adapters.base import (
    ObjectStore,
    ObjectEntry,
    StoreStats,
    AdapterRunResult,
    BaseAdapter,
    BaseDynamicAdapter,
)
from optimization_core.adapters.optimizer_adapter import (
    OptimizerAdapter,
    PyTorchOptimizerAdapter,
    OptimizerCreateResult,
    OptimizerStateResult,
)
from optimization_core.adapters.data_adapter import (
    DataAdapter,
    JSONLDataAdapter,
    HuggingFaceDataAdapter,
    DataSplitStats,
)
from optimization_core.adapters.model_adapter import (
    ModelAdapter,
    HuggingFaceModelAdapter,
    ModelInfoResult,
)
from optimization_core.adapters.training_adapter import (
    TrainingAdapter,
    TrainingCreateResult,
)
from optimization_core.adapters.truthgpt_adapters import (
    TruthGPTAdapter,
    TruthGPTConfig,
    TruthGPTPerformanceAdapter,
    TruthGPTMemoryAdapter,
    TruthGPTGPUAdapter,
    TruthGPTValidationAdapter,
    TruthGPTIntegratedAdapter,
    create_truthgpt_adapter,
    quick_truthgpt_setup,
)
from optimization_core.adapters.enterprise_truthgpt_adapter import (
    EnterpriseTruthGPTAdapter,
)


class DummyModel(nn.Module):
    """Simple linear model for testing."""
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(10, 2)

    def forward(self, x):
        return self.fc(x)


class TestObjectStore(unittest.TestCase):
    """Tests for ObjectStore singleton and operations."""

    def setUp(self):
        self.store = ObjectStore.instance()
        self.store.clear()

    def test_put_get_has_optional(self):
        dummy = {"a": 123}
        obj_id = self.store.put(dummy, kind="test_kind", meta={"foo": "bar"})
        
        self.assertTrue(self.store.has(obj_id))
        self.assertFalse(self.store.has("non_existent_id"))
        
        retrieved = self.store.get(obj_id)
        self.assertEqual(retrieved, dummy)
        
        optional_obj = self.store.get_optional(obj_id)
        self.assertEqual(optional_obj, dummy)
        
        missing_optional = self.store.get_optional("non_existent_id", default="fallback")
        self.assertEqual(missing_optional, "fallback")

    def test_get_key_error(self):
        with self.assertRaises(KeyError):
            self.store.get("non_existent_id")

    def test_entry_meta_delete_clear(self):
        obj_id = self.store.put("sample_data", kind="string", meta={"tag": "v1"})
        
        entry = self.store.get_entry(obj_id)
        self.assertIsInstance(entry, ObjectEntry)
        self.assertEqual(entry.kind, "string")
        
        meta = self.store.get_meta(obj_id)
        self.assertEqual(meta["tag"], "v1")
        
        ids = self.store.list_ids(kind="string")
        self.assertIn(obj_id, ids)
        
        stats = self.store.stats()
        self.assertIsInstance(stats, StoreStats)
        self.assertEqual(stats.total_objects, 1)
        
        deleted = self.store.delete(obj_id)
        self.assertTrue(deleted)
        self.assertFalse(self.store.has(obj_id))
        
        self.store.put("item1", kind="k1")
        self.store.put("item2", kind="k2")
        cleared_count = self.store.clear()
        self.assertEqual(cleared_count, 2)
        self.assertEqual(len(self.store.list_ids()), 0)

    def test_custom_id_get_by_kind_clear_kind(self):
        cid = self.store.put("custom_val", kind="custom_kind", custom_id="my_custom_id_123")
        self.assertEqual(cid, "my_custom_id_123")
        self.assertEqual(self.store.get("my_custom_id_123"), "custom_val")

        by_kind = self.store.get_by_kind("custom_kind")
        self.assertIn("my_custom_id_123", by_kind)
        self.assertEqual(by_kind["my_custom_id_123"], "custom_val")

        cleared = self.store.clear_kind("custom_kind")
        self.assertEqual(cleared, 1)
        self.assertFalse(self.store.has("my_custom_id_123"))

    def test_ttl_expiration(self):
        import time
        obj_id = self.store.put("short_lived", kind="temp", ttl_seconds=0.05)
        self.assertTrue(self.store.has(obj_id))
        time.sleep(0.06)
        self.assertFalse(self.store.has(obj_id))
        with self.assertRaises(KeyError):
            self.store.get(obj_id)



class TestOptimizerAdapter(unittest.TestCase):
    """Tests for OptimizerAdapter and PyTorchOptimizerAdapter."""

    def setUp(self):
        self.store = ObjectStore.instance()
        self.store.clear()
        self.adapter = PyTorchOptimizerAdapter()
        self.model = DummyModel()
        self.model_id = self.store.put(self.model, kind="model")

    def test_create_optimizer_success(self):
        res = self.adapter.process({
            "action": "create",
            "model_id": self.model_id,
            "optimizer_type": "adamw",
            "kwargs": {"lr": 0.001}
        })
        self.assertEqual(res["status"], "success")
        self.assertIn("optimizer_id", res)
        opt_id = res["optimizer_id"]
        
        optimizer = self.store.get(opt_id)
        self.assertIsInstance(optimizer, torch.optim.Optimizer)

    def test_extended_optimizers_and_actions(self):
        res_adamax = self.adapter.process({
            "action": "create",
            "model_id": self.model_id,
            "optimizer_type": "adamax",
            "kwargs": {"lr": 0.002}
        })
        self.assertEqual(res_adamax["status"], "success")
        opt_id = res_adamax["optimizer_id"]

        # Test zero_grad and step actions
        zg_res = self.adapter.process({"action": "zero_grad", "optimizer_id": opt_id})
        self.assertEqual(zg_res["status"], "success")

        st_res = self.adapter.process({"action": "step", "optimizer_id": opt_id})
        self.assertEqual(st_res["status"], "success")

    def test_create_optimizer_missing_model_id(self):
        res = self.adapter.process({
            "action": "create",
            "optimizer_type": "adamw"
        })
        self.assertEqual(res["status"], "error")
        self.assertIn("model_id is required", res["message"])

    def test_get_state_and_list(self):
        create_res = self.adapter.process({
            "action": "create",
            "model_id": self.model_id,
            "optimizer_type": "sgd",
            "kwargs": {"lr": 0.01}
        })
        opt_id = create_res["optimizer_id"]
        
        state_res = self.adapter.process({
            "action": "get_state",
            "optimizer_id": opt_id
        })
        self.assertEqual(state_res["status"], "success")
        self.assertEqual(state_res["type_name"], "SGD")
        self.assertEqual(state_res["lr"], 0.01)
        
        list_res = self.adapter.process({"action": "list"})
        self.assertEqual(list_res["status"], "success")
        self.assertIn(opt_id, list_res["optimizers"])

    def test_unknown_action(self):
        res = self.adapter.process({"action": "unknown_act"})
        self.assertEqual(res["status"], "error")


class TestDataAdapter(unittest.TestCase):
    """Tests for DataAdapter and JSONLDataAdapter."""

    def setUp(self):
        self.store = ObjectStore.instance()
        self.store.clear()

    def test_jsonl_data_adapter(self):
        adapter = JSONLDataAdapter()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            f.write('{"text": "hello world 1"}\n')
            f.write('{"text": "hello world 2"}\n')
            f.write('{"text": "hello world 3"}\n')
            temp_path = f.name

        try:
            res = adapter.process({
                "action": "load",
                "source": temp_path,
                "kwargs": {"text_field": "text", "train_split": 0.66}
            })
            self.assertEqual(res["status"], "success")
            self.assertIn("data_id", res)
            self.assertEqual(res["total_samples"], 3)
            
            info_res = adapter.process({
                "action": "info",
                "data_id": res["data_id"]
            })
            self.assertEqual(info_res["status"], "success")
            self.assertEqual(info_res["meta"]["train_samples"] + info_res["meta"]["val_samples"], 3)
            
            list_res = adapter.process({"action": "list"})
            self.assertIn(res["data_id"], list_res["datasets"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_gzip_jsonl_loading(self):
        import gzip
        adapter = JSONLDataAdapter()
        with tempfile.NamedTemporaryFile(suffix=".jsonl.gz", delete=False) as f:
            temp_path = f.name

        try:
            with gzip.open(temp_path, "wt", encoding="utf-8") as gz:
                gz.write('{"text": "compressed line 1"}\n')
                gz.write('{"text": "compressed line 2"}\n')

            train, val = adapter.load_data(temp_path, text_field="text", train_split=0.5)
            self.assertEqual(len(train), 1)
            self.assertEqual(len(val), 1)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_jsonl_file_not_found(self):
        adapter = JSONLDataAdapter()
        with self.assertRaises(FileNotFoundError):
            adapter.load_data("non_existent_file.jsonl")


class TestModelAdapter(unittest.TestCase):
    """Tests for ModelAdapter."""

    def setUp(self):
        self.store = ObjectStore.instance()
        self.store.clear()
        self.adapter = ModelAdapter()
        self.model = DummyModel()
        self.model_id = self.store.put(self.model, kind="model")

    def test_info_and_list_action(self):
        info_res = self.adapter.process({
            "action": "info",
            "model_id": self.model_id
        })
        self.assertEqual(info_res["status"], "success")
        self.assertEqual(info_res["num_parameters"], 22)  # 10*2 + 2 = 22
        
        list_res = self.adapter.process({"action": "list"})
        self.assertIn(self.model_id, list_res["models"])

    def test_eval_train_count_actions(self):
        eval_res = self.adapter.process({"action": "eval", "model_id": self.model_id})
        self.assertEqual(eval_res["status"], "success")
        self.assertEqual(eval_res["mode"], "eval")

        train_res = self.adapter.process({"action": "train", "model_id": self.model_id})
        self.assertEqual(train_res["status"], "success")
        self.assertEqual(train_res["mode"], "train")

        cnt_res = self.adapter.process({"action": "count_parameters", "model_id": self.model_id})
        self.assertEqual(cnt_res["status"], "success")
        self.assertEqual(cnt_res["num_parameters"], 22)


class TestTruthGPTAdapter(unittest.TestCase):
    """Tests for TruthGPTAdapter and legacy adapters."""

    def setUp(self):
        self.store = ObjectStore.instance()
        self.store.clear()
        self.adapter = TruthGPTAdapter()
        self.model = DummyModel()
        self.model_id = self.store.put(self.model, kind="model")

    def test_truthgpt_config_dict(self):
        cfg = TruthGPTConfig(model_name="CustomName")
        d = cfg.to_dict()
        self.assertEqual(d["model_name"], "CustomName")
        cfg2 = TruthGPTConfig.from_dict(d)
        self.assertEqual(cfg2.model_name, "CustomName")

    def test_truthgpt_adapt(self):
        res = self.adapter.process({
            "action": "adapt",
            "model_id": self.model_id
        })
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["model_type"], "DummyModel")
        self.assertEqual(res["parameter_count"], 22)

    def test_backward_compat_legacy_adapters(self):
        cfg = TruthGPTConfig(model_name="test_model")
        perf_adapter = TruthGPTPerformanceAdapter(cfg)
        mem_adapter = TruthGPTMemoryAdapter(cfg)
        gpu_adapter = TruthGPTGPUAdapter(cfg)
        val_adapter = TruthGPTValidationAdapter(cfg)
        
        m = DummyModel()
        self.assertIs(perf_adapter.optimize_for_performance(m), m)
        self.assertIs(mem_adapter.optimize_for_memory(m), m)
        self.assertIs(gpu_adapter.optimize_for_gpu(m), m)
        self.assertTrue(val_adapter.validate_model(m)["validated"])
        
        integrated, _ = quick_truthgpt_setup("test")
        full_res = integrated.full_adaptation(m)
        self.assertEqual(full_res["summary"]["successful_adaptations"], 3)


class TestEnterpriseTruthGPTAdapter(unittest.TestCase):
    """Tests for EnterpriseTruthGPTAdapter."""

    def setUp(self):
        self.store = ObjectStore.instance()
        self.store.clear()
        self.adapter = EnterpriseTruthGPTAdapter()

    def test_enterprise_create_info_optimize(self):
        create_res = self.adapter.process({"action": "create"})
        self.assertEqual(create_res["status"], "success")
        model_id = create_res["model_id"]
        
        info_res = self.adapter.process({
            "action": "info",
            "model_id": model_id
        })
        self.assertEqual(info_res["status"], "success")
        
        opt_res = self.adapter.process({
            "action": "optimize",
            "model_id": model_id
        })
        self.assertEqual(opt_res["status"], "success")

    def test_enterprise_error_handling_no_attribute_error(self):
        res = self.adapter.process({"action": "invalid_action"})
        self.assertEqual(res["status"], "error")
        self.assertIn("Unknown truthgpt enterprise action", res["message"])


class TestAdapterFactory(unittest.TestCase):
    """Tests for unified create_adapter factory and module registry."""

    def test_create_adapter(self):
        opt_adapter = adapters.create_adapter("optimizer", "pytorch")
        self.assertIsInstance(opt_adapter, PyTorchOptimizerAdapter)

        opt_adapter_alias = adapters.create_adapter("optimizer", "torch")
        self.assertIsInstance(opt_adapter_alias, PyTorchOptimizerAdapter)
        
        jsonl_adapter = adapters.create_adapter("data", "jsonl")
        self.assertIsInstance(jsonl_adapter, JSONLDataAdapter)

        hf_adapter_alias = adapters.create_adapter("data", "hf")
        self.assertIsInstance(hf_adapter_alias, HuggingFaceDataAdapter)
        
        truth_adapter = adapters.create_adapter("truthgpt", "default")
        self.assertIsInstance(truth_adapter, TruthGPTAdapter)
        
        ent_adapter = adapters.create_adapter("enterprise", "default")
        self.assertIsInstance(ent_adapter, EnterpriseTruthGPTAdapter)

    def test_registry_inspection_helpers(self):
        types = adapters.list_available_adapter_types()
        self.assertIn("optimizer", types)
        self.assertIn("data", types)
        
        subtypes = adapters.list_available_adapter_subtypes("optimizer")
        self.assertIn("pytorch", subtypes)
        
        info = adapters.get_adapter_info("optimizer", "pytorch")
        self.assertEqual(info["type"], "optimizer")
        self.assertEqual(info["subtype"], "pytorch")

    def test_register_adapter(self):
        class CustomTestAdapter(BaseDynamicAdapter):
            name = "custom_test_adapter"
            def process(self, input_data):
                return {"status": "custom"}

        adapters.register_adapter("custom_type", "v1", CustomTestAdapter, description="Custom Test")
        self.assertIn("custom_type", adapters.list_available_adapter_types())
        info = adapters.get_adapter_info("custom_type", "v1")
        self.assertEqual(info["class"], "CustomTestAdapter")


    def test_dual_module_resolution(self):
        import adapters as a1
        import optimization_core.adapters as a2
        self.assertIs(a1, a2)


class TestBaseDynamicAdapterRun(unittest.IsolatedAsyncioTestCase):
    """Tests for BaseDynamicAdapter.run() JSON parsing interface."""

    def setUp(self):
        self.store = ObjectStore.instance()
        self.store.clear()
        self.model_id = self.store.put(DummyModel(), kind="model")
        self.adapter = PyTorchOptimizerAdapter()

    async def test_run_valid_json(self):
        input_str = f'{{"action": "create", "model_id": "{self.model_id}", "optimizer_type": "adam"}}'
        result = await self.adapter.run(input_str)
        if isinstance(result, dict):
            self.assertEqual(result["status"], "success")
        else:
            # If ToolResult object
            self.assertIn("success", result.output)

    async def test_run_invalid_json(self):
        input_str = '{"action": invalid json...}'
        result = await self.adapter.run(input_str)
        if isinstance(result, dict):
            self.assertIn("error", result)
        else:
            self.assertIn("Error", result.output)


if __name__ == "__main__":
    unittest.main()
