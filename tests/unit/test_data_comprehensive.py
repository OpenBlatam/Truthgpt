"""
Comprehensive Unit Tests for optimization_core.data Module.

Tests cover:
- DatasetManager (JSONL, plain text, HuggingFace loading)
- DataLoaderFactory (train/val loader creation, length bucketing sampler)
- LMCollator (dynamic padding, token batching)
- Processor Factory & PolarsProcessor (data processor creation, availability)
- Dataset Registry (register_dataset, build_dataset)
- Unified Data Factory (create_data_component, list_available_data_components, get_data_component_info)
"""

import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock, patch

import torch
from torch.utils.data import DataLoader

from optimization_core.data import (
    DatasetManager,
    DataLoaderFactory,
    LMCollator,
    PolarsProcessor,
    ProcessorType,
    create_data_processor,
    list_available_processors,
    register_dataset,
    build_dataset,
    create_data_component,
    list_available_data_components,
    get_data_component_info,
    DATA_COMPONENT_REGISTRY,
)


class DummyTokenizer:
    """Mock tokenizer for testing collators and data loaders."""
    def __init__(self):
        self.pad_token = None
        self.eos_token = "<eos>"
    
    def __call__(self, batch, padding=True, truncation=True, max_length=512, return_tensors="pt"):
        # Dummy encoding: string length as pseudo token IDs
        max_len = max(len(text) for text in batch) if batch else 0
        max_len = min(max_len, max_length)
        batch_size = len(batch)
        
        input_ids = torch.zeros((batch_size, max_len), dtype=torch.long)
        attention_mask = torch.ones((batch_size, max_len), dtype=torch.long)
        
        for i, text in enumerate(batch):
            tokens = [ord(c) % 100 for c in text[:max_len]]
            input_ids[i, :len(tokens)] = torch.tensor(tokens, dtype=torch.long)
            if len(tokens) < max_len:
                attention_mask[i, len(tokens):] = 0
                
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }

    def encode(self, text, add_special_tokens=False):
        return [ord(c) % 100 for c in text]


# ════════════════════════════════════════════════════════════════════════════════
# DATASET MANAGER TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestDatasetManager:
    """Tests for DatasetManager class."""

    def test_load_text_file(self):
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
            f.write("Paragraph 1 line 1.\nParagraph 1 line 2.\n\nParagraph 2 line 1.\n\nParagraph 3.")
            temp_path = f.name
        
        try:
            train_texts, val_texts = DatasetManager.load_text_file(temp_path, train_split=0.7)
            assert len(train_texts) == 2
            assert len(val_texts) == 1
            assert "Paragraph 1" in train_texts[0]
            assert "Paragraph 3" in val_texts[0]
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_load_text_file_chunks(self):
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
            f.write("0123456789" * 10)  # 100 chars
            temp_path = f.name
        
        try:
            train_texts, val_texts = DatasetManager.load_text_file(temp_path, train_split=0.8, chunk_size=20)
            assert len(train_texts) + len(val_texts) == 5
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_load_jsonl_dataset(self):
        samples = [
            {"text": f"Sample string number {i}"} for i in range(10)
        ]
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".jsonl", encoding="utf-8") as f:
            for s in samples:
                f.write(json.dumps(s) + "\n")
            temp_path = f.name
        
        try:
            train_texts, val_texts = DatasetManager.load_jsonl_dataset(temp_path, text_field="text", train_split=0.8)
            assert len(train_texts) == 8
            assert len(val_texts) == 2
            assert train_texts[0] == "Sample string number 0"
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_load_dataset_dispatcher(self):
        with patch.object(DatasetManager, "load_text_file", return_value=(["a"], ["b"])) as mock_text:
            res = DatasetManager.load_dataset("text", path="dummy.txt")
            assert res == (["a"], ["b"])
            mock_text.assert_called_once_with(path="dummy.txt")

        with pytest.raises(ValueError, match="Unsupported dataset source"):
            DatasetManager.load_dataset("invalid_source")


# ════════════════════════════════════════════════════════════════════════════════
# LM COLLATOR & DATA LOADER FACTORY TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestDataLoaderFactory:
    """Tests for LMCollator and DataLoaderFactory."""

    def test_lm_collator(self):
        tokenizer = DummyTokenizer()
        collator = LMCollator(tokenizer=tokenizer, max_length=128)
        
        batch = ["Hello world", "Short text"]
        result = collator(batch)
        
        assert "input_ids" in result
        assert "attention_mask" in result
        assert "labels" in result
        assert result["input_ids"].shape == result["labels"].shape
        assert result["input_ids"].shape[0] == 2

    def test_create_loader_basic(self):
        texts = ["Text item 1", "Text item 2", "Text item 3", "Text item 4"]
        tokenizer = DummyTokenizer()
        collator = LMCollator(tokenizer, max_length=64)

        loader = DataLoaderFactory.create_loader(
            dataset=texts,
            batch_size=2,
            shuffle=False,
            collate_fn=collator,
            num_workers=0
        )
        assert isinstance(loader, DataLoader)
        batch = next(iter(loader))
        assert batch["input_ids"].shape[0] == 2

    def test_create_train_and_val_loader(self):
        texts = [f"Sample sentence number {i}" for i in range(10)]
        tokenizer = DummyTokenizer()

        train_loader = DataLoaderFactory.create_train_loader(
            texts=texts,
            tokenizer=tokenizer,
            max_length=64,
            batch_size=4,
            bucket_by_length=False,
            num_workers=0
        )
        assert isinstance(train_loader, DataLoader)
        
        val_loader = DataLoaderFactory.create_val_loader(
            texts=texts[:2],
            tokenizer=tokenizer,
            max_length=64,
            batch_size=2,
            num_workers=0
        )
        assert isinstance(val_loader, DataLoader)

    def test_length_bucket_sampler(self):
        texts = ["short", "a much longer text sentence for testing bucketing", "tiny", "medium length phrase"]
        tokenizer = DummyTokenizer()

        train_loader = DataLoaderFactory.create_train_loader(
            texts=texts,
            tokenizer=tokenizer,
            max_length=64,
            batch_size=2,
            bucket_by_length=True,
            bucket_bins=[10, 30, 60],
            num_workers=0
        )
        assert isinstance(train_loader, DataLoader)
        batches = list(train_loader)
        assert len(batches) > 0


# ════════════════════════════════════════════════════════════════════════════════
# PROCESSOR FACTORY & POLARS PROCESSOR TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestProcessorFactory:
    """Tests for processor_factory and PolarsProcessor."""

    def test_list_available_processors(self):
        available = list_available_processors()
        assert isinstance(available, dict)
        assert "polars" in available
        assert "pandas" in available

    def test_create_data_processor_auto(self):
        processor = create_data_processor(processor_type=ProcessorType.AUTO)
        assert processor is not None

    def test_create_data_processor_invalid(self):
        with pytest.raises(ValueError):
            create_data_processor(processor_type="invalid_processor_xyz")

    def test_polars_processor_init(self):
        try:
            import polars as pl
            processor = PolarsProcessor(lazy=True)
            assert processor is not None
        except ImportError:
            pytest.skip("Polars not installed")


# ════════════════════════════════════════════════════════════════════════════════
# DATASET REGISTRY TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestDatasetRegistry:
    """Tests for dataset registration and building."""

    def test_register_and_build(self):
        @register_dataset("mock_test_dataset")
        def dummy_builder(cfg):
            return "mock_train", "mock_val"

        result = build_dataset("mock_test_dataset", {})
        assert result == ("mock_train", "mock_val")

    def test_build_unregistered_fails(self):
        with pytest.raises(KeyError):
            build_dataset("non_existent_dataset_name_123", {})


# ════════════════════════════════════════════════════════════════════════════════
# UNIFIED DATA FACTORY TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestUnifiedDataFactory:
    """Tests for create_data_component and component registry functions."""

    def test_list_available_data_components(self):
        components = list_available_data_components()
        assert "dataset_manager" in components
        assert "data_loader_factory" in components
        assert "collator" in components
        assert "processor_factory" in components
        assert "polars_processor" in components

    def test_create_data_component_dataset_manager(self):
        comp = create_data_component("dataset_manager")
        assert isinstance(comp, DatasetManager)

    def test_create_data_component_data_loader_factory(self):
        comp = create_data_component("data_loader_factory")
        assert isinstance(comp, DataLoaderFactory)

    def test_create_data_component_collator(self):
        tokenizer = DummyTokenizer()
        comp = create_data_component("collator", {"tokenizer": tokenizer, "max_length": 64})
        assert isinstance(comp, LMCollator)

    def test_create_data_component_invalid(self):
        with pytest.raises(ValueError, match="Unknown data component type"):
            create_data_component("unknown_comp_type")

    def test_get_data_component_info(self):
        info = get_data_component_info("dataset_manager")
        assert info["name"] == "dataset_manager"
        assert info["module"] == "data.dataset_manager"

        with pytest.raises(ValueError):
            get_data_component_info("invalid_component_xyz")


# ════════════════════════════════════════════════════════════════════════════════
# VALIDATORS AND FILE UTILS TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestValidatorsAndFileUtils:
    """Tests for data module validation and file utility helper functions."""

    def test_validators(self):
        from optimization_core.data.utils.validators import (
            validate_non_empty_string,
            validate_positive_number,
            validate_dataframe_schema,
            ValidationError,
        )
        
        # String validation
        validate_non_empty_string("valid_name", "test_param")
        with pytest.raises(ValidationError):
            validate_non_empty_string("", "test_param")

        # Positive number validation
        validate_positive_number(10, "test_num", min_value=0, max_value=20)
        with pytest.raises(ValidationError):
            validate_positive_number(-1, "test_num", min_value=0)

        # DataFrame schema validation
        schema_dict = {"col1": "int", "col2": "str"}
        validate_dataframe_schema(schema_dict, ["col1"], "test_dict")
        with pytest.raises(ValidationError):
            validate_dataframe_schema(schema_dict, ["missing_col"], "test_dict")

    def test_file_utils(self):
        from optimization_core.data.utils.file_utils import (
            detect_file_format,
            validate_file_format,
            ensure_output_directory,
        )

        assert detect_file_format("data.parquet") == "parquet"
        assert detect_file_format("data.csv") == "csv"
        assert validate_file_format("sample.jsonl", allowed_formats={"jsonl", "csv"}) == "jsonl"
        
        with pytest.raises(ValueError):
            detect_file_format("file.unknown_extension_xyz")

