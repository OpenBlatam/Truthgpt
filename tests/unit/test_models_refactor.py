"""
Comprehensive Unit Tests for Refactored Models Subsystem
=========================================================
Covers lazy loading, exceptions, interfaces, schemas, ModelRegistry, ModelBuilder,
ModelManager, AttentionUtils & Positional Encodings, DiffusionManager, HuggingFace
wrappers (HFTransformersModel, HFDiffusersModel), and native TruthGPT architectures.
"""

import os
import sys
import tempfile
import unittest
from typing import Any, Dict

import torch
import torch.nn as nn

# Ensure workspace paths in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_opt_core_dir = os.path.abspath(os.path.join(_current_dir, "..", ".."))
_parent_dir = os.path.dirname(_opt_core_dir)
if _opt_core_dir not in sys.path:
    sys.path.insert(0, _opt_core_dir)
if _parent_dir not in sys.path:
    sys.path.append(_parent_dir)

import models
from models.exceptions import (
    AttentionError,
    DevicePlacementError,
    DiffusionError,
    ModelConfigurationError,
    ModelError,
    ModelInitializationError,
    ModelInferenceError,
    ModelLoadError,
    ModelNotFoundError,
    ModelOptimizationError,
    ModelSaveError,
    QuantizationError,
)
from models.interfaces import (
    AttentionOptimizationResult,
    BaseAttentionOptimizer,
    BaseDiffusionManager,
    BaseModel,
    BaseModelManager,
    BaseModelManagerProtocol,
    BaseModelProtocol,
    DiffusionInferenceResult,
    GenerationConfig,
    IAttentionOptimizer,
    IDiffusionManager,
    IModel,
    IModelManager,
    ModelInfoResult,
    ModelInferenceResult,
    ModelLoadResult,
    ModelSaveResult,
)
from models.registry import (
    MODEL_REGISTRY,
    ModelRegistry,
    build_model,
    create_model,
    get_model_info,
    list_available_models,
    register_model,
)
from models.model_builder import (
    ModelBuilder,
    create_model_builder,
)
from models.model_manager import ModelManager
from models.attention_utils import (
    ALiBiPositionalEmbedding,
    AttentionOptimizer,
    AttentionUtils,
    EfficientAttention,
    PositionalEncoding,
    RotaryPositionalEmbedding,
)
from models.diffusion_manager import (
    DiffusionManager,
    DiffusionModelManager,
    DiffusionTrainer,
)
from models.hf_transformers import (
    HFLLM,
    HFTransformersModel,
    create_hf_transformers_model,
)
from models.hf_diffusers import (
    HFDiffusion,
    HFDiffusersModel,
    create_hf_diffusers_model,
)
from models.truthgpt_model import (
    TruthGPTBlock,
    TruthGPTForCausalLM,
    TruthGPTMLP,
    TruthGPTModel,
    TruthGPTModelConfig,
    TruthGPTSelfAttention,
    create_truthgpt_model,
    load_truthgpt_model,
    save_truthgpt_model,
)


class TestModelsModuleExportsAndLazyLoading(unittest.TestCase):
    """Test module exports, directory reflection, and lazy loader behavior."""

    def test_dir_and_all_contain_key_classes(self):
        dir_keys = dir(models)
        all_keys = models.__all__

        expected = [
            "ModelManager",
            "ModelBuilder",
            "create_model_builder",
            "PositionalEncoding",
            "RotaryPositionalEmbedding",
            "ALiBiPositionalEmbedding",
            "EfficientAttention",
            "AttentionOptimizer",
            "AttentionUtils",
            "DiffusionModelManager",
            "DiffusionManager",
            "HFTransformersModel",
            "HFLLM",
            "HFDiffusersModel",
            "HFDiffusion",
            "TruthGPTModelConfig",
            "TruthGPTModel",
            "TruthGPTForCausalLM",
            "create_truthgpt_model",
            "ModelRegistry",
            "MODEL_REGISTRY",
            "create_model",
            "build_model",
            "list_available_models",
            "get_model_info",
            "register_model",
            "ModelError",
            "ModelNotFoundError",
            "BaseModel",
            "BaseModelManager",
        ]

        for item in expected:
            self.assertIn(item, dir_keys, f"Missing {item} in dir(models)")
            self.assertIn(item, all_keys, f"Missing {item} in models.__all__")

    def test_lazy_attribute_access(self):
        self.assertIsNotNone(models.ModelManager)
        self.assertIsNotNone(models.ModelBuilder)
        self.assertIsNotNone(models.PositionalEncoding)
        self.assertIsNotNone(models.RotaryPositionalEmbedding)
        self.assertIsNotNone(models.ALiBiPositionalEmbedding)
        self.assertIsNotNone(models.EfficientAttention)
        self.assertIsNotNone(models.DiffusionModelManager)
        self.assertIsNotNone(models.HFTransformersModel)
        self.assertIsNotNone(models.HFDiffusersModel)
        self.assertIsNotNone(models.TruthGPTModelConfig)

    def test_invalid_attribute_raises_attribute_error(self):
        with self.assertRaises(AttributeError):
            _ = models.NonExistentModelClassXYZ


class TestModelsExceptionsHierarchy(unittest.TestCase):
    """Verify exception hierarchy inheritance and formatting."""

    def test_exception_inheritance(self):
        self.assertTrue(issubclass(ModelNotFoundError, ModelError))
        self.assertTrue(issubclass(ModelInitializationError, ModelError))
        self.assertTrue(issubclass(ModelLoadError, ModelError))
        self.assertTrue(issubclass(ModelSaveError, ModelError))
        self.assertTrue(issubclass(ModelInferenceError, ModelError))
        self.assertTrue(issubclass(ModelConfigurationError, ModelError))
        self.assertTrue(issubclass(ModelOptimizationError, ModelError))
        self.assertTrue(issubclass(DevicePlacementError, ModelError))
        self.assertTrue(issubclass(QuantizationError, ModelOptimizationError))
        self.assertTrue(issubclass(AttentionError, ModelOptimizationError))
        self.assertTrue(issubclass(DiffusionError, ModelError))

    def test_exception_formatting_and_details(self):
        err = ModelNotFoundError(
            message="Check model path",
            model_name="truthgpt-7b",
            details={"path": "/models/tgpt"},
        )
        self.assertIn("Check model path", str(err))
        self.assertIn("truthgpt-7b", str(err))
        self.assertEqual(err.details["path"], "/models/tgpt")


class TestModelsInterfacesAndSchemas(unittest.TestCase):
    """Verify protocols, abstract base classes, and Pydantic schemas."""

    def test_pydantic_schemas(self):
        info = ModelInfoResult(
            model_type="causal_lm",
            model_name="truthgpt-tiny",
            device="cpu",
            num_parameters=1000000,
            trainable_parameters=1000000,
            memory_footprint_mb=4.0,
        )
        self.assertEqual(info.model_type, "causal_lm")
        self.assertEqual(info.num_parameters, 1000000)

        gen_cfg = GenerationConfig(
            max_new_tokens=100,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
        )
        self.assertEqual(gen_cfg.max_new_tokens, 100)
        self.assertEqual(gen_cfg.temperature, 0.7)

        load_res = ModelLoadResult(
            model_name="test-model",
            model_type="transformer",
            device="cpu",
            load_time_seconds=0.05,
        )
        self.assertTrue(load_res.success)

        save_res = ModelSaveResult(
            save_path="/tmp/saved_model",
            saved_tokenizer=True,
        )
        self.assertTrue(save_res.saved_tokenizer)

    def test_base_model_subclass(self):
        class DummyModel(BaseModel):
            def load(self, cfg: Dict[str, Any]) -> None:
                self.loaded = True

            def infer(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                return {"result": inputs.get("text", "") + " output"}

        m = DummyModel(config={"test": 123})
        m.load({})
        self.assertTrue(m.loaded)
        out = m.infer({"text": "hello"})
        self.assertEqual(out["result"], "hello output")
        info = m.get_info()
        self.assertEqual(info["model_class"], "DummyModel")


class TestModelRegistryAndFactory(unittest.TestCase):
    """Test registry operations, decorator registration, querying, and factory dispatch."""

    def test_registry_contains_default_models(self):
        available = list_available_models()
        self.assertIn("manager", available)
        self.assertIn("builder", available)
        self.assertIn("diffusion", available)
        self.assertIn("hf_transformers", available)
        self.assertIn("hf_diffusers", available)
        self.assertIn("truthgpt", available)

    def test_get_model_info(self):
        info = get_model_info("manager")
        self.assertEqual(info["type"], "manager")
        self.assertIn("ModelManager", info["class"])

        info_builder = get_model_info("builder")
        self.assertEqual(info_builder["type"], "builder")

    def test_custom_model_registration(self):
        registry = ModelRegistry()

        @registry.register_decorator("custom_agent_model", aliases=["cam", "custom_cam"])
        class CustomAgentModel:
            def __init__(self, config=None):
                self.config = config or {}

        self.assertIn("custom_agent_model", registry.list_available())
        inst1 = registry.create("custom_agent_model", config={"mode": "fast"})
        self.assertEqual(inst1.config["mode"], "fast")

        inst2 = registry.create("cam", config={"mode": "accurate"})
        self.assertEqual(inst2.config["mode"], "accurate")

    def test_unknown_model_raises_model_not_found(self):
        with self.assertRaises(ModelNotFoundError):
            create_model("non_existent_super_model_999")

    def test_create_model_and_build_model_aliases(self):
        builder1 = create_model("builder")
        self.assertIsInstance(builder1, ModelBuilder)

        builder2 = build_model("builder")
        self.assertIsInstance(builder2, ModelBuilder)


class TestModelBuilder(unittest.TestCase):
    """Verify fluent builder methods and configuration building."""

    def test_builder_fluent_chaining(self):
        builder = (
            create_model_builder()
            .with_model_name("gpt2")
            .with_dtype("float16")
            .with_device("cpu")
            .with_gradient_checkpointing(True)
            .with_lora(enabled=True, r=8, alpha=16)
            .with_quantization(bits=4, quant_type="nf4")
            .with_attn_implementation("sdpa")
            .with_torch_compile(enabled=False)
            .with_multi_gpu(False)
            .with_device_settings(allow_tf32=True)
        )

        d = builder.to_dict()
        self.assertEqual(d["model_name"], "gpt2")
        self.assertEqual(d["torch_dtype"], "torch.float16")
        self.assertEqual(d["device"], "cpu")
        self.assertTrue(d["gradient_checkpointing"])
        self.assertEqual(d["lora_config"]["r"], 8)
        self.assertEqual(d["quantization_config"]["bits"], 4)
        self.assertEqual(d["attn_implementation"], "sdpa")

    def test_builder_with_config_dictionary(self):
        cfg = {
            "model_name": "meta-llama/Llama-3-8b",
            "dtype": "bfloat16",
            "lora": {"enabled": True, "r": 32, "alpha": 64},
            "gradient_checkpointing": True,
        }
        builder = create_model_builder(cfg)
        d = builder.to_dict()
        self.assertEqual(d["model_name"], "meta-llama/Llama-3-8b")
        self.assertEqual(d["torch_dtype"], "torch.bfloat16")
        self.assertEqual(d["lora_config"]["r"], 32)

    def test_builder_missing_model_name_raises_error(self):
        builder = ModelBuilder()
        with self.assertRaises(ModelConfigurationError):
            builder.build()


class TestModelManager(unittest.TestCase):
    """Verify ModelManager methods, device detection, quantization helper, and saving."""

    def setUp(self):
        self.manager = ModelManager()

    def test_get_model_device(self):
        linear = nn.Linear(10, 5)
        dev = self.manager.get_model_device(linear)
        self.assertEqual(dev.type, "cpu")

    def test_get_model_info(self):
        model = nn.Sequential(nn.Linear(64, 128), nn.ReLU(), nn.Linear(128, 10))
        info = self.manager.get_model_info(model)
        self.assertGreater(info["total_parameters"], 0)
        self.assertEqual(info["trainable_parameters"], info["total_parameters"])
        self.assertIn("estimated_memory_mb", info)

    def test_dtype_resolution(self):
        self.assertEqual(self.manager._resolve_dtype("fp16"), torch.float16)
        self.assertEqual(self.manager._resolve_dtype("bf16"), torch.bfloat16)
        self.assertEqual(self.manager._resolve_dtype("fp32"), torch.float32)
        self.assertEqual(self.manager._resolve_dtype(torch.float64), torch.float64)
        self.assertIsNone(self.manager._resolve_dtype(None))

    def test_save_model_fallback(self):
        model = nn.Linear(8, 4)
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "test_save")
            self.manager.save_model(model, save_path, metadata={"version": "1.0"})
            self.assertTrue(os.path.exists(save_path))
            self.assertTrue(
                os.path.exists(os.path.join(save_path, "pytorch_model.bin"))
                or os.path.exists(os.path.join(save_path, "model.safetensors"))
            )
            self.assertTrue(os.path.exists(os.path.join(save_path, "model_metadata.json")))


class TestAttentionUtilitiesAndPositionalEncodings(unittest.TestCase):
    """Verify sinusoidal PE, RoPE, ALiBi, EfficientAttention, and AttentionUtils."""

    def test_positional_encoding(self):
        pe = PositionalEncoding(d_model=64, max_len=128, dropout=0.0)
        x = torch.zeros(2, 32, 64)
        out = pe(x)
        self.assertEqual(out.shape, (2, 32, 64))
        # Should not be all zeros after adding PE
        self.assertFalse(torch.allclose(out, x))

    def test_rotary_positional_embedding(self):
        rope = RotaryPositionalEmbedding(dim=32, max_seq_len=256)
        q = torch.randn(2, 4, 16, 32)
        k = torch.randn(2, 4, 16, 32)
        rot_q, rot_k = rope(q, k)
        self.assertEqual(rot_q.shape, q.shape)
        self.assertEqual(rot_k.shape, k.shape)

    def test_rotary_scaling_dynamic_ntk(self):
        rope = RotaryPositionalEmbedding(
            dim=32,
            max_seq_len=64,
            scaling_type="dynamic_ntk",
            scaling_factor=2.0,
        )
        q = torch.randn(1, 2, 128, 32)
        k = torch.randn(1, 2, 128, 32)
        rot_q, rot_k = rope(q, k)
        self.assertEqual(rot_q.shape, (1, 2, 128, 32))

    def test_alibi_positional_embedding(self):
        alibi = ALiBiPositionalEmbedding(num_heads=8)
        bias = alibi(seq_len=32, device=torch.device("cpu"))
        self.assertEqual(bias.shape, (1, 8, 32, 32))
        # Diagonal should be 0, off-diagonal negative
        diag = torch.diagonal(bias[0, 0], 0)
        self.assertTrue(torch.allclose(diag, torch.zeros_like(diag)))

    def test_efficient_attention_forward(self):
        attn = EfficientAttention(dim=64, num_heads=4, attention_backend="torch")
        x = torch.randn(2, 16, 64)
        out = attn(x, causal=True)
        self.assertEqual(out.shape, (2, 16, 64))

    def test_efficient_attention_gqa(self):
        # 8 query heads, 2 KV heads (GQA)
        attn = EfficientAttention(dim=64, num_heads=8, num_kv_heads=2, attention_backend="torch")
        x = torch.randn(2, 12, 64)
        out = attn(x)
        self.assertEqual(out.shape, (2, 12, 64))

    def test_attention_utils(self):
        mask = AttentionUtils.compute_causal_mask(10)
        self.assertEqual(mask.shape, (10, 10))
        self.assertTrue(mask[0, 0])
        self.assertFalse(mask[0, 1])

        mem_mb = AttentionUtils.estimate_kv_cache_memory_mb(
            batch_size=4,
            max_seq_len=2048,
            num_layers=32,
            num_kv_heads=8,
            head_dim=128,
            dtype_bytes=2,
        )
        self.assertGreater(mem_mb, 0.0)

        flops = AttentionUtils.estimate_attention_flops(
            seq_len=512,
            d_model=768,
            num_heads=12,
        )
        self.assertGreater(flops, 0)


class TestDiffusionManager(unittest.TestCase):
    """Verify DiffusionModelManager and DiffusionTrainer."""

    def test_diffusion_manager_initialization(self):
        dm = DiffusionModelManager()
        self.assertIsNone(dm.pipeline)
        self.assertIsInstance(dm, BaseDiffusionManager)

        # Backward compatibility alias
        dm_alias = DiffusionManager()
        self.assertIsInstance(dm_alias, DiffusionModelManager)

    def test_diffusion_manager_generate_without_load_raises(self):
        dm = DiffusionModelManager()
        with self.assertRaises(DiffusionError):
            dm.generate(prompt="A beautiful sunset")


class TestHuggingFaceWrappers(unittest.TestCase):
    """Verify HFTransformersModel and HFDiffusersModel wrappers."""

    def test_hf_transformers_unloaded_infer_raises(self):
        model = HFTransformersModel()
        with self.assertRaises(ModelInferenceError):
            model.infer({"text": "Hello"})

    def test_hf_transformers_aliases_and_factory(self):
        self.assertEqual(HFLLM, HFTransformersModel)
        inst = create_hf_transformers_model()
        self.assertIsInstance(inst, HFTransformersModel)

    def test_hf_diffusers_unloaded_infer_raises(self):
        diff = HFDiffusersModel()
        with self.assertRaises(DiffusionError):
            diff.infer({"prompt": "A cat"})

    def test_hf_diffusers_aliases_and_factory(self):
        self.assertEqual(HFDiffusion, HFDiffusersModel)
        inst = create_hf_diffusers_model()
        self.assertIsInstance(inst, HFDiffusersModel)


class TestTruthGPTModelArchitecture(unittest.TestCase):
    """Verify native TruthGPT transformer architecture components."""

    def test_truthgpt_config(self):
        cfg = TruthGPTModelConfig(
            vocab_size=1000,
            hidden_size=128,
            num_layers=2,
            num_attention_heads=4,
            intermediate_size=256,
            max_position_embeddings=128,
        )
        d = cfg.to_dict()
        self.assertEqual(d["vocab_size"], 1000)
        self.assertEqual(d["hidden_size"], 128)

    def test_truthgpt_attention_and_block(self):
        cfg = TruthGPTModelConfig(
            vocab_size=1000,
            hidden_size=64,
            num_layers=2,
            num_attention_heads=4,
            intermediate_size=128,
            max_position_embeddings=64,
        )
        block = TruthGPTBlock(cfg)
        x = torch.randn(2, 8, 64)
        out = block(x)
        self.assertEqual(out.shape, (2, 8, 64))

    def test_truthgpt_causal_lm_forward_and_loss(self):
        cfg = TruthGPTModelConfig(
            vocab_size=500,
            hidden_size=64,
            num_layers=2,
            num_attention_heads=4,
            intermediate_size=128,
            max_position_embeddings=64,
        )
        model = create_truthgpt_model(cfg)

        input_ids = torch.randint(0, 500, (2, 16))
        out = model(input_ids)
        self.assertIn("logits", out)
        self.assertEqual(out["logits"].shape, (2, 16, 500))

        # With labels for cross entropy loss computation
        labels = input_ids.clone()
        out_loss = model(input_ids, labels=labels)
        self.assertIn("loss", out_loss)
        self.assertIsNotNone(out_loss["loss"])
        self.assertGreater(out_loss["loss"].item(), 0.0)

    def test_truthgpt_causal_lm_infer(self):
        cfg = TruthGPTModelConfig(
            vocab_size=200,
            hidden_size=32,
            num_layers=1,
            num_attention_heads=2,
            intermediate_size=64,
            max_position_embeddings=64,
        )
        model = create_truthgpt_model(cfg)
        input_ids = torch.randint(0, 200, (1, 4))
        res = model.infer({"input_ids": input_ids, "max_new_tokens": 3})
        self.assertIn("output_ids", res)
        self.assertEqual(res["output_ids"].shape, (1, 7))

    def test_save_and_load_truthgpt_model(self):
        cfg = TruthGPTModelConfig(
            vocab_size=200,
            hidden_size=32,
            num_layers=1,
            num_attention_heads=2,
            intermediate_size=64,
        )
        model1 = create_truthgpt_model(cfg)
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, "truthgpt_model.pt")
            save_truthgpt_model(model1, model_path)
            self.assertTrue(os.path.exists(model_path))

            model2 = load_truthgpt_model(model_path, config=cfg)
            # Check weights match
            for p1, p2 in zip(model1.parameters(), model2.parameters()):
                self.assertTrue(torch.allclose(p1, p2))


if __name__ == "__main__":
    unittest.main()
