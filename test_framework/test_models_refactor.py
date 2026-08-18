"""
Unit and Integration Tests for Optimization Core Models Refactoring
===================================================================
Tests registry discovery, fluent builders, managers, attention utilities,
TruthGPT native architectures, and backward compatibility.
"""

import pytest
import torch
import torch.nn as nn
from typing import Dict, Any

import models
from models import (
    MODEL_REGISTRY,
    register_model,
    list_available_models,
    get_model_info,
    create_model,
    build_model,
    ModelManager,
    ModelBuilder,
    DiffusionModelManager,
    DiffusionManager,
    HFTransformersModel,
    HFLLM,
    HFDiffusersModel,
    HFDiffusion,
    TruthGPTModel,
    TruthGPTModelConfig,
    TruthGPTConfig,
    create_truthgpt_model,
    PositionalEncoding,
    RotaryPositionalEmbedding,
    EfficientAttention,
    AttentionOptimizer,
    AttentionUtils,
    create_attention,
)


class TestModelRegistry:
    """Tests for model registration, metadata discovery, and factory dispatch."""

    def test_list_available_models(self):
        available = list_available_models()
        assert isinstance(available, list)
        assert "manager" in available
        assert "builder" in available
        assert "diffusion" in available
        assert "hf_transformers" in available
        assert "hf_diffusers" in available
        assert "truthgpt" in available

    def test_get_model_info(self):
        info = get_model_info("manager")
        assert info["type"] == "manager"
        assert info["class"] == "ModelManager"
        assert len(info["description"]) > 0

        info_tgpt = get_model_info("truthgpt")
        assert info_tgpt["type"] == "truthgpt"
        assert info_tgpt["class"] == "TruthGPTModel"

    def test_get_model_info_invalid(self):
        with pytest.raises(Exception):
            get_model_info("non_existent_model_type_xyz")

    def test_custom_registration(self):
        @register_model("custom_dummy_model", aliases=["custom_dummy"])
        class CustomDummyModel:
            def __init__(self, config=None):
                self.config = config or {}

        assert "custom_dummy_model" in list_available_models()
        instance = create_model("custom_dummy", {"test_key": 42})
        assert isinstance(instance, CustomDummyModel)
        assert instance.config.get("test_key") == 42


class TestTruthGPTModelArchitecture:
    """Tests for native TruthGPT transformer architecture."""

    def test_config_initialization(self):
        config = TruthGPTModelConfig(
            vocab_size=1000,
            hidden_size=64,
            num_layers=2,
            num_attention_heads=2,
            intermediate_size=128,
            max_position_embeddings=128,
        )
        assert config.hidden_size == 64
        cfg_dict = config.to_dict()
        assert cfg_dict["vocab_size"] == 1000
        assert cfg_dict["num_layers"] == 2

    def test_legacy_config_initialization(self):
        config = TruthGPTConfig(vocab_size=500, hidden_size=32)
        assert config.vocab_size == 500
        assert config.hidden_size == 32
        cfg_dict = config.to_dict()
        assert cfg_dict["vocab_size"] == 500

    def test_model_forward_pass(self):
        config = TruthGPTModelConfig(
            vocab_size=500,
            hidden_size=64,
            num_layers=2,
            num_attention_heads=4,
            intermediate_size=128,
            max_position_embeddings=64,
        )
        model = create_truthgpt_model(config)
        model.eval()

        batch_size = 2
        seq_len = 16
        input_ids = torch.randint(0, 500, (batch_size, seq_len))

        with torch.no_grad():
            logits = model(input_ids)

        assert logits.shape == (batch_size, seq_len, 500)
        assert model.num_parameters() > 0

    def test_model_size_reporting(self):
        config = TruthGPTModelConfig(
            vocab_size=100,
            hidden_size=32,
            num_layers=1,
            num_attention_heads=2,
            intermediate_size=64,
            max_position_embeddings=32,
        )
        model = TruthGPTModel(config)
        size_info = model.get_model_size()
        assert "total_parameters" in size_info
        assert "trainable_parameters" in size_info
        assert "model_size_mb" in size_info
        assert size_info["total_parameters"] > 0


class TestAttentionUtilities:
    """Tests for positional encoding and efficient attention mechanisms."""

    def test_positional_encoding(self):
        d_model = 64
        max_len = 128
        pe = PositionalEncoding(d_model=d_model, max_len=max_len, dropout=0.0)
        pe.eval()

        x = torch.zeros(32, 2, d_model)  # [seq_len, batch_size, d_model]
        out = pe(x)
        assert out.shape == (32, 2, d_model)

    def test_rotary_positional_embedding(self):
        head_dim = 32
        rope = RotaryPositionalEmbedding(dim=head_dim, max_seq_len=64)
        rope.eval()

        batch_size, num_heads, seq_len = 2, 4, 16
        q = torch.randn(batch_size, num_heads, seq_len, head_dim)
        k = torch.randn(batch_size, num_heads, seq_len, head_dim)

        q_rot, k_rot = rope(q, k)
        assert q_rot.shape == q.shape
        assert k_rot.shape == k.shape

    def test_efficient_attention_sdpa(self):
        dim = 64
        num_heads = 4
        attn = create_attention(dim=dim, num_heads=num_heads, attention_backend="sdpa")
        attn.eval()

        batch_size, seq_len = 2, 8
        x = torch.randn(batch_size, seq_len, dim)

        with torch.no_grad():
            out = attn(x)

        assert out.shape == (batch_size, seq_len, dim)

    def test_attention_utils_alias(self):
        assert AttentionUtils is AttentionOptimizer


class TestModelManagerAndBuilder:
    """Tests for ModelManager and ModelBuilder fluent construction."""

    def test_model_manager_instantiation(self):
        manager = ModelManager()
        assert hasattr(manager, "load_model")
        assert hasattr(manager, "save_model")
        assert hasattr(manager, "get_model_device")
        assert hasattr(manager, "enable_multi_gpu")
        assert hasattr(manager, "enable_torch_compile")
        assert hasattr(manager, "configure_device_settings")

    def test_model_builder_truthgpt(self):
        config = TruthGPTModelConfig(
            vocab_size=200,
            hidden_size=32,
            num_layers=1,
            num_attention_heads=2,
            intermediate_size=64,
            max_position_embeddings=32,
        )
        builder = (
            ModelBuilder()
            .with_truthgpt_config(config)
            .with_device_settings(allow_tf32=False)
        )
        model = builder.build()
        assert isinstance(model, TruthGPTModel)
        assert model.num_parameters() > 0

    def test_model_builder_missing_config_raises(self):
        builder = ModelBuilder()
        with pytest.raises(ValueError):
            builder.build()


class TestFactoryAndAliases:
    """Tests for unified create_model factory and backward-compatible aliases."""

    def test_create_manager(self):
        mgr = create_model("manager")
        assert isinstance(mgr, ModelManager)

    def test_create_builder(self):
        bld = create_model("builder")
        assert isinstance(bld, ModelBuilder)

    def test_create_diffusion(self):
        diff = create_model("diffusion")
        assert isinstance(diff, DiffusionModelManager)

    def test_aliases_consistency(self):
        assert DiffusionManager is DiffusionModelManager
        assert HFLLM is HFTransformersModel
        assert HFDiffusion is HFDiffusersModel
        assert build_model is create_model
