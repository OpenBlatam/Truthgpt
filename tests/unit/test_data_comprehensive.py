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
    DataLoaderBuilder,
    LengthBucketBatchSampler,
    LengthBucketSampler,
    BaseCollator,
    LMCollator,
    ClassificationCollator,
    BaseDataProcessor,
    PolarsProcessor,
    PandasProcessor,
    ProcessorType,
    create_data_processor,
    list_available_processors,
    DatasetRegistry,
    register_dataset,
    unregister_dataset,
    build_dataset,
    has_dataset,
    get_dataset_info,
    list_registered_datasets,
    get_dataset_builder,
    clear_dataset_registry,
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
        self.pad_token_id = 0
    
    def __call__(self, batch, padding=True, truncation=True, max_length=512, return_tensors="pt"):
        # Dummy encoding: string length as pseudo token IDs
        max_len = max(len(text) for text in batch) if batch else 0
        max_len = min(max_len, max_length)
        batch_size = len(batch)
        
        input_ids = torch.zeros((batch_size, max_len), dtype=torch.long)
        attention_mask = torch.ones((batch_size, max_len), dtype=torch.long)
        
        for i, text in enumerate(batch):
            tokens = [ord(c) % 100 + 1 for c in text[:max_len]]
            input_ids[i, :len(tokens)] = torch.tensor(tokens, dtype=torch.long)
            if len(tokens) < max_len:
                attention_mask[i, len(tokens):] = 0
                input_ids[i, len(tokens):] = self.pad_token_id
                
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }

    def encode(self, text, add_special_tokens=False):
        return [ord(c) % 100 + 1 for c in text]


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

    def test_get_dataset_stats(self):
        sample_texts = ["Hello world", "A longer sentence for testing statistics calculation", "Short"]
        stats = DatasetManager.get_dataset_stats(sample_texts)
        assert stats["total_samples"] == 3
        assert stats["total_characters"] == len("Hello world") + len("A longer sentence for testing statistics calculation") + len("Short")
        assert stats["min_length"] == 5
        assert stats["max_length"] == len("A longer sentence for testing statistics calculation")
        assert stats["mean_length"] > 0

        empty_stats = DatasetManager.get_dataset_stats([])
        assert empty_stats["total_samples"] == 0

    def test_load_dataset_dispatcher(self):
        with patch.object(DatasetManager, "load_text_file", return_value=(["a"], ["b"])) as mock_text:
            res = DatasetManager.load_dataset("text", path="dummy.txt")
            assert res == (["a"], ["b"])
            mock_text.assert_called_once_with(path="dummy.txt")

        with pytest.raises(ValueError, match="Unsupported dataset source"):
            DatasetManager.load_dataset("invalid_source")

    def test_instance_instantiation_and_load(self):
        mgr = DatasetManager(config={"train_split": 0.8}, source="text")
        assert mgr.config["train_split"] == 0.8
        assert mgr.config["source"] == "text"

        with patch.object(DatasetManager, "load_text_file", return_value=(["tr"], ["val"])) as mock_text:
            res = mgr.load(path="dummy.txt")
            assert res == (["tr"], ["val"])
            mock_text.assert_called_once_with(train_split=0.8, path="dummy.txt")


# ════════════════════════════════════════════════════════════════════════════════
# LM COLLATOR & DATA LOADER FACTORY TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestDataLoaderFactory:
    """Tests for LMCollator, DataLoaderBuilder and DataLoaderFactory."""

    def test_lm_collator(self):
        tokenizer = DummyTokenizer()
        collator = LMCollator(tokenizer=tokenizer, max_length=128, ignore_index=-100, pad_labels=True)
        
        batch = ["Hello world", "Short"]
        result = collator(batch)
        
        assert "input_ids" in result
        assert "attention_mask" in result
        assert "labels" in result
        assert result["input_ids"].shape == result["labels"].shape
        assert result["input_ids"].shape[0] == 2
        # Verify padded position in label has ignore_index (-100)
        assert (result["labels"] == -100).any()

    def test_lm_collator_options(self):
        tokenizer = DummyTokenizer()
        collator = LMCollator(
            tokenizer=tokenizer,
            max_length=64,
            truncation_side="left",
            text_key="input_text",
            label_key="target_ids"
        )
        batch = [{"input_text": "Sample text one"}, {"input_text": "Sample text two"}]
        result = collator(batch)
        assert "input_ids" in result
        assert "target_ids" in result
        assert result["target_ids"].shape[0] == 2

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

    def test_dataloader_builder(self):
        texts = ["Sample sentence A", "Sample sentence B", "Sample sentence C"]
        tokenizer = DummyTokenizer()

        builder = (
            DataLoaderBuilder()
            .with_texts(texts)
            .with_tokenizer(tokenizer)
            .with_batch_size(2)
            .with_max_length(32)
            .with_workers(num_workers=0)
            .with_pin_memory(False)
            .with_seed(42)
            .with_drop_last(False)
        )

        train_loader = builder.build_train()
        val_loader = builder.build_val()

        assert isinstance(train_loader, DataLoader)
        assert isinstance(val_loader, DataLoader)

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

        sampler = LengthBucketBatchSampler(
            texts=texts,
            tokenizer=tokenizer,
            batch_size=2,
            bucket_bins=[10, 30, 60],
            shuffle=False,
        )
        assert len(sampler) > 0
        batches = list(sampler)
        assert sum(len(b) for b in batches) == len(texts)

        train_loader = DataLoaderFactory.create_train_loader(
            texts=texts,
            tokenizer=tokenizer,
            max_length=64,
            batch_size=2,
            bucket_by_length=True,
            bucket_bins=[60, 10, 30],
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
        @register_dataset("mock_test_dataset", description="Mock dataset for test", tags=["test"])
        def dummy_builder(cfg):
            return "mock_train", "mock_val"

        assert has_dataset("mock_test_dataset") is True
        info = get_dataset_info("mock_test_dataset")
        assert info["description"] == "Mock dataset for test"
        assert info["tags"] == ["test"]

        result = build_dataset("mock_test_dataset", {})
        assert result == ("mock_train", "mock_val")
        assert "mock_test_dataset" in list_registered_datasets()
        assert get_dataset_builder("mock_test_dataset") is not None

        # Clean up
        assert unregister_dataset("mock_test_dataset") is True
        assert unregister_dataset("mock_test_dataset") is False
        assert has_dataset("mock_test_dataset") is False

    def test_register_dataset_bare_decorator(self):
        @register_dataset
        def my_custom_builder(cfg):
            return "train_data"

        assert build_dataset("my_custom_builder", {}) == "train_data"
        assert unregister_dataset("my_custom_builder") is True

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
        assert "data_loader_builder" in components
        assert "collator" in components
        assert "processor_factory" in components
        assert "polars_processor" in components

    def test_create_data_component_dataset_manager(self):
        comp = create_data_component("dataset_manager")
        assert isinstance(comp, DatasetManager)

    def test_create_data_component_data_loader_factory(self):
        comp = create_data_component("data_loader_factory")
        assert isinstance(comp, DataLoaderFactory)

    def test_create_data_component_data_loader_builder(self):
        comp = create_data_component("data_loader_builder")
        assert isinstance(comp, DataLoaderBuilder)

    def test_create_data_component_collator(self):
        tokenizer = DummyTokenizer()
        comp = create_data_component("collator", {"tokenizer": tokenizer, "max_length": 64})
        assert isinstance(comp, LMCollator)

    def test_create_data_component_classification_collator(self):
        tokenizer = DummyTokenizer()
        comp = create_data_component("classification_collator", {"tokenizer": tokenizer, "max_length": 64})
        assert isinstance(comp, ClassificationCollator)

    def test_create_data_component_dataset_registry(self):
        comp = create_data_component("dataset_registry")
        assert isinstance(comp, DatasetRegistry)

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

    def test_pandas_processor_adapter(self):
        import pandas as pd
        processor = PandasProcessor()
        assert isinstance(processor, BaseDataProcessor)
        
        # Test read/write parquet & csv with temp file
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("col1,col2\n1,a\n2,b\n")
            temp_csv = f.name

        try:
            df = processor.read_csv(temp_csv)
            assert len(df) == 2
            stats = processor.get_stats(df)
            assert stats["rows"] == 2
            assert stats["columns"] == 2
        finally:
            if os.path.exists(temp_csv):
                os.remove(temp_csv)

    def test_classification_collator(self):
        tokenizer = DummyTokenizer()
        collator = ClassificationCollator(tokenizer=tokenizer, max_length=32)
        batch = [
            {"text": "Sample classification text 1", "label": 1},
            {"text": "Sample text 2", "label": 0},
        ]
        res = collator(batch)
        assert "input_ids" in res
        assert "labels" in res
        assert torch.equal(res["labels"], torch.tensor([1, 0]))

    def test_dataset_registry_class_thread_safety(self):
        import threading

        registry = DatasetRegistry()
        
        def worker(i):
            @registry.register(f"ds_{i}")
            def builder(cfg):
                return f"result_{i}"

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        registered = registry.list_datasets()
        assert len(registered) == 10
        assert registry.build("ds_5") == "result_5"

    def test_length_bucket_sampler(self):
        texts = ["short", "a much longer text sentence for testing bucketing", "tiny", "medium length phrase"]
        tokenizer = DummyTokenizer()
        sampler = LengthBucketSampler(texts, tokenizer, batch_size=2)
        assert len(sampler) > 0
        batches = list(sampler)
        assert sum(len(b) for b in batches) == 4

    def test_pq_extension_validation(self):
        import pandas as pd
        df = pd.DataFrame({"text": ["hello", "world"]})
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pq") as f:
            pq_path = f.name
        try:
            df.to_parquet(pq_path)
            processor = PandasProcessor()
            res_df = processor.read_parquet(pq_path)
            assert len(res_df) == 2
            assert list(res_df["text"]) == ["hello", "world"]
        finally:
            if os.path.exists(pq_path):
                os.remove(pq_path)

    def test_load_tabular_dataset_csv_fallback(self):
        import pandas as pd
        df = pd.DataFrame({"text": ["train item 1", "train item 2", "val item 1"]})
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", newline="") as f:
            csv_path = f.name
        try:
            df.to_csv(csv_path, index=False)
            train_texts, val_texts = DatasetManager.load_tabular_dataset(csv_path, text_field="text", train_split=0.66)
            assert len(train_texts) == 2
            assert len(val_texts) == 1
            assert train_texts[0] == "train item 1"
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)




