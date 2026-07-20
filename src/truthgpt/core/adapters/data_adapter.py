"""
Data adapters for abstracting data loading implementations.
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)


class DataAdapter(ABC):
    """Base adapter for data operations."""
    
    @abstractmethod
    def load_data(self, source: str, **kwargs) -> Tuple[List[str], List[str]]:
        """Load training and validation data."""
        pass
    
    @abstractmethod
    def get_data_info(self, data: List[str]) -> Dict[str, Any]:
        """Get data information."""
        pass


class HuggingFaceDataAdapter(DataAdapter):
    """Adapter for HuggingFace datasets."""
    
    def load_data(self, source: str, **kwargs) -> Tuple[List[str], List[str]]:
        """Load data from HuggingFace."""
        from datasets import load_dataset
        
        dataset_name = kwargs.get("dataset_name", source)
        subset = kwargs.get("subset")
        text_field = kwargs.get("text_field", "text")
        streaming = kwargs.get("streaming", False)
        
        if subset:
            ds = load_dataset(dataset_name, subset, streaming=streaming)
        else:
            ds = load_dataset(dataset_name, streaming=streaming)
        
        train_data = ds["train"][text_field] if not streaming else ds["train"]
        
        if "validation" in ds:
            val_data = ds["validation"][text_field] if not streaming else ds["validation"]
        elif "val" in ds:
            val_data = ds["val"][text_field] if not streaming else ds["val"]
        else:
            val_data = train_data
        
        train_list = list(train_data) if not isinstance(train_data, list) else train_data
        val_list = list(val_data) if not isinstance(val_data, list) else val_data
        
        return train_list, val_list
    
    def get_data_info(self, data: List[str]) -> Dict[str, Any]:
        """Get data information."""
        return {
            "num_samples": len(data),
            "avg_length": sum(len(text.split()) for text in data) / len(data) if data else 0,
        }


class JSONLDataAdapter(DataAdapter):
    """Adapter for JSONL files."""
    
    def load_data(self, source: str, **kwargs) -> Tuple[List[str], List[str]]:
        """Load data from JSONL file."""
        import json
        
        text_field = kwargs.get("text_field", "text")
        train_split = kwargs.get("train_split", 0.9)
        
        texts = []
        with open(source, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line.strip())
                if text_field in data:
                    texts.append(data[text_field])
        
        split_idx = int(len(texts) * train_split)
        return texts[:split_idx], texts[split_idx:]
    
    def get_data_info(self, data: List[str]) -> Dict[str, Any]:
        """Get data information."""
        return {
            "num_samples": len(data),
            "avg_length": sum(len(text.split()) for text in data) / len(data) if data else 0,
        }


