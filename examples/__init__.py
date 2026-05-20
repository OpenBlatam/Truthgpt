"""
Unified Examples System
=======================
Centralized access to all example scripts in optimization_core.
"""

# Example files are organized by category
# All examples can be run directly as scripts
# This module provides a registry and discovery system

import os
from pathlib import Path
from typing import Dict, List, Optional

# Get the examples directory
_EXAMPLES_DIR = Path(__file__).parent

# Registry of all available examples
EXAMPLE_REGISTRY: Dict[str, Dict[str, str]] = {
    "basic_usage": {
        "file": "basic_usage.py",
        "description": "Basic transformer usage example",
        "category": "basic",
    },
    "complete_workflow": {
        "file": "complete_workflow.py",
        "description": "Complete workflow demonstration",
        "category": "workflow",
    },
    "advanced_optimization": {
        "file": "advanced_optimization_example.py",
        "description": "Advanced optimization techniques",
        "category": "optimization",
    },
    "enhanced_optimization": {
        "file": "enhanced_optimization_example.py",
        "description": "Enhanced optimization example",
        "category": "optimization",
    },
    "extreme_optimization": {
        "file": "extreme_optimization_example.py",
        "description": "Extreme optimization example",
        "category": "optimization",
    },
    "complementary_optimization": {
        "file": "complementary_optimization_example.py",
        "description": "Complementary optimization example",
        "category": "optimization",
    },
    "modular_optimization": {
        "file": "modular_optimization_example.py",
        "description": "Modular optimization example",
        "category": "optimization",
    },
    "robust_optimization": {
        "file": "robust_optimization_example.py",
        "description": "Robust optimization example",
        "category": "optimization",
    },
    "modern_truthgpt": {
        "file": "modern_truthgpt_example.py",
        "description": "Modern TruthGPT example",
        "category": "truthgpt",
    },
    "supreme_truthgpt": {
        "file": "supreme_truthgpt_example.py",
        "description": "Supreme TruthGPT example",
        "category": "truthgpt",
    },
    "truthgpt_pytorch": {
        "file": "truthgpt_pytorch_example.py",
        "description": "TruthGPT PyTorch example",
        "category": "truthgpt",
    },
    "kv_cache_demo": {
        "file": "kv_cache_demo.py",
        "description": "KV cache demonstration",
        "category": "demo",
    },
    "ultra_kv_cache_demo": {
        "file": "ultra_kv_cache_demo.py",
        "description": "Ultra KV cache demonstration",
        "category": "demo",
    },
    "library_optimization_demo": {
        "file": "library_optimization_demo.py",
        "description": "Library optimization demonstration",
        "category": "demo",
    },
    "super_fast_optimization_demo": {
        "file": "super_fast_optimization_demo.py",
        "description": "Super fast optimization demonstration",
        "category": "demo",
    },
    "modular_inference": {
        "file": "modular_inference_example.py",
        "description": "Modular inference example",
        "category": "inference",
    },
    "modular_training": {
        "file": "modular_training_example.py",
        "description": "Modular training example",
        "category": "training",
    },
    "train_with_datasets": {
        "file": "train_with_datasets.py",
        "description": "Training with datasets example",
        "category": "training",
    },
    "switch_attention_backend": {
        "file": "switch_attention_backend.py",
        "description": "Switch attention backend example",
        "category": "attention",
    },
    "plugin_example": {
        "file": "plugin_example.py",
        "description": "Plugin system example",
        "category": "plugin",
    },
    "refactored_example": {
        "file": "refactored_example.py",
        "description": "Refactored system example",
        "category": "refactored",
    },
    "advanced_improvements": {
        "file": "advanced_improvements_example.py",
        "description": "Advanced improvements example",
        "category": "advanced",
    },
    "best_libraries": {
        "file": "best_libraries_example.py",
        "description": "Best libraries example",
        "category": "libraries",
    },
    "example_tensorflow_optimization": {
        "file": "example_tensorflow_optimization.py",
        "description": "TensorFlow optimization example",
        "category": "tensorflow",
    },
    "benchmark_tokens_per_sec": {
        "file": "benchmark_tokens_per_sec.py",
        "description": "Benchmark tokens per second",
        "category": "benchmark",
    },
    "gradio_interface": {
        "file": "gradio_interface.py",
        "description": "Gradio interface example",
        "category": "interface",
    },
}


def list_available_examples() -> List[str]:
    """List all available example names."""
    return list(EXAMPLE_REGISTRY.keys())


def list_examples_by_category(category: Optional[str] = None) -> List[str]:
    """
    List examples by category.
    
    Args:
        category: Optional category to filter by
    
    Returns:
        List of example names
    """
    if category is None:
        return list(EXAMPLE_REGISTRY.keys())
    
    return [
        name
        for name, info in EXAMPLE_REGISTRY.items()
        if info.get("category") == category
    ]


def get_example_info(example_name: str) -> Dict[str, str]:
    """
    Get information about a specific example.
    
    Args:
        example_name: Name of the example
    
    Returns:
        Dictionary with example information
    """
    if example_name not in EXAMPLE_REGISTRY:
        raise ValueError(f"Unknown example: {example_name}")
    
    info = EXAMPLE_REGISTRY[example_name].copy()
    info["path"] = str(_EXAMPLES_DIR / info["file"])
    info["exists"] = (_EXAMPLES_DIR / info["file"]).exists()
    return info


def get_example_path(example_name: str) -> Path:
    """
    Get the file path for an example.
    
    Args:
        example_name: Name of the example
    
    Returns:
        Path to the example file
    """
    if example_name not in EXAMPLE_REGISTRY:
        raise ValueError(f"Unknown example: {example_name}")
    
    return _EXAMPLES_DIR / EXAMPLE_REGISTRY[example_name]["file"]


def list_categories() -> List[str]:
    """List all available example categories."""
    categories = set()
    for info in EXAMPLE_REGISTRY.values():
        categories.add(info.get("category", "other"))
    return sorted(categories)


__all__ = [
    "EXAMPLE_REGISTRY",
    "list_available_examples",
    "list_examples_by_category",
    "get_example_info",
    "get_example_path",
    "list_categories",
]
