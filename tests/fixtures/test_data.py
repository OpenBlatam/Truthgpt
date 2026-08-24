"""
Test data factory for generating synthetic datasets, tensors, and multi-backend test cases.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple
import torch
import numpy as np


class TestDataFactory:
    """Factory for creating reproducible test data, synthetic tensors, and test scenarios."""

    @staticmethod
    def set_seed(seed: int = 42) -> None:
        """Seed all RNGs for reproducible test data generation."""
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    @staticmethod
    def create_random_tensor(shape: Tuple[int, ...], dtype: torch.dtype = torch.float32) -> torch.Tensor:
        """Create random tensor with specified shape and dtype."""
        return torch.randn(shape, dtype=dtype)

    @staticmethod
    def create_attention_data(
        batch_size: int = 2,
        seq_len: int = 128,
        d_model: int = 512,
        dtype: torch.dtype = torch.float32,
    ) -> Dict[str, torch.Tensor]:
        """Create attention test data (query, key, value, and causal mask)."""
        return {
            'query': torch.randn(batch_size, seq_len, d_model, dtype=dtype),
            'key': torch.randn(batch_size, seq_len, d_model, dtype=dtype),
            'value': torch.randn(batch_size, seq_len, d_model, dtype=dtype),
            'mask': torch.ones(batch_size, seq_len, seq_len, dtype=torch.bool),
        }

    @staticmethod
    def create_mlp_data(
        batch_size: int = 2,
        seq_len: int = 128,
        d_model: int = 512,
        dtype: torch.dtype = torch.float32,
    ) -> torch.Tensor:
        """Create MLP input test data."""
        return torch.randn(batch_size, seq_len, d_model, dtype=dtype)

    @staticmethod
    def create_optimization_data(
        num_params: int = 1000,
        num_epochs: int = 10,
        batch_size: int = 32,
    ) -> Dict[str, Any]:
        """Create optimizer test trajectory data."""
        return {
            'parameters': [torch.randn(num_params, requires_grad=True)],
            'losses': [random.uniform(0.1, 10.0) for _ in range(num_epochs)],
            'gradients': [torch.randn(num_params) for _ in range(num_epochs)],
            'learning_rates': [0.001 * (0.9 ** i) for i in range(num_epochs)],
            'batch_size': batch_size,
        }

    @staticmethod
    def create_kv_cache_data(
        batch_size: int = 2,
        seq_len: int = 128,
        d_model: int = 512,
        num_layers: int = 6,
        dtype: torch.dtype = torch.float32,
    ) -> Dict[str, torch.Tensor]:
        """Create KV cache key/value state tensors."""
        return {
            'keys': torch.randn(batch_size, num_layers, seq_len, d_model, dtype=dtype),
            'values': torch.randn(batch_size, num_layers, seq_len, d_model, dtype=dtype),
            'positions': torch.arange(seq_len).unsqueeze(0).expand(batch_size, -1),
        }

    @staticmethod
    def create_transformer_data(
        batch_size: int = 2,
        seq_len: int = 128,
        d_model: int = 512,
        vocab_size: int = 10000,
    ) -> Dict[str, torch.Tensor]:
        """Create transformer test tokens and masks."""
        return {
            'input_ids': torch.randint(0, vocab_size, (batch_size, seq_len)),
            'attention_mask': torch.ones(batch_size, seq_len, dtype=torch.bool),
            'token_type_ids': torch.zeros(batch_size, seq_len, dtype=torch.long),
        }

    @staticmethod
    def create_quantization_data(
        tensor_shape: Tuple[int, ...] = (32, 128),
        num_bits: int = 8,
    ) -> Dict[str, Any]:
        """Create quantization calibration tensors."""
        return {
            'tensor': torch.randn(tensor_shape),
            'scale': torch.tensor(0.1),
            'zero_point': torch.tensor(0),
            'num_bits': num_bits,
            'quantized': torch.randint(0, 2**num_bits, tensor_shape, dtype=torch.uint8),
        }

    @staticmethod
    def create_text_samples(num_samples: int = 10) -> List[str]:
        """Generate synthetic text samples for NLP pipeline testing."""
        templates = [
            "The quick brown fox jumps over the lazy dog.",
            "Deep learning optimization and polyglot execution accelerate LLM training.",
            "FlashAttention and PagedAttention minimize activation memory overhead.",
            "TruthGPT unified optimization engine ensures maximum throughput.",
            "Gradient descent with momentum stabilizes model weight updates.",
        ]
        return [f"[{i}] {random.choice(templates)}" for i in range(num_samples)]

    @staticmethod
    def create_benchmark_data(
        model_sizes: Optional[List[Tuple[int, int, int]]] = None,
        sequence_lengths: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """Create benchmark matrix configurations."""
        model_sizes = model_sizes or [(512, 512, 2048), (1024, 1024, 4096)]
        sequence_lengths = sequence_lengths or [128, 256, 512]
        benchmark_data = []
        for d_model, hidden_size, vocab_size in model_sizes:
            for seq_len in sequence_lengths:
                benchmark_data.append({
                    'd_model': d_model,
                    'hidden_size': hidden_size,
                    'vocab_size': vocab_size,
                    'seq_len': seq_len,
                    'input_data': torch.randint(0, vocab_size, (2, seq_len)),
                    'expected_shape': (2, seq_len, d_model),
                })
        return benchmark_data

    @staticmethod
    def create_error_cases() -> List[Dict[str, Any]]:
        """Create structured error and corner case scenarios."""
        return [
            {
                'name': 'invalid_tensor_shape',
                'data': torch.randn(1, 2, 3, 4, 5),
                'expected_error': ValueError,
            },
            {
                'name': 'negative_dimensions',
                'data': torch.randn(-1, 128),
                'expected_error': RuntimeError,
            },
            {
                'name': 'mismatched_batch_sizes',
                'query': torch.randn(2, 128, 512),
                'key': torch.randn(3, 128, 512),
                'expected_error': RuntimeError,
            },
        ]

    @staticmethod
    def create_performance_data(
        sizes: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """Create performance benchmark matrices."""
        sizes = sizes or [128, 256, 512, 1024]
        performance_data = []
        for size in sizes:
            performance_data.append({
                'size': size,
                'tensor': torch.randn(size, size),
                'expected_time': size * size * 1e-6,
                'memory_usage': size * size * 4,
            })
        return performance_data


__all__ = ["TestDataFactory"]
