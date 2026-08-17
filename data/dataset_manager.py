"""
Dataset management module for loading and preprocessing datasets.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
from datasets import load_dataset, Dataset

from .utils.validators import validate_file_path, validate_positive_number

logger = logging.getLogger(__name__)


class DatasetManager:
    """Manages dataset loading from various sources."""
    
    def __init__(self, config: Optional[Union[Dict[str, Any], Any]] = None, **kwargs: Any):
        """
        Initialize DatasetManager instance with configuration.
        
        Args:
            config: Optional configuration dictionary or object
            **kwargs: Additional configuration parameters
        """
        if config is None:
            self.config = {}
        elif isinstance(config, dict):
            self.config = dict(config)
        elif hasattr(config, "to_dict"):
            self.config = config.to_dict()
        else:
            self.config = getattr(config, "__dict__", {})
        
        self.config.update(kwargs)
    
    def load(self, source: Optional[str] = None, **kwargs: Any) -> Tuple[List[str], List[str]]:
        """
        Instance method to load dataset using stored instance configuration.
        
        Args:
            source: Source type (hf|jsonl|text|parquet|csv|polars|tabular)
            **kwargs: Overriding arguments
        
        Returns:
            Tuple of (train_texts, val_texts)
        """
        merged_kwargs = dict(self.config)
        merged_kwargs.update(kwargs)
        
        src = source or merged_kwargs.pop("source", None) or merged_kwargs.pop("type", None) or "text"
        return self.load_dataset(source=src, **merged_kwargs)

    @staticmethod
    def load_hf_dataset(
        dataset_name: str,
        subset: Optional[str] = None,
        text_field: str = "text",
        streaming: bool = False,
        split: Optional[str] = None,
    ) -> Tuple[List[str], List[str]]:
        """
        Load dataset from HuggingFace.
        
        Args:
            dataset_name: Name of the dataset
            subset: Optional subset name
            text_field: Field containing text data
            streaming: Whether to use streaming
            split: Optional split specification (e.g., 'train', 'train[:80%]')
        
        Returns:
            Tuple of (train_texts, val_texts)
        """
        try:
            logger.info(f"Loading HuggingFace dataset: {dataset_name} (subset: {subset}, split: {split})")
            
            kwargs = {}
            if subset:
                kwargs["name"] = subset
            if split:
                kwargs["split"] = split
                
            ds = load_dataset(dataset_name, streaming=streaming, **kwargs)
            
            # Handle case where load_dataset returned a single Dataset (when split is passed)
            if hasattr(ds, text_field) or (hasattr(ds, "__getitem__") and not isinstance(ds, dict) and hasattr(ds, "column_names")):
                all_data = ds[text_field] if not streaming else ds
                if streaming:
                    all_list = list(all_data.take(5000))
                else:
                    all_list = list(all_data) if not isinstance(all_data, list) else all_data
                
                split_idx = int(len(all_list) * 0.9) if len(all_list) > 1 else len(all_list)
                return all_list[:split_idx], all_list[split_idx:]
            
            # Handle DatasetDict
            if "train" not in ds:
                raise ValueError(f"Dataset {dataset_name} does not contain 'train' split")
            
            # Get training data
            train_data = ds["train"][text_field] if not streaming else ds["train"]
            
            # Get validation data
            if "validation" in ds:
                val_data = ds["validation"][text_field] if not streaming else ds["validation"]
            elif "val" in ds:
                val_data = ds["val"][text_field] if not streaming else ds["val"]
            elif "test" in ds:
                val_data = ds["test"][text_field] if not streaming else ds["test"]
            else:
                logger.warning("No validation split found, using train split for validation")
                val_data = train_data
            
            # Convert to lists if not streaming
            if streaming:
                train_list = list(train_data.take(5000))
                val_list = list(val_data.take(500))
            else:
                train_list = list(train_data) if not isinstance(train_data, list) else train_data
                val_list = list(val_data) if not isinstance(val_data, list) else val_data
            
            logger.info(
                f"Loaded {len(train_list)} training samples and "
                f"{len(val_list)} validation samples"
            )
            return train_list, val_list
            
        except Exception as e:
            logger.error(f"Error loading HuggingFace dataset {dataset_name}: {e}", exc_info=True)
            raise
    
    @staticmethod
    def load_jsonl_dataset(
        path: Union[str, Path],
        text_field: str = "text",
        train_split: float = 0.9,
    ) -> Tuple[List[str], List[str]]:
        """
        Load dataset from JSONL file.
        
        Args:
            path: Path to JSONL file
            text_field: Field containing text data
            train_split: Ratio for train/val split
        
        Returns:
            Tuple of (train_texts, val_texts)
        """
        import json
        
        file_path = validate_file_path(path, must_exist=True)
        validate_positive_number(train_split, "train_split", min_value=0.0, max_value=1.0)
        
        try:
            logger.info(f"Loading JSONL dataset from {file_path}")
            
            texts = []
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    data = json.loads(line_str)
                    if text_field in data:
                        texts.append(data[text_field])
            
            # Split train/val
            split_idx = int(round(len(texts) * train_split)) if len(texts) > 1 else len(texts)
            train_texts = texts[:split_idx]
            val_texts = texts[split_idx:]
            
            logger.info(
                f"Loaded {len(train_texts)} training samples and "
                f"{len(val_texts)} validation samples"
            )
            return train_texts, val_texts
            
        except Exception as e:
            logger.error(f"Error loading JSONL dataset {path}: {e}", exc_info=True)
            raise
    
    @staticmethod
    def load_text_file(
        path: Union[str, Path],
        train_split: float = 0.9,
        chunk_size: Optional[int] = None,
    ) -> Tuple[List[str], List[str]]:
        """
        Load dataset from text file.
        
        Args:
            path: Path to text file
            train_split: Ratio for train/val split
            chunk_size: Optional chunk size for splitting large texts
        
        Returns:
            Tuple of (train_texts, val_texts)
        """
        file_path = validate_file_path(path, must_exist=True)
        validate_positive_number(train_split, "train_split", min_value=0.0, max_value=1.0)
        if chunk_size is not None:
            validate_positive_number(chunk_size, "chunk_size", min_value=1)

        try:
            logger.info(f"Loading text file from {file_path}")
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if chunk_size:
                # Split into chunks
                texts = [
                    content[i:i + chunk_size]
                    for i in range(0, len(content), chunk_size)
                ]
            else:
                # Split by paragraphs
                texts = [p.strip() for p in content.split("\n\n") if p.strip()]
            
            # Split train/val
            split_idx = int(round(len(texts) * train_split)) if len(texts) > 1 else len(texts)
            train_texts = texts[:split_idx]
            val_texts = texts[split_idx:]
            
            logger.info(
                f"Loaded {len(train_texts)} training samples and "
                f"{len(val_texts)} validation samples"
            )
            return train_texts, val_texts
            
        except Exception as e:
            logger.error(f"Error loading text file {path}: {e}", exc_info=True)
            raise

    @staticmethod
    def get_dataset_stats(texts: List[str]) -> dict:
        """
        Compute descriptive summary statistics for a dataset of text strings.
        
        Args:
            texts: List of text samples
            
        Returns:
            Dictionary containing total_samples, total_characters, min_length,
            max_length, mean_length, and std_length.
        """
        if not texts:
            return {
                "total_samples": 0,
                "total_characters": 0,
                "min_length": 0,
                "max_length": 0,
                "mean_length": 0.0,
                "std_length": 0.0,
            }
        
        lengths = [len(t) for t in texts]
        total_samples = len(lengths)
        total_chars = sum(lengths)
        min_len = min(lengths)
        max_len = max(lengths)
        mean_len = total_chars / total_samples
        
        variance = sum((l - mean_len) ** 2 for l in lengths) / total_samples if total_samples > 0 else 0.0
        std_len = variance ** 0.5
        
        return {
            "total_samples": total_samples,
            "total_characters": total_chars,
            "min_length": min_len,
            "max_length": max_len,
            "mean_length": round(mean_len, 2),
            "std_length": round(std_len, 2),
        }

    @staticmethod
    def load_tabular_dataset(
        path: Union[str, Path],
        text_field: str = "text",
        train_split: float = 0.9,
    ) -> Tuple[List[str], List[str]]:
        """
        Load tabular dataset (Parquet/CSV) using PolarsProcessor or fallback.
        
        Args:
            path: Path to Parquet or CSV file
            text_field: Column containing text data
            train_split: Ratio for train/val split
        
        Returns:
            Tuple of (train_texts, val_texts)
        """
        file_path = validate_file_path(path, must_exist=True)
        validate_positive_number(train_split, "train_split", min_value=0.0, max_value=1.0)
        
        from .processor_factory import create_data_processor, ProcessorType
        
        processor = create_data_processor(ProcessorType.AUTO, lazy=False)
        suffix = file_path.suffix.lower()
        
        if hasattr(processor, "read_parquet") and suffix in (".parquet", ".pq"):
            df = processor.read_parquet(file_path)
            if hasattr(df, "collect"):
                df = df.collect()
            if text_field not in df.columns:
                raise KeyError(f"Column '{text_field}' not found in tabular dataset {file_path}. Available columns: {list(df.columns)}")
            texts = df[text_field].to_list() if hasattr(df[text_field], "to_list") else df[text_field].tolist()
        elif hasattr(processor, "read_csv") and suffix in (".csv", ".tsv"):
            df = processor.read_csv(file_path)
            if hasattr(df, "collect"):
                df = df.collect()
            if text_field not in df.columns:
                raise KeyError(f"Column '{text_field}' not found in tabular dataset {file_path}. Available columns: {list(df.columns)}")
            texts = df[text_field].to_list() if hasattr(df[text_field], "to_list") else df[text_field].tolist()
        else:
            # Fallback
            import pandas as pd
            df = pd.read_parquet(file_path) if suffix in (".parquet", ".pq") else pd.read_csv(file_path)
            if text_field not in df.columns:
                raise KeyError(f"Column '{text_field}' not found in tabular dataset {file_path}. Available columns: {list(df.columns)}")
            texts = df[text_field].tolist()
        
        split_idx = int(round(len(texts) * train_split)) if len(texts) > 1 else len(texts)
        return texts[:split_idx], texts[split_idx:]

    @classmethod
    def load_parquet_dataset(
        cls,
        path: Union[str, Path],
        text_field: str = "text",
        train_split: float = 0.9,
    ) -> Tuple[List[str], List[str]]:
        """Explicit loader for Parquet files."""
        return cls.load_tabular_dataset(path=path, text_field=text_field, train_split=train_split)

    @classmethod
    def load_csv_dataset(
        cls,
        path: Union[str, Path],
        text_field: str = "text",
        train_split: float = 0.9,
    ) -> Tuple[List[str], List[str]]:
        """Explicit loader for CSV files."""
        return cls.load_tabular_dataset(path=path, text_field=text_field, train_split=train_split)

    @classmethod
    def load_dataset(
        cls,
        source: str,
        **kwargs
    ) -> Tuple[List[str], List[str]]:
        """
        Load dataset from any supported source.
        
        Args:
            source: Source type (hf|jsonl|text|parquet|csv|polars|tabular)
            **kwargs: Source-specific arguments
        
        Returns:
            Tuple of (train_texts, val_texts)
        """
        source_lower = source.lower()
        if source_lower in ("hf", "huggingface"):
            return cls.load_hf_dataset(**kwargs)
        elif source_lower in ("jsonl", "ndjson"):
            return cls.load_jsonl_dataset(**kwargs)
        elif source_lower in ("text", "txt"):
            return cls.load_text_file(**kwargs)
        elif source_lower in ("parquet", "pq"):
            return cls.load_parquet_dataset(**kwargs)
        elif source_lower in ("csv", "tsv"):
            return cls.load_csv_dataset(**kwargs)
        elif source_lower in ("polars", "tabular"):
            return cls.load_tabular_dataset(**kwargs)
        else:
            raise ValueError(
                f"Unsupported dataset source: '{source}'. "
                f"Supported sources: hf, jsonl, text, parquet, csv, polars, tabular."
            )





